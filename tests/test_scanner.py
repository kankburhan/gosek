from gosek.patterns_loader import load_patterns
from gosek.scanner import scan_text
import re


def test_basic_match(tmp_path):
    patterns = [
        ("Dummy", r"TEST_[0-9]{3}", re.compile(r"TEST_[0-9]{3}")),
    ]
    text = "foo TEST_123 bar"
    findings = scan_text("mem", text, patterns, context=10)
    assert findings and findings[0].match == "TEST_123"


def test_real_patterns_file():
    import pathlib

    p = pathlib.Path(__file__).resolve().parents[1] / "patterns" / "patterns.json"
    loaded = load_patterns(str(p))
    assert any(name == "AWS Access Key ID" for name, *_ in loaded)