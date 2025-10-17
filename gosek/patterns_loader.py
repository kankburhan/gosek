from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple, Any

try:
    import yaml  # optional
except Exception:
    yaml = None

try:
    import tomllib  # Python 3.11+
except Exception:
    try:
        import tomli as tomllib  # fallback for <3.11
    except Exception:
        tomllib = None


# Flags yang bisa diset via kolom "flags" di template
EXTERNAL_FLAG_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
    "VERBOSE": re.VERBOSE,
}

# Pemetaan inline flags → compiler flags
INLINE_FLAG_MAP = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "x": re.VERBOSE,
}

# Pola untuk mendeteksi inline flags yang tidak scoped:
#   (?i), (?isx), (?imx-i), (?-i), (?-mx), dll.
_RE_INLINE_MIX = re.compile(r"\(\?([imsx]+)(?:-([imsx]+))?\)")
_RE_INLINE_OFF = re.compile(r"\(\?-([imsx]+)\)")

def _sanitize_inline_flags(pat: str) -> tuple[str, int]:
    i = 0
    n = len(pat)
    out: list[str] = []
    extra = 0

    while i < n:
        # Deteksi awal grup (? ... ). Jika scoped "(?...: ...)" → biarkan utuh.
        if pat.startswith("(?", i):
            j = i + 2
            scoped = False
            while j < n:
                ch = pat[j]
                if ch == ":":
                    # scoped group: (?flags:...) atau (?:...) — biarkan
                    scoped = True
                    break
                if ch == ")":
                    # end of group header tanpa ":" → kandidat unscoped
                    break
                j += 1

            if scoped:
                # Salin karakter "(?...:" lalu lanjut proses normal untuk isi berikutnya
                out.append(pat[i:j+1])
                i = j + 1
                continue

            # Coba match bentuk unscoped campuran (?imx-i) atau (?imx)
            m = _RE_INLINE_MIX.match(pat, i)
            if m:
                on_flags, off_flags = m.group(1), m.group(2)
                for ch in on_flags:
                    extra |= INLINE_FLAG_MAP.get(ch, 0)
                # off_flags diabaikan (tak bisa dimatikan global)
                i = m.end()
                continue

            # Coba (?-i) / (?-mx)
            m = _RE_INLINE_OFF.match(pat, i)
            if m:
                # buang saja
                i = m.end()
                continue

        # karakter biasa
        out.append(pat[i])
        i += 1

    return ("".join(out), extra)


def _compile(pattern: str, flags: Iterable[str] | None) -> re.Pattern:
    f = 0
    for name in (flags or []):
        f |= EXTERNAL_FLAG_MAP.get(name.upper(), 0)

    # Sanitasi inline flags unscoped
    pattern, extra = _sanitize_inline_flags(pattern)
    f |= extra

    return re.compile(pattern, f | re.MULTILINE)


def _load_from_obj(data: Any, src: Path) -> List[Tuple[str, str, re.Pattern]]:
    items = data if isinstance(data, list) else data.get("patterns", [])
    out: List[Tuple[str, str, re.Pattern]] = []

    if not isinstance(items, list):
        raise ValueError(f"Invalid template structure in {src}: expected list or dict['patterns']")

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid pattern entry at index {idx} in {src}: expected object")
        name = item.get("name")
        pat = item.get("pattern")
        flags = item.get("flags")

        if not isinstance(name, str) or not isinstance(pat, str):
            raise ValueError(f"Invalid pattern entry at index {idx} in {src}: missing name/pattern")

        if flags is not None and not isinstance(flags, (list, tuple)):
            raise ValueError(f"Invalid flags at index {idx} in {src}: expected list of strings")

        out.append((name, pat, _compile(pat, flags)))
    return out


def _load_one_file(path: Path) -> List[Tuple[str, str, re.Pattern]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if not yaml:
            raise RuntimeError("PyYAML not installed; install with `pip install gosek[yaml]`.")
        data = yaml.safe_load(text)
    elif path.suffix.lower() == ".toml":
        if not tomllib:
            raise RuntimeError("tomllib/tomli not available; install with `pip install gosek[toml]`.")
        data = tomllib.loads(text)
    else:
        data = json.loads(text)

    return _load_from_obj(data, path)


def load_patterns_from_dir(templates_dir: Path) -> List[Tuple[str, str, re.Pattern]]:
    """Load semua pattern secara rekursif dari direktori templates."""
    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates dir not found: {templates_dir}")
    patterns: List[Tuple[str, str, re.Pattern]] = []
    for p in templates_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".json", ".yaml", ".yml", ".toml"}:
            patterns.extend(_load_one_file(p))
    if not patterns:
        raise RuntimeError(f"No pattern files found under {templates_dir}")
    return patterns
