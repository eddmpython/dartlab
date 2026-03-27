# dartlab 구조 맵 (자동 생성)

**총계**: 650개 파일, 3899개 함수, 426개 클래스, 136,024줄
**Registry**: 70개 DataEntry
**복잡도 핫스팟**: E/F 등급 125개

## 레이어별 현황

| 레이어 | 파일 | 함수 | 클래스 | 줄 |
|--------|------|------|--------|------|
| L0 core | 44 | 354 | 44 | 10,488 |
| L1 providers | 260 | 1363 | 126 | 45,429 |
| L1 gather | 33 | 212 | 43 | 5,624 |
| L1 market | 27 | 102 | 1 | 4,609 |
| L2 analysis | 84 | 470 | 88 | 23,647 |
| L3 ai | 100 | 735 | 56 | 27,539 |
| Server | 27 | 214 | 36 | 5,261 |
| CLI | 30 | 158 | 5 | 4,403 |
| Export | 5 | 43 | 5 | 1,017 |
| MCP | 3 | 13 | 2 | 381 |
| Display | 9 | 28 | 0 | 822 |
| Tools | 5 | 52 | 1 | 2,555 |
| Channel | 7 | 43 | 8 | 692 |
| Review | 12 | 58 | 10 | 2,117 |
| Root | 4 | 54 | 1 | 1,440 |

## 레이어별 외부 import

- **L0 core**: alive_progress, base64, contextlib, ctypes, diff_match_patch, difflib, gc, huggingface_hub, importlib, inspect, io, plotly, polars, rich, scipy
- **L1 providers**: alive_progress, asyncio, bs4, calendar, concurrent, contextlib, csv, difflib, gc, httpx, importlib, io, lxml, polars, random
- **L1 gather**: asyncio, bs4, cache, client, concurrent, domains, duckduckgo_search, html, http, httpx, market_config, polars, random, requests, resilience
- **L1 market**: bisect, polars, shutil, threading
- **L2 analysis**: asyncio, concurrent, difflib, importlib, numpy, polars, random, rich, scipy, sklearn, statistics, synthesizer, threading, types, warnings
- **L3 ai**: _helpers, analysis, analyze, anthropic, ast, base64, benchmarkData, chart, coding, company, contextlib, defaults, dialogue, explore, finance
- **Server**: ai, analysis, api, argparse, ask, asyncio, cache, chat, common, company, contextlib, data, difflib, embed, fastapi
- **CLI**: argparse, asyncio, http, importlib, io, main, polars, prompt_toolkit, qrcode, rich, shutil, sqlite3, subprocess, threading, urllib
- **Export**: openpyxl, polars
- **MCP**: asyncio, bridge, mcp
- **Display**: altair, great_tables, itables, polars, rich
- **Tools**: base64, difflib, plotly, polars, tempfile, webbrowser
- **Channel**: asyncio, atexit, discord, importlib, inspect, pycloudflared, pyngrok, slack_bolt, subprocess, telegram
- **Review**: IPython, contextlib, polars, rich, unicodedata
- **Root**: getpass, importlib, rich, yaml

## 복잡도 핫스팟 (E/F 등급, Top 20)

| 파일 | 함수 | 복잡도 | 등급 |
|------|------|--------|------|
| analysis/forecast/revenueForecast.py:912 | forecastRevenue | 174 | F |
| providers/dart/docs/disclosure/rawMaterial/parser.py:71 | parseRawMaterials | 168 | F |
| core/finance/ratios.py:1441 | calcRatioSeries | 158 | F |
| core/finance/ratios.py:981 | _calcComposite | 141 | F |
| ai/context/finance_context.py:604 | _build_ratios_section | 129 | F |
| ai/runtime/core.py:498 | _analyze_inner | 122 | F |
| analysis/financial/research/orchestrator.py:329 | _buildFinancial | 114 | F |
| providers/dart/finance/sceMapper.py:648 | normalizeDetail | 99 | F |
| analysis/financial/research/narrative.py:2330 | _detectCrossReferences | 97 | F |
| providers/dart/docs/finance/affiliate/parser.py:201 | extractProfiles | 97 | F |
| analysis/financial/research/narrative.py:213 | _analyzeMarginTrend | 86 | F |
| providers/dart/docs/sections/pipeline.py:1401 | sections | 86 | F |
| providers/edgar/finance/_reference/experiments/005_rollbackBadFixes.py:136 | phase1_identifyBadFixes | 85 | F |
| providers/dart/_table_horizontalizer.py:83 | horizontalizeTableBlock | 74 | F |
| market/network/classifier.py:196 | classify_balanced | 72 | F |
| analysis/financial/research/narrative.py:569 | _analyzeEfficiency | 70 | F |
| analysis/financial/research/narrative.py:904 | _analyzeDebtStructure | 70 | F |
| analysis/forecast/proforma.py:316 | extract_historical_ratios | 68 | F |
| providers/edgar/finance/_reference/experiments/003_fixAndDerive.py:452 | autoClassify | 68 | F |
| ai/context/builder.py:1087 | _build_compact_context_modules_inner | 66 | F |

... 외 105개

---
*`python scripts/structureMap.py`로 자동 생성*
