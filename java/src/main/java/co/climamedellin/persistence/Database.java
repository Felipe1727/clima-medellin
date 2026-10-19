package co.climamedellin.persistence;

import co.climamedellin.entities.AirQualityRecord;
import co.climamedellin.entities.IngestionBatch;
import co.climamedellin.entities.Location;
import co.climamedellin.entities.WeatherRecord;
import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Archivo de ObjectDB abierto. Solo Java abre la base (D-002); cada operación pide
 * su propio EntityManager y lo cierra al terminar.
 */
public final class Database implements AutoCloseable {

    /** Las cuatro clases de entidad del proyecto (D-010). */
    private static final Class<?>[] ENTITY_CLASSES = {
        Location.class, WeatherRecord.class, AirQualityRecord.class, IngestionBatch.class
    };

    private final EntityManagerFactory emf;

    private Database(EntityManagerFactory emf) {
        this.emf = emf;
    }

    /** Abre (o crea, si no existe) la base en la ruta indicada. */
    public static Database open(Path file) {
        Path parent = file.toAbsolutePath().getParent();
        try {
            if (parent != null) {
                Files.createDirectories(parent);
            }
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        // Con ObjectDB basta una URL "objectdb:" con la ruta; no hace falta persistence.xml.
        EntityManagerFactory emf =
                Persistence.createEntityManagerFactory("objectdb:" + file.toAbsolutePath());
        // ObjectDB solo conoce una clase cuando se guarda su primer objeto; registrarlas
        // al abrir permite consultar una entidad aunque todavía no tenga registros. El
        // registro se hace desde un EntityManager porque es él quien abre el archivo.
        EntityManager em = emf.createEntityManager();
        try {
            for (Class<?> entityClass : ENTITY_CLASSES) {
                em.getMetamodel().entity(entityClass);
            }
        } finally {
            em.close();
        }
        return new Database(emf);
    }

    public EntityManager entityManager() {
        return emf.createEntityManager();
    }

    @Override
    public void close() {
        emf.close();
    }
}
