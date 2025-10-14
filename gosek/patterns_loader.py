from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple

try:
    import yaml  # optional
except Exception:
    yaml = None

try:
    import tomllib  # Python 3.11+
except Exception:
    try:
        import tomli as tomllib  # fallback
    except Exception:
        tomllib = None


FLAG_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
}


def _compile(pattern: str, flags: Iterable[str] | None) -> re.Pattern:
    f = 0
    for name in (flags or []):
        f |= FLAG_MAP.get(name.upper(), 0)
    return re.compile(pattern, f | re.MULTILINE)


def _load_one_file(path: Path) -> List[Tuple[str, str, re.Pattern]]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        if not yaml:
            raise RuntimeError("PyYAML not installed; install with `pip install gosek[yaml]`.")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".toml":
        if not tomllib:
            raise RuntimeError("tomllib/tomli not available; install with `pip install gosek[toml]`.")
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))

    items = data if isinstance(data, list) else data.get("patterns", [])
    out: List[Tuple[str, str, re.Pattern]] = []
    for item in items:
        name = item["name"]
        pat = item["pattern"]
        flags = item.get("flags") if isinstance(item, dict) else None
        out.append((name, pat, _compile(pat, flags)))
    return out


def load_patterns_from_dir(templates_dir: Path) -> List[Tuple[str, str, re.Pattern]]:
    """Load all patterns from a directory (recursively) across JSON/YAML/TOML files."""
    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates dir not found: {templates_dir}")
    patterns: List[Tuple[str, str, re.Pattern]] = []
    for p in templates_dir.rglob("*"):
        if p.suffix.lower() in {".json", ".yaml", ".yml", ".toml"} and p.is_file():
            patterns.extend(_load_one_file(p))
    if not patterns:
        raise RuntimeError(f"No pattern files found under {templates_dir}")
    return patterns
