from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import List

from .patterns_loader import load_patterns_from_dir
from .scanner import scan_many, to_jsonl, summary

DEFAULT_TEMPLATES = Path(os.environ.get("GOSEK_TEMPLATES", Path.home() / ".gosek" / "templates")).resolve()


def _gather_targets(url: str | None, file: str | None) -> List[tuple[str, str]]:
    """Return list of (kind, value) where kind in {"url","file"}.
    - If --url points to an existing local file → treat as URL list (one per line)
    - If --file points to local file → scan that file
    - If stdin is piped → detect line by line (URL or file path)
    """
    targets: List[tuple[str, str]] = []

    if url:
        upath = Path(url)
        if upath.exists():
            for line in upath.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if not s:
                    continue
                if s.startswith("http://") or s.startswith("https://"):
                    targets.append(("url", s))
                else:
                    targets.append(("file", s))
        else:
            targets.append(("url", url))

    if file:
        fpath = Path(file)
        if fpath.exists():
            targets.append(("file", str(fpath)))
        else:
            raise FileNotFoundError(f"--file not found: {file}")

    if not targets and not sys.stdin.isatty():
        for line in sys.stdin.read().splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith("http://") or s.startswith("https://"):
                targets.append(("url", s))
            else:
                targets.append(("file", s))

    return targets


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gosek",
        description="Find secrets using regex templates (fast, concurrent, with retry)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- Scan ---
    scan = sub.add_parser("scan", help="Scan URL(s)/file(s)/pipeline for secrets")
    scan.add_argument("--url", "-u", help="Single URL or path to file with list of URLs")
    scan.add_argument("--file", "-f", help="Path to local file to scan")
    scan.add_argument("--templates", "-t", default=str(DEFAULT_TEMPLATES),
                      help="Templates folder (json/yaml/toml). Default: ~/.gosek/templates")
    scan.add_argument("--format", choices=["jsonl", "summary"], default="jsonl")
    scan.add_argument("--context", type=int, default=80, help="Context chars around each finding")
    scan.add_argument("--concurrent", type=int, default=20, help="Number of concurrent workers")
    scan.add_argument("--proxy", help="HTTP/HTTPS proxy, e.g. http://127.0.0.1:8080")
    scan.add_argument("--timeout", type=int, default=20, help="Per-URL timeout (seconds)")
    scan.add_argument("--retries", type=int, default=3, help="Retries for fetching URLs")
    scan.add_argument("--backoff", type=float, default=0.5, help="Backoff factor (seconds)")

    # --- Templates mgmt ---
    tpl = sub.add_parser("templates", help="Manage templates (install/update/list)")
    tpl_sub = tpl.add_subparsers(dest="tpl_cmd", required=True)

    tpl_install = tpl_sub.add_parser("install", help="Install templates from git/zip")
    tpl_install.add_argument("--from", dest="src", required=True, help="Templates repo or zip URL")
    tpl_install.add_argument("--to", dest="dst", default=str(DEFAULT_TEMPLATES),
                             help="Destination folder (default: ~/.gosek/templates)")

    tpl_update = tpl_sub.add_parser("update", help="Update templates (git pull / re-download)")
    tpl_update.add_argument("--to", dest="dst", default=str(DEFAULT_TEMPLATES),
                            help="Templates folder")

    tpl_list = tpl_sub.add_parser("list", help="List readable template files")
    tpl_list.add_argument("--templates", "-t", default=str(DEFAULT_TEMPLATES))

    args = parser.parse_args()

    if args.cmd == "scan":
        tdir = Path(args.templates)
        if not tdir.exists():
            raise SystemExit(
                f"Templates dir not found: {tdir}\n"
                f"→ Run: gosek templates install --from <repo_or_zip_url> --to {tdir}"
            )
        patterns = load_patterns_from_dir(tdir)
        targets = _gather_targets(args.url, args.file)
        if not targets:
            scan.print_help()
            sys.exit(1)

        findings = scan_many(
            targets,
            compiled_patterns=patterns,
            context=args.context,
            max_workers=max(1, args.concurrent),
            proxy=args.proxy,
            timeout=args.timeout,
            retries=args.retries,
            backoff=args.backoff,
        )

        if args.format == "jsonl":
            sys.stdout.write(to_jsonl(findings) if findings else "")
        else:
            sys.stdout.write(summary(findings))

    elif args.cmd == "templates":
        if args.tpl_cmd == "install":
            dst = Path(args.dst)
            dst.mkdir(parents=True, exist_ok=True)
            if args.src.endswith(".zip"):
                import tempfile, zipfile, requests
                with tempfile.TemporaryDirectory() as td:
                    zpath = Path(td) / "templates.zip"
                    r = requests.get(args.src, timeout=60)
                    r.raise_for_status()
                    zpath.write_bytes(r.content)
                    with zipfile.ZipFile(zpath) as zf:
                        zf.extractall(dst)
            else:
                # assume git
                import subprocess
                if (dst / ".git").exists():
                    subprocess.run(["git", "-C", str(dst), "pull", "--ff-only"], check=True)
                else:
                    subprocess.run(["git", "clone", "--depth", "1", args.src, str(dst)], check=True)
            print(f"Templates installed at: {dst}")

        elif args.tpl_cmd == "update":
            import subprocess
            dst = Path(args.dst)
            if (dst / ".git").exists():
                subprocess.run(["git", "-C", str(dst), "pull", "--ff-only"], check=True)
                print(f"Templates updated at: {dst}")
            else:
                print(f"{dst} is not a git repo; use `gosek templates install` instead.")

        elif args.tpl_cmd == "list":
            tdir = Path(args.templates)
            if not tdir.exists():
                raise SystemExit(f"Templates folder not found: {tdir}")
            files = [
                str(p.relative_to(tdir))
                for p in tdir.rglob("*")
                if p.suffix.lower() in {".json", ".yaml", ".yml", ".toml"} and p.is_file()
            ]
            for f in sorted(files):
                print(f)
