package co.climamedellin.cli;

/** Subcomando u opciones inválidos (código de salida 1). */
public class UsageException extends RuntimeException {
    public UsageException(String message) {
        super(message);
    }
}
