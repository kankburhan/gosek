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
  --from https://github.com/your-org/gosek-templates.git \
  --to   ~/.gosek/templates
```

> Default templates path: `~/.gosek/templates`
> You can override it using `--templates` or `GOSEK_TEMPLATES` environment variable.

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
While it’s powerful, regex-based detection may result in **false positives** or expose sensitive infor
