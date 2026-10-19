"""Constantes del proyecto: ubicación, fuentes y parámetros fijados en el roadmap."""

from dataclasses import dataclass
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Bogota")


@dataclass(frozen=True)
class Location:
    code: str
    name: str
    latitude: float
    longitude: float
    elevation_m: float
    timezone: str


# Punto representativo del centro de Medellín (D-007, DP-11).
LOCATION = Location(
    code="MED-CENTRO",
    name="Medellín – Centro",
    latitude=6.2447,
    longitude=-75.5748,
    elevation_m=1495,
    timezone="America/Bogota",
)


@dataclass(frozen=True)
class Variable:
    """Variable de la API con su columna canónica, unidad esperada y rango plausible."""

    api_name: str
    column: str
    unit: str
    minimum: float
    maximum: float


@dataclass(frozen=True)
class SourceConfig:
    name: str
    url: str
    fixed_params: dict
    variables: tuple[Variable, ...]

    @property
    def columns(self) -> list[str]:
        return [v.column for v in self.variables]


ERA5 = SourceConfig(
    name="ERA5",
    url="https://archive-api.open-meteo.com/v1/archive",
    fixed_params={
        "latitude": LOCATION.latitude,
        "longitude": LOCATION.longitude,
        "elevation": LOCATION.elevation_m,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "models": "era5",
        "wind_speed_unit": "ms",
        "timezone": "GMT",
    },
    variables=(
        Variable("temperature_2m", "temperature_2m_c", "°C", -20.0, 50.0),
        Variable("relative_humidity_2m", "relative_humidity_2m_pct", "%", 0.0, 100.0),
        Variable("wind_speed_10m", "wind_speed_10m_ms", "m/s", 0.0, 75.0),
    ),
)

# La Air Quality API no documenta el parámetro "elevation", así que no se envía.
CAMS_GLOBAL = SourceConfig(
    name="CAMS_GLOBAL",
    url="https://air-quality-api.open-meteo.com/v1/air-quality",
    fixed_params={
        "latitude": LOCATION.latitude,
        "longitude": LOCATION.longitude,
        "hourly": "pm2_5",
        "domains": "cams_global",
        "timezone": "GMT",
    },
    variables=(Variable("pm2_5", "pm25_ug_m3", "µg/m³", 0.0, 1000.0),),
)

SOURCES = {source.name: source for source in (ERA5, CAMS_GLOBAL)}
