package co.climamedellin.cli;

import co.climamedellin.entities.Source;
import co.climamedellin.persistence.Database;
import co.climamedellin.persistence.RecordStore;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.PrintStream;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Set;

/**
 * {@code export --location <código> --source <fuente> --from <ISO> --to <ISO> --out <jsonl>
 * [--db <ruta>]}: escribe los registros del rango [from, to) para que Python los lea.
 */
final class ExportCommand {

    static final Set<String> OPTIONS = Set.of("db", "location", "source", "from", "to", "out");

    private ExportCommand() {
    }

    static ObjectNode run(Options options, PrintStream err) {
        String code = options.require("location");
        Source source = options.source();
        Instant from = options.instant("from");
        Instant to = options.instant("to");
        Path out = options.path("out");
        try (Database database = Database.open(options.db())) {
            RecordStore store = new RecordStore(database);
            List<ObjectNode> lines = source == Source.ERA5
                    ? store.findWeather(code, from, to).stream().map(JsonLines::line).toList()
                    : store.findAirQuality(code, from, to).stream().map(JsonLines::line).toList();
            int written = JsonLines.write(out, lines);
            err.println("[export] " + written + " registros de " + source);

            ObjectNode response = JsonLines.MAPPER.createObjectNode();
            response.put("file", out.toString());
            response.put("lines", written);
            return response;
        }
    }
}
