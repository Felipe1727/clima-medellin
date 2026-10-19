package co.climamedellin.entities;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import javax.jdo.annotations.Unique;

/** Punto geográfico del que se piden datos (D-007). */
@Entity
public class Location {

    @Id
    @GeneratedValue
    private long id;

    /** Código legible y único, por ejemplo «MED-CENTRO». */
    @Unique
    private String code;

    private String name;
    private double latitude;
    private double longitude;
    private double elevationM;
    private String timezone;

    /** Constructor vacío exigido por JPA. */
    protected Location() {
    }

    public Location(String code, String name, double latitude, double longitude,
                    double elevationM, String timezone) {
        this.code = code;
        this.name = name;
        this.latitude = latitude;
        this.longitude = longitude;
        this.elevationM = elevationM;
        this.timezone = timezone;
    }

    public long getId() {
        return id;
    }

    public String getCode() {
        return code;
    }

    public String getName() {
        return name;
    }

    public double getLatitude() {
        return latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public double getElevationM() {
        return elevationM;
    }

    public String getTimezone() {
        return timezone;
    }
}
