package co.climamedellin.cli;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CommandsTest {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final Instant T0 = Instant.parse("2026-03-01T00:00:00Z");
    private static final String META_ERA5 = """
            {"source":"ERA5","location":{"code":"MED-CENTRO","name":"Medellín – Centro",\
            "latitude":6.2447,"longitude":-75.5748,"elevation_m":1495,"timezone":"America/Bogota"},\
            "requested_start_utc":"2026-03-01T00:00:00Z","requested_end_utc":"2026-03-02T00:00:00Z",\
            "endpoint":"https://archive-api.open-meteo.com/v1/archive","params":{"models":"era5"}}""";
    private static final String META_CAMS = META_ERA5.replace("\"ERA5\"", "\"CAMS_GLOBAL\"");

    @TempDir
    Path tmp;

    private record Result(int exitCode, JsonNode json) {
    }

    private Result run(String... args) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        int code = Main.run(args, new PrintStream(out, true, StandardCharsets.UTF_8),
                new PrintStream(err, true, StandardCharsets.UTF_8));
        String[] lines = out.toString(StandardCharsets.UTF_8).strip().split("\\R");
        assertEquals(1, lines.length, "stdout debe tener exactamente una línea");
        return new Result(code, MAPPER.readTree(lines[0]));
    }

    private Path db() {
        return tmp.resolve("data/test.odb");
    }

    private static String era5Line(int hour, String temperature, String humidity, String wind) {
        return "{\"location_code\":\"MED-CENTRO\",\"source\":\"ERA5\",\"timestamp_utc\":\""
                + T0.plus(Duration.ofHours(hour)) + "\",\"temperature_2m_c\":" + temperature
                + ",\"relative_humidity_2m_pct\":" + humidity + ",\"wind_speed_10m_ms\":" + wind + "}";
    }

    private Path era5File(int hours) throws IOException {
        List<String> lines = new ArrayList<>();
        for (int h = 0; h < hours; h++) {
            lines.add(era5Line(h, String.valueOf(20 + h / 10.0), "80.5", h == 3 ? "null" : "1.25"));
        }
        return write("era5.jsonl", lines);
    }

    private Path write(String name, List<String> lines) throws IOException {
        Path file = tmp.resolve("staging").resolve(name);
        Files.createDirectories(file.getParent());
        Files.write(file, lines, StandardCharsets.UTF_8);
        return file;
    }

    private Result importFile(Path file, String meta) throws Exception {
        return run("import", "--db", db().toString(), "--file", file.toString(), "--meta", meta);
    }

    private Result coverage(String source) throws Exception {
        return run("coverage", "--db", db().toString(), "--location", "MED-CENTRO",
                "--source", source, "--out", tmp.resolve("exchange/coverage.jsonl").toString());
    }

    @Test
    void importStoresTheBatchAndReportsCounts() throws Exception {
        Result result = importFile(era5File(24), META_ERA5);

        assertEquals(0, result.exitCode());
        assertTrue(result.json().get("ok").asBoolean());
        assertEquals(24, result.json().get("received").asInt());
        assertEquals(24, result.json().get("inserted").asInt());
        assertEquals(0, result.json().get("duplicates").asInt());
        assertFalse(result.json().get("batch_id").asText().isBlank());
    }

    @Test
    void importingTheSameFileTwiceInsertsNothingTheSecondTime() throws Exception {
        Path file = era5File(24);
        importFile(file, META_ERA5);

        Result again = importFile(file, META_ERA5);

        assertEquals(0, again.exitCode());
        assertEquals(0, again.json().get("inserted").asInt());
        assertEquals(24, again.json().get("duplicates").asInt());
    }

    @Test
    void corruptLinesFailWithDataErrorAndLeaveTheDatabaseUnchanged() throws Exception {
        importFile(era5File(2), META_ERA5);
        List<String> corrupt = List.of(
                "{no es json",
                era5Line(5, "\"21\"", "80", "1"),
                era5Line(5, "21", "80", "1").replace("2026-03-01T05:00:00Z", "2026-03-01 05:00"),
                era5Line(5, "21", "80", "1").replace("\"ERA5\"", "\"CAMS_GLOBAL\""),
                era5Line(5, "21", "80", "1").replace("}", ",\"extra\":1}"));
        for (String bad : corrupt) {
            Path file = write("bad.jsonl", List.of(era5Line(10, "21", "80", "1"), bad));

            Result result = importFile(file, META_ERA5);

            assertEquals(2, result.exitCode(), bad);
            assertEquals("DATA", result.json().at("/error/type").asText());
            assertTrue(result.json().at("/error/message").asText().contains("Línea 2"), bad);
        }
        assertEquals(2, coverage("ERA5").json().get("count").asInt());
    }

    @Test
    void missingFileIsADataError() throws Exception {
        Result result = importFile(tmp.resolve("no-existe.jsonl"), META_ERA5);

        assertEquals(2, result.exitCode());
        assertEquals("DATA", result.json().at("/error/type").asText());
    }

    @Test
    void unknownOptionIsAUsageError() throws Exception {
        Result result = run("import", "--db", db().toString(), "--foo", "1");

        assertEquals(1, result.exitCode());
        assertTrue(result.json().at("/error/message").asText().contains("--foo"));
    }

    @Test
    void optionWithoutValueIsAUsageError() throws Exception {
        Result result = run("coverage", "--location");

        assertEquals(1, result.exitCode());
        assertEquals("USAGE", result.json().at("/error/type").asText());
    }

    @Test
    void invalidSourceIsAUsageError() throws Exception {
        Result result = run("coverage", "--location", "MED-CENTRO", "--source", "OTRA",
                "--out", tmp.resolve("c.jsonl").toString());

        assertEquals(1, result.exitCode());
        assertTrue(result.json().at("/error/message").asText().contains("OTRA"));
    }

    @Test
    void databasePathThatIsADirectoryIsADatabaseError() throws Exception {
        Path directory = Files.createDirectories(tmp.resolve("soy-un-directorio"));

        Result result = run("coverage", "--db", directory.toString(), "--location", "MED-CENTRO",
                "--source", "ERA5", "--out", tmp.resolve("c.jsonl").toString());

        assertEquals(3, result.exitCode());
        assertEquals("DATABASE", result.json().at("/error/type").asText());
    }

    @Test
    void coverageSummarizesAndListsNonNullVariables() throws Exception {
        importFile(era5File(5), META_ERA5);

        Result result = coverage("ERA5");

        assertEquals(0, result.exitCode());
        assertEquals(5, result.json().get("count").asInt());
        assertEquals(4, result.json().at("/non_null/wind_speed_10m_ms").asInt());
        assertEquals(5, result.json().at("/non_null/temperature_2m_c").asInt());
        assertEquals("2026-03-01T00:00:00Z", result.json().get("first").asText());
        assertEquals("2026-03-01T04:00:00Z", result.json().get("last").asText());
        List<String> lines = Files.readAllLines(tmp.resolve("exchange/coverage.jsonl"));
        assertEquals(5, lines.size());
        JsonNode fourth = MAPPER.readTree(lines.get(3));
        assertEquals("2026-03-01T03:00:00Z", fourth.get("timestamp_utc").asText());
        assertEquals("[\"temperature_2m_c\",\"relative_humidity_2m_pct\"]",
                fourth.get("non_null").toString());
    }

    @Test
    void coverageOfAnEmptyDatabase() throws Exception {
        Result result = coverage("CAMS_GLOBAL");

        assertEquals(0, result.exitCode());
        assertEquals(0, result.json().get("count").asInt());
        assertTrue(result.json().get("first").isNull());
        assertEquals(0, Files.readAllLines(tmp.resolve("exchange/coverage.jsonl")).size());
    }

    @Test
    void exportWritesTheHalfOpenRangeInOrderWithBatchId() throws Exception {
        Result imported = importFile(era5File(24), META_ERA5);
        Path out = tmp.resolve("exchange/export-ERA5.jsonl");

        Result result = run("export", "--db", db().toString(), "--location", "MED-CENTRO",
                "--source", "ERA5", "--from", "2026-03-01T05:00:00Z",
                "--to", "2026-03-01T15:00:00Z", "--out", out.toString());

        assertEquals(0, result.exitCode());
        assertEquals(10, result.json().get("lines").asInt());
        List<String> lines = Files.readAllLines(out);
        assertEquals(10, lines.size());
        JsonNode first = MAPPER.readTree(lines.get(0));
        assertEquals("2026-03-01T05:00:00Z", first.get("timestamp_utc").asText());
        assertEquals(20.5, first.get("temperature_2m_c").asDouble());
        assertEquals("MED-CENTRO", first.get("location_code").asText());
        assertEquals("ERA5", first.get("source").asText());
        assertEquals(imported.json().get("batch_id").asText(), first.get("batch_id").asText());
        assertEquals("2026-03-01T14:00:00Z",
                MAPPER.readTree(lines.get(9)).get("timestamp_utc").asText());
    }

    @Test
    void airQualityRoundTripKeepsNulls() throws Exception {
        Path file = write("cams.jsonl", List.of(
                "{\"location_code\":\"MED-CENTRO\",\"source\":\"CAMS_GLOBAL\","
                        + "\"timestamp_utc\":\"2026-03-01T00:00:00Z\",\"pm25_ug_m3\":12.3}",
                "{\"location_code\":\"MED-CENTRO\",\"source\":\"CAMS_GLOBAL\","
                        + "\"timestamp_utc\":\"2026-03-01T01:00:00Z\",\"pm25_ug_m3\":null}"));
        Result imported = importFile(file, META_CAMS);
        Path out = tmp.resolve("exchange/export-CAMS_GLOBAL.jsonl");

        run("export", "--db", db().toString(), "--location", "MED-CENTRO", "--source",
                "CAMS_GLOBAL", "--from", "2026-03-01T00:00:00Z", "--to", "2026-03-02T00:00:00Z",
                "--out", out.toString());

        assertEquals(1, imported.json().get("inserted").asInt());
        assertEquals(1, imported.json().get("rejected").asInt());
        List<String> lines = Files.readAllLines(out);
        assertEquals(1, lines.size());
        assertEquals(12.3, MAPPER.readTree(lines.get(0)).get("pm25_ug_m3").asDouble());
    }
}
