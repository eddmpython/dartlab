# DartLab Marimo 노트북

11개 엔진별 노트북. 각 노트북은 **무인자 호출(가이드) + 단일 예시** 의 최소 단위.

dartlab 호출 계약은 단순하다 — 무인자 호출로 어떤 축이 있는지 본 후 단일 예시로 실제 데이터를 받는다. 나머지는 사용자가 추론한다.

각 셀은 주석으로 설명한다 (마크다운 셀 미사용 — marimo 노트북 관례).

## 노트북 (레이어 순)

| # | 노트북 | 엔진 | 설계 문서 |
|---|---|---|---|
| 01 | [01_company.py](01_company.py) | Company facade (L0/L1) — panel/select/sections/diff | [engines.company](../../engines.company) |
| 02 | [02_gather.py](02_gather.py) | gather — 외부 시장 데이터 (주가/수급/매크로/뉴스) | [engines.gather](../../engines.gather) |
| 03 | [03_scan.py](03_scan.py) | scan — 전 종목 횡단 사전 빌드 (parquet) | [engines.scan](../../engines.scan) |
| 04 | [04_quant.py](04_quant.py) | quant — 가격 기반 정량 신호 | [engines.quant](../../engines.quant) |
| 05 | [05_analysis.py](05_analysis.py) | analysis — 14축 재무분석 + forecast + valuation | [engines.analysis](../../engines.analysis) |
| 06 | [06_macro.py](06_macro.py) | macro — 사이클/금리/유동성/심리/자산 | [engines.macro](../../engines.macro) |
| 07 | [07_credit.py](07_credit.py) | credit — 독립 신용평가 (dCR 등급, 7축) | [engines.credit](../../engines.credit) |
| 08 | [08_story.py](08_story.py) | story — 4엔진 조합 보고서 (6막 서사) | [engines.story](../../engines.story) |
| 09 | [09_ai.py](09_ai.py) | ai — ask/chat (provider 키 필요) | [operation.opsAsSkills](../../operation.opsAsSkills) |
| 10 | [10_search.py](10_search.py) | search — 공시 시맨틱 검색 (beta) | [engines.search](../../engines.search) |
| 11 | [11_listing.py](11_listing.py) | listing — 종목/공시/topic 카탈로그 | [engines.gather](../../engines.gather) |

## 실행

```bash
pip install marimo dartlab
marimo edit notebooks/marimo/05_analysis.py
```

uv 사용 시 프로젝트 의존성에 marimo를 추가하지 말고 일회성 실행으로 연다:

```bash
uv run --with marimo marimo edit notebooks/marimo/05_analysis.py
```

또는 marimo.app 에서 바로 열기:

[![Open in marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo)

## 호출 계약 — 모든 엔진 동일

```python
import dartlab
dartlab.엔진()        # 가이드 — 어떤 축이 있는지 출력
dartlab.엔진("축")    # 단일 예시
```

각 엔진의 자세한 사용법은 ops 문서 링크 참조.

## marimo 노트북 작성 규약

- **마크다운 셀 금지** — `mo.md(...)` 사용하지 않는다. 셀마다 `# 주석` 으로 설명.
- **import 반복 금지** — `import dartlab` 은 첫 셀에서 1회. 이후 셀은 `def _(dartlab):` 로 받는다.
- **무인자 호출 = 가이드** 패턴 유지 — 첫 예시는 항상 `dartlab.엔진()` 또는 `c.엔진()`.
