package co.climamedellin.entities;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;
import java.time.Instant;
import javax.jdo.annotations.Unique;

/** Un paso horario de calidad del aire (PM2.5 de CAMS global). */
@Entity
@Unique(members = {"location", "source", "timestampUtc"})
public class AirQualityRecord {

    @Id
    @GeneratedValue
    private long id;

    @ManyToOne
    private Location location;

    @Enumerated(EnumType.STRING)
    private Source source;

    /** Instante UTC del dato (D-008). */
    private Instant timestampUtc;

    /** PM2.5 en µg/m³; null si falta (D-012). */
    private Double pm25UgM3;

    /** Lote que insertó este registro (procedencia). */
    @ManyToOne
    private IngestionBatch batch;

    /** Constructor vacío exigido por JPA. */
    protected AirQualityRecord() {
    }

    public AirQualityRecord(Location location, Source source, Instant timestampUtc,
                            Double pm25UgM3, IngestionBatch batch) {
        this.location = location;
        this.source = source;
        this.timestampUtc = timestampUtc;
        this.pm25UgM3 = pm25UgM3;
        this.batch = batch;
    }

    public long getId() {
        return id;
    }

    public Location getLocation() {
        return location;
    }

    public Source getSource() {
        return source;
    }

    public Instant getTimestampUtc() {
        return timestampUtc;
    }

    public Double getPm25UgM3() {
        return pm25UgM3;
    }

    public IngestionBatch getBatch() {
        return batch;
    }
}
