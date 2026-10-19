package co.climamedellin.persistence;

/** Resultado de guardar un lote. */
public record InsertResult(String batchId, int received, int inserted, int duplicates,
                           int rejected, int blocksCommitted) {
}
