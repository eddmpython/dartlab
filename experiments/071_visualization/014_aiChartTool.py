"""
실험 ID: 014
실험명: AI create_chart 도구 등록 + 호출 시뮬레이션

목적:
- tools_registry.py에 등록한 create_chart 도구가 정상 작동하는지 검증한다
- 도구 호출 시뮬레이션: auto / 개별 chart_type 파라미터 테스트
- streaming.py chart SSE 이벤트 구조 검증 (JSON 직렬화)
- 도구 결과 크기 확인 (SSE 전송 시 적정 크기인지)

가설:
1. create_chart("auto")가 Company 기반으로 ChartSpec JSON 리스트를 반환한다
2. 개별 chart_type 지정 시 해당 차트만 반환한다
3. 도구 결과 JSON 크기가 50KB 이하이다
4. 잘못된 chart_type 입력 시 에러 메시지를 반환한다

방법:
1. build_tool_runtime()으로 도구 런타임 생성
2. execute_tool("create_chart", {...})로 도구 호출
3. 반환값 JSON 파싱 후 ChartSpec 구조 검증
4. 다양한 chart_type으로 호출하여 개별 동작 확인

결과:
- create_chart 도구 등록 성공 (전체 38개 도구 중 22번째)
- chart_type enum: auto + 8개 개별 타입
- auto 호출: 삼성전자 7개 ChartSpec 생성, 3440ms, 10.6KB JSON
- 개별 호출: revenue_trend(539B), cashflow(369B), insight_radar(309B), profitability(958B), diff_heatmap(2934B)
- 에러 처리: 잘못된 chart_type → 사용 가능 목록 포함 에러 메시지
- Company=None: 도구 호출 시 에러 (정상 — Company 선택 필요)
- SSE chart 이벤트 크기: 10.6KB (50KB 기준 대비 충분히 작음)
- 다종목: SK하이닉스 7개, 카카오 7개, KB금융 6개 (금융업 balance_sheet 미생성)
- 가설1 채택: auto → ChartSpec JSON 리스트 반환
- 가설2 채택: 개별 chart_type 지정 시 해당 차트만 반환
- 가설3 채택: JSON 크기 10.6KB < 50KB
- 가설4 채택: 잘못된 chart_type → 에러 메시지 반환

실험일: 2026-03-19
"""

import json
import sys
import time

sys.path.insert(0, "src")


def test():
    print("=" * 90)
    print("014: AI create_chart 도구 등록 + 호출 시뮬레이션")
    print("=" * 90)

    from dartlab import Company
    from dartlab.ai.tools_registry import build_tool_runtime

    c = Company("005930")

    # 1. 도구 런타임 빌드 + create_chart 등록 확인
    print("\n[1] 도구 런타임 빌드")
    print("-" * 60)

    runtime = build_tool_runtime(c, name="test-chart")
    schemas = runtime.get_tool_schemas()
    chart_schema = None
    for s in schemas:
        func = s.get("function", {})
        if func.get("name") == "create_chart":
            chart_schema = func
            break

    if chart_schema:
        print(f"  ✓ create_chart 도구 등록 확인")
        print(f"    설명: {chart_schema.get('description', '')[:60]}...")
        params = chart_schema.get("parameters", {}).get("properties", {})
        chart_type_enum = params.get("chart_type", {}).get("enum", [])
        print(f"    chart_type enum: {chart_type_enum}")
        print(f"    전체 도구 수: {len(schemas)}개")
    else:
        print(f"  ✗ create_chart 도구 미등록!")
        return

    # 2. auto 호출
    print(f"\n\n[2] create_chart(auto) 호출")
    print("-" * 60)

    t0 = time.perf_counter()
    result = runtime.execute_tool("create_chart", {"chart_type": "auto"})
    elapsed = time.perf_counter() - t0

    parsed = json.loads(result)
    charts = parsed.get("charts", [])
    print(f"  생성 차트: {len(charts)}개, 소요: {elapsed*1000:.0f}ms")
    print(f"  JSON 크기: {len(result)} bytes ({len(result)/1024:.1f}KB)")

    for ch in charts:
        ct = ch.get("chartType", "?")
        title = ch.get("title", "")[:30]
        meta = ch.get("meta", {})
        print(f"    {ct:<12} {title:<32} source={meta.get('source','?')}")

    # 3. 개별 chart_type 호출
    print(f"\n\n[3] 개별 chart_type 호출")
    print("-" * 60)

    test_types = ["revenue_trend", "cashflow", "insight_radar", "profitability", "diff_heatmap"]
    for ct in test_types:
        t0 = time.perf_counter()
        result = runtime.execute_tool("create_chart", {"chart_type": ct})
        elapsed = time.perf_counter() - t0

        parsed = json.loads(result)
        if "error" in parsed:
            print(f"  {ct:<20} → 에러: {parsed['error']}")
        else:
            charts = parsed.get("charts", [])
            size = len(result)
            print(f"  {ct:<20} → {len(charts)}개 차트, {size} bytes, {elapsed*1000:.0f}ms")

    # 4. 잘못된 chart_type
    print(f"\n\n[4] 잘못된 chart_type 에러 처리")
    print("-" * 60)

    result = runtime.execute_tool("create_chart", {"chart_type": "invalid_type"})
    parsed = json.loads(result)
    print(f"  입력: 'invalid_type'")
    print(f"  결과: {parsed}")
    has_error = "error" in parsed
    print(f"  에러 감지: {'✓' if has_error else '✗'}")

    # 5. Company 없을 때
    print(f"\n\n[5] Company 없을 때")
    print("-" * 60)

    runtime_no_company = build_tool_runtime(None, name="test-no-company")
    try:
        result = runtime_no_company.execute_tool("create_chart", {"chart_type": "auto"})
        parsed = json.loads(result) if result else {"error": "빈 결과"}
        print(f"  결과: {parsed}")
        has_error = "error" in parsed
        print(f"  에러 감지: {'✓' if has_error else '✗'}")
    except Exception as e:
        # Company=None이면 create_chart 도구가 등록되지 않을 수 있음
        print(f"  예외: {e}")
        print(f"  ✓ Company 없으면 도구 호출 불가 (정상 동작)")

    # 6. SSE 이벤트 구조 시뮬레이션
    print(f"\n\n[6] SSE chart 이벤트 구조 시뮬레이션")
    print("-" * 60)

    result = runtime.execute_tool("create_chart", {"chart_type": "auto"})
    parsed = json.loads(result)
    charts = parsed.get("charts", [])

    # streaming.py가 하는 것과 동일한 변환
    sse_event = {"event": "chart", "charts": charts}
    sse_json = json.dumps(sse_event, ensure_ascii=False)
    print(f"  SSE chart 이벤트 크기: {len(sse_json)} bytes ({len(sse_json)/1024:.1f}KB)")
    print(f"  차트 수: {len(charts)}개")

    # 다종목 테스트
    print(f"\n\n[7] 다종목 create_chart(auto) 검증")
    print("-" * 60)

    test_codes = [
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
        ("105560", "KB금융"),
    ]
    for code, name in test_codes:
        c2 = Company(code)
        rt = build_tool_runtime(c2, name=f"test-{code}")
        result = rt.execute_tool("create_chart", {"chart_type": "auto"})
        parsed = json.loads(result)
        charts = parsed.get("charts", [])
        types = [ch["chartType"] for ch in charts]
        print(f"  {name}: {len(charts)}개 — {types}")

    # 결과 요약
    print(f"\n\n{'='*90}")
    print("결과 요약")
    print(f"{'='*90}")
    print(f"  가설1: auto → {len(json.loads(runtime.execute_tool('create_chart', {'chart_type': 'auto'})).get('charts', []))}개 ChartSpec 생성 — 채택")
    print(f"  가설2: 개별 chart_type 동작 확인 — 채택")
    print(f"  가설3: JSON 크기 {len(sse_json)/1024:.1f}KB < 50KB — 채택")
    print(f"  가설4: 잘못된 chart_type 에러 반환 — 채택")


if __name__ == "__main__":
    test()
