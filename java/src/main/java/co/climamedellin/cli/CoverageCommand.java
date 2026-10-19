package co.climamedellin.cli;

import co.climamedellin.entities.AirQualityRecord;
import co.climamedellin.entities.Source;
import co.climamedellin.entities.WeatherRecord;
import co.climamedellin.persistence.Database;
import co.climamedellin.persistence.RecordStore;
import co.climamedellin.persistence.RecordSummary;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.PrintStream;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * {@code coverage --location <código> --source <fuente> --out <jsonl> [--db <ruta>]}:
 * resume lo guardado y lista cada timestamp con sus variables no nulas. Los cálculos de
 * cobertura (porcentajes, huecos, faltantes) los hace Python.
 */
final class CoverageCommand {

    static final Set<String> OPTIONS = Set.of("db", "location", "source", "out");

    /** Rango que abarca cualquier dato posible del proyecto. */
    private static final Instant MIN = Instant.parse("1900-01-01T00:00:00Z");
    private static final Instant MAX = Instant.parse("3000-01-01T00:00:00Z");

    private CoverageCommand() {
    }

    static ObjectNode run(Options options, PrintStream err) {
        String code = options.require("location");
        Source source = options.source();
        Path out = options.path("out");
        try (Database database = Database.open(options.db())) {
            RecordStore store = new RecordStore(database);
            RecordSummary summary;
            List<ObjectNode> lines = new ArrayList<>();
            if (source == Source.ERA5) {
                summary = store.summarizeWeather(code);
                for (WeatherRecord r : store.findWeather(code, MIN, MAX)) {
                    lines.add(line(r.getTimestampUtc(), Map.of(
                            JsonLines.TEMPERATURE, r.getTemperature2mC() != null,
                            JsonLines.HUMIDITY, r.getRelativeHumidity2mPct() != null,
                            JsonLines.WIND, r.getWindSpeed10mMs() != null), source));
                }
            } else {
                summary = store.summarizeAirQuality(code);
                for (AirQualityRecord r : store.findAirQuality(code, MIN, MAX)) {
                    lines.add(line(r.getTimestampUtc(),
                            Map.of(JsonLines.PM25, r.getPm25UgM3() != null), source));
                }
            }
            int written = JsonLines.write(out, lines);
            err.println("[coverage] " + written + " timestamps de " + source);

            ObjectNode response = JsonLines.MAPPER.createObjectNode();
            response.put("location", code);
            response.put("source", source.name());
            response.put("count", summary.count());
            ObjectNode nonNull = response.putObject("non_null");
            summary.nonNullByVariable().forEach(nonNull::put);
            response.put("first", summary.first() == null ? null : summary.first().toString());
            response.put("last", summary.last() == null ? null : summary.last().toString());
            response.put("file", out.toString());
            response.put("lines", written);
            return response;
        }
    }

    /** Línea de cobertura: el timestamp y la lista de variables con valor. */
    private static ObjectNode line(Instant timestamp, Map<String, Boolean> present,
                                   Source source) {
        ObjectNode node = JsonLines.MAPPER.createObjectNode();
        node.put(JsonLines.TIMESTAMP, timestamp.toString());
        ArrayNode nonNull = node.putArray("non_null");
        for (String variable : JsonLines.variables(source)) {
            if (present.get(variable)) {
                nonNull.add(variable);
            }
        }
        return node;
    }
}
