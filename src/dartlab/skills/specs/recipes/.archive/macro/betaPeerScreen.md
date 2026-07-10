---
id: recipes.macro.betaPeerScreen
title: 같은 산업 동종업체 macroBeta outlier — idiosyncratic 매크로 노출
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 동일 산업 peer set 안에서 회사 별 macro beta (rate / FX / oil) 가 within-industry z ≥ |2| 인 outlier 식별. cross-market 단순 macro beta 는 "유가 상승 = 정유주" 같은 trivial 매핑만 잡지만, 같은 산업 안 outlier 는 회사 specifics (FX 헤지 / 변동금리 차입 / 원자재 다변화) 가 만든 idiosyncratic 노출을 드러냄. industry ↔ scan 격리 메우는 조합. 트리거 — 'macroBeta peer', 'idiosyncratic 매크로 노출', '같은 산업 outlier'.
whenToUse:
  - macroBeta peer
  - idiosyncratic 매크로
  - 동종업체 outlier
  - within-industry 베타
linkedSkills:
  - engines.gather
  - engines.scan
  - engines.industry
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.scenarioVisuals"
  - "engines.viz.tableBackedChart"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "stress·민감도·충격 전파는 engines.viz.scenarioVisuals를 사용하고 assumption grid 또는 수치 임계가 없으면 scenario table로 낮춘다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

gap:
  primary:
    - industry
    - scan
  secondary:
    - quant
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
    - "035420"
    - "051910"
    - "055550"
  asOfPolicy: latest
falsifier:
  description: "outlier 종목의 known FX 충격 (2022 USDKRW +12%) 시 실현 P&L 이 peer 평균과 동일하면 detection 무효"
  pythonCheck: |
    assert outlier_pnl_during_fx_shock != peer_mean_pnl_during_fx_shock
expectedNovelty:
  - withinIndustryZ
  - outlierFlag
forbidden:
  - cross-market beta 만으로 "매크로 sensitive 종목" 단정 금지 — peer 정규화 필수.
  - peer set 정의 (좁은 vs 넓은 산업) 에 따라 outlier 변동 — 자의적 선택 금지.
failureModes:
  - peer set 이 너무 좁으면 (3-4 개) z 통계 신뢰도 약함.
  - 60m rolling beta 가 regime change 가 있으면 평균 이동.
examples:
  - 화학업종 안 LG화학 oil-beta outlier
  - 자동차업종 현대차 FX-beta z
lastUpdated: '2026-05-13'
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import statistics

c = dartlab.Company("005930")

# 1. 동종업체 peer set
peers = c.gather("industryPeers") if hasattr(c, "gather") else None
if isinstance(peers, pl.DataFrame) and "stockCode" in peers.columns:
    peer_codes = peers["stockCode"].to_list()
elif isinstance(peers, list):
    peer_codes = [p.get("stockCode") for p in peers if isinstance(p, dict)]
else:
    peer_codes = []

# 자기 자신 + peer 합쳐서 macroBeta 산출
all_codes = list(set(["005930"] + peer_codes))[:20]

# 2. 각 종목의 macroBeta (rate / FX / oil)
beta_rows = []
for code in all_codes:
    try:
        co = dartlab.Company(code)
        beta = dartlab.scan("macroBeta") if hasattr(co, "scan") else None
        if isinstance(beta, dict):
            beta_rows.append({
                "stockCode": code,
                "rateBeta": float(beta.get("rateBeta", 0)),
                "fxBeta": float(beta.get("fxBeta", 0)),
                "oilBeta": float(beta.get("oilBeta", 0)),
            })
    except Exception:
        continue

if not beta_rows:
    emit_result(table=[], values={"outlierCount": 0}, date="2024-12-31")
else:
    # 3. within-industry z 계산 (각 beta 별)
    df = pl.DataFrame(beta_rows)
    out_rows = []
    for col in ("rateBeta", "fxBeta", "oilBeta"):
        values = df[col].to_list()
        if len(values) < 3:
            continue
        mean = statistics.fmean(values)
        stdev = statistics.pstdev(values)
        if stdev <= 0:
            continue
        for code, v in zip(df["stockCode"].to_list(), values):
            z = (v - mean) / stdev
            if abs(z) >= 2:
                out_rows.append({
                    "stockCode": code,
                    "betaType": col,
                    "betaValue": round(v, 4),
                    "peerMean": round(mean, 4),
                    "withinIndustryZ": round(z, 2),
                    "outlierFlag": True,
                })

    emit_result(
        table=out_rows,
        values={"outlierCount": len(out_rows), "peerCount": len(beta_rows)},
        date="2024-12-31",
        sources=["dartlab://company/gather/industryPeers", "dartlab://company/scan/macroBeta"],
    )
```

## 호출 동작

1. `c.gather("industryPeers")` — 동종업체 peer set.
2. 자기 + peer 의 `dartlab.scan("macroBeta")` — rate / FX / oil beta.
3. 각 beta 별 within-industry z = (value - peer_mean) / peer_stdev.
4. |z| ≥ 2 인 outlier 만 결과.

## 대표 반환 형태

`pl.DataFrame` — 컬럼 (outlier 만):
- `stockCode : str`
- `betaType : str` — rateBeta / fxBeta / oilBeta
- `betaValue : float`
- `peerMean : float`
- `withinIndustryZ : float`
- `outlierFlag : bool`

## 연계 절차

1. 본 recipe → idiosyncratic 매크로 outlier 종목.
2. outlier flag → `recipes.fundamental.credit.macroStress` 와 결합 — 매크로 충격 시 영향 정량화.
3. 시장 stress 시 → 기대 P&L 분기 (outlier vs peer) 검증 → backtest.
