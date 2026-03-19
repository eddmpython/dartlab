---
title: Installation
---

# Installation

DartLab requires **uv** and **Python**. Even if you've never installed Python, that's fine — uv handles it automatically.

> **What is uv?** A Python package manager written in Rust. 10–100x faster than pip, and it manages Python versions for you. Just install uv — no separate Python install needed.

---

## Step 0: Open a Terminal

A terminal is a program where you type text commands to install or run software.

### Windows

**Option 1** — Press `Win + R` on your keyboard. In the dialog that appears, type `powershell` and press Enter.

**Option 2** — Search for `PowerShell` in the taskbar search box. Click **Windows PowerShell**.

A blue (or black) window should appear. This is where you type commands.

> **Note**: Make sure to open **PowerShell**, not Command Prompt (cmd). The install commands won't work in cmd.

### macOS

**Option 1** — Press `Cmd + Space` to open Spotlight Search. Type `Terminal` and press Enter.

**Option 2** — Finder → Applications → Utilities → Terminal.

### Linux

Press `Ctrl + Alt + T` to open a terminal on most distributions.

---

## Step 1: Install uv

Copy and paste the command below into your terminal and press Enter.

### Windows (PowerShell)

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, **close and reopen** your terminal for the `uv` command to be recognized.

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, reopen your terminal or run `source ~/.bashrc` (or `~/.zshrc`).

### Verify Installation

```bash
uv --version
```

If a version number is printed, you're good. If you see `uv: command not found`, try reopening your terminal.

---

## Step 2: Create a Project

Create a folder for your DartLab work and initialize a Python project with uv.

```bash
uv init my-dart-analysis
cd my-dart-analysis
```

This command automatically:
- Detects or **downloads** Python 3.12+
- Creates `pyproject.toml` (project config file)
- Creates `.venv/` virtual environment

**No need to install Python manually.** uv downloads the appropriate version for you.

---

## Step 3: Install DartLab

```bash
uv add dartlab
```

That's it. Dependencies (Polars, rich, alive-progress) are installed automatically.

---

## Step 4: Verify Installation

```bash
uv run python -c "import dartlab; c = dartlab.Company('005930'); print(c.corpName)"
```

If `삼성전자` is printed, you're all set.

> `uv run` executes within the virtual environment. Using `uv run python` ensures the dartlab package you just installed is available.

---

## AI Analysis (dartlab ai)

To use the web interface for LLM-powered company analysis, install with AI dependencies:

```bash
uv add dartlab[ai]
uv run dartlab ai
```

A browser opens at `http://localhost:8400`. You'll need Ollama — install from [ollama.com](https://ollama.com/download), then run `ollama pull gemma3` to download a model.

---

## Requirements

| Package | Minimum Version | Note |
|---------|----------------|------|
| Python | 3.12 | Auto-installed by uv |
| Polars | 1.0.0 | Auto-installed |
| alive-progress | 3.0.0 | Progress bars |
| rich | 13.0.0 | Terminal output |

---

## Data

DartLab uses Parquet files parsed from DART disclosure originals. Over 260 listed companies are available on [GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-docs).

You don't need to download data manually. When you call `dartlab.Company("005930")`, missing files are **downloaded automatically**.

### Auto Download Behavior

```python
import dartlab

c = dartlab.Company("005930")   # auto-downloads if not local
```

1. Checks local `data/docsData/` directory
2. If missing, downloads the Parquet file from GitHub Releases
3. Loads automatically after download

### Manual Download

To download a single company:

```bash
mkdir -p data/docsData
curl -L -o data/docsData/005930.parquet \
  "https://github.com/eddmpython/dartlab/releases/download/data-docs/005930.parquet"
```

To bulk download all 260+ companies:

```python
from dartlab.core import downloadAll

downloadAll()
```

---

## Using Google Colab

To try DartLab without any local setup, run it in Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb)

In a Colab cell:

```python
!pip install dartlab

import dartlab
c = dartlab.Company("005930")
c.BS
```

---

## Troubleshooting

### `uv: command not found`

Close and reopen your terminal. If it still doesn't work, re-run the install script.

### Windows: `irm` command not recognized

You're likely in CMD (Command Prompt) instead of PowerShell. Press `Win + R` → type `powershell` → Enter.

### `ModuleNotFoundError: No module named 'dartlab'`

Make sure you're running with `uv run python`, not just `python`. `uv run python` uses the virtual environment where dartlab is installed.

### Slow data download

Data is downloaded from GitHub Releases, so speed depends on your network. Use `downloadAll()` to pre-download everything for faster subsequent use.

---

## Next Steps

- [Quick Start](./quickstart) — Full feature walkthrough
- [API Overview](../api/overview) — Complete property list

