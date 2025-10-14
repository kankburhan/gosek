from __future__ import annotations
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple
import requests


@dataclass
class Finding:
    pattern_name: str
    pattern: str
    match: str
    context: str
    source: str


def fetch_url(
    url: str,
    timeout: int = 20,
    proxy: str | None = None,
    retries: int = 3,
    backoff: float = 0.5,
) -> str:
    """Fetch URL with retry + exponential backoff."""
    proxies = {"http": proxy, "https": proxy} if proxy else None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(
                url,
                headers={"User-Agent": "gosek/0.4"},
                timeout=timeout,
                proxies=proxies,
            )
            r.raise_for_status()
            r.encoding = r.encoding or "utf-8"
            return r.text
        except Exception as e:
            if attempt == retries:
                raise
            delay = backoff * (2 ** (attempt - 1))
            sys.stderr.write(f"[gosek] attempt {attempt} failed for {url}: {e} → retry in {delay:.1f}s\n")
            time.sleep(delay)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def context_snippet(text: str, start: int, end: int, ctx: int) -> str:
    s = max(0, start - ctx)
    e = min(len(text), end + ctx)
    return text[s:e].replace("\n", " ").replace("\r", " ").strip()


def scan_text(
    source: str,
    text: str,
    compiled_patterns: Iterable[Tuple[str, str, re.Pattern]],
    context: int = 80,
) -> List[Finding]:
    findings: List[Finding] = []
    for name, raw, cre in compiled_patterns:
        for m in cre.finditer(text):
            findings.append(
                Finding(
                    pattern_name=name,
                    pattern=raw,
                    match=m.group(0),
                    context=context_snippet(text, m.start(), m.end(), context),
                    source=source,
                )
            )
    return findings


def scan_many(
    targets: List[tuple[str, str]],
    *,
    compiled_patterns: Iterable[Tuple[str, str, re.Pattern]],
    context: int = 80,
    max_workers: int = 20,
    proxy: str | None = None,
    timeout: int = 20,
    retries: int = 3,
    backoff: float = 0.5,
) -> List[Finding]:
    results: List[Finding] = []

    def _work(kind: str, value: str) -> List[Finding]:
        try:
            if kind == "url":
                content = fetch_url(value, timeout=timeout, proxy=proxy, retries=retries, backoff=backoff)
            else:
                content = read_file(value)
            return scan_text(value, content, compiled_patterns, context=context)
        except Exception as e:
            sys.stderr.write(f"[gosek] skip {kind}:{value} — {e}\n")
            return []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_work, k, v) for k, v in targets]
        for fut in as_completed(futs):
            results.extend(fut.result())
    return results


def to_jsonl(findings: List[Finding]) -> str:
    return "\n".join(json.dumps(f.__dict__, ensure_ascii=False) for f in findings) + ("\n" if findings else "")


def summary(findings: List[Finding]) -> str:
    from collections import Counter
    c = Counter(f.pattern_name for f in findings)
    lines = ["pattern,count"] + [f"{name},{cnt}" for name, cnt in sorted(c.items())]
    return "\n".join(lines) + ("\n" if lines else "")
