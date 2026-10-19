"""Descarga las respuestas de muestra de Open-Meteo y las guarda en ``samples/``.

Uso (desde ``python/``)::

    uv run python scripts/fetch_samples.py

Es la única pieza del proyecto que accede a la red fuera de la aplicación. Las pruebas
usan los archivos que deja en ``samples/`` y nunca llaman a las APIs.
"""

import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "samples"

# Punto representativo fijado en el roadmap (D-007, DP-11).
LATITUDE = 6.2447
LONGITUDE = -75.5748
ELEVATION_M = 1495
LOCAL_TZ = ZoneInfo("America/Bogota")

ERA5_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

ERA5_PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "elevation": ELEVATION_M,
    "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
    "models": "era5",
    "wind_speed_unit": "ms",
    "timezone": "GMT",
}
# La Air Quality API no documenta el parámetro "elevation", así que no se envía.
PM25_PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "hourly": "pm2_5",
    "domains": "cams_global",
    "timezone": "GMT",
}


@dataclass(frozen=True)
class SampleRequest:
    filename: str
    description: str
    url: str
    params: dict
    start: date
    end: date

    def full_params(self) -> dict:
        return {
            **self.params,
            "start_date": self.start.isoformat(),
            "end_date": self.end.isoformat(),
        }


def one_year_before(day: date) -> date:
    """Mismo día del año anterior; el 29 de febrero pasa al 28 (DP-09)."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def sample_requests(today_local: date) -> list[SampleRequest]:
    """Define las cuatro muestras a partir de la fecha D en America/Bogota."""
    yesterday = today_local - timedelta(days=1)
    year_start = one_year_before(today_local)
    return [
        SampleRequest(
            "era5_year.json",
            "ERA5: temperatura, humedad y viento de un año",
            ERA5_URL,
            ERA5_PARAMS,
            year_start,
            yesterday,
        ),
        SampleRequest(
            "era5_recent_month.json",
            "ERA5: últimos 30 días (incluye los nulos finales de los días no publicados)",
            ERA5_URL,
            ERA5_PARAMS,
            today_local - timedelta(days=30),
            yesterday,
        ),
        SampleRequest(
            "cams_pm25_year.json",
            "CAMS global: PM2.5 de un año",
            AIR_QUALITY_URL,
            PM25_PARAMS,
            year_start,
            yesterday,
        ),
        SampleRequest(
            "cams_pm25_last_week.json",
            "CAMS global: PM2.5 de los últimos 7 días",
            AIR_QUALITY_URL,
            PM25_PARAMS,
            today_local - timedelta(days=7),
            yesterday,
        ),
    ]


def trailing_nulls_start(payload: dict, today_local: date) -> bool:
    """Comprueba que ERA5 es nulo exactamente desde las 00:00 UTC de D-4."""
    cutoff = (today_local - timedelta(days=4)).isoformat() + "T00:00"
    hourly = payload["hourly"]
    for name, values in hourly.items():
        if name == "time":
            continue
        for timestamp, value in zip(hourly["time"], values, strict=True):
            if (timestamp >= cutoff) != (value is None):
                return False
    return True


def render_readme(manifest: dict) -> str:
    lines = [
        "# Muestras de las APIs de Open-Meteo",
        "",
        "Respuestas reales guardadas tal cual por `python/scripts/fetch_samples.py`. "
        "Sirven de referencia del formato y de datos de prueba sin red.",
        "",
        f"- Fecha de referencia D (America/Bogota): {manifest['today_local']}",
        f"- Descarga (UTC): {manifest['downloaded_at_utc']}",
        "- Datos: Open-Meteo.com (CC BY 4.0), a partir de ERA5 (Copernicus Climate Change "
        "Service) y CAMS global (Copernicus Atmosphere Monitoring Service).",
        "",
        "| Archivo | Contenido | Rango | URL |",
        "|---|---|---|---|",
    ]
    for item in manifest["samples"]:
        lines.append(
            f"| `{item['file']}` | {item['description']} | "
            f"{item['start_date']} → {item['end_date']} | {item['url']} |"
        )
    lines += ["", "Los parámetros completos de cada petición están en `manifest.json`.", ""]
    return "\n".join(lines)


def main() -> int:
    today_local = datetime.now(LOCAL_TZ).date()
    SAMPLES_DIR.mkdir(exist_ok=True)
    manifest = {
        "today_local": today_local.isoformat(),
        "downloaded_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "samples": [],
    }
    for request in sample_requests(today_local):
        params = request.full_params()
        response = requests.get(request.url, params=params, timeout=60)
        if response.status_code != 200:
            print(f"[ERROR] {request.filename}: HTTP {response.status_code}", file=sys.stderr)
            return 1
        payload = response.json()
        if request.filename == "era5_recent_month.json" and not trailing_nulls_start(
            payload, today_local
        ):
            print(
                "[AVISO] ERA5 no termina en D-5 hoy; repite la descarga otro día.",
                file=sys.stderr,
            )
            return 1
        path = SAMPLES_DIR / request.filename
        path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        manifest["samples"].append(
            {
                "file": request.filename,
                "description": request.description,
                "url": response.url,
                "params": params,
                "start_date": request.start.isoformat(),
                "end_date": request.end.isoformat(),
            }
        )
        print(f"[OK] {request.filename}")
    (SAMPLES_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (SAMPLES_DIR / "README.md").write_text(render_readme(manifest), encoding="utf-8")
    print("[OK] manifest.json y README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
