package co.climamedellin.cli;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class MainTest {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    /** Resultado de una ejecución: código de salida y contenido de stdout. */
    private record Result(int exitCode, String stdout) {
    }

    private static Result execute(String... args) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        int code = Main.run(args,
                new PrintStream(out, true, StandardCharsets.UTF_8),
                new PrintStream(err, true, StandardCharsets.UTF_8));
        return new Result(code, out.toString(StandardCharsets.UTF_8));
    }

    /** Comprueba que stdout tiene exactamente una línea y que es un objeto JSON. */
    private static JsonNode singleJsonObject(String stdout) throws Exception {
        String[] lines = stdout.strip().split("\\R");
        assertEquals(1, lines.length, "stdout debe tener una sola línea");
        JsonNode node = MAPPER.readTree(lines[0]);
        assertTrue(node.isObject(), "stdout debe ser un objeto JSON");
        return node;
    }

    @Test
    void noArgumentsReturnsUsageError() throws Exception {
        Result result = execute();

        assertEquals(Main.EXIT_USAGE, result.exitCode());
        JsonNode json = singleJsonObject(result.stdout());
        assertFalse(json.get("ok").asBoolean());
        assertEquals("USAGE", json.at("/error/type").asText());
        assertFalse(json.at("/error/message").asText().isBlank());
    }

    @Test
    void unknownSubcommandReturnsUsageErrorMentioningIt() throws Exception {
        Result result = execute("foo");

        assertEquals(Main.EXIT_USAGE, result.exitCode());
        JsonNode json = singleJsonObject(result.stdout());
        assertFalse(json.get("ok").asBoolean());
        assertEquals("USAGE", json.at("/error/type").asText());
        assertTrue(json.at("/error/message").asText().contains("foo"));
    }
}
