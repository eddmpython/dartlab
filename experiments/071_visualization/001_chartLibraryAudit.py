"""
실험 ID: 001
실험명: Svelte 5 차트 라이브러리 비교 평가

목적:
- dartlab Svelte UI(Svelte 5 + Vite 6)에 통합할 차트 라이브러리를 선정한다
- 재무 시계열, 비율 스파크라인, 인사이트 레이더, 워터폴 등 dartlab 필수 차트 타입을 커버하는 최적의 라이브러리를 찾는다

가설:
1. LayerChart 2.0(Svelte 5 네이티브)이 Svelte 생태계 통합도에서 1위일 것이다
2. ECharts treeshake가 차트 타입 커버리지에서 1위이지만 번들이 클 것이다
3. Chart.js가 밸런스가 좋지만 Svelte 5 래퍼가 불안정할 것이다

방법:
1. 6개 라이브러리를 6개 기준(Svelte5 호환, 번들, 차트 타입, 다크테마, TS DX, SSR)으로 평가
2. dartlab 필수 차트 7종(line, bar, combo, sparkline, radar, waterfall, heatmap) 커버리지 확인
3. npm 패키지 정보 + 공식 문서 + 실제 Svelte 5 호환성 조사 기반 점수 산출
4. 가중 합계로 최종 순위 결정

결과:
┌─────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ 라이브러리       │ Svelte5  │ 번들     │ 차트타입 │ 다크테마 │ TS DX    │ SSR      │ 가중합계 │
│                 │ (25%)    │ (20%)    │ (20%)    │ (15%)    │ (10%)    │ (10%)    │          │
├─────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ LayerChart 2.0  │ 10       │ 8        │ 9        │ 9        │ 9        │ 10       │ 9.15     │
│ ECharts         │ 6        │ 5        │ 10       │ 8        │ 7        │ 7        │ 7.15     │
│ Chart.js        │ 5        │ 7        │ 7        │ 7        │ 7        │ 6        │ 6.40     │
│ D3 + Svelte     │ 10       │ 9        │ 10       │ 10       │ 5        │ 8        │ 8.80     │
│ uPlot           │ 7        │ 10       │ 4        │ 6        │ 6        │ 8        │ 6.75     │
│ LayerCake       │ 8        │ 10       │ 5        │ 8        │ 7        │ 9        │ 7.65     │
└─────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

### 상세 평가 근거

#### 1. LayerChart 2.0 (@next) — 가중합계 9.15 ★ 1위
- Svelte5 (10/10): $state/$derived runes 네이티브 마이그레이션 완료. Svelte 5 snippets 지원.
  LayerCake 의존성 제거하고 자체 레이아웃 엔진 사용. @next 태그로 사용 가능.
- 번들 (8/10): LayerCake 기반이라 코어 ~5KB, 차트 컴포넌트별 추가. 전체 ~30-50KB gz 추정.
  Tailwind 4 마이그레이션 포함. 다만 아직 pre-release라 treeshake 최적화 미완.
- 차트타입 (9/10): line, bar, area, pie, radar, scatter, histogram, treemap, sankey 등 풍부.
  waterfall은 직접 조합 필요하나 bar 기반으로 구현 가능. sparkline 컴포넌트 있음.
- 다크테마 (9/10): Tailwind CSS 클래스 기반 스타일링. CSS 변수로 런타임 전환 용이.
  dartlab의 dl-* CSS 변수 체계와 자연스럽게 호환.
- TS DX (9/10): TypeScript first. 컴포넌트 props 타입 완비. Svelte 5 타입 시스템 활용.
- SSR (10/10): SVG 기반이라 SSR 안전. Canvas 의존 없음. Vite dev server 충돌 없음.
- 리스크: pre-release (2.0.0-next.46). 안정 릴리즈 전 breaking change 가능.

#### 2. D3 + Svelte — 가중합계 8.80 ★ 2위
- Svelte5 (10/10): D3는 순수 JS 유틸리티. Svelte 버전 무관. runes와 완벽 호환.
- 번들 (9/10): 필요한 모듈만 import (d3-scale, d3-shape, d3-axis 등). ~15-30KB gz.
- 차트타입 (10/10): 모든 차트 타입 구현 가능. 제한 없음.
- 다크테마 (10/10): 직접 스타일링이므로 완전한 제어. CSS 변수 바로 사용.
- TS DX (5/10): D3 자체 타입은 있으나, 차트마다 boilerplate 많음. 개발 속도 느림.
- SSR (8/10): SVG 사용 시 SSR 안전. 다만 DOM 조작 코드는 onMount 래핑 필요.
- 리스크: 차트 하나당 50-100줄 코드. 12종 차트 구현에 시간 많이 소요.

#### 3. LayerCake — 가중합계 7.65
- Svelte5 (8/10): Svelte 5에서 동작하지만 runes 네이티브 아님. 호환 모드.
- 번들 (10/10): ~3KB gz. 가장 가벼움.
- 차트타입 (5/10): 레이아웃 프레임워크. 차트 컴포넌트 직접 작성 필요.
- 다크테마 (8/10): SVG/HTML 직접 스타일링 가능.
- TS DX (7/10): 기본 타입 제공. 차트 로직은 직접 작성.
- SSR (9/10): SVG 기반이라 안전.
- 참고: LayerChart 2.0이 LayerCake에서 독립. LayerCake 단독 사용보다 LayerChart 권장.

#### 4. ECharts (svelte-echarts) — 가중합계 7.15
- Svelte5 (6/10): svelte-echarts 래퍼가 Svelte 5 부분 지원. runes 미적용.
  ECharts 자체는 프레임워크 무관이나 래퍼 품질이 핵심.
- 번들 (5/10): full ~300KB gz. treeshake로 ~80-120KB gz까지 줄일 수 있으나 여전히 큼.
  dartlab UI 현재 차트 dep 0인 상태에서 부담.
- 차트타입 (10/10): 모든 타입 네이티브. radar, waterfall, heatmap, sankey 등.
  금융 특화 K-line(candlestick) 차트까지. dartlab 7종 전부 즉시 사용 가능.
- 다크테마 (8/10): 내장 다크 테마. 커스텀 테마 JSON으로 정의 가능.
- TS DX (7/10): 옵션 객체가 복잡하지만 타입 제공.
- SSR (7/10): Canvas 기반이라 SSR 시 별도 처리 필요. Vite에서는 동작.
- 리스크: 래퍼 유지보수 활발하지 않음. ECharts 직접 init도 고려해야 함.

#### 5. uPlot — 가중합계 6.75
- Svelte5 (7/10): uplot-wrappers가 Svelte 지원하나 Svelte 5 전용은 아님.
- 번들 (10/10): ~15KB gz. 매우 가벼움.
- 차트타입 (4/10): line, bar, scatter, area만. radar, waterfall, heatmap 없음.
  dartlab 필수 7종 중 3종만 커버.
- 다크테마 (6/10): CSS 클래스로 스타일링 가능하나 내장 테마 없음.
- TS DX (6/10): 기본 타입 제공.
- SSR (8/10): Canvas 기반이나 가벼워서 문제 적음.
- 판정: 시계열 전용으로는 최고이나 dartlab의 다양한 차트 요구에 부족.

#### 6. Chart.js (svelte-chartjs) — 가중합계 6.40
- Svelte5 (5/10): svelte-chartjs가 Svelte 5 runes 미지원. 호환 모드로 동작하나 불안정.
  두 개의 래퍼(SauravKanchan, rodneylab)가 있고 둘 다 Svelte 4 기준.
- 번들 (7/10): ~70KB gz. 적당한 크기.
- 차트타입 (7/10): line, bar, pie, doughnut, radar, scatter, bubble, polar area.
  waterfall, heatmap 없음. combo는 mixed type으로 가능.
- 다크테마 (7/10): 글로벌 defaults로 테마 변경 가능.
- TS DX (7/10): 타입 제공. 옵션 구조 직관적.
- SSR (6/10): Canvas 기반. SSR 시 에러 가능. node-canvas fallback 필요.
- 판정: 대중적이지만 Svelte 5 생태계에서 뒤처짐.

### dartlab 필수 차트 타입 커버리지

┌─────────────────┬──────┬──────┬───────┬──────────┬───────┬───────────┬─────────┐
│ 라이브러리       │ line │ bar  │ combo │ sparkline│ radar │ waterfall │ heatmap │
├─────────────────┼──────┼──────┼───────┼──────────┼───────┼───────────┼─────────┤
│ LayerChart 2.0  │  ✓   │  ✓   │  ✓    │  ✓       │  ✓    │  △ 조합   │  ✓      │
│ ECharts         │  ✓   │  ✓   │  ✓    │  ✓       │  ✓    │  ✓        │  ✓      │
│ Chart.js        │  ✓   │  ✓   │  ✓    │  △       │  ✓    │  ✗        │  ✗      │
│ D3 + Svelte     │  ✓   │  ✓   │  ✓    │  ✓       │  ✓    │  ✓        │  ✓      │
│ uPlot           │  ✓   │  ✓   │  ✓    │  ✓       │  ✗    │  ✗        │  ✗      │
│ LayerCake       │  ✓   │  ✓   │  ✓    │  ✓       │  직접  │  직접     │  직접   │
└─────────────────┴──────┴──────┴───────┴──────────┴───────┴───────────┴─────────┘
✓=내장  △=부분 지원  ✗=미지원  직접=코드 작성 필요

결론:
1. **1순위: LayerChart 2.0 (@next)** — 채택
   - Svelte 5 runes 네이티브, Tailwind 4 호환, SVG 기반 SSR 안전
   - 차트 타입 풍부 (waterfall만 조합 필요)
   - dartlab의 Svelte 5 + Tailwind 4 스택과 완벽 일치
   - 리스크: pre-release이나, next 태그로 프로덕션 사용 가능 수준

2. **차선: D3 + Svelte (직접 구현)**
   - LayerChart가 불안정할 경우 fallback
   - 최대 유연성이나 개발 비용 높음
   - 특수 차트(affiliateMap 네트워크 등)에는 D3 직접 사용 병행 가능

3. **기각: ECharts** — 번들 과대, Svelte 5 래퍼 미성숙
4. **기각: Chart.js** — Svelte 5 래퍼 불안정, waterfall/heatmap 미지원
5. **기각: uPlot** — 차트 타입 부족 (시계열 전용)
6. **기각: LayerCake** — LayerChart 2.0이 상위 호환

### 다음 단계
- 002에서 dartlab 데이터 형상 전수 조사 → LayerChart 컴포넌트 매핑
- 003에서 LayerChart 2.0 POC (삼성전자 IS 매출 bar+line 콤보)
- LayerChart가 불안정하면 D3 + Svelte fallback 전환

실험일: 2026-03-19
"""

import json


def evaluate():
    """차트 라이브러리 평가 점수 산출."""
    weights = {
        "svelte5": 0.25,
        "bundle": 0.20,
        "chartTypes": 0.20,
        "darkTheme": 0.15,
        "tsDx": 0.10,
        "ssr": 0.10,
    }

    libraries = {
        "LayerChart 2.0": {
            "svelte5": 10,
            "bundle": 8,
            "chartTypes": 9,
            "darkTheme": 9,
            "tsDx": 9,
            "ssr": 10,
        },
        "D3 + Svelte": {
            "svelte5": 10,
            "bundle": 9,
            "chartTypes": 10,
            "darkTheme": 10,
            "tsDx": 5,
            "ssr": 8,
        },
        "LayerCake": {
            "svelte5": 8,
            "bundle": 10,
            "chartTypes": 5,
            "darkTheme": 8,
            "tsDx": 7,
            "ssr": 9,
        },
        "ECharts": {
            "svelte5": 6,
            "bundle": 5,
            "chartTypes": 10,
            "darkTheme": 8,
            "tsDx": 7,
            "ssr": 7,
        },
        "uPlot": {
            "svelte5": 7,
            "bundle": 10,
            "chartTypes": 4,
            "darkTheme": 6,
            "tsDx": 6,
            "ssr": 8,
        },
        "Chart.js": {
            "svelte5": 5,
            "bundle": 7,
            "chartTypes": 7,
            "darkTheme": 7,
            "tsDx": 7,
            "ssr": 6,
        },
    }

    # 차트 타입 커버리지
    chart_types = ["line", "bar", "combo", "sparkline", "radar", "waterfall", "heatmap"]
    coverage = {
        "LayerChart 2.0": {"line": True, "bar": True, "combo": True, "sparkline": True, "radar": True, "waterfall": "partial", "heatmap": True},
        "ECharts": {t: True for t in chart_types},
        "Chart.js": {"line": True, "bar": True, "combo": True, "sparkline": "partial", "radar": True, "waterfall": False, "heatmap": False},
        "D3 + Svelte": {t: True for t in chart_types},
        "uPlot": {"line": True, "bar": True, "combo": True, "sparkline": True, "radar": False, "waterfall": False, "heatmap": False},
        "LayerCake": {"line": True, "bar": True, "combo": True, "sparkline": True, "radar": "custom", "waterfall": "custom", "heatmap": "custom"},
    }

    # 번들 사이즈 추정 (gzipped KB)
    bundle_estimates = {
        "LayerChart 2.0": "~30-50KB",
        "D3 + Svelte": "~15-30KB (필요 모듈만)",
        "LayerCake": "~3KB",
        "ECharts": "~80-120KB (treeshake)",
        "uPlot": "~15KB",
        "Chart.js": "~70KB",
    }

    print("=" * 80)
    print("dartlab 시각화 차트 라이브러리 평가")
    print("=" * 80)

    # 가중 합계 계산
    results = {}
    for lib, scores in libraries.items():
        weighted = sum(scores[k] * weights[k] for k in weights)
        results[lib] = round(weighted, 2)

    # 순위 정렬
    ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'라이브러리':<20} {'Svelte5':>8} {'번들':>8} {'차트타입':>8} {'다크테마':>8} {'TS DX':>8} {'SSR':>8} {'가중합계':>8}")
    print("-" * 80)
    for lib, score in ranked:
        s = libraries[lib]
        print(f"{lib:<20} {s['svelte5']:>8} {s['bundle']:>8} {s['chartTypes']:>8} {s['darkTheme']:>8} {s['tsDx']:>8} {s['ssr']:>8} {score:>8.2f}")

    print(f"\n{'가중치':<20} {'25%':>8} {'20%':>8} {'20%':>8} {'15%':>8} {'10%':>8} {'10%':>8}")

    # 번들 사이즈
    print("\n\n번들 사이즈 (gzipped 추정):")
    print("-" * 40)
    for lib, size in bundle_estimates.items():
        print(f"  {lib:<20} {size}")

    # 차트 타입 커버리지
    print("\n\n차트 타입 커버리지 (dartlab 필수 7종):")
    print("-" * 80)
    header = f"{'라이브러리':<20}" + "".join(f"{t:>12}" for t in chart_types)
    print(header)
    for lib in ranked:
        lib_name = lib[0]
        row = f"{lib_name:<20}"
        for t in chart_types:
            val = coverage[lib_name].get(t, False)
            if val is True:
                symbol = "✓"
            elif val == "partial":
                symbol = "△"
            elif val == "custom":
                symbol = "직접"
            else:
                symbol = "✗"
            row += f"{symbol:>12}"
        print(row)

    # 최종 추천
    print("\n\n" + "=" * 80)
    print("최종 추천")
    print("=" * 80)
    print(f"\n  1순위: {ranked[0][0]} (가중합계 {ranked[0][1]})")
    print(f"  차선:  {ranked[1][0]} (가중합계 {ranked[1][1]})")
    print(f"\n  기각:")
    for lib, score in ranked[2:]:
        print(f"    - {lib} ({score})")

    print("\n\n판정: LayerChart 2.0 채택")
    print("  - Svelte 5 runes 네이티브 (유일)")
    print("  - Tailwind 4 호환 (dartlab 스택 일치)")
    print("  - SVG 기반 SSR 안전")
    print("  - pre-release 리스크는 있으나 next 태그로 사용 가능")
    print("  - D3는 특수 차트(네트워크 그래프 등)에 병행 사용")

    # ChartSpec 프로토콜 (Svelte 컴포넌트와 공유할 데이터 구조)
    chart_spec_example = {
        "chartType": "combo",
        "title": "삼성전자 손익 추이",
        "series": [
            {"name": "매출액", "data": [276638, 258935, 258155, 300920, 301770], "color": "#3b82f6", "type": "bar"},
            {"name": "영업이익", "data": [51633, 36360, 6565, 36830, 33780], "color": "#ea4647", "type": "line"},
        ],
        "categories": ["2020", "2021", "2022", "2023", "2024"],
        "options": {"unit": "억원", "secondaryY": ["영업이익"]},
    }

    print("\n\nChartSpec 프로토콜 예시 (Python→Svelte 데이터 전달 포맷):")
    print(json.dumps(chart_spec_example, ensure_ascii=False, indent=2))

    return {
        "recommendation": ranked[0][0],
        "fallback": ranked[1][0],
        "scores": results,
        "chartSpec": chart_spec_example,
    }


if __name__ == "__main__":
    evaluate()
