package co.climamedellin.persistence;

import java.time.Instant;
import java.util.Map;

/**
 * Resumen de los registros de una ubicación y fuente: total, valores no nulos por
 * variable (con el nombre del campo de JSON Lines) y primer y último timestamp.
 */
public record RecordSummary(long count, Map<String, Long> nonNullByVariable, Instant first,
                            Instant last) {
}
