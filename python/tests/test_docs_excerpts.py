"""Verifica que los fragmentos reales de ``docs/implementacion.md`` coinciden con el código.

Un fragmento real es un bloque de código precedido por ``<!-- fragmento: <ruta> -->``.
La prueba falla si el texto del bloque no aparece literalmente en el archivo citado.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE = REPO_ROOT / "docs" / "implementacion.md"

MARKER = re.compile(r"^<!--\s*fragmento:\s*(?P<path>\S+)\s*-->\s*$")
FENCE = re.compile(r"^(?P<ticks>`{3,})")


@dataclass
class Excerpt:
    path: str
    code: str
    line: int


def extract_excerpts(markdown: str) -> list[Excerpt]:
    """Devuelve los fragmentos marcados, ignorando las marcas que estén dentro de otro bloque."""
    lines = markdown.splitlines()
    excerpts: list[Excerpt] = []
    open_fence: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = FENCE.match(line)
        if open_fence is not None:
            # Dentro de un bloque: solo buscamos su cierre.
            if fence and line.strip() == open_fence:
                open_fence = None
            i += 1
            continue
        if fence:
            open_fence = fence.group("ticks")
            i += 1
            continue
        marker = MARKER.match(line)
        if marker:
            start = i + 1
            opening = FENCE.match(lines[start]) if start < len(lines) else None
            if opening is None:
                raise ValueError(f"Línea {i + 1}: la marca de fragmento no va seguida de un bloque")
            ticks = opening.group("ticks")
            end = start + 1
            while end < len(lines) and lines[end].strip() != ticks:
                end += 1
            if end == len(lines):
                raise ValueError(f"Línea {i + 1}: el bloque del fragmento no se cierra")
            code = "\n".join(lines[start + 1 : end])
            excerpts.append(Excerpt(path=marker.group("path"), code=code, line=i + 1))
            i = end + 1
            continue
        i += 1
    return excerpts


def normalize(text: str) -> str:
    """Quita los espacios al final de cada línea."""
    return "\n".join(line.rstrip() for line in text.splitlines())


def check_excerpt(excerpt: Excerpt, root: Path) -> str | None:
    """Devuelve un mensaje de error si el fragmento no coincide, o ``None`` si es correcto."""
    source = root / excerpt.path
    if not source.is_file():
        return f"{excerpt.path} (línea {excerpt.line}): el archivo no existe"
    if normalize(excerpt.code) not in normalize(source.read_text(encoding="utf-8")):
        return f"{excerpt.path} (línea {excerpt.line}): el fragmento no coincide con el código"
    return None


def test_guide_has_real_excerpts_matching_the_code():
    excerpts = extract_excerpts(GUIDE.read_text(encoding="utf-8"))
    assert excerpts, "docs/implementacion.md no contiene ningún fragmento marcado"
    errors = [msg for e in excerpts if (msg := check_excerpt(e, REPO_ROOT)) is not None]
    assert not errors, "Fragmentos desactualizados:\n" + "\n".join(errors)


# --- Pruebas del propio verificador, sobre textos de ejemplo ---

SAMPLE_GUIDE = """\
Texto previo.

````text
<!-- fragmento: ejemplo/ignorado.py -->
```python
esto no se verifica
```
````

<!-- fragmento: src/modulo.py -->
```python
def suma(a, b):
    return a + b
```
"""


@pytest.fixture
def sample_root(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "modulo.py").write_text(
        "# cabecera\ndef suma(a, b):   \n    return a + b\n", encoding="utf-8"
    )
    return tmp_path


def test_markers_inside_other_blocks_are_ignored():
    excerpts = extract_excerpts(SAMPLE_GUIDE)
    assert [e.path for e in excerpts] == ["src/modulo.py"]
    assert excerpts[0].code == "def suma(a, b):\n    return a + b"


def test_current_excerpt_passes(sample_root: Path):
    (excerpt,) = extract_excerpts(SAMPLE_GUIDE)
    assert check_excerpt(excerpt, sample_root) is None


def test_outdated_excerpt_fails_with_its_path(sample_root: Path):
    (sample_root / "src" / "modulo.py").write_text("def suma(a, b):\n    return b + a\n")
    (excerpt,) = extract_excerpts(SAMPLE_GUIDE)
    message = check_excerpt(excerpt, sample_root)
    assert message is not None and "src/modulo.py" in message


def test_missing_source_file_fails_with_its_path(tmp_path: Path):
    (excerpt,) = extract_excerpts(SAMPLE_GUIDE)
    message = check_excerpt(excerpt, tmp_path)
    assert message is not None and "src/modulo.py" in message and "no existe" in message


def test_guide_without_excerpts_yields_none():
    assert extract_excerpts("# Guía\n\nSin fragmentos.\n") == []
