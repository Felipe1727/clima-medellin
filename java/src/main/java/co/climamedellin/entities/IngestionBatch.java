package co.climamedellin.entities;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;
import java.time.Instant;
import javax.jdo.annotations.Unique;

/** Procedencia: una descarga concreta y lo que pasó al guardarla. */
@Entity
public class IngestionBatch {

    @Id
    @GeneratedValue
    private long id;

    /** Identificador legible del lote (UUID en texto). */
    @Unique
    private String batchId;

    @Enumerated(EnumType.STRING)
    private Source source;

    @ManyToOne
    private Location location;

    @Enumerated(EnumType.STRING)
    private BatchType type;

    /** Rango pedido a la API, en UTC. */
    private Instant requestedStartUtc;
    private Instant requestedEndUtc;

    /** Momento en que se guardó el lote, en UTC. */
    private Instant ingestedAtUtc;

    private String endpoint;

    /** Parámetros de la petición, como texto JSON. */
    private String params;

    private int received;
    private int inserted;
    private int duplicates;
    private int rejected;
    private String notes;

    /** Constructor vacío exigido por JPA. */
    protected IngestionBatch() {
    }

    public IngestionBatch(String batchId, Source source, Location location,
                          Instant requestedStartUtc, Instant requestedEndUtc,
                          Instant ingestedAtUtc, String endpoint, String params, String notes) {
        this.batchId = batchId;
        this.source = source;
        this.location = location;
        this.type = BatchType.NORMAL;
        this.requestedStartUtc = requestedStartUtc;
        this.requestedEndUtc = requestedEndUtc;
        this.ingestedAtUtc = ingestedAtUtc;
        this.endpoint = endpoint;
        this.params = params;
        this.notes = notes;
    }

    /** Guarda los conteos finales del lote. */
    public void setCounts(int received, int inserted, int duplicates, int rejected) {
        this.received = received;
        this.inserted = inserted;
        this.duplicates = duplicates;
        this.rejected = rejected;
    }

    public long getId() {
        return id;
    }

    public String getBatchId() {
        return batchId;
    }

    public Source getSource() {
        return source;
    }

    public Location getLocation() {
        return location;
    }

    public BatchType getType() {
        return type;
    }

    public Instant getRequestedStartUtc() {
        return requestedStartUtc;
    }

    public Instant getRequestedEndUtc() {
        return requestedEndUtc;
    }

    public Instant getIngestedAtUtc() {
        return ingestedAtUtc;
    }

    public String getEndpoint() {
        return endpoint;
    }

    public String getParams() {
        return params;
    }

    public int getReceived() {
        return received;
    }

    public int getInserted() {
        return inserted;
    }

    public int getDuplicates() {
        return duplicates;
    }

    public int getRejected() {
        return rejected;
    }

    public String getNotes() {
        return notes;
    }
}
