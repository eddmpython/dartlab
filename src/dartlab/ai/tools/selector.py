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

    lines.extend(
        [
            "",
            "### [필수] 도구 사용 규칙:",
            "- **모든 수치 답변은 반드시 execute_code로 실제 데이터를 조회한 뒤 답변하세요.**",
            "- 추측이나 일반 지식으로 숫자를 답하지 마세요.",
            "- 도구 호출 없이 재무 수치를 언급하면 오답 위험이 큽니다.",
            "",
            "### 분석 절차:",
            "1. 질문이 회사/재무/공시에 관한 것이면 → execute_code로 dartlab API 호출 코드 생성",
            "2. 일반 대화(인사, 잡담)이면 → 도구 없이 직접 답변",
            "3. 결과를 종합하여 구조화된 답변 작성 (테이블 활용)",
            "",
            "### 코드 생성 패턴:",
            "- **사업 구조**: `c.show('businessOverview')`, `c.show('productService')`",
            "- **재무 심층**: `c.IS`, `c.BS`, `c.CF`, `c.ratios`",
            "- **리스크**: `c.show('riskFactor')`, `c.diff('riskFactor')`",
            "- **배당**: `c.show('dividend')`, `c.CF`",
            "- **기업 비교**: 복수 Company 생성 후 데이터 비교",
            "- **시장 스캔**: `dartlab.scan('governance')`, `dartlab.scan('screen', ...)`",
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
