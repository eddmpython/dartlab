"""ReportType 보고서 뼈대 단일축 정의.

기존 perspective(순서 재배치) + preset(섹션 부분집합) + emphasize(강조)를
하나의 ReportType으로 통합. 사용자는 c.story(type="credit") 처럼 한 축만 지정.

STORY_TEMPLATES (기업유형 7개)는 독립 차원이며 자동 감지 보조로 유지한다.
"""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.story.templates import TEMPLATE_ORDER


@dataclass(frozen=True)
class ReportType:
    """보고서별 섹션 순서와 강조 블록 및 검증 질문을 정의한다."""

    key: str
    label: str
    description: str
    sectionOrder: tuple[str, ...]  # 렌더링할 섹션들 + 순서
    emphasize: frozenset[str] = frozenset()  # ★ 강조 블록
    focusQuestions: tuple[str, ...] = ()  # 보고서 상단에 표시
    detail: bool = True


# ── 11 ReportType 정의 ──

REPORT_TYPES: dict[str, ReportType] = {
    "investment": ReportType(
        key="investment",
        label="투자 의사결정 브리프",
        description="논지·반대논지·실적 변곡·가격 비대칭·무효화 조건을 한 번에 점검",
        sectionOrder=(
            "종합평가",
            "수익구조",
            "현금흐름",
            "storyValidation",
        ),
        emphasize=frozenset(
            {
                "scorecard",
                "growthTrend",
                "marginTrend",
                "cashQuality",
                "roicTimeline",
                "valuationSynthesis",
                "plausibilityBand",
                "revenueForecast",
                "macroCycle",
            }
        ),
        focusQuestions=(
            "이 기업의 검증 가능한 중심 투자논지는 무엇인가?",
            "가장 강한 반대논지와 논지 훼손 조건은 무엇인가?",
            "실적은 어디서 변곡했고 그 원인은 무엇인가?",
            "현재 가격은 어떤 성장을 이미 반영하는가?",
            "bear/base/bull의 하방과 상방은 비대칭적인가?",
            "다음 촉매와 확인해야 할 tripwire는 무엇인가?",
        ),
        detail=True,
    ),
    "full": ReportType(
        key="full",
        label="전체 6막",
        description="바텀업 인과 서사 기본 보고서",
        sectionOrder=tuple(TEMPLATE_ORDER),
        detail=True,
    ),
    "executive": ReportType(
        key="executive",
        label="경영 요약",
        description="의사결정자용 3분컷: 결론/수익/현금/가치",
        sectionOrder=("종합평가", "수익구조", "현금흐름", "가치평가", "storyValidation"),
        emphasize=frozenset({"scorecard", "valuationSynthesis", "cashFlowOverview"}),
        focusQuestions=(
            "한 문장 결론은?",
            "돈을 버는 구조인가?",
            "현금이 제대로 도는가?",
            "지금 가격은 합당한가?",
        ),
        detail=False,
    ),
    "credit": ReportType(
        key="credit",
        label="신용분석",
        description="채권/여신 심사: 안정성/현금/자금조달/7축등급",
        sectionOrder=("안정성", "현금흐름", "자금조달", "효율성", "신용평가", "storyValidation"),
        emphasize=frozenset(
            {"leverageTrend", "distressScore", "coverageTrend", "cashFlowOverview", "creditScore", "creditNarrative"}
        ),
        focusQuestions=(
            "부채를 감당할 현금흐름이 있는가?",
            "이자보상 배율은 안전한가?",
            "만기 차환 리스크는?",
            "신용등급은 어디에 서 있는가?",
        ),
        detail=True,
    ),
    "valuation": ReportType(
        key="valuation",
        label="가치평가 집중",
        description="가치투자자용: DCF/상대가치/매출전망",
        sectionOrder=("가치평가", "수익성", "성장성", "매출전망", "자본배분", "안정성", "storyValidation"),
        emphasize=frozenset({"valuationSynthesis", "dcfValuation", "relativeValuation", "revenueForecast"}),
        focusQuestions=(
            "적정 가치는 얼마인가?",
            "안전마진이 있는가?",
            "현재 가격이 미래 성장을 얼마나 가격반영했는가?",
            "자본 배분이 가치를 창출하는가?",
        ),
        detail=True,
    ),
    "growth": ReportType(
        key="growth",
        label="성장 스토리",
        description="성장투자자용: CAGR/마진확장/투자효율",
        sectionOrder=("수익구조", "성장성", "매출전망", "수익성", "투자효율", "효율성", "자본배분", "storyValidation"),
        emphasize=frozenset({"growthTrend", "cagrComparison", "revenueForecast", "roicTree", "reinvestment"}),
        focusQuestions=(
            "성장의 원천은 무엇인가?",
            "수익성을 동반한 성장인가?",
            "재투자가 ROIC로 돌아오는가?",
            "이 성장은 지속 가능한가?",
        ),
        detail=True,
    ),
    "crisis": ReportType(
        key="crisis",
        label="위기 진단",
        description="위험 진단: 부실/레버리지/유동성/턴어라운드",
        sectionOrder=(
            "매크로",
            "안정성",
            "자금조달",
            "현금흐름",
            "이익품질",
            "신용평가",
            "종합평가",
            "storyValidation",
        ),
        emphasize=frozenset(
            {"leverageTrend", "distressScore", "coverageTrend", "cashQuality", "cashFlowOverview", "creditScore"}
        ),
        focusQuestions=(
            "단기에 현금이 마를 위험은?",
            "이자 감당이 되는가?",
            "이익이 진짜인가 (발생액 리스크)?",
            "악화 추세가 구조적인가?",
        ),
        detail=True,
    ),
    "audit": ReportType(
        key="audit",
        label="감사 관점",
        description="감사/포렌식: 이익품질/재무정합성/공시변화",
        sectionOrder=("이익품질", "재무정합성", "안정성", "지배구조", "공시변화", "storyValidation"),
        emphasize=frozenset(
            {"cashQuality", "accrualAnalysis", "fundamentalDivergence", "governanceSummary", "disclosureChange"}
        ),
        focusQuestions=(
            "이익의 현금 전환은 정상인가?",
            "재무제표 간 정합성은 맞는가?",
            "지배구조 리스크가 있는가?",
            "공시에서 달라진 것은?",
        ),
        detail=True,
    ),
    # ── 신규 4종 (P2~P5에서 블록 추가) ──
    "dividend": ReportType(
        key="dividend",
        label="배당·주주환원",
        description="인컴 투자자용: 배당지속성/FCF커버리지/총환원",
        sectionOrder=("수익구조", "현금흐름", "자본배분", "자금조달", "안정성", "storyValidation"),
        emphasize=frozenset(
            {
                "dividendPolicy",
                "shareholderReturn",
                "fcfUsage",
                "cashFlowOverview",
                "dividendSustainability",  # 신규
                "totalShareholderReturn",  # 신규
            }
        ),
        focusQuestions=(
            "배당은 지속 가능한가 (FCF 커버)?",
            "배당 외 자사주·감자까지 합친 총환원율은?",
            "성향은 과도한가 적정한가?",
            "환원 여력을 깎는 재무 부담이 있는가?",
        ),
        detail=True,
    ),
    "governance": ReportType(
        key="governance",
        label="경영진·지배구조",
        description="거버넌스 리스크: 임원보수/외부이사 독립성/지분구조",
        sectionOrder=("지배구조", "자본배분", "공시변화", "종합평가", "storyValidation"),
        emphasize=frozenset(
            {
                "governanceSummary",
                "ownershipTrend",
                "executivePayDivergence",  # 신규
                "independentDirectorQuality",  # 신규
                "disclosureChange",
            }
        ),
        focusQuestions=(
            "임원보수 증가가 실적과 맞는가?",
            "외부이사는 실질적으로 독립적인가?",
            "지분 구조가 소수주주에 불리한가?",
            "최근 공시 변화에 거버넌스 신호는?",
        ),
        detail=True,
    ),
    "macro": ReportType(
        key="macro",
        label="매크로 사이클 위치",
        description="탑다운 투자자용: 사이클 + 역사적 팩트로 이 기업의 위치",
        sectionOrder=("매크로", "시장분석", "매출전망", "가치평가", "storyValidation"),
        emphasize=frozenset(
            {
                "macroCycle",
                "macroRates",
                "macroForecast",
                "companyCyclePosition",  # 신규
                "valuationBand",
            }
        ),
        focusQuestions=(
            "지금은 사이클 어디에 있는가?",
            "과거 유사 에포크에서 이 기업은 어땠는가?",
            "이 기업의 매크로 민감도는?",
            "현 매크로에서 예상 방향은?",
        ),
        detail=True,
    ),
    "thesis": ReportType(
        key="thesis",
        label="AI 논제 검증",
        description="사용자 가설 → 증거 수집 → 찬반 정리",
        sectionOrder=(
            "thesisReport",
            "storyValidation",
        ),  # 신규 섹션
        emphasize=frozenset({"thesisStatement", "evidenceFor", "evidenceAgainst", "verdict"}),
        focusQuestions=(),
        detail=True,
    ),
    # ── P6: 대시보드 ── (2026-Q2)
    "dashboard": ReportType(
        key="dashboard",
        label="질문형 대시보드",
        description="질문 중심 회사 스냅샷: 재무제표·정기보고서·원문 근거 집약",
        sectionOrder=(
            "종합평가",
            "수익구조",
            "수익성",
            "현금흐름",
            "안정성",
            "자본배분",
            "가치평가",
            "storyValidation",
        ),
        emphasize=frozenset(
            {
                "scorecard",
                "creditScore",
                "valuationSynthesis",
                "peerPosition",
                "marginTrend",
                "cashFlowOverview",
                "cashQuality",
                "leverageTrend",
                "distressScore",
                "dividendPolicy",
                "storyPrecedents",
            }
        ),
        focusQuestions=(
            "한눈에 결론은 무엇인가?",
            "이 회사는 무엇으로 돈을 버나?",
            "번 돈은 얼마나 남나?",
            "이익은 현금으로 바뀌나?",
            "자산과 부채 구조는 안전한가?",
            "번 돈은 어디에 묶이고 어디에 재투자되나?",
            "현재 가격은 무엇을 반영하나?",
            "보고서와 원문은 숫자를 뒷받침하나?",
        ),
        detail=False,  # executive처럼 간결
    ),
}


# ── 한글/영문 alias ──

_ALIASES: dict[str, str] = {
    "투자": "investment",
    "투자분석": "investment",
    "investment": "investment",
    "invest": "investment",
    # 기존 perspective 한글
    "바텀업": "full",
    "bottomup": "full",
    "bottomUp": "full",
    "탑다운": "macro",  # topDown → macro 보고서로 재정립
    "topdown": "macro",
    "topDown": "macro",
    "사이클": "macro",  # cycle perspective → macro 보고서로 흡수
    "cycle": "macro",
    "가치": "valuation",
    "value": "valuation",
    "성장": "growth",
    "위기": "crisis",
    # 기존 preset 한글
    "경영요약": "executive",
    "신용": "credit",
    "신용분석": "credit",
    "밸류에이션": "valuation",
    "감사": "audit",
    "배당": "dividend",
    "지배구조": "governance",
    "매크로": "macro",
    "논제": "thesis",
    "가설": "thesis",
    "검증": "thesis",
    "대시보드": "dashboard",
    "snapshot": "dashboard",
    "스냅샷": "dashboard",
    "요약": "dashboard",
}


def resolveReportType(name: str | None) -> ReportType:
    """한글/영문 alias → ReportType. 빈값이면 full."""
    if not name:
        return REPORT_TYPES["full"]
    s = name.strip()
    if s in REPORT_TYPES:
        return REPORT_TYPES[s]
    if s in _ALIASES:
        return REPORT_TYPES[_ALIASES[s]]
    low = s.lower()
    if low in _ALIASES:
        return REPORT_TYPES[_ALIASES[low]]
    raise ValueError(f"알 수 없는 보고서 타입: {name!r}. 사용 가능: {', '.join(REPORT_TYPES)}")


def _validateSectionKeys() -> None:
    """REPORT_TYPES[*].sectionOrder 섹션 키가 catalog.SECTIONS 에 존재하는지 검증.

    신규 보고서 타입 추가 시 오타·폐기된 섹션 키를 import 시점에 조기 감지.
    """
    from dartlab.story.catalog import SECTIONS

    valid_keys = {s.key for s in SECTIONS}
    missing: list[tuple[str, str]] = []
    for rt in REPORT_TYPES.values():
        for sec_key in rt.sectionOrder:
            if sec_key not in valid_keys:
                missing.append((rt.key, sec_key))
    if missing:
        items = ", ".join(f"{rt}/{sec}" for rt, sec in missing)
        raise RuntimeError(
            f"reportTypes sectionOrder 에 catalog.SECTIONS 에 없는 키 발견: {items}. "
            f"catalog.SECTIONS 에 섹션 등록 또는 reportTypes sectionOrder 에서 제거."
        )


_validateSectionKeys()
