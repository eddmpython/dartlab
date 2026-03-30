---
title: Notebooks
---

# Notebooks

Colab은 브라우저에서 바로 실행 (Google 계정). Molab은 marimo 클라우드 (무료).

| 기능 | 설명 | Colab | Molab |
|------|------|-------|-------|
| **Company** | `Company("005930")` -- sections, show, trace, diff, 재무 | [![Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) | [![Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) |
| **Scan** | `scan()` -- 13축 전종목 횡단 스캔 | [![Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) | [![Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/02_scan.py) |
| **Review** | `c.review()` -- 구조화 보고서 + AI 해석 | [![Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_review.ipynb) | [![Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/03_review.py) |
| **Gather** | `gather()` -- 주가, 수급, 거시, 뉴스 | [![Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_gather.ipynb) | [![Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/04_gather.py) |
| **Analysis** | `c.analysis()` -- 14축 분석, 인사이트, 전망, 밸류에이션 | [![Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/05_analysis.ipynb) | [![Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/05_analysis.py) |
| **Ask (AI)** | `ask("...")` -- 자연어 LLM 분석 | [![Colab](https://img.shields.io/badge/Colab-ea4647?style=flat-square&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/06_ask.ipynb) | [![Molab](https://img.shields.io/badge/Molab-38bdf8?style=flat-square)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/06_ask.py) |

## 로컬에서 Marimo로 실행

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/01_company.py
```
