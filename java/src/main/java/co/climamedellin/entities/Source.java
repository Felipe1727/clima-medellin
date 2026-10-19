package co.climamedellin.entities;

/** Fuente de un registro: el modelo del que procede el dato. */
public enum Source {
    /** Reanálisis ERA5 (Historical Weather API de Open-Meteo). */
    ERA5,
    /** Pronósticos archivados de CAMS global (Air Quality API de Open-Meteo). */
    CAMS_GLOBAL
}
