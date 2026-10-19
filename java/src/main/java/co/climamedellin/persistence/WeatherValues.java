package co.climamedellin.persistence;

import java.time.Instant;

/** Una fila de meteorología por insertar; cualquier variable puede ser null. */
public record WeatherValues(Instant timestampUtc, Double temperature2mC,
                            Double relativeHumidity2mPct, Double windSpeed10mMs) {

    boolean allValuesNull() {
        return temperature2mC == null && relativeHumidity2mPct == null && windSpeed10mMs == null;
    }
}
