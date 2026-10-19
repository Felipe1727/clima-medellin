package co.climamedellin.entities;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;
import java.time.Instant;
import javax.jdo.annotations.Unique;

/**
 * Un paso horario de meteorología. Las variables son Double (no double) para poder
 * guardar null cuando falta el dato (D-012).
 */
@Entity
@Unique(members = {"location", "source", "timestampUtc"})
public class WeatherRecord {

    @Id
    @GeneratedValue
    private long id;

    @ManyToOne
    private Location location;

    @Enumerated(EnumType.STRING)
    private Source source;

    /** Instante UTC del dato (D-008). */
    private Instant timestampUtc;

    private Double temperature2mC;
    private Double relativeHumidity2mPct;
    private Double windSpeed10mMs;

    /** Lote que insertó este registro (procedencia). */
    @ManyToOne
    private IngestionBatch batch;

    /** Constructor vacío exigido por JPA. */
    protected WeatherRecord() {
    }

    public WeatherRecord(Location location, Source source, Instant timestampUtc,
                         Double temperature2mC, Double relativeHumidity2mPct,
                         Double windSpeed10mMs, IngestionBatch batch) {
        this.location = location;
        this.source = source;
        this.timestampUtc = timestampUtc;
        this.temperature2mC = temperature2mC;
        this.relativeHumidity2mPct = relativeHumidity2mPct;
        this.windSpeed10mMs = windSpeed10mMs;
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

    public Double getTemperature2mC() {
        return temperature2mC;
    }

    public Double getRelativeHumidity2mPct() {
        return relativeHumidity2mPct;
    }

    public Double getWindSpeed10mMs() {
        return windSpeed10mMs;
    }

    public IngestionBatch getBatch() {
        return batch;
    }
}
