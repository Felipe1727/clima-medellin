package co.climamedellin.persistence;

/** Datos de una ubicación tal como llegan de Python. */
public record LocationData(String code, String name, double latitude, double longitude,
                           double elevationM, String timezone) {
}
