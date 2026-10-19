"""Conversión entre DataFrames y archivos JSON Lines del protocolo con Java."""

import json
import math
from pathlib import Path

import pandas as pd

from clima_medellin.config import SOURCES


def _format_timestamp(ts: pd.Timestamp) -> str:
    """ISO 8601 en UTC con sufijo Z, como espera Java (``2026-03-01T13:00:00Z``)."""
    return ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def write_frame(frame: pd.DataFrame, source: str, location_code: str, path: Path) -> int:
    """Escribe una línea por fila; los NaN se escriben como null. Devuelve las líneas."""
    columns = SOURCES[source].columns
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        for ts, row in zip(frame.index, frame[columns].itertuples(index=False), strict=True):
            record = {
                "location_code": location_code,
                "source": source,
                "timestamp_utc": _format_timestamp(ts),
            }
            for column, value in zip(columns, row, strict=True):
                record[column] = None if value is None or math.isnan(value) else float(value)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(frame)


def read_frame(path: Path, source: str) -> pd.DataFrame:
    """Lee una exportación de Java como DataFrame indexado por timestamp UTC."""
    columns = SOURCES[source].columns
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    extra = ["batch_id"] if records and "batch_id" in records[0] else []
    index = pd.DatetimeIndex(
        pd.to_datetime([r["timestamp_utc"] for r in records], utc=True), name="timestamp_utc"
    )
    data = {c: [r.get(c) for r in records] for c in columns + extra}
    frame = pd.DataFrame(data, index=index)
    frame[columns] = frame[columns].astype(float)
    return frame
