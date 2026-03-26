"""CapabilitySpec 메타데이터 기반 동적 도구 선택 엔진."""

from __future__ import annotations

from dartlab.ai.tools.runtime import ToolRuntime
from dartlab.core.capabilities import CapabilityChannel, get_capability_specs

_COMPANY_BOUND_CATEGORIES = {"company", "finance", "analysis", "valuation"}


def selectTools(
    runtime: ToolRuntime,
    *,
    questionType: str | None = None,
    question: str = "",
    maxTools: int | None = None,
    hasCompany: bool = False,
) -> list[dict]:
    """CapabilitySpec 메타데이터 기반 동적 도구 선택.

    스코어 계산:
    - hasCompany=True: company/finance/analysis 카테고리 +30, meta 보너스 제거
    - hasCompany=False: meta 카테고리 +30 (기존 동작)
    - questionType 매칭: +40점
    - priority 필드: 0-100 → 0-30점 스케일링
    - question 텍스트 내 description 키워드 매칭: +10점

    반환: 스코어 높은 순으로 정렬된 도구 스키마 리스트
    """
    schemas = runtime.get_tool_schemas()
    if not schemas:
        return schemas

    specs = get_capability_specs(channel=CapabilityChannel.CHAT)
    specMap = {s.id: s for s in specs}

    scored: list[tuple[float, dict]] = []
    for schema in schemas:
        name = schema.get("function", {}).get("name", "")
        spec = specMap.get(name)

        score = 0.0

        if spec is None:
            score = 10.0
            scored.append((score, schema))
            continue

        if hasCompany:
            # company가 있으면 데이터 도구 우선, meta 하향
            if spec.category in _COMPANY_BOUND_CATEGORIES:
                score += 30.0
            elif spec.category == "meta":
                score += 5.0
        else:
            # company 없으면 meta 우선 (기존 동작)
            if spec.category == "meta":
                score += 30.0

        # questionType 매칭
        if questionType and questionType in spec.questionTypes:
            score += 40.0

        # priority 필드 (0-100 → 0-30)
        score += spec.priority * 0.3

        # question 텍스트 내 description 키워드 매칭
        if question:
            questionLower = question.lower()
            desc = spec.description[:200].lower()
            descWords = set(desc.split())
            questionWords = set(questionLower.split())
            overlap = descWords & questionWords
            if overlap:
                score += min(len(overlap) * 3.0, 10.0)

        scored.append((score, schema))

    # 스코어 내림차순 정렬
    scored.sort(key=lambda x: x[0], reverse=True)
    ordered = [s[1] for s in scored]

    if maxTools is None or len(ordered) <= maxTools:
        return ordered

    return ordered[:maxTools]


def buildToolPrompt(runtime: ToolRuntime | None = None) -> str:
    """CapabilitySpec 메타데이터에서 도구 안내 프롬프트 자동 생성."""
    from collections import defaultdict

    from dartlab.ai.tools.registry import get_coding_runtime_policy

    specs = get_capability_specs(channel=CapabilityChannel.CHAT)
    if not specs:
        return ""

    codingEnabled, codingReason = get_coding_runtime_policy()

    # 카테고리별 그룹핑
    byCategory: dict[str, list] = defaultdict(list)
    for spec in specs:
        byCategory[spec.category].append(spec)

    # 카테고리 순서 + 라벨
    categoryOrder = [
        ("company", "공시 탐색 도구"),
        ("finance", "재무 데이터 도구"),
        ("analysis", "분석 도구"),
        ("valuation", "밸류에이션/예측 도구"),
        ("export", "내보내기 도구"),
        ("meta", "메타 도구 (시스템 정보)"),
        ("global", "전역 도구 (회사 없어도 사용 가능)"),
        ("coding", "코딩 도구"),
        ("ui", "UI 제어 도구"),
    ]

    lines = [
        "",
        "## 도구 사용 안내",
        "",
        "당신은 DartLab 분석 도구를 사용할 수 있습니다.",
        "필요한 데이터를 도구를 통해 조회하고, 분석 결과를 종합하여 답변하세요.",
    ]

    for catKey, catLabel in categoryOrder:
        catSpecs = byCategory.get(catKey, [])
        if not catSpecs:
            if catKey == "coding" and not codingEnabled:
                lines.extend(["", f"### {catLabel}:", f"- coding runtime 도구가 등록되지 않았습니다. ({codingReason})"])
            continue

        # priority 내림차순 정렬
        catSpecs.sort(key=lambda s: s.priority, reverse=True)

        lines.append("")
        lines.append(f"### {catLabel}:")
        for spec in catSpecs:
            # description 첫 80자
            shortDesc = spec.description[:80]
            if len(spec.description) > 80:
                shortDesc = shortDesc.rsplit(" ", 1)[0] + "…"
            lines.append(f"- `{spec.id}`: {shortDesc}")

    # 나머지 카테고리 (정의되지 않은)
    knownCats = {c[0] for c in categoryOrder}
    for cat, catSpecs in byCategory.items():
        if cat in knownCats:
            continue
        catSpecs.sort(key=lambda s: s.priority, reverse=True)
        lines.append("")
        lines.append(f"### {cat} 도구:")
        for spec in catSpecs:
            shortDesc = spec.description[:80]
            if len(spec.description) > 80:
                shortDesc = shortDesc.rsplit(" ", 1)[0] + "…"
            lines.append(f"- `{spec.id}`: {shortDesc}")

    # Super Tool 모드 여부 판단 (도구가 10개 이하면 Super Tool)
    _isSuperToolMode = len(specs) <= 10

    if _isSuperToolMode:
        lines.extend(
            [
                "",
                "### [필수] 도구 선택 규칙:",
                "- **회사 데이터가 필요한 질문은 반드시 explore 또는 finance를 먼저 호출한다.**",
                "- 위에 제공된 핵심 수치는 참고용 요약이다. 질문에 답하려면 반드시 도구로 상세 데이터를 조회해야 한다.",
                "- system은 메타 질문('뭘 할 수 있어?', '데이터 상태')에만 사용한다.",
                "- 회사 분석 질문에 system을 호출하면 안 된다.",
                "- 데이터를 조회하지 않고 답변을 지어내면 안 된다. 반드시 도구 결과를 근거로 답변한다.",
                "- 재무/공시/배당/리스크 질문에 도구 호출 없이 답변하면 안 된다.",
                "",
                "### 분석 절차 (Super Tool):",
                "1. 질문이 회사/재무/공시에 관한 것이면 → explore 또는 finance 호출",
                "2. 질문이 시스템 기능에 관한 것이면 → system 호출",
                "3. 일반 대화(인사, 잡담)이면 → 도구 없이 직접 답변",
                "",
                "### 도구 매핑:",
                "- 사업/제품/리스크/경영진/주석/원재료 → explore(action='show', target=topic)",
                "- 재무제표/매출/이익/비율 → finance(action='data', module='IS/BS/CF/ratios')",
                "- 배당/임원보수/최대주주 → finance(action='report', apiType='dividend/executive/majorHolder')",
                "- topic을 모르겠으면 → explore(action='topics') 또는 explore(action='search', keyword='키워드')",
                "- 인사이트/ESG/밸류에이션 → analyze(action='insight/esg/valuation')",
                "",
                "### 전문가 플로우:",
                "- **사업 구조**: explore(show, businessOverview) → explore(show, productService)",
                "- **재무 심층**: finance(data, IS) → finance(data, BS) → finance(ratios)",
                "- **리스크**: explore(show, riskDerivative) → explore(diff, riskDerivative)",
                "- **배당**: finance(report, dividend) → finance(data, CF)",
                "- **키워드 검색**: explore(search, '비용의 성격별분류') → explore(show, 찾은topic)",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "### 분석 절차:",
                "1. 질문을 이해하고 `기능 탐색`인지 `회사 분석`인지 먼저 구분",
                "2. 기능 탐색 질문이면 meta 도구 (`get_runtime_capabilities`, `get_system_spec`, `get_tool_catalog`) 먼저 호출",
                "3. 회사 분석이면 `list_topics`로 공시 topic을 먼저 확인",
                "4. 최근 공시/filing 목록은 `list_live_filings`, 공시 본문은 `read_filing`",
                "5. 공시 topic 원문이 필요하면 `show_topic`, 변화가 궁금하면 `diff_topic`",
                "6. 재무 수치가 필요하면 `get_data`(BS/IS/CF), 정기보고서는 `get_report_data`",
                "7. 코드 작업 요청이면 coding 도구 사용 검토",
                "8. 필요 시 분석 엔진 도구로 심층 분석",
                "9. 결과를 종합하여 구조화된 답변 작성 (테이블 활용)",
                "10. 모든 수치에 출처(테이블명, 연도)를 반드시 인용",
                "",
                "### 전문가 분석 도구 플로우:",
                "- **사업 구조**: list_topics → show_topic('businessOverview') → show_topic('segments') → show_topic('productService')",
                "- **최근 공시 읽기**: list_live_filings() → read_filing(doc_id/doc_url)",
                "- **재무 심층**: get_data('IS') → get_data('BS') → compute_ratios() → get_insight()",
                "- **이익의 질**: get_data('IS') → get_data('CF') → compute_ratios() → detect_anomalies()",
                "- **리스크 종합**: show_topic('riskFactor') → show_topic('contingentLiability') → diff_topic('riskFactor')",
                "- **배당 지속가능성**: get_report_data('dividend') → get_data('CF') → compute_ratios()",
                "- **경영진 품질**: show_topic('executive') → show_topic('executivePay') → show_topic('boardOfDirectors')",
                "- **종합 평가**: get_insight() → compute_ratios() → list_topics() → show_topic('riskFactor') → get_data('CF')",
            ]
        )

    lines.extend(
        [
            "",
            "### 답변 방식:",
            "- 범위를 물으면 가능한 것 / 바로 할 수 있는 것 / 아직 안 되는 것을 짧게 정리한 뒤 다음 액션을 제안",
            "- 도구와 기능 목록은 고정 문구를 외우지 말고 현재 등록된 tool registry 결과를 우선 신뢰",
        ]
    )
    return "\n".join(lines)
