from gosek.scanner import scan_text
import re

def test_scan_text_selfcontained():
    # self-contained pattern; no external templates needed
    pats = [("DummyKey", r"AKIA[0-9A-Z]{16}", re.compile(r"AKIA[0-9A-Z]{16}"))]
    text = "noise AKIAABCDEFGHIJKLMNOP noise"
    findings = scan_text("mem", text, pats, context=8)
    assert findings and findings[0].match == "AKIAABCDEFGHIJKLMNOP"
