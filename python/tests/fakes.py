"""Capa HTTP falsa de Open-Meteo para las pruebas de integración.

Sirve cualquier rango de fechas con el formato real de la API, tomando cada valor de las
muestras anuales de ``samples/`` por (mes, día, hora). Imita la latencia de ERA5: las horas
desde las 00:00 UTC de D-4 llegan como null.
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
SAMPLE_FILES = {"ERA5": "era5_year.json", "CAMS_GLOBAL": "cams_pm25_year.json"}


class FakeOpenMeteo:
    def __init__(self, today: date, *, skip: dict[str, set[date]] | None = None, empty=False):
        self.today = today
        self.skip = skip or {}
        self.empty = empty
        self.calls: list[tuple[str, date, date]] = []
        self.samples = {
            source: json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))
            for source, name in SAMPLE_FILES.items()
        }
        self.lookup = {}
        for source, payload in self.samples.items():
            hourly = payload["hourly"]
            names = [k for k in hourly if k != "time"]
            self.lookup[source] = {
                t[5:]: {n: hourly[n][i] for n in names} for i, t in enumerate(hourly["time"])
            }

    def __call__(self, source: str, start: date, end: date) -> dict:
        self.calls.append((source, start, end))
        sample = self.samples[source]
        names = [k for k in sample["hourly"] if k != "time"]
        unpublished = datetime.combine(self.today - timedelta(days=4), datetime.min.time())
        hourly = {"time": [], **{n: [] for n in names}}
        moment = datetime.combine(start, datetime.min.time())
        while moment.date() <= end:
            stamp = moment.strftime("%Y-%m-%dT%H:%M")
            values = self.lookup[source].get(stamp[5:], {})
            hidden = (
                self.empty
                or moment.date() in self.skip.get(source, set())
                or (source == "ERA5" and moment >= unpublished)
            )
            hourly["time"].append(stamp)
            for n in names:
                hourly[n].append(None if hidden else values.get(n))
            moment += timedelta(hours=1)
        return {**{k: v for k, v in sample.items() if k != "hourly"}, "hourly": hourly}
