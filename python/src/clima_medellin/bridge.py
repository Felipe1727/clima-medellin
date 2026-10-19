"""Puente con el JAR de persistencia: Python nunca abre la base, se lo pide a Java (D-002)."""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from clima_medellin import paths
from clima_medellin.config import LOCATION, SOURCES
from clima_medellin.jsonlines import read_frame, write_frame

# Mensaje en español para cada código de salida del JAR (DP-05).
EXIT_MESSAGES = {
    1: "Error de uso del JAR (subcomando u opciones inválidos)",
    2: "El lote tiene datos inválidos",
    3: "No se pudo usar la base de datos; cierra otras ejecuciones de la aplicación "
    "e inténtalo de nuevo",
    4: "Error inesperado en el programa Java",
}


class BridgeError(Exception):
    """El JAR terminó con error o devolvió una respuesta que no se puede interpretar."""

    def __init__(
        self,
        message: str,
        *,
        exit_code: int | None = None,
        error_type: str | None = None,
        staging_file: Path | None = None,
    ):
        super().__init__(message)
        self.exit_code = exit_code
        self.error_type = error_type
        self.staging_file = staging_file


@dataclass
class CoverageSnapshot:
    """Lo que hay guardado de una fuente: resumen de Java y timestamps con sus variables."""

    summary: dict
    existing: pd.DataFrame


class JavaBridge:
    def __init__(
        self,
        db_path: Path = paths.DB_PATH,
        *,
        jar: Path = paths.JAR_PATH,
        staging_dir: Path = paths.STAGING_DIR,
        exchange_dir: Path = paths.EXCHANGE_DIR,
        verbose: bool = False,
        java: str = "java",
    ):
        self.db_path = Path(db_path)
        self.jar = Path(jar)
        self.staging_dir = Path(staging_dir)
        self.exchange_dir = Path(exchange_dir)
        self.verbose = verbose
        self.java = java

    def run(self, *args: str) -> dict:
        """Ejecuta un subcomando del JAR y devuelve su único objeto JSON de respuesta."""
        if not self.jar.is_file():
            raise BridgeError(
                f"No se encuentra el JAR en {self.jar}; compílalo con "
                "«cd java && mvn -q -DskipTests package»."
            )
        command = [
            self.java,
            # Silencia el aviso de sun.misc.Unsafe que ObjectDB provoca en Java 25.
            "--sun-misc-unsafe-memory-access=allow",
            "-jar",
            str(self.jar),
            *args,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if self.verbose and completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        lines = completed.stdout.strip().splitlines()
        try:
            if len(lines) != 1:
                raise ValueError("stdout no tiene exactamente una línea")
            response = json.loads(lines[0])
        except ValueError as exc:
            raise BridgeError(
                f"Respuesta no válida del JAR (código {completed.returncode}): {exc}",
                exit_code=completed.returncode,
            ) from exc
        if completed.returncode != 0:
            error = response.get("error", {})
            text = EXIT_MESSAGES.get(completed.returncode, "Error del JAR")
            raise BridgeError(
                f"{text}: {error.get('message', '')}",
                exit_code=completed.returncode,
                error_type=error.get("type"),
            )
        return response

    def import_frame(
        self,
        source: str,
        frame: pd.DataFrame,
        *,
        requested_start: datetime,
        requested_end: datetime,
        endpoint: str,
        params: dict,
        notes: str | None = None,
    ) -> dict:
        """Escribe el lote en staging/, lo importa y borra el archivo si todo fue bien."""
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        staging_file = self.staging_dir / f"{source}-{stamp}.jsonl"
        write_frame(frame, source, LOCATION.code, staging_file)
        meta = {
            "source": source,
            "location": {
                "code": LOCATION.code,
                "name": LOCATION.name,
                "latitude": LOCATION.latitude,
                "longitude": LOCATION.longitude,
                "elevation_m": LOCATION.elevation_m,
                "timezone": LOCATION.timezone,
            },
            "requested_start_utc": _iso(requested_start),
            "requested_end_utc": _iso(requested_end),
            "endpoint": endpoint,
            "params": params,
            "notes": notes,
        }
        try:
            response = self.run(
                "import",
                "--db",
                str(self.db_path),
                "--file",
                str(staging_file),
                "--meta",
                json.dumps(meta, ensure_ascii=False),
            )
        except BridgeError as exc:
            # El lote se conserva para poder abrirlo y ver qué falló.
            raise BridgeError(
                f"{exc} (lote conservado en {staging_file})",
                exit_code=exc.exit_code,
                error_type=exc.error_type,
                staging_file=staging_file,
            ) from exc
        staging_file.unlink()
        return response

    def coverage(self, source: str) -> CoverageSnapshot:
        """Pide a Java lo que hay guardado de una fuente."""
        out = self.exchange_dir / f"coverage-{source}.jsonl"
        summary = self.run(
            "coverage",
            "--db",
            str(self.db_path),
            "--location",
            LOCATION.code,
            "--source",
            source,
            "--out",
            str(out),
        )
        columns = SOURCES[source].columns
        records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
        index = pd.DatetimeIndex(
            pd.to_datetime([r["timestamp_utc"] for r in records], utc=True),
            name="timestamp_utc",
        )
        existing = pd.DataFrame(
            {c: [c in r["non_null"] for r in records] for c in columns}, index=index, dtype=bool
        )
        return CoverageSnapshot(summary=summary, existing=existing)

    def export(self, source: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Exporta los registros de [start, end) y los devuelve como DataFrame."""
        out = self.exchange_dir / f"export-{source}.jsonl"
        self.run(
            "export",
            "--db",
            str(self.db_path),
            "--location",
            LOCATION.code,
            "--source",
            source,
            "--from",
            _iso(start),
            "--to",
            _iso(end),
            "--out",
            str(out),
        )
        return read_frame(out, source)


def _iso(moment: datetime) -> str:
    """Instante en ISO 8601 UTC con sufijo Z (un instante sin zona se toma como UTC)."""
    ts = pd.Timestamp(moment)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")
