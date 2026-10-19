package co.climamedellin.cli;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.persistence.PersistenceException;

import java.io.PrintStream;

/**
 * Punto de entrada del JAR de persistencia.
 *
 * <p>Contrato con Python: stdout recibe exactamente un objeto JSON por ejecución y
 * stderr recibe los mensajes de registro. El código de salida indica el tipo de
 * resultado (0 éxito, 1 uso, 2 datos, 3 base de datos, 4 inesperado).
 */
public final class Main {

    /** Códigos de salida acordados con Python (DP-05). */
    public static final int EXIT_OK = 0;
    public static final int EXIT_USAGE = 1;
    public static final int EXIT_DATA = 2;
    public static final int EXIT_DATABASE = 3;
    public static final int EXIT_UNEXPECTED = 4;

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private Main() {
    }

    public static void main(String[] args) {
        System.exit(run(args, System.out, System.err));
    }

    /**
     * Ejecuta el subcomando pedido y devuelve el código de salida.
     * Separado de {@link #main} para poder probarlo sin lanzar un proceso.
     */
    public static int run(String[] args, PrintStream out, PrintStream err) {
        if (args.length == 0) {
            return fail(out, EXIT_USAGE, "USAGE",
                    "Falta el subcomando. Uso: java -jar clima-medellin.jar <subcomando> [opciones]");
        }
        String command = args[0];
        try {
            ObjectNode response = switch (command) {
                case "import" -> ImportCommand.run(Options.parse(args, ImportCommand.OPTIONS), err);
                case "coverage" ->
                        CoverageCommand.run(Options.parse(args, CoverageCommand.OPTIONS), err);
                case "export" -> ExportCommand.run(Options.parse(args, ExportCommand.OPTIONS), err);
                default -> throw new UsageException("Subcomando desconocido: " + command);
            };
            return succeed(out, response);
        } catch (UsageException e) {
            return fail(out, EXIT_USAGE, "USAGE", e.getMessage());
        } catch (DataException e) {
            return fail(out, EXIT_DATA, "DATA", e.getMessage());
        } catch (PersistenceException e) {
            e.printStackTrace(err);
            return fail(out, EXIT_DATABASE, "DATABASE",
                    "No se pudo usar la base de datos: " + firstLine(e.getMessage()));
        } catch (RuntimeException e) {
            e.printStackTrace(err);
            return fail(out, EXIT_UNEXPECTED, "UNEXPECTED",
                    e.getClass().getSimpleName() + ": " + firstLine(e.getMessage()));
        }
    }

    /** Escribe en stdout la respuesta de éxito con "ok": true como primer campo. */
    static int succeed(PrintStream out, ObjectNode body) {
        ObjectNode response = MAPPER.createObjectNode();
        response.put("ok", true);
        response.setAll(body);
        out.println(response.toString());
        return EXIT_OK;
    }

    private static String firstLine(String message) {
        return message == null ? "" : message.lines().findFirst().orElse("");
    }

    /** Escribe en stdout el sobre JSON de error y devuelve el código de salida. */
    static int fail(PrintStream out, int exitCode, String type, String message) {
        ObjectNode response = MAPPER.createObjectNode();
        response.put("ok", false);
        ObjectNode error = response.putObject("error");
        error.put("type", type);
        error.put("message", message);
        out.println(response.toString());
        return exitCode;
    }
}
