package co.climamedellin.cli;

/** Archivo inexistente, línea JSON inválida o violación del formato (código de salida 2). */
public class DataException extends RuntimeException {
    public DataException(String message) {
        super(message);
    }

    public DataException(String message, Throwable cause) {
        super(message, cause);
    }
}
