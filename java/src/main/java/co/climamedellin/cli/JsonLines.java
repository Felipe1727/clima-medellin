package co.climamedellin.cli;

import co.climamedellin.entities.AirQualityRecord;
import co.climamedellin.entities.Source;
import co.climamedellin.entities.WeatherRecord;
import co.climamedellin.persistence.AirQualityValues;
import co.climamedellin.persistence.WeatherValues;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

/** Lectura y escritura de los archivos JSON Lines de staging/ y exchange/. */
final class JsonLines {

    static final ObjectMapper MAPPER = new ObjectMapper();

    static final String LOCATION_CODE = "location_code";
    static final String SOURCE = "source";
    static final String TIMESTAMP = "timestamp_utc";
    static final String BATCH_ID = "batch_id";
    static final String TEMPERATURE = "temperature_2m_c";
    static final String HUMIDITY = "relative_humidity_2m_pct";
    static final String WIND = "wind_speed_10m_ms";
    static final String PM25 = "pm25_ug_m3";

    private JsonLines() {
    }

    /** Variables (campos con unidad) de cada fuente, en el orden en que se escriben. */
    static List<String> variables(Source source) {
        return source == Source.ERA5 ? List.of(TEMPERATURE, HUMIDITY, WIND) : List.of(PM25);
    }

    /** Una línea ya validada: su timestamp y sus valores en el orden de {@link #variables}. */
    record Row(Instant timestampUtc, List<Double> values) {
    }

    /**
     * Lee y valida todas las líneas antes de devolver nada, para que un archivo con una
     * sola línea corrupta no llegue a escribir en la base.
     */
    static List<Row> read(Path file, Source source, String locationCode) {
        List<String> lines;
        try {
            lines = Files.readAllLines(file, StandardCharsets.UTF_8);
        } catch (NoSuchFileException e) {
            throw new DataException("No existe el archivo del lote: " + file);
        } catch (IOException e) {
            throw new DataException("No se pudo leer el archivo del lote: " + file, e);
        }
        List<String> variables = variables(source);
        Set<String> allowed = new java.util.HashSet<>(variables);
        allowed.addAll(Set.of(LOCATION_CODE, SOURCE, TIMESTAMP));
        List<Row> rows = new ArrayList<>();
        for (int i = 0; i < lines.size(); i++) {
            String line = lines.get(i);
            if (line.isBlank()) {
                continue;
            }
            rows.add(parseLine(line, i + 1, source, locationCode, variables, allowed));
        }
        return rows;
    }

    private static Row parseLine(String line, int number, Source source, String locationCode,
                                 List<String> variables, Set<String> allowed) {
        JsonNode node;
        try {
            node = MAPPER.readTree(line);
        } catch (JsonProcessingException e) {
            throw new DataException("Línea " + number + ": no es un JSON válido");
        }
        if (node == null || !node.isObject()) {
            throw new DataException("Línea " + number + ": no es un objeto JSON");
        }
        for (Iterator<String> it = node.fieldNames(); it.hasNext(); ) {
            String field = it.next();
            if (!allowed.contains(field)) {
                throw new DataException("Línea " + number + ": campo desconocido " + field);
            }
        }
        if (!source.name().equals(node.path(SOURCE).asText(null))) {
            throw new DataException("Línea " + number + ": la fuente no es " + source);
        }
        if (!locationCode.equals(node.path(LOCATION_CODE).asText(null))) {
            throw new DataException("Línea " + number + ": la ubicación no es " + locationCode);
        }
        JsonNode ts = node.path(TIMESTAMP);
        Instant timestamp;
        try {
            if (!ts.isTextual() || !ts.asText().endsWith("Z")) {
                throw new DateTimeParseException("sin Z", ts.asText(), 0);
            }
            timestamp = Instant.parse(ts.asText());
        } catch (DateTimeParseException e) {
            throw new DataException("Línea " + number + ": timestamp_utc inválido: " + ts);
        }
        List<Double> values = new ArrayList<>();
        for (String variable : variables) {
            JsonNode value = node.path(variable);
            if (value.isMissingNode() || value.isNull()) {
                values.add(null);
            } else if (value.isNumber()) {
                values.add(value.asDouble());
            } else {
                throw new DataException("Línea " + number + ": " + variable
                        + " no es numérico ni null: " + value);
            }
        }
        return new Row(timestamp, values);
    }

    static List<WeatherValues> toWeather(List<Row> rows) {
        return rows.stream()
                .map(r -> new WeatherValues(r.timestampUtc(), r.values().get(0),
                        r.values().get(1), r.values().get(2)))
                .toList();
    }

    static List<AirQualityValues> toAirQuality(List<Row> rows) {
        return rows.stream()
                .map(r -> new AirQualityValues(r.timestampUtc(), r.values().get(0)))
                .toList();
    }

    /** Línea de exportación de un registro meteorológico. */
    static ObjectNode line(WeatherRecord r) {
        ObjectNode node = header(r.getLocation().getCode(), r.getSource(), r.getTimestampUtc());
        putNullable(node, TEMPERATURE, r.getTemperature2mC());
        putNullable(node, HUMIDITY, r.getRelativeHumidity2mPct());
        putNullable(node, WIND, r.getWindSpeed10mMs());
        node.put(BATCH_ID, r.getBatch() == null ? null : r.getBatch().getBatchId());
        return node;
    }

    /** Línea de exportación de un registro de calidad del aire. */
    static ObjectNode line(AirQualityRecord r) {
        ObjectNode node = header(r.getLocation().getCode(), r.getSource(), r.getTimestampUtc());
        putNullable(node, PM25, r.getPm25UgM3());
        node.put(BATCH_ID, r.getBatch() == null ? null : r.getBatch().getBatchId());
        return node;
    }

    private static ObjectNode header(String locationCode, Source source, Instant timestamp) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put(LOCATION_CODE, locationCode);
        node.put(SOURCE, source.name());
        node.put(TIMESTAMP, timestamp.toString());
        return node;
    }

    private static void putNullable(ObjectNode node, String field, Double value) {
        if (value == null) {
            node.putNull(field);
        } else {
            node.put(field, value);
        }
    }

    /** Escribe un objeto JSON por línea, creando el directorio si hace falta. */
    static int write(Path file, List<ObjectNode> nodes) {
        try {
            Path parent = file.toAbsolutePath().getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            try (BufferedWriter out = Files.newBufferedWriter(file, StandardCharsets.UTF_8)) {
                for (ObjectNode node : nodes) {
                    out.write(MAPPER.writeValueAsString(node));
                    out.write('\n');
                }
            }
            return nodes.size();
        } catch (IOException e) {
            throw new UncheckedIOException("No se pudo escribir " + file, e);
        }
    }
}
