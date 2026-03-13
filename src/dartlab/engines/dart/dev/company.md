# DART Company Development Guide

본체 위치:
- `src/dartlab/engines/dart/company.py`

핵심 모델:
- `index / show / trace`

## Source 역할

- `sections`
  - docs source of truth
  - 회사 전체 수평화 spine
- `finance`
  - `BS / IS / CIS / CF / SCE`
  - 숫자 authoritative source
- `report`
  - sections보다 더 좋은 structured 시계열 source

## show 계약

- statement topic
  - 원형 `pl.DataFrame`
- report topic
  - annual/pivot `pl.DataFrame`
- sections-heavy topic
  - 기본: `subtopic` wide `pl.DataFrame`
  - `raw=True`: long `pl.DataFrame`

## Trace 규칙

- `trace("BS")` -> `finance`
- `trace("dividend")` -> `report`
- `trace("riskDerivative")` -> `docs`

## 현재 sections 우선 topic

- `salesOrder`
- `riskDerivative`
- `segments`
- `rawMaterial`
- `costByNature`

## 현재 legacy 유지 topic

- `tangibleAsset`
