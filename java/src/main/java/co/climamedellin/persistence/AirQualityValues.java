package co.climamedellin.persistence;

import java.time.Instant;

/** Una fila de calidad del aire por insertar; PM2.5 puede ser null. */
public record AirQualityValues(Instant timestampUtc, Double pm25UgM3) {

    boolean allValuesNull() {
        return pm25UgM3 == null;
    }
}
