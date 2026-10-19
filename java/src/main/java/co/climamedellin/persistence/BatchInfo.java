package co.climamedellin.persistence;

import java.time.Instant;

/** Metadatos de la descarga que originó un lote. */
public record BatchInfo(Instant requestedStartUtc, Instant requestedEndUtc, String endpoint,
                        String params, String notes) {
}
