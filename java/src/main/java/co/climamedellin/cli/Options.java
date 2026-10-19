package co.climamedellin.cli;

import co.climamedellin.entities.Source;
import java.nio.file.Path;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/** Opciones de un subcomando, escritas como pares «--nombre valor». */
final class Options {

    static final String DEFAULT_DB = "data/clima.odb";

    private final String command;
    private final Map<String, String> values;

    private Options(String command, Map<String, String> values) {
        this.command = command;
        this.values = values;
    }

    /** Lee las opciones que siguen al subcomando; solo admite las de {@code allowed}. */
    static Options parse(String[] args, Set<String> allowed) {
        String command = args[0];
        Map<String, String> values = new HashMap<>();
        for (int i = 1; i < args.length; i += 2) {
            String name = args[i];
            if (!name.startsWith("--") || !allowed.contains(name.substring(2))) {
                throw new UsageException("Opción desconocida para " + command + ": " + name);
            }
            if (i + 1 >= args.length) {
                throw new UsageException("Falta el valor de la opción " + name);
            }
            values.put(name.substring(2), args[i + 1]);
        }
        return new Options(command, values);
    }

    String require(String name) {
        String value = values.get(name);
        if (value == null) {
            throw new UsageException("Falta la opción obligatoria --" + name + " de " + command);
        }
        return value;
    }

    Path db() {
        return Path.of(values.getOrDefault("db", DEFAULT_DB));
    }

    Path path(String name) {
        return Path.of(require(name));
    }

    Source source() {
        String value = require("source");
        try {
            return Source.valueOf(value);
        } catch (IllegalArgumentException e) {
            throw new UsageException("Fuente desconocida: " + value + " (válidas: ERA5, CAMS_GLOBAL)");
        }
    }

    Instant instant(String name) {
        String value = require(name);
        try {
            return Instant.parse(value);
        } catch (DateTimeParseException e) {
            throw new UsageException("Fecha inválida en --" + name + ": " + value
                    + " (formato esperado: 2026-03-01T00:00:00Z)");
        }
    }
}
