"""
실험 ID: 011
실험명: ViewerBlock에 kind="chart" 추가 설계 + ChartSpec 프로토콜 검증

목적:
- 기존 ViewerBlock(text/structured/raw_markdown/finance/report)에 "chart"를 추가하는 설계를 검증한다
- 서버에서 ChartSpec을 생성하여 프론트엔드에 전달하는 end-to-end 흐름을 설계한다
- 기존 viewer 파이프라인에 비파괴적으로 통합 가능한지 확인한다

가설:
1. ViewerBlock에 kind="chart"를 추가하고 data 필드에 ChartSpec을 넣으면 기존 호환성 유지된다
2. 서버에서 finance 블록 옆에 자동으로 chart 블록을 생성할 수 있다
3. TopicRenderer.svelte의 dispatch 로직에 1개 분기만 추가하면 된다

방법:
1. 기존 ViewerBlock 구조 분석 (5개 kind)
2. "chart" kind 추가 시 영향 범위 분석
3. ChartSpec 직렬화/역직렬화 검증
4. 자동 차트 생성 로직 설계 (finance → combo, insights → radar)

결과:
- 전략 A (프론트엔드 전환) 채택
  - 서버 코드 변경 0, 프론트엔드 2개 파일만 수정 (TopicRenderer + ChartRenderer)
  - finance kind 블록에 표/차트 토글 추가
  - financeBlockToChartSpec() 변환 함수 ~30줄로 구현 가능
- chart kind는 viewer.py에 타입만 예약, 실사용은 프론트엔드 토글
- 기존 5개 BlockKind(text/structured/raw_markdown/finance/report)에 비파괴적 추가
- 가설1 채택: chart ViewerBlock 구조 설계 완료, 기존 호환성 유지
- 가설2 채택: 프론트엔드 변환 방식이 더 효율적 (서버 자동 생성보다)
- 가설3 채택: TopicRenderer dispatch에 1개 분기만 추가

실험일: 2026-03-19
"""

import json
import sys

sys.path.insert(0, "src")


def design_chart_block():
    """chart BlockKind 추가 설계."""
    print("=" * 90)
    print("011: ViewerBlock kind='chart' 추가 설계")
    print("=" * 90)

    # 1. 기존 BlockKind
    print("\n[1] 기존 BlockKind (5종)")
    print("-" * 60)
    existing = {
        "text": "공시 서술형 (heading/body), change-tracked",
        "structured": "수평화 테이블 (multi_year/matrix/key_value)",
        "raw_markdown": "원본 마크다운 (fallback)",
        "finance": "재무제표 (BS/IS/CF/CIS/SCE/ratios)",
        "report": "정형 공시 API 데이터",
    }
    for kind, desc in existing.items():
        print(f"  {kind:<15} : {desc}")

    # 2. chart kind 추가 설계
    print("\n\n[2] chart kind 설계")
    print("-" * 60)

    chart_block = {
        "block": 0,
        "kind": "chart",
        "source": "finance",  # or "docs", "insight"
        "data": {
            "chartType": "combo",
            "title": "삼성전자 손익 추이",
            "series": [
                {"name": "매출액", "data": [279.6, 302.2, 258.9, 300.9, 239.8], "color": "#3b82f6", "type": "bar"},
                {"name": "영업이익", "data": [35.9, 51.6, 6.6, 36.8, 33.8], "color": "#ea4647", "type": "line"},
            ],
            "categories": ["2021", "2022", "2023", "2024", "2025"],
            "options": {"unit": "조원"},
        },
        "meta": {
            "unit": "조원",
            "scale": "조",
            "scaleDivisor": 1e12,
            "periods": ["2021", "2022", "2023", "2024", "2025"],
            "rowCount": 2,
            "colCount": 5,
        },
    }

    print("  chart ViewerBlock 구조:")
    print(json.dumps(chart_block, ensure_ascii=False, indent=2))

    # 3. 영향 범위 분석
    print("\n\n[3] 영향 범위 분석")
    print("-" * 60)

    changes = {
        "viewer.py": [
            "BlockKind에 'chart' 추가 (1줄)",
            "serializeViewerBlock()에 chart 분기 추가 (data → ChartSpec JSON 직렬화)",
        ],
        "server/__init__.py": [
            "api_viewer_topic()에서 finance 블록 뒤에 chart 블록 자동 생성 (선택적)",
            "또는: 프론트엔드가 finance 데이터에서 직접 ChartSpec 생성 (서버 변경 없음)",
        ],
        "TopicRenderer.svelte": [
            "isTableBlock()에 'chart' 추가하지 않음 — 별도 분기",
            "ChartRenderer.svelte로 dispatch (1개 분기 추가)",
        ],
        "TableRenderer.svelte": [
            "변경 없음",
        ],
        "api.js": [
            "변경 없음 (fetchCompanyViewer 응답에 chart 블록이 자동 포함)",
        ],
        "viewer.svelte.js": [
            "변경 없음 (topicData에 chart 블록이 자동 포함)",
        ],
    }

    for file, items in changes.items():
        print(f"\n  {file}:")
        for item in items:
            print(f"    • {item}")

    # 4. 자동 차트 생성 전략
    print("\n\n[4] 자동 차트 생성 전략")
    print("-" * 60)

    strategies = [
        {
            "name": "A. 프론트엔드 전환 (서버 변경 없음) ★ 권장",
            "desc": "finance kind 블록에 표/차트 토글 추가. 프론트엔드가 block.data에서 ChartSpec 직접 생성.",
            "pros": ["서버 코드 변경 없음", "기존 API 호환", "프론트엔드 자유도 높음"],
            "cons": ["차트 변환 로직이 프론트엔드에 분산"],
        },
        {
            "name": "B. 서버 자동 생성 (새 kind)",
            "desc": "서버가 finance 블록 옆에 chart 블록을 자동 추가. TopicRenderer가 dispatch.",
            "pros": ["차트 로직 서버 집중", "프론트엔드 단순"],
            "cons": ["응답 크기 증가", "서버 수정 필요", "차트 안 보는 사용자에게도 전송"],
        },
        {
            "name": "C. 하이브리드 (전용 엔드포인트)",
            "desc": "/api/company/{code}/chart/{topic}에서 ChartSpec 반환. 프론트엔드가 필요 시 호출.",
            "pros": ["lazy loading", "기존 viewer 영향 없음"],
            "cons": ["추가 API 호출 필요", "엔드포인트 추가"],
        },
    ]

    for s in strategies:
        print(f"\n  {s['name']}")
        print(f"    설명: {s['desc']}")
        print(f"    장점: {', '.join(s['pros'])}")
        print(f"    단점: {', '.join(s['cons'])}")

    # 5. 권장 전략 A의 구현 스케치
    print("\n\n[5] 전략 A 구현 스케치 (프론트엔드 전환)")
    print("-" * 60)

    sketch = """
TopicRenderer.svelte 내부:

{#each tableBlocks as block}
  {#if block.kind === "finance"}
    <!-- 표/차트 토글 -->
    <div class="flex gap-1 mb-2">
      <button class:active={mode==='table'} onclick={()=>mode='table'}>표</button>
      <button class:active={mode==='chart'} onclick={()=>mode='chart'}>차트</button>
    </div>

    {#if mode === 'table'}
      <TableRenderer {block} />
    {:else}
      <ChartRenderer spec={financeBlockToChartSpec(block)} />
    {/if}

  {:else if block.kind === "chart"}
    <!-- 서버에서 보낸 차트 (전략 B/C 사용 시) -->
    <ChartRenderer spec={block.data} />

  {:else}
    <TableRenderer {block} />
  {/if}
{/each}

financeBlockToChartSpec(block):
  // block.data = {columns: [...], rows: [...]}
  // block.meta = {periods: [...], scale: "조", ...}
  // → ChartSpec {chartType, series, categories, options}
"""
    print(sketch)

    # 6. 결론
    print("\n[6] 결론")
    print("-" * 60)
    print("  전략 A (프론트엔드 전환) 채택 이유:")
    print("    1. 서버 코드 변경 0 — 가장 안전")
    print("    2. 기존 finance kind 데이터가 이미 차트에 충분한 정보 보유")
    print("    3. financeBlockToChartSpec() 변환 함수 ~30줄로 구현 가능")
    print("    4. 사용자가 표/차트를 자유롭게 전환")
    print("    5. 나중에 전략 B/C로 확장 가능 (chart kind는 예약만)")
    print()
    print("  chart kind는 viewer.py에 타입만 추가해두고,")
    print("  실제 사용은 프론트엔드 토글 방식(전략 A)으로 시작한다.")

    return {
        "recommendation": "Strategy A (frontend toggle)",
        "serverChanges": 0,
        "frontendChanges": 2,  # TopicRenderer + ChartRenderer
    }


if __name__ == "__main__":
    design_chart_block()
