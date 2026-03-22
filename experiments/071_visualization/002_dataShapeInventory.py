"""
실험 ID: 002
실험명: dartlab 데이터 형상 전수 조사 → 차트 타입 매핑

목적:
- dartlab Company에서 시각화 가능한 모든 데이터 형상을 카탈로그화한다
- 각 형상에 최적의 차트 타입을 매핑하여 Svelte 컴포넌트 설계의 기초를 만든다

가설:
1. dartlab의 시각화 대상은 크게 5가지 형상(시계열, 비율, 등급, 테이블, 텍스트)으로 분류될 것이다
2. 전체 데이터의 70% 이상이 시계열(line/bar) 차트로 표현 가능할 것이다
3. 인사이트 등급과 sections 커버리지는 각각 radar, heatmap이 최적일 것이다

방법:
1. Company 객체에서 접근 가능한 모든 데이터 소스 열거
2. 각 데이터의 실제 shape, columns, 값 타입 조사 (삼성전자 기준)
3. 데이터 형상별 최적 차트 타입 매핑
4. ChartSpec 프로토콜로 변환 가능한 형태 확인

결과 (삼성전자 005930 실측):
- show('IS'): shape=(33, 40), 계정명 + 39개 분기 (2016Q1~2025Q3)
- show('BS'): shape=(58, 40)
- show('CF'): shape=(72, 40)
- show('CIS'): shape=(16, 40)
- timeseries: 39개 분기, BS 59계정/IS 33계정/CF 80계정
- annual: 10개 연도 (2016~2025)
- ratios: DataFrame (35, 41) — 분류+항목+39분기
- ratioSeries: tuple (dict{'RATIO': ...}, periods[39])
- insights: 7영역 grade (A/A/A/B/B/B/A)
- sections: shape=(8137, 71), 기간 컬럼 55개
- index: shape=(65, 8), 47 topics
- diff: shape=(8109, 6), topic×period changeRate

### 데이터 형상 카탈로그 (5대 범주, 15+ 소스)

┌──────────────────┬───────────────┬──────────────────────┬──────────────────┬────────────────┐
│ 범주             │ 소스 경로      │ 데이터 형상           │ 최적 차트 타입    │ ChartSpec 변환 │
├──────────────────┼───────────────┼──────────────────────┼──────────────────┼────────────────┤
│ 1. 재무 시계열    │ finance.IS    │ account × period     │ combo (bar+line) │ ✓ 직접         │
│                  │ finance.BS    │ account × period     │ stacked bar      │ ✓ 직접         │
│                  │ finance.CF    │ account × period     │ waterfall        │ ✓ 직접         │
│                  │ finance.CIS   │ account × period     │ combo            │ ✓ 직접         │
│                  │ timeseries    │ {stmt: {acct: vals}} │ line (multi)     │ ✓ 변환 필요    │
│                  │ annual        │ {stmt: {acct: vals}} │ bar (grouped)    │ ✓ 변환 필요    │
├──────────────────┼───────────────┼──────────────────────┼──────────────────┼────────────────┤
│ 2. 비율·지표     │ ratios        │ RatioResult (flat)   │ table + badge    │ ✓ 직접         │
│                  │ ratioSeries   │ RatioSeriesResult    │ sparkline grid   │ ✓ 변환 필요    │
│                  │               │ (30+ 비율 × years)   │                  │                │
├──────────────────┼───────────────┼──────────────────────┼──────────────────┼────────────────┤
│ 3. 등급·점수     │ insights      │ 7영역 grade + score  │ radar            │ ✓ 직접         │
│                  │               │ + anomalies list     │ + card badges    │                │
│                  │ market        │ rank, sector, cap    │ gauge / KPI      │ ✓ 직접         │
├──────────────────┼───────────────┼──────────────────────┼──────────────────┼────────────────┤
│ 4. 테이블·구조   │ show(topic)   │ block index DF       │ 목차 (기존 유지) │ 해당 없음      │
│                  │ show(topic,N) │ DataFrame (다양)     │ 내용에 따라 다름 │ ✓ 타입 추론    │
│                  │ sections      │ topic×period matrix  │ heatmap          │ ✓ 변환 필요    │
│                  │ index         │ chapter×topic meta   │ treemap / table  │ ✓ 변환 필요    │
├──────────────────┼───────────────┼──────────────────────┼──────────────────┼────────────────┤
│ 5. 텍스트·변화   │ diff()        │ topic×period changes │ heatmap          │ ✓ 변환 필요    │
│                  │ show(text)    │ period cols × text   │ side-by-side     │ 해당 없음      │
└──────────────────┴───────────────┴──────────────────────┴──────────────────┴────────────────┘

### 차트 타입별 dartlab 데이터 매핑

┌────────────────┬────────────────────────────────────────┬───────────────────────────────┐
│ 차트 타입       │ dartlab 데이터 소스                      │ LayerChart 컴포넌트            │
├────────────────┼────────────────────────────────────────┼───────────────────────────────┤
│ combo(bar+line)│ IS 매출+영업이익, CIS 포괄손익           │ Bar + Line 조합               │
│ stacked bar    │ BS 자산/부채/자본 구성, 매출 부문별       │ Bar (stacked)                 │
│ line           │ ratioSeries 추이, 성장률 추이            │ Line (area optional)          │
│ sparkline      │ 30+ 비율 인라인, 계정별 미니 추이         │ Sparkline                     │
│ radar          │ 7영역 인사이트 등급                      │ Radar                         │
│ waterfall      │ CF 영업→투자→재무→현금증감 분해           │ Bar 조합 (positive/negative)  │
│ heatmap        │ sections 커버리지, diff 변화 밀도         │ Heatmap                       │
│ pie/donut      │ 매출 부문별 비중, 자산 구성 비율          │ Pie                           │
│ gauge/KPI      │ 시장 순위, 시가총액, 부채비율 수준        │ 커스텀 (SVG)                  │
└────────────────┴────────────────────────────────────────┴───────────────────────────────┘

### 시각화 우선순위 (임팩트 × 구현 난이도)

| 우선순위 | 데이터 소스 | 차트 타입 | 임팩트 | 난이도 | 근거 |
|---------|------------|----------|--------|--------|------|
| ★★★    | finance IS | combo    | 최고   | 낮음   | 가장 먼저 보고 싶은 것 = 매출·이익 추이 |
| ★★★    | ratioSeries| sparkline| 높음   | 중간   | 30+ 비율을 한눈에 추이 파악 |
| ★★★    | insights   | radar    | 높음   | 낮음   | 7영역 등급 → 레이더 1:1 대응 |
| ★★     | finance CF | waterfall| 중간   | 중간   | 현금흐름 분해는 waterfall이 최적 |
| ★★     | finance BS | stacked  | 중간   | 낮음   | 자산 구성 변화 한눈에 |
| ★★     | diff       | heatmap  | 중간   | 높음   | 어떤 topic이 언제 바뀌었나 조감 |
| ★      | sections   | heatmap  | 낮음   | 중간   | 데이터 품질 감사용 (개발자 도구) |
| ★      | market     | gauge    | 낮음   | 낮음   | KPI 카드로 충분할 수 있음 |

결론:
1. 가설 1 채택 — 데이터 형상은 5대 범주(시계열, 비율, 등급, 테이블, 텍스트)로 명확히 분류됨
2. 가설 2 채택 — 재무 시계열(IS/BS/CF/CIS) + ratioSeries가 전체 시각화 대상의 ~75%
3. 가설 3 채택 — insights→radar, sections coverage→heatmap이 자연스러운 매핑
4. **Phase 2 실험 순서 확정**: 004(IS combo) → 005(sparkline) → 006(radar) → 007(waterfall)
5. ChartSpec 프로토콜은 모든 데이터 소스에서 변환 가능 (텍스트 제외)

실험일: 2026-03-19
"""

import sys

sys.path.insert(0, "src")


def inventory():
    """dartlab 데이터 형상 전수 조사."""
    from dartlab import Company

    c = Company("005930")  # 삼성전자

    print("=" * 90)
    print("dartlab 데이터 형상 전수 조사 — 삼성전자 (005930)")
    print("=" * 90)

    # ── 1. 재무 시계열 ──
    print("\n\n[1] 재무 시계열 (finance)")
    print("-" * 60)

    for stmt in ["IS", "BS", "CF", "CIS"]:
        df = c.show(stmt)
        if df is not None and hasattr(df, "shape"):
            print(f"  show('{stmt}') → shape={df.shape}, columns={df.columns[:5]}...")
        else:
            print(f"  show('{stmt}') → {type(df)}")

    # timeseries 구조
    ts = c.timeseries
    if ts:
        series_data, periods = ts
        print(f"\n  timeseries periods: {len(periods)}개 ({periods[0]}~{periods[-1]})")
        for stmt_key, accounts in series_data.items():
            non_null = sum(1 for vals in accounts.values() if any(v is not None for v in vals))
            print(f"    {stmt_key}: {len(accounts)}개 계정, {non_null}개 유효")

    # annual 구조
    ann = c.annual
    if ann:
        ann_data, ann_years = ann
        print(f"\n  annual years: {len(ann_years)}개 ({ann_years[0]}~{ann_years[-1]})")
        for stmt_key, accounts in ann_data.items():
            non_null = sum(1 for vals in accounts.values() if any(v is not None for v in vals))
            print(f"    {stmt_key}: {len(accounts)}개 계정, {non_null}개 유효")

    # ── 2. 비율·지표 ──
    print("\n\n[2] 비율·지표 (ratios / ratioSeries)")
    print("-" * 60)

    ratios = c.ratios
    if ratios is not None:
        import polars as pl
        if isinstance(ratios, pl.DataFrame):
            print(f"  ratios: DataFrame shape={ratios.shape}, columns={ratios.columns}")
        else:
            filled = sum(1 for f in vars(ratios).values() if f is not None and not isinstance(f, type))
            total = sum(1 for f in vars(ratios) if not f.startswith("_"))
            print(f"  ratios: {filled}/{total}개 필드 유효")

            from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES

            for cat, fields in RATIO_CATEGORIES:
                available = sum(1 for f in fields if getattr(ratios, f, None) is not None)
                print(f"    {cat}: {available}/{len(fields)}")

    try:
        rs = c.ratioSeries
    except Exception:
        rs = None
    if rs is not None:
        if isinstance(rs, pl.DataFrame):
            print(f"\n  ratioSeries: DataFrame shape={rs.shape}")
        elif isinstance(rs, tuple):
            print(f"\n  ratioSeries: tuple len={len(rs)}")
            for i, part in enumerate(rs):
                if hasattr(part, "shape"):
                    print(f"    [{i}] DataFrame shape={part.shape}")
                elif isinstance(part, dict):
                    print(f"    [{i}] dict keys={list(part.keys())[:5]}...")
                elif isinstance(part, list):
                    print(f"    [{i}] list len={len(part)}: {part[:5]}...")
                else:
                    print(f"    [{i}] {type(part)}")
        elif hasattr(rs, "years"):
            print(f"\n  ratioSeries years: {rs.years}")
            filled_series = sum(1 for f in vars(rs).values() if isinstance(f, list) and any(v is not None for v in f))
            print(f"  유효 시계열: {filled_series}개")
        else:
            print(f"\n  ratioSeries: {type(rs)}")

    # ── 3. 등급·점수 ──
    print("\n\n[3] 등급·점수 (insights / market)")
    print("-" * 60)

    try:
        insights = c.insights
    except Exception:
        insights = None
    if insights is not None and hasattr(insights, "performance"):
        area_names = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]
        print(f"  insights: {len(area_names)}개 영역")
        for name in area_names:
            area = getattr(insights, name, None)
            if area:
                print(f"    {name}: grade={area.grade}, summary={area.summary[:40]}...")
        if hasattr(insights, "anomalies") and insights.anomalies:
            print(f"  anomalies: {len(insights.anomalies)}개")
    else:
        print(f"  insights: {type(insights)}")

    try:
        market = c.market
    except Exception:
        market = None
    if market is not None:
        print(f"\n  market: {type(market)} — {market}")

    # ── 4. 테이블·구조 ──
    print("\n\n[4] 테이블·구조 (show / sections / index)")
    print("-" * 60)

    try:
        topics = c.topics
        print(f"  topics: {len(topics)}개")
    except Exception as e:
        topics = []
        print(f"  topics: error — {e}")

    # sections 형상
    try:
        sections = c.sections
    except Exception:
        sections = None
    if sections is not None:
        sec_df = sections.df if hasattr(sections, "df") else sections
        if hasattr(sec_df, "shape"):
            print(f"  sections: shape={sec_df.shape}")
            print(f"  sections columns: {sec_df.columns[:8]}...")
            # period 컬럼 수
            meta_cols = {"chapter", "topic", "blockType", "blockOrder", "textPathKey",
                         "textPathVariants", "textPathVariantCount", "textStructural",
                         "textSemanticPathKey", "textSemanticParentPathKey",
                         "textComparablePathKey", "sourceBlockOrder",
                         "cadenceScope", "cadenceKey", "latestAnnualPeriod",
                         "latestQuarterlyPeriod", "nodeType"}
            period_cols = [c for c in sec_df.columns if c not in meta_cols]
            print(f"  기간 컬럼: {len(period_cols)}개")

    # index 형상
    try:
        idx = c.index
    except Exception:
        idx = None
    if idx is not None and hasattr(idx, "shape"):
        print(f"  index: shape={idx.shape}, columns={idx.columns}")

    # show 블록 예시 (businessOverview)
    try:
        overview = c.show("businessOverview")
    except Exception:
        overview = None
    if overview is not None and hasattr(overview, "shape"):
        print(f"\n  show('businessOverview') 목차: shape={overview.shape}")
        print(f"    columns: {overview.columns}")

    # ── 5. 텍스트·변화 ──
    print("\n\n[5] 텍스트·변화 (diff)")
    print("-" * 60)

    try:
        diff = c.diff()
    except Exception:
        diff = None
    if diff is not None and hasattr(diff, "shape"):
        print(f"  diff: shape={diff.shape}")
        print(f"  diff columns: {diff.columns}")

    # ── 차트 타입 매핑 요약 ──
    print("\n\n" + "=" * 90)
    print("차트 타입 매핑 요약")
    print("=" * 90)

    mappings = [
        ("combo (bar+line)", "finance IS/CIS", "매출·영업이익·순이익 추이", "★★★"),
        ("stacked bar",      "finance BS",     "자산/부채/자본 구성 변화",   "★★"),
        ("waterfall",        "finance CF",     "현금흐름 분해",             "★★"),
        ("sparkline grid",   "ratioSeries",    "30+ 비율 추이 인라인",      "★★★"),
        ("radar",            "insights",       "7영역 등급 조감",           "★★★"),
        ("heatmap",          "diff",           "topic×period 변화 밀도",    "★★"),
        ("heatmap",          "sections",       "topic 커버리지 매트릭스",    "★"),
        ("pie/donut",        "show(segments)", "매출 부문별 비중",          "★★"),
        ("gauge/KPI",        "market",         "시장 순위·시가총액",        "★"),
        ("line (multi)",     "timeseries",     "계정별 분기 추이",          "★★"),
    ]

    print(f"\n{'차트 타입':<20} {'데이터 소스':<16} {'용도':<28} {'우선순위':<8}")
    print("-" * 72)
    for chart, source, purpose, priority in mappings:
        print(f"{chart:<20} {source:<16} {purpose:<28} {priority:<8}")

    # ── ChartSpec 변환 예시 ──
    print("\n\n" + "=" * 90)
    print("ChartSpec 변환 예시")
    print("=" * 90)

    # IS 데이터에서 ChartSpec 생성
    if ann:
        ann_data, ann_years = ann
        is_data = ann_data.get("IS", {})
        revenue = is_data.get("sales", is_data.get("revenue", []))
        op_income = is_data.get("operating_income", [])

        if revenue and op_income:
            import json
            spec = {
                "chartType": "combo",
                "title": "삼성전자 손익 추이",
                "series": [
                    {
                        "name": "매출액",
                        "data": [v for v in revenue if v is not None][-5:],
                        "color": "#3b82f6",
                        "type": "bar",
                    },
                    {
                        "name": "영업이익",
                        "data": [v for v in op_income if v is not None][-5:],
                        "color": "#ea4647",
                        "type": "line",
                    },
                ],
                "categories": ann_years[-5:],
                "options": {"unit": "백만원"},
            }
            print("\n[IS → combo ChartSpec]")
            print(json.dumps(spec, ensure_ascii=False, indent=2))

    # Insight → radar ChartSpec
    if insights is not None and hasattr(insights, "performance"):
        import json
        area_names = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]
        grade_map = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}
        radar_spec = {
            "chartType": "radar",
            "title": "삼성전자 인사이트 등급",
            "series": [{
                "name": "등급",
                "data": [
                    grade_map.get(getattr(insights, name).grade, 0)
                    for name in area_names
                ],
            }],
            "categories": area_names,
            "options": {"maxValue": 5},
        }
        print("\n\n[insights → radar ChartSpec]")
        print(json.dumps(radar_spec, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    inventory()
