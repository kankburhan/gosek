# 🕵️‍♂️ gosek — Secret Finder

> **Name origins (Javanese + English):**
> *Golek* (to seek) + *Sekret* (secret) → **gosek** = “secret seeker”.
>
> **Philosophy:**
> *Gosek* represents the Javanese spirit of exploration, curiosity, and persistence.
> In Javanese, *nggosek* means to search deeply — to uncover hidden truths beneath the surface.
> It’s the embodiment of a lifelong learner who never stops seeking knowledge and meaning.

---

## 🌍 Overview

**gosek** is a fast, concurrent, and extensible CLI tool for discovering secrets or sensitive tokens within text, files, or URLs.
It loads its regex-based detection patterns from **external template repositories**, just like `nuclei` does with its template packs.

---

## ⚡ Features

* 🧩 **Template-based** architecture (JSON, YAML, or TOML)
* ⚙️ **Concurrent scanning** (configurable workers)
* 🌐 **Proxy support** for remote scanning
* 🔁 **Retry + exponential backoff** for resilient URL fetching
* 🧵 **Pipeline input** for streaming scans from stdin
* 🔄 **Self-updating templates** (from Git or ZIP)

---

## 🧭 Installation

```bash
# install core
pip install -e .[yaml,toml]

# install templates repository (separate)
gosek templates install \
  --from https://github.com/kankburhan/gosek-templates.git \
  --to   ~/.gosek/templates
```

> Default templates path: `~/.gosek/templates`
> You can override it using `--templates` or `GOSEK_TEMPLATES` environment variable.
 
 ## 🚀 Easy install

 If you just want to try gosek quickly, here are two simple options:

 - Quick install from PyPI (if available):

 ```bash
 pip install gosek
 ```

 - Developer / editable install (recommended when modifying or contributing):

 ```bash
 pip install -e .[yaml,toml]
 ```

 Notes:
 - The `[yaml,toml]` extras install optional parsers (PyYAML / tomli) used for template files.
 - If the PyPI package isn't available, use the editable install above.

---

## 🔍 Usage Examples

```bash
# Scan a single URL
gosek scan --url https://example.com/app.js

# Scan a file containing many URLs
gosek scan --url ./urls.txt

# Scan a local file
gosek scan --file ./bundle.js

# Use stdin pipeline
cat targets.txt | gosek scan

# Run faster with more workers
gosek scan --url ./urls.txt --concurrent 50

# Add proxy, retry, and backoff options
gosek scan --url ./urls.txt --proxy http://127.0.0.1:8080 --retries 4 --backoff 0.6
```

---

## ✨ Quick start — easy to use

Copy-paste the shortest commands to get results fast (zsh-compatible):

- Scan a single remote URL and print JSONL results:

```bash
gosek scan -u https://example.com/app.js -t ~/.gosek/templates -f jsonl
```

- Scan a local file (single file scan):

```bash
gosek scan -f ./bundle.js
```

- Stream targets via stdin (pipeline):

```bash
cat urls.txt | gosek scan -t ~/.gosek/templates
```

- Install templates (from a git repo):

```bash
gosek templates install --from https://github.com/kankburhan/gosek-templates.git --to ~/.gosek/templates
```

Tips:
- Use `--concurrent N` to speed up many URL scans (increase N cautiously).
- Use `--format summary` for a compact CSV-like pattern counts view.
- If you see no templates found, confirm `~/.gosek/templates` exists or pass `--templates`.


## 📚 Template Management

### Install

```bash
gosek templates install --from <git_or_zip_url> --to ~/.gosek/templates
```

### Update

```bash
gosek templates update --to ~/.gosek/templates
```

### List

```bash
gosek templates list --templates ~/.gosek/templates
```

---

## 🧩 Template Format

Templates are stored as structured data files (JSON/YAML/TOML), where each file contains multiple pattern objects:

```json
[
  {"name": "AWS Access Key ID", "pattern": "AKIA[0-9A-Z]{16}"},
  {"name": "GitHub Token", "pattern": "ghp_[0-9a-zA-Z]{36}"}
]
```

Each pattern object supports optional fields like `flags` (e.g. `IGNORECASE`, `MULTILINE`, etc.).

---

## 🔐 Responsible Use

**gosek** should be used only on assets you own or have permission to test.
While it’s powerful, regex-based detection may result in **false positives** or expose sensitive information; always verify findings manually and ensure you have explicit permission before scanning targets. Respect legal and ethical boundaries when using this tool.

---

If you'd like, I can further shorten the README to a one-page quickstart or add example `requirements.txt`/`pyproject.toml` snippets for easier installs in virtualenvs.
