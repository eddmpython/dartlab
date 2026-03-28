---
title: Notebooks
---

# Notebooks

DartLab does three things. One notebook each, in two formats.

| Feature | What it covers | Colab | Molab |
|---------|---------------|-------|-------|
| **Company** | `Company("005930")` -- sections, show, trace, diff, BS/IS/CF, ratios, EDGAR | [![Open in Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) | [![Open in Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) |
| **Scan** | `scan()` -- 13-axis market scan, 2,700+ companies | [![Open in Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) | [![Open in Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/02_scan.py) |
| **Ask** | `ask()` -- AI analysis, streaming, 9 LLM providers | [![Open in Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_ask.ipynb) | [![Open in Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/03_ask.py) |

**Colab** runs in browser (Google account). **Molab** runs in browser (marimo cloud, free).

## Run locally with Marimo

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/01_company.py
marimo edit notebooks/marimo/02_scan.py
marimo edit notebooks/marimo/03_ask.py
```
