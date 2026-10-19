package co.climamedellin.persistence;

import co.climamedellin.entities.AirQualityRecord;
import co.climamedellin.entities.BatchType;
import co.climamedellin.entities.IngestionBatch;
import co.climamedellin.entities.Location;
import co.climamedellin.entities.Source;
import co.climamedellin.entities.WeatherRecord;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.TimeZone;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

class RecordStoreTest {

    private static final LocationData MED = new LocationData(
            "MED-CENTRO", "Medellín – Centro", 6.2447, -75.5748, 1495, "America/Bogota");
    private static final Instant T0 = Instant.parse("2026-03-01T13:00:00Z");

    @TempDir
    Path tmp;

    private Path dbFile;
    private Database database;
    private RecordStore store;
    private Location location;

    @BeforeEach
    void openDatabase() {
        dbFile = tmp.resolve("data").resolve("test.odb");
        database = Database.open(dbFile);
        store = new RecordStore(database);
        location = store.ensureLocation(MED);
    }

    @AfterEach
    void closeDatabase() {
        database.close();
    }

    private static Instant hour(int n) {
        return T0.plus(Duration.ofHours(n));
    }

    private static WeatherValues weather(int hour, Double t, Double rh, Double wind) {
        return new WeatherValues(hour(hour), t, rh, wind);
    }

    private static BatchInfo info() {
        return new BatchInfo(T0, T0.plus(Duration.ofDays(1)),
                "https://archive-api.open-meteo.com/v1/archive", "{\"models\":\"era5\"}", null);
    }

    private long countWeather() {
        EntityManager em = database.entityManager();
        try {
            return em.createQuery("SELECT COUNT(r) FROM WeatherRecord r", Long.class)
                    .getSingleResult();
        } finally {
            em.close();
        }
    }

    @Test
    void ensureLocationDoesNotDuplicateTheCode() {
        Location again = store.ensureLocation(MED);

        assertEquals(location.getId(), again.getId());
        EntityManager em = database.entityManager();
        try {
            long count = em.createQuery("SELECT COUNT(l) FROM Location l", Long.class)
                    .getSingleResult();
            assertEquals(1, count);
        } finally {
            em.close();
        }
    }

    @Test
    void duplicateWithinTheSameBatchIsCountedNotInserted() {
        InsertResult result = store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(0, 20.0, 80.0, 1.0),
                weather(0, 99.0, 99.0, 9.0),
                weather(1, 21.0, 78.0, 1.2)));

        assertEquals(3, result.received());
        assertEquals(2, result.inserted());
        assertEquals(1, result.duplicates());
        assertEquals(0, result.rejected());
        assertEquals(2, countWeather());
        WeatherRecord first = store.findWeather("MED-CENTRO", hour(0), hour(1)).get(0);
        assertEquals(20.0, first.getTemperature2mC());
    }

    @Test
    void duplicatesFromAnEarlierBatchKeepTheirValuesAndBatch() {
        InsertResult first = store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(0, 20.0, 80.0, 1.0),
                weather(1, 21.0, 78.0, 1.2),
                weather(2, 22.0, 75.0, 1.5)));

        InsertResult second = store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(1, 50.0, 10.0, 9.0),
                weather(2, 50.0, 10.0, 9.0),
                weather(3, 23.0, 70.0, 1.8),
                weather(4, 24.0, 68.0, 2.0)));

        assertEquals(2, second.inserted());
        assertEquals(2, second.duplicates());
        assertEquals(5, countWeather());
        List<WeatherRecord> records = store.findWeather("MED-CENTRO", hour(0), hour(5));
        assertEquals(21.0, records.get(1).getTemperature2mC());
        assertEquals(first.batchId(), records.get(1).getBatch().getBatchId());
        assertEquals(second.batchId(), records.get(3).getBatch().getBatchId());
    }

    @Test
    void rowsWithoutTimestampOrWithAllValuesNullAreRejected() {
        InsertResult result = store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(0, 20.0, 80.0, 1.0),
                new WeatherValues(null, 20.0, 80.0, 1.0),
                weather(1, null, null, null),
                weather(2, 22.0, null, null)));

        assertEquals(4, result.received());
        assertEquals(2, result.inserted());
        assertEquals(2, result.rejected());
        assertEquals(2, countWeather());
    }

    @Test
    void batchRecordsProvenanceAndCounts() {
        InsertResult result = store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(0, 20.0, 80.0, 1.0),
                weather(0, 20.0, 80.0, 1.0),
                weather(1, null, null, null)));

        EntityManager em = database.entityManager();
        try {
            IngestionBatch batch = em.createQuery(
                            "SELECT b FROM IngestionBatch b WHERE b.batchId = :id",
                            IngestionBatch.class)
                    .setParameter("id", result.batchId())
                    .getSingleResult();
            assertEquals(Source.ERA5, batch.getSource());
            assertEquals(BatchType.NORMAL, batch.getType());
            assertEquals("MED-CENTRO", batch.getLocation().getCode());
            assertEquals(T0, batch.getRequestedStartUtc());
            assertEquals("https://archive-api.open-meteo.com/v1/archive", batch.getEndpoint());
            assertNotNull(batch.getIngestedAtUtc());
            assertEquals(3, batch.getReceived());
            assertEquals(1, batch.getInserted());
            assertEquals(1, batch.getDuplicates());
            assertEquals(1, batch.getRejected());
        } finally {
            em.close();
        }
    }

    @Test
    void largeBatchIsCommittedInBlocksOf500() {
        List<WeatherValues> rows = new ArrayList<>();
        for (int i = 0; i < 1200; i++) {
            rows.add(weather(i, 20.0, 80.0, 1.0));
        }

        InsertResult result = store.insertWeather(location, Source.ERA5, info(), rows);

        assertEquals(1200, result.inserted());
        assertEquals(3, result.blocksCommitted());
        assertEquals(1200, countWeather());
    }

    @Test
    void databaseRejectsADuplicateNaturalKeyEvenWithoutTheService() {
        store.insertWeather(location, Source.ERA5, info(), List.of(weather(0, 20.0, 80.0, 1.0)));

        EntityManager em = database.entityManager();
        try {
            em.getTransaction().begin();
            Location managed = em.find(Location.class, location.getId());
            em.persist(new WeatherRecord(managed, Source.ERA5, hour(0), 1.0, 1.0, 1.0, null));
            assertThrows(PersistenceException.class, () -> em.getTransaction().commit());
        } finally {
            if (em.getTransaction().isActive()) {
                em.getTransaction().rollback();
            }
            em.close();
        }
        assertEquals(1, countWeather());
    }

    @Test
    void sameTimestampFromAnotherSourceIsNotADuplicate() {
        store.insertAirQuality(location, Source.CAMS_GLOBAL, info(),
                List.of(new AirQualityValues(hour(0), 12.5)));
        InsertResult again = store.insertAirQuality(location, Source.CAMS_GLOBAL, info(),
                List.of(new AirQualityValues(hour(0), 99.0), new AirQualityValues(hour(1), 8.0)));

        assertEquals(1, again.inserted());
        assertEquals(1, again.duplicates());
        List<AirQualityRecord> records = store.findAirQuality("MED-CENTRO", hour(0), hour(2));
        assertEquals(12.5, records.get(0).getPm25UgM3());
        assertEquals(Source.CAMS_GLOBAL, records.get(0).getSource());
    }

    @Test
    void nullValuesRoundTripAsNull() {
        store.insertWeather(location, Source.ERA5, info(), List.of(weather(0, 20.0, 80.0, null)));
        reopen();

        WeatherRecord record = store.findWeather("MED-CENTRO", hour(0), hour(1)).get(0);
        assertNull(record.getWindSpeed10mMs());
        assertEquals(80.0, record.getRelativeHumidity2mPct());
    }

    @Test
    void timestampRoundTripsExactlyInAnotherJvmTimeZone() {
        TimeZone original = TimeZone.getDefault();
        try {
            TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
            store.insertWeather(location, Source.ERA5, info(), List.of(weather(0, 20.0, 80.0, 1.0)));
            reopen();
            TimeZone.setDefault(TimeZone.getTimeZone("America/Bogota"));

            List<WeatherRecord> records = store.findWeather("MED-CENTRO",
                    Instant.parse("2026-03-01T00:00:00Z"), Instant.parse("2026-03-02T00:00:00Z"));
            assertEquals(Instant.parse("2026-03-01T13:00:00Z"), records.get(0).getTimestampUtc());
        } finally {
            TimeZone.setDefault(original);
        }
    }

    @Test
    void dataSurvivesClosingAndReopening() {
        store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(0, 20.0, 80.0, 1.0), weather(1, 21.0, 78.0, 1.2)));
        store.insertAirQuality(location, Source.CAMS_GLOBAL, info(),
                List.of(new AirQualityValues(hour(0), 10.0)));

        reopen();

        assertEquals(2, countWeather());
        assertEquals(1, store.summarizeAirQuality("MED-CENTRO").count());
        EntityManager em = database.entityManager();
        try {
            assertEquals(2L, em.createQuery("SELECT COUNT(b) FROM IngestionBatch b", Long.class)
                    .getSingleResult());
        } finally {
            em.close();
        }
    }

    @Test
    void findReturnsOnlyTheRangeOrderedByTime() {
        store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(5, 25.0, 60.0, 2.0),
                weather(1, 21.0, 78.0, 1.2),
                weather(3, 23.0, 70.0, 1.8),
                weather(0, 20.0, 80.0, 1.0),
                weather(4, 24.0, 68.0, 2.0)));

        List<WeatherRecord> records = store.findWeather("MED-CENTRO", hour(1), hour(5));

        assertEquals(List.of(hour(1), hour(3), hour(4)),
                records.stream().map(WeatherRecord::getTimestampUtc).toList());
        assertEquals(List.of(), store.findWeather("OTRA", hour(0), hour(10)));
    }

    @Test
    void summaryCountsRecordsNonNullValuesAndBounds() {
        store.insertWeather(location, Source.ERA5, info(), List.of(
                weather(2, 22.0, 75.0, null),
                weather(0, 20.0, null, null),
                weather(1, 21.0, 78.0, 1.2)));

        RecordSummary summary = store.summarizeWeather("MED-CENTRO");

        assertEquals(3, summary.count());
        assertEquals(3L, summary.nonNullByVariable().get("temperature_2m_c"));
        assertEquals(2L, summary.nonNullByVariable().get("relative_humidity_2m_pct"));
        assertEquals(1L, summary.nonNullByVariable().get("wind_speed_10m_ms"));
        assertEquals(hour(0), summary.first());
        assertEquals(hour(2), summary.last());
    }

    @Test
    void summaryOfAnEmptyDatabaseHasZeroCounts() {
        RecordSummary summary = store.summarizeAirQuality("MED-CENTRO");

        assertEquals(0, summary.count());
        assertEquals(0L, summary.nonNullByVariable().get("pm25_ug_m3"));
        assertNull(summary.first());
    }

    private void reopen() {
        database.close();
        database = Database.open(dbFile);
        store = new RecordStore(database);
        location = store.ensureLocation(MED);
    }
}
