package co.climamedellin.persistence;

import co.climamedellin.entities.AirQualityRecord;
import co.climamedellin.entities.IngestionBatch;
import co.climamedellin.entities.Location;
import co.climamedellin.entities.Source;
import co.climamedellin.entities.WeatherRecord;
import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityTransaction;
import jakarta.persistence.PersistenceException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.BiFunction;
import java.util.function.Function;
import java.util.function.Predicate;

/** Operaciones de persistencia: ubicaciones, inserción de lotes y consultas. */
public final class RecordStore {

    /** Máximo de registros por transacción. */
    public static final int BLOCK_SIZE = 500;

    private final Database database;

    public RecordStore(Database database) {
        this.database = database;
    }

    /** Devuelve la ubicación con ese código, creándola si todavía no existe. */
    public Location ensureLocation(LocationData data) {
        EntityManager em = database.entityManager();
        try {
            List<Location> found = em.createQuery(
                            "SELECT l FROM Location l WHERE l.code = :code", Location.class)
                    .setParameter("code", data.code())
                    .getResultList();
            if (!found.isEmpty()) {
                return found.get(0);
            }
            Location location = new Location(data.code(), data.name(), data.latitude(),
                    data.longitude(), data.elevationM(), data.timezone());
            em.getTransaction().begin();
            em.persist(location);
            em.getTransaction().commit();
            return location;
        } finally {
            em.close();
        }
    }

    /** Guarda un lote de meteorología (solo inserciones). */
    public InsertResult insertWeather(Location location, Source source, BatchInfo info,
                                      List<WeatherValues> rows) {
        return insert(WeatherRecord.class, location, source, info, rows,
                WeatherValues::timestampUtc, WeatherValues::allValuesNull,
                (row, ctx) -> new WeatherRecord(ctx.location(), source, row.timestampUtc(),
                        row.temperature2mC(), row.relativeHumidity2mPct(),
                        row.windSpeed10mMs(), ctx.batch()));
    }

    /** Guarda un lote de calidad del aire (solo inserciones). */
    public InsertResult insertAirQuality(Location location, Source source, BatchInfo info,
                                         List<AirQualityValues> rows) {
        return insert(AirQualityRecord.class, location, source, info, rows,
                AirQualityValues::timestampUtc, AirQualityValues::allValuesNull,
                (row, ctx) -> new AirQualityRecord(ctx.location(), source, row.timestampUtc(),
                        row.pm25UgM3(), ctx.batch()));
    }

    /** Ubicación y lote gestionados por el EntityManager actual. */
    private record Context(Location location, IngestionBatch batch) {
    }

    private <V, E> InsertResult insert(Class<E> entityClass, Location location, Source source,
                                       BatchInfo info, List<V> rows,
                                       Function<V, Instant> timestampOf,
                                       Predicate<V> allValuesNull,
                                       BiFunction<V, Context, E> toEntity) {
        EntityManager em = database.entityManager();
        try {
            // 1. El lote se guarda primero, para que cada registro pueda apuntar a él.
            IngestionBatch batch = new IngestionBatch(UUID.randomUUID().toString(), source,
                    em.find(Location.class, location.getId()), info.requestedStartUtc(),
                    info.requestedEndUtc(), Instant.now(), info.endpoint(), info.params(),
                    info.notes());
            em.getTransaction().begin();
            em.persist(batch);
            em.getTransaction().commit();
            long batchId = batch.getId();

            // 2. Rechazos: sin timestamp o con todas las variables a null (DP-12).
            int rejected = 0;
            List<V> valid = new ArrayList<>();
            for (V row : rows) {
                if (timestampOf.apply(row) == null || allValuesNull.test(row)) {
                    rejected++;
                } else {
                    valid.add(row);
                }
            }

            // 3. Claves que ya existen en la base para el rango del lote.
            Set<Instant> seen = existingTimestamps(em, entityClass, location, source, valid,
                    timestampOf);

            // 4. Duplicados (en la base o dentro del propio lote) y bloques de inserción.
            int duplicates = 0;
            List<V> pending = new ArrayList<>();
            for (V row : valid) {
                if (seen.add(timestampOf.apply(row))) {
                    pending.add(row);
                } else {
                    duplicates++;
                }
            }

            int inserted = 0;
            int blocks = 0;
            for (int start = 0; start < pending.size(); start += BLOCK_SIZE) {
                List<V> block = pending.subList(start, Math.min(start + BLOCK_SIZE, pending.size()));
                int ok = commitBlock(em, location, batchId, block, toEntity);
                if (ok == block.size()) {
                    blocks++;
                    inserted += ok;
                } else {
                    // 6. El bloque falló: se reintenta registro a registro.
                    int retried = commitOneByOne(em, location, batchId, block, toEntity);
                    inserted += retried;
                    rejected += block.size() - retried;
                }
            }

            // 7. Conteos finales del lote.
            em.getTransaction().begin();
            IngestionBatch managed = em.find(IngestionBatch.class, batchId);
            managed.setCounts(rows.size(), inserted, duplicates, rejected);
            em.getTransaction().commit();
            return new InsertResult(managed.getBatchId(), rows.size(), inserted, duplicates,
                    rejected, blocks);
        } finally {
            if (em.getTransaction().isActive()) {
                em.getTransaction().rollback();
            }
            em.close();
        }
    }

    private <V, E> Set<Instant> existingTimestamps(EntityManager em, Class<E> entityClass,
                                                   Location location, Source source,
                                                   List<V> rows,
                                                   Function<V, Instant> timestampOf) {
        Set<Instant> existing = new HashSet<>();
        if (rows.isEmpty()) {
            return existing;
        }
        Instant min = rows.stream().map(timestampOf).min(Instant::compareTo).orElseThrow();
        Instant max = rows.stream().map(timestampOf).max(Instant::compareTo).orElseThrow();
        String jpql = "SELECT r.timestampUtc FROM " + entityClass.getSimpleName() + " r"
                + " WHERE r.location.id = :loc AND r.source = :source"
                + " AND r.timestampUtc >= :min AND r.timestampUtc <= :max";
        existing.addAll(em.createQuery(jpql, Instant.class)
                .setParameter("loc", location.getId())
                .setParameter("source", source)
                .setParameter("min", min)
                .setParameter("max", max)
                .getResultList());
        return existing;
    }

    /** Confirma un bloque en una sola transacción; devuelve los insertados (0 si falla). */
    private <V, E> int commitBlock(EntityManager em, Location location, long batchId,
                                   List<V> block, BiFunction<V, Context, E> toEntity) {
        EntityTransaction tx = em.getTransaction();
        try {
            tx.begin();
            Context ctx = managedContext(em, location, batchId);
            for (V row : block) {
                em.persist(toEntity.apply(row, ctx));
            }
            tx.commit();
            return block.size();
        } catch (PersistenceException e) {
            if (tx.isActive()) {
                tx.rollback();
            }
            return 0;
        } finally {
            // Se vacía el contexto para no acumular miles de objetos en memoria.
            em.clear();
        }
    }

    private <V, E> int commitOneByOne(EntityManager em, Location location, long batchId,
                                      List<V> block, BiFunction<V, Context, E> toEntity) {
        int inserted = 0;
        for (V row : block) {
            inserted += commitBlock(em, location, batchId, List.of(row), toEntity);
        }
        return inserted;
    }

    private static Context managedContext(EntityManager em, Location location, long batchId) {
        return new Context(em.find(Location.class, location.getId()),
                em.find(IngestionBatch.class, batchId));
    }

    /** Registros de meteorología de una ubicación en [from, to), ordenados por tiempo. */
    public List<WeatherRecord> findWeather(String locationCode, Instant from, Instant to) {
        return find(WeatherRecord.class, locationCode, from, to);
    }

    /** Registros de calidad del aire de una ubicación en [from, to), ordenados por tiempo. */
    public List<AirQualityRecord> findAirQuality(String locationCode, Instant from, Instant to) {
        return find(AirQualityRecord.class, locationCode, from, to);
    }

    private <E> List<E> find(Class<E> entityClass, String locationCode, Instant from,
                             Instant to) {
        EntityManager em = database.entityManager();
        try {
            String jpql = "SELECT r FROM " + entityClass.getSimpleName() + " r"
                    + " JOIN r.location l"
                    + " WHERE l.code = :code AND r.timestampUtc >= :from AND r.timestampUtc < :to"
                    + " ORDER BY r.timestampUtc";
            return em.createQuery(jpql, entityClass)
                    .setParameter("code", locationCode)
                    .setParameter("from", from)
                    .setParameter("to", to)
                    .getResultList();
        } finally {
            em.close();
        }
    }

    /** Resumen de la meteorología guardada para una ubicación. */
    public RecordSummary summarizeWeather(String locationCode) {
        Object[] row = aggregate("SELECT COUNT(r), COUNT(r.temperature2mC),"
                + " COUNT(r.relativeHumidity2mPct), COUNT(r.windSpeed10mMs),"
                + " MIN(r.timestampUtc), MAX(r.timestampUtc)"
                + " FROM WeatherRecord r JOIN r.location l WHERE l.code = :code", locationCode);
        Map<String, Long> nonNull = new LinkedHashMap<>();
        nonNull.put("temperature_2m_c", (Long) row[1]);
        nonNull.put("relative_humidity_2m_pct", (Long) row[2]);
        nonNull.put("wind_speed_10m_ms", (Long) row[3]);
        return new RecordSummary((Long) row[0], nonNull, (Instant) row[4], (Instant) row[5]);
    }

    /** Resumen de la calidad del aire guardada para una ubicación. */
    public RecordSummary summarizeAirQuality(String locationCode) {
        Object[] row = aggregate("SELECT COUNT(r), COUNT(r.pm25UgM3),"
                + " MIN(r.timestampUtc), MAX(r.timestampUtc)"
                + " FROM AirQualityRecord r JOIN r.location l WHERE l.code = :code", locationCode);
        Map<String, Long> nonNull = new LinkedHashMap<>();
        nonNull.put("pm25_ug_m3", (Long) row[1]);
        return new RecordSummary((Long) row[0], nonNull, (Instant) row[2], (Instant) row[3]);
    }

    private Object[] aggregate(String jpql, String locationCode) {
        EntityManager em = database.entityManager();
        try {
            return em.createQuery(jpql, Object[].class)
                    .setParameter("code", locationCode)
                    .getSingleResult();
        } finally {
            em.close();
        }
    }
}
