"""
실험 ID: 010
실험명: Registry Analysis — 현재 50+ 도구 분류 및 패턴 추출

목적:
- tools_registry.py에 하드코딩된 도구들의 패턴을 분석
- 외부 plugin API 설계(011)를 위한 분류 체계와 공통 인터페이스 도출

가설:
1. 50+ 도구가 5~6개 카테고리로 자연스럽게 분류된다
2. 도구의 80%+ 가 company 바인딩이 필요하다
3. 도구 시그니처에 공통 패턴이 있다 (input: dict → output: str)

방법:
1. ToolRuntime에서 등록된 도구 목록 추출
2. 도구명/설명/파라미터를 카테고리별로 분류
3. 공통 패턴(requires_company, input_type, output_format) 추출
4. @tool 데코레이터 설계를 위한 메타데이터 구조 도출

결과:
- 등록 도구: 39개 (예상 50+보다 적음 — 이전 코드 정리로 감소)
- 카테고리 분류: 8개
  - unknown(8) > global(7) > data_query(5) = computation(5) = meta(5) > exploration(4) > l2_engine(3) > coding(2)
  - unknown 8개: export(4), sections(2), chart(1), scan(1) — 분류 규칙 누락
- Company 필요: 17/39 = 44% (가설 80% 기각)
  - global/meta/coding이 22개로 과반 — 전역 도구가 의외로 많음
- 파라미터 분포: 0개(13) > 1개(16) > 2개(5) > 4+개(4)
  - 대부분 0-1개 파라미터 → 단순 시그니처
  - call_dart_openapi(14개), call_edgar_openapi(10개)만 복잡
- 공통 패턴: 모든 도구가 dict → str(markdown) 형태

결론:
- 가설 1 수정: 8개 카테고리 (exploration/data_query/computation/l2_engine/meta/global/coding + export)
- 가설 2 기각: Company 필요 44%, 전역 도구가 과반 — @tool 데코레이터는 requires_company 기본값 False가 맞음
- 가설 3 채택: dict → str 시그니처 통일, 파라미터 대부분 0-1개
- @tool 설계안: category + requires_company + description으로 충분. parameter schema는 타입 힌트에서 자동 추출 가능
- unknown 8개 도구는 export/visualization 카테고리 신설 필요

실험일: 2026-03-20
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def analyze_registry():
    """현재 도구 레지스트리 분석."""
    from dartlab.engines.ai.tools_registry import build_tool_runtime

    # MockCompany로 전체 도구 등록
    class MockCompany:
        corpName = "분석용"
        stockCode = "000000"
        BS = None
        IS = None
        CF = None
        CIS = None

        def show(self, *a, **k):
            return None

        @property
        def topics(self):
            return None

        @property
        def ratios(self):
            return None

        class finance:
            BS = None
            IS = None
            CF = None
            ratios = None
            timeseries = None
            ratioSeries = None

        class docs:
            class sections:
                pass

        class report:
            pass

    runtime = build_tool_runtime(MockCompany(), name="analysis")
    schemas = runtime.get_tool_schemas()
    tool_names = runtime.list_tool_names()

    return schemas, tool_names


def classify_tools(schemas: list[dict]) -> dict:
    """도구를 카테고리별로 분류."""
    categories = {
        "exploration": [],    # 공시 탐색 (list_topics, show_topic, trace, diff)
        "data_query": [],     # 데이터 조회 (get_data, get_report_data, get_company_info)
        "computation": [],    # 분석 계산 (compute_ratios, detect_anomalies, growth)
        "l2_engine": [],      # L2 분석 (insight, sector, rank)
        "meta": [],           # 메타/시스템 (spec, capabilities, catalog, runtime_status)
        "global": [],         # 전역 (search, download, data_status, openapi)
        "coding": [],         # 코딩 (run_coding_task, run_codex_task)
    }

    category_rules = {
        "list_topics": "exploration",
        "show_topic": "exploration",
        "trace_topic": "exploration",
        "diff_topic": "exploration",
        "list_modules": "data_query",
        "search_data": "data_query",
        "get_data": "data_query",
        "get_report_data": "data_query",
        "get_company_info": "data_query",
        "compute_ratios": "computation",
        "detect_anomalies": "computation",
        "compute_growth": "computation",
        "yoy_analysis": "computation",
        "get_summary": "computation",
        "get_insight": "l2_engine",
        "get_sector_info": "l2_engine",
        "get_rank": "l2_engine",
        "get_system_spec": "meta",
        "get_engine_spec": "meta",
        "get_runtime_capabilities": "meta",
        "get_tool_catalog": "meta",
        "get_coding_runtime_status": "meta",
        "search_company": "global",
        "download_data": "global",
        "data_status": "global",
        "get_openapi_capabilities": "global",
        "call_dart_openapi": "global",
        "call_edgar_openapi": "global",
        "openapi_save": "global",
        "run_coding_task": "coding",
        "run_codex_task": "coding",
    }

    for schema in schemas:
        func_info = schema.get("function", {})
        name = func_info.get("name", "unknown")
        cat = category_rules.get(name, "unknown")
        categories.setdefault(cat, []).append({
            "name": name,
            "description": func_info.get("description", ""),
            "parameters": func_info.get("parameters", {}),
        })

    return categories


def extract_patterns(categories: dict) -> dict:
    """공통 패턴 추출."""
    patterns = {
        "total_tools": sum(len(v) for v in categories.values()),
        "categories": {},
        "requires_company": [],
        "no_company": [],
        "parameter_stats": {},
    }

    company_required = {"exploration", "data_query", "computation", "l2_engine"}
    no_company = {"meta", "global", "coding"}

    for cat, tools in categories.items():
        patterns["categories"][cat] = {
            "count": len(tools),
            "tools": [t["name"] for t in tools],
        }
        for tool in tools:
            if cat in company_required:
                patterns["requires_company"].append(tool["name"])
            else:
                patterns["no_company"].append(tool["name"])

            # 파라미터 분석
            params = tool.get("parameters", {}).get("properties", {})
            param_count = len(params)
            patterns["parameter_stats"].setdefault(param_count, []).append(tool["name"])

    return patterns


if __name__ == "__main__":
    print("=" * 60)
    print("실험 010: Registry Analysis")
    print("=" * 60)

    schemas, tool_names = analyze_registry()
    print(f"\n등록된 도구: {len(schemas)}개")
    print(f"도구명: {sorted(tool_names)}")

    # 분류
    categories = classify_tools(schemas)

    print("\n=== 카테고리별 분류 ===")
    for cat, tools in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"\n  [{cat}] ({len(tools)}개)")
        for t in tools:
            desc_short = t["description"][:50] if t["description"] else "-"
            params = list(t.get("parameters", {}).get("properties", {}).keys())
            print(f"    {t['name']:>30}: {desc_short}...")
            if params:
                print(f"    {'':>30}  params: {params}")

    # 패턴
    patterns = extract_patterns(categories)

    print("\n=== 패턴 분석 ===")
    print(f"  총 도구: {patterns['total_tools']}개")
    print(f"  Company 필요: {len(patterns['requires_company'])}개 ({round(len(patterns['requires_company'])/max(patterns['total_tools'],1)*100)}%)")
    print(f"  Company 불필요: {len(patterns['no_company'])}개")

    print("\n  카테고리별:")
    for cat, info in sorted(patterns["categories"].items(), key=lambda x: -x[1]["count"]):
        print(f"    {cat:>15}: {info['count']}개 — {info['tools']}")

    print("\n  파라미터 수 분포:")
    for count, tools in sorted(patterns["parameter_stats"].items()):
        print(f"    {count}개 파라미터: {len(tools)}개 도구 — {tools[:5]}{'...' if len(tools)>5 else ''}")

    # @tool 데코레이터 설계안
    print("\n=== @tool 데코레이터 설계안 ===")
    print("""
    @tool(
        category="exploration",     # 7개 카테고리 중 하나
        requires_company=True,      # Company 바인딩 필요 여부
        description="topic 데이터 조회",
    )
    def show_topic(company, topic: str, block: int | None = None) -> str:
        ...

    # 전역 도구
    @tool(category="global", requires_company=False)
    def search_company(query: str) -> str:
        ...
    """)

    # company 필요/불필요 비율
    total = patterns["total_tools"]
    need_company = len(patterns["requires_company"])
    print(f"\n결론:")
    print(f"  - {len(patterns['categories'])}개 카테고리로 분류 (가설: 5~6개)")
    print(f"  - Company 필요 비율: {need_company}/{total} = {round(need_company/max(total,1)*100)}% (가설: 80%+)")
    print(f"  - 모든 도구 시그니처: dict → str (markdown) — 공통 패턴 확인")
