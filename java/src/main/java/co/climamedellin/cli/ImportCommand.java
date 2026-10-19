package co.climamedellin.cli;

import co.climamedellin.entities.Location;
import co.climamedellin.entities.Source;
import co.climamedellin.persistence.BatchInfo;
import co.climamedellin.persistence.Database;
import co.climamedellin.persistence.InsertResult;
import co.climamedellin.persistence.LocationData;
import co.climamedellin.persistence.RecordStore;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.PrintStream;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.List;
import java.util.Set;

/** {@code import --file <jsonl> --meta <json> [--db <ruta>]}: guarda un lote. */
final class ImportCommand {

    static final Set<String> OPTIONS = Set.of("db", "file", "meta");

    private ImportCommand() {
    }

    static ObjectNode run(Options options, PrintStream err) {
        JsonNode meta = parseMeta(options.require("meta"));
        Source source = sourceOf(meta);
        LocationData locationData = locationOf(meta.path("location"));
        BatchInfo info = new BatchInfo(
                instantOf(meta, "requested_start_utc"),
                instantOf(meta, "requested_end_utc"),
                textOf(meta, "endpoint"),
                meta.path("params").toString(),
                meta.path("notes").isTextual() ? meta.path("notes").asText() : null);

        // Primero se valida el archivo entero; la base solo se abre si todo es correcto.
        List<JsonLines.Row> rows = JsonLines.read(options.path("file"), source,
                locationData.code());
        err.println("[import] " + rows.size() + " líneas válidas de " + source);

        try (Database database = Database.open(options.db())) {
            RecordStore store = new RecordStore(database);
            Location location = store.ensureLocation(locationData);
            InsertResult result = source == Source.ERA5
                    ? store.insertWeather(location, source, info, JsonLines.toWeather(rows))
                    : store.insertAirQuality(location, source, info, JsonLines.toAirQuality(rows));
            ObjectNode response = JsonLines.MAPPER.createObjectNode();
            response.put("batch_id", result.batchId());
            response.put("received", result.received());
            response.put("inserted", result.inserted());
            response.put("duplicates", result.duplicates());
            response.put("rejected", result.rejected());
            return response;
        }
    }

    private static JsonNode parseMeta(String text) {
        try {
            JsonNode meta = JsonLines.MAPPER.readTree(text);
            if (meta == null || !meta.isObject()) {
                throw new UsageException("--meta debe ser un objeto JSON");
            }
            return meta;
        } catch (JsonProcessingException e) {
            throw new UsageException("--meta no es un JSON válido");
        }
    }

    private static Source sourceOf(JsonNode meta) {
        String value = textOf(meta, "source");
        try {
            return Source.valueOf(value);
        } catch (IllegalArgumentException e) {
            throw new UsageException("Fuente desconocida en --meta: " + value);
        }
    }

    private static LocationData locationOf(JsonNode node) {
        if (!node.isObject()) {
            throw new UsageException("Falta location en --meta");
        }
        return new LocationData(textOf(node, "code"), textOf(node, "name"),
                numberOf(node, "latitude"), numberOf(node, "longitude"),
                numberOf(node, "elevation_m"), textOf(node, "timezone"));
    }

    private static String textOf(JsonNode node, String field) {
        JsonNode value = node.path(field);
        if (!value.isTextual()) {
            throw new UsageException("Falta el texto " + field + " en --meta");
        }
        return value.asText();
    }

    private static double numberOf(JsonNode node, String field) {
        JsonNode value = node.path(field);
        if (!value.isNumber()) {
            throw new UsageException("Falta el número " + field + " en --meta");
        }
        return value.asDouble();
    }

    private static Instant instantOf(JsonNode node, String field) {
        String value = textOf(node, field);
        try {
            return Instant.parse(value);
        } catch (DateTimeParseException e) {
            throw new UsageException("Fecha inválida en --meta." + field + ": " + value);
        }
    }
}
