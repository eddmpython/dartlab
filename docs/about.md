---
title: About DartLab
description: What DartLab builds, what data it handles, and who maintains it.
---

# About DartLab

DartLab is an open-source project built for structurally reading Korean FSS DART disclosures and US SEC EDGAR data. The goal is not simple lookup — it's creating a repeatable analysis foundation by unifying financial numbers and disclosure documents into a single data flow.

## What It Builds

DartLab handles three layers together:

- Quantitative data like financial statements and ratios
- Qualitative data like annual reports, audit reports, MD&A, and footnotes
- A standardization layer that makes all of the above directly reusable in code

The core idea: connecting "how to read disclosures" and "how to use disclosures as data" within one project.

## Why It Was Built

DART and EDGAR contain excellent information, but most of it requires manually opening websites and navigating documents one by one. Investors, researchers, and developers repeat the same work.

DartLab started to reduce this inefficiency:

- Structures disclosure documents by topic
- Organizes XBRL financial data into time series
- Handles disclosure text and numbers within the same company object
- Publishes interpretation methods through blog posts and documentation

## What Data It Covers

Key data sources:

- DART disclosure document originals
- OpenDART API and XBRL financial statements
- DART periodic report structured data
- SEC EDGAR filing originals and XBRL data

An important principle is **source-aware structure**: numbers prioritize the stronger source, while narrative information prioritizes preserving original context.

## Who Maintains It

The project author and maintainer is `eddmpython`. Tools and articles are continuously published through GitHub, PyPI, YouTube, Threads, and blog.

- GitHub: https://github.com/eddmpython
- PyPI: https://pypi.org/user/eddmpython/
- YouTube: https://www.youtube.com/@eddmpython
- Threads: https://www.threads.net/@eddmpython
- Blog: https://eddm.tistory.com

## How to Read This Site

If you're visiting for the first time, this order is most efficient:

1. Installation guide
2. Quick Start
3. API Overview
4. Introductory blog posts

Documentation covers usage and structure; the blog covers interpretation frameworks for actually reading disclosures. Reading both together is faster.

## Citations and Sources

DartLab documentation and blog posts include official sources wherever possible. Primary sources like DART, OpenDART, SEC, and IFRS are prioritized, with interpretations and implementations clearly separated.

When citing this project, these pages serve as good starting points:

- Documentation: `/docs/api/overview`
- Installation: `/docs/getting-started/installation`
- Blog hub: `/blog/`
- GitHub repository: `https://github.com/eddmpython/dartlab`

## FAQ

### What problem does DartLab solve?

It transforms disclosure data from a human-read-only state into a structure that can be reused in code and pipelines.

### Who is DartLab for?

It's most directly useful for investors, quant researchers, data engineers, and developers working on accounting/disclosure automation.

### What should I read first on this site?

Most users find it most efficient to start with the Installation guide and Quick Start. If you need an interpretation perspective, read the introductory blog posts alongside.

### What are the data sources?

Core sources are FSS DART, OpenDART, SEC EDGAR, XBRL originals, and periodic report API data.

### How should I cite DartLab?

Use the canonical URLs for documentation, blog posts, and the GitHub repository. For implementation topics, GitHub is more appropriate; for interpretation topics, use the blog/documentation.
