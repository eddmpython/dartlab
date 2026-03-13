# Engines Development Guide

이 문서는 `src/dartlab/engines/` 하위 엔진 구조를 설명하는 내부 개발 문서다.

## 레이어

- 루트 facade
  - `dartlab.Company`
  - `dartlab.Compare`
- 엔진 본체
  - `dartlab.engines.dart.*`
  - `dartlab.engines.edgar.*`

의존 방향:
- 루트 facade -> 엔진 본체
- 엔진 본체 -> 루트 facade 금지

## Company 사상

- `Company`는 source 묶음이 아니라 merged company object다.
- `docs`는 구조 spine이다.
- `finance`는 숫자 authoritative source다.
- `report`는 structured disclosure authoritative source다.

사용자 모델:
- `index` : 전체 수평화 보드
- `show(topic, period?, raw?)` : 실제 payload
- `trace(topic, period?)` : source provenance

## DART Company 구조

- `c.docs`
  - `sections`, `retrievalBlocks`, `contextSlices`, `filings`
- `c.finance`
  - `BS`, `IS`, `CIS`, `CF`, `SCE`, `ratios`, `timeseries`
- `c.report`
  - 28개 apiType 체계, `result()`, `status()`, `extract()`, `extractAnnual()`
- `c.profile`
  - merged layer

기본 사용은 `Company(...)` 후 `index/show/trace`다.

상세 문서:
- `src/dartlab/engines/dart/DEV.md`
