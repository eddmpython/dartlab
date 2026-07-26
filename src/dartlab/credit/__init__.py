"""dartlab 독립 신용분석 엔진 (dCR).

공시 데이터만으로 재현 가능한 독립 신용등급을 산출한다.
7축 정량 스코어링 + 업종별 차등 + 시계열 안정화 → dCR-AAA ~ dCR-D.

사용법::

    import dartlab

    # 루트 함수
    dartlab.credit("005930")                # 삼성전자 등급 종합
    dartlab.credit("005930", "채무상환")     # 채무상환 축만

    # Company-bound
    c = dartlab.Company("005930")
    c.credit()                              # 등급 종합
    c.credit("채무상환")                     # 축별 접근
    c.credit(detail=True)                   # 7축 상세 + 지표 시계열

    # story 경유 보고서
    c.story("신용분석")                     # 신용분석 전문 보고서
    c.story("신용분석").toMarkdown()         # 마크다운 출력

src/dartlab/analysis/CREDIT.md 참조.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dartlab.core.logger import getLogger

if TYPE_CHECKING:
    import polars as pl

_log = getLogger(__name__)

# Public surface - Company.credit() 와 단독 호출 양쪽 진입.
__all__ = ["axes", "credit", "creditCompany", "guide"]


# ── 7축 레지스트리 (Phase 8 A4: 4엔진 통일 - @dataclass _AxisEntry) ──


@dataclass(frozen=True)
class _AxisEntry:
    """credit 축 메타데이터. analysis/quant/macro 와 동일 패턴."""

    axis: str  # 영문 키 (정규)
    label: str  # 한글 라벨 = 과거 _CREDIT_AXES 의 fullName
    description: str
    example: str
    group: str = "dCR"  # 그룹 분류 (가이드 DF 표준 컬럼)


_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "grade": _AxisEntry(
        axis="grade",
        label="등급",
        description="dCR 종합 등급 + 점수 + 7축 가중평균 (default)",
        example='c.credit("등급")',
        group="dCR",
    ),
    "repayment": _AxisEntry(
        axis="repayment",
        label="채무상환능력",
        description="이자보상배율, 부채상환능력",
        example='c.credit("채무상환")',
        group="dCR",
    ),
    "leverage": _AxisEntry(
        axis="leverage",
        label="자본구조",
        description="부채비율, 자본 안정성",
        example='c.credit("자본구조")',
        group="dCR",
    ),
    "liquidity": _AxisEntry(
        axis="liquidity",
        label="유동성",
        description="유동비율, 단기 상환 여력",
        example='c.credit("유동성")',
        group="dCR",
    ),
    "cashflow": _AxisEntry(
        axis="cashflow",
        label="현금흐름",
        description="OCF, FCF 안정성",
        example='c.credit("현금흐름")',
        group="dCR",
    ),
    "business": _AxisEntry(
        axis="business",
        label="사업안정성",
        description="매출 변동성, 사업 지속성",
        example='c.credit("사업안정성")',
        group="dCR",
    ),
    "reliability": _AxisEntry(
        axis="reliability",
        label="재무신뢰성",
        description="감사의견, 회계 일관성",
        example='c.credit("재무신뢰성")',
        group="dCR",
    ),
    "disclosure": _AxisEntry(
        axis="disclosure",
        label="공시리스크",
        description="공시 변경, 정정 빈도",
        example='c.credit("공시리스크")',
        group="dCR",
    ),
}

# 하위 호환 - 기존 코드가 _CREDIT_AXES (한글키→fullName) 참조하는 곳용.
_CREDIT_AXES: dict[str, str] = {
    "채무상환": "채무상환능력",
    "자본구조": "자본구조",
    "유동성": "유동성",
    "현금흐름": "현금흐름",
    "사업안정성": "사업안정성",
    "재무신뢰성": "재무신뢰성",
    "공시리스크": "공시리스크",
}

_ALIASES: dict[str, str] = {
    "repayment": "채무상환",
    "leverage": "자본구조",
    "capital": "자본구조",
    "liquidity": "유동성",
    "cashflow": "현금흐름",
    "business": "사업안정성",
    "reliability": "재무신뢰성",
    "disclosure": "공시리스크",
    "채무상환능력": "채무상환",
    "사업위험": "사업안정성",
    "사업": "사업안정성",
    "신뢰성": "재무신뢰성",
    "공시": "공시리스크",
}

# 종합 등급 alias (가이드 무인자 호출과 구분)
_GRADE_ALIASES = {"등급", "grade", "종합", "종합등급", "credit", "신용등급"}


def guide() -> "pl.DataFrame":
    """credit 엔진 7축 + 종합 가이드 DataFrame.

    Capabilities:
        dCR 신용분석 엔진의 7 축 (채무상환능력/자본구조/유동성/현금흐름/사업안정성/재무신뢰성/
        공시리스크) + 종합 등급 카탈로그를 polars DataFrame 으로 반환. 동시에 빠른 시작 안내
        로그 출력. 신규 사용자 self-discovery 진입점.

    공시 재무제표만으로 독립 신용등급(dCR)을 산출하는 엔진의 축 카탈로그.
    외부 API 키 불필요 - DART/EDGAR 재무 데이터 기반.

    Returns
    -------
    polars.DataFrame
        axis : str - 영문 축 키 (grade, repayment, leverage, …)
        label : str - 한글 라벨 (등급, 채무상환능력, 자본구조, …)
        description : str - 축 설명
        example : str - 호출 예시
        group : str - 그룹 분류 (dCR)
        apiKey : str - API 키 필요 여부 ("불필요" - 재무 데이터 기반)

    Examples
    --------
    >>> import dartlab
    >>> dartlab.credit()                        # 이 가이드
    >>> dartlab.credit("005930")                # 삼성전자 종합 등급
    >>> dartlab.credit("005930", "채무상환")     # 채무상환 축만
    >>> c = dartlab.Company("005930")
    >>> c.credit()                              # Company-bound 가이드
    >>> c.credit("등급")                        # 종합 등급
    >>> c.credit("채무상환", detail=True)        # 채무상환 축 상세

    Raises:
        없음.

    When:
        ``dartlab.credit()`` / ``Company.credit()`` 무인자 호출 시 self-discovery 진입점. 신규
        사용자가 축 목록 확인할 때.

    How:
        ``_AXIS_REGISTRY`` 내부 카탈로그 → ``synth.axisGuide.buildAxisGuideDataFrame`` → 빠른
        시작 안내 로그.

    Requires:
        - 외부 데이터 불필요 (메모리 카탈로그만).

    See Also:
        - ``dartlab.credit.credit`` : 본 가이드 + 등급 산출 진입점
        - ``dartlab.credit.creditCompany`` : Company-bound 진입점

    AIContext:
        AI 가 신규 종목 분석 전 축 목록 확인할 때 직접 호출. 답변 시 "credit 엔진 7 축" 정식
        명칭 표기 권장.
    """
    from dartlab.synth.axisGuide import buildAxisGuideDataFrame

    df = buildAxisGuideDataFrame(
        _AXIS_REGISTRY,
        groupExtractor=lambda _k, e: e.group,
    )

    # 빠른 시작 안내 출력
    _lines = [
        "",
        "dCR - 독립 신용등급 (7축 정량 스코어링)",
        "",
        "━━━ 빠른 시작 ━━━",
        '  c = dartlab.Company("005930")',
        '  c.credit("등급")                        # dCR 종합 등급',
        '  c.credit("채무상환")                     # 채무상환능력 축',
        '  c.credit("등급", detail=True)            # 7축 상세 + 시계열',
        "",
        "━━━ 7축 ━━━",
        "  채무상환능력 · 자본구조 · 유동성 · 현금흐름",
        "  사업안정성 · 재무신뢰성 · 공시리스크",
        "",
        "━━━ 데이터 ━━━",
        "  재무제표: DART/EDGAR 공시 (API 키 불필요)",
        "  등급 범위: dCR-AAA ~ dCR-D",
        "",
    ]
    _log.info("\n".join(_lines))

    return df


def _resolveAxis(axis: str) -> str | None:
    """축 이름 또는 명시 alias → 정규 축 이름.

    consistency_no_alias: case-insensitive (``axis.lower()``) silent alias
    인정 안 함. 사용자는 한글 정식 또는 ``_ALIASES`` 명시 매핑만 사용.
    """
    if axis in _CREDIT_AXES:
        return axis
    if axis in _ALIASES:
        return _ALIASES[axis]
    return None


def _filterAxis(result: dict, axis: str) -> dict | None:
    """등급 결과에서 특정 축만 추출."""
    resolved = _resolveAxis(axis)
    if resolved is None:
        available = ", ".join(sorted(_CREDIT_AXES))
        raise ValueError(
            f"알 수 없는 신용분석 축: '{axis}'. 가용 축: {available}\n"
            f"  사용법: c.credit() 으로 전체 신용분석 결과를 확인하세요."
        )

    fullName = _CREDIT_AXES[resolved]
    for a in result.get("axes", []):
        if a.get("name") == fullName:
            return {
                "axis": fullName,
                "score": a.get("score"),
                "weight": a.get("weight"),
                "metrics": a.get("metrics", []),
                "grade": result.get("grade"),
                "overallScore": result.get("score"),
                # R22-1: 단일 축 추출에도 score 의미 안내 전달
                "_scoreMeaning": result.get("_scoreMeaning"),
            }
    return None


def credit(
    axis: str | None = None, target: str | None = None, *, detail: bool = False, basePeriod: str | None = None
) -> dict | "pl.DataFrame" | None:
    """신용등급 산출 단일 진입점 - gather 표준 ``credit(axis, target)`` axis-first.

    gather 표준: ``credit("채무상환", "005930")`` (axis, target=stockCode). 종합등급은
    ``credit("등급", "005930")`` 또는 단축 ``credit("005930")``. **backward-compat**: 옛
    id-first ``credit("005930", "채무상환")`` 은 자동 swap + DeprecationWarning 으로 흡수.

    Capabilities:
        DART/EDGAR 공시 재무제표만으로 dCR 독립 신용등급을 산출하는 단일 진입점. 무인자 호출 시
        가이드, stockCode 만 호출 시 종합 등급, axis 지정 시 해당 축만 반환. 79 개사 검증 대기업
        87% / 중대형 82% 정확도. 외부 API 키 불필요.

    AIContext:
        AI 가 회사 부도 위험 / 재무 건전성 평가 진입점. axes 7 개 score 와 grade 종합 인용.
        시점 단정보다 "정기보고서 마감 후 30~45 일 시차" 단서 권장.

    Parameters
    ----------
    stockCode : str | None
        종목코드 또는 ticker. None이면 7축 가이드 DataFrame 반환.
    axis : str | None
        축 이름 ("등급" → 종합, "채무상환"/"자본구조"/"유동성"/"현금흐름"/
        "사업안정성"/"재무신뢰성"/"공시리스크" → 해당 축만).
        영문 alias("repayment", "leverage" 등)도 지원.
    detail : bool
        True이면 7축 상세 + 모든 지표 시계열 + 서사(narrative) 포함.
    basePeriod : str | None
        분석 기준 기간 (예: "2024"). None이면 최신.

    Returns
    -------
    DataFrame | dict | None
        - stockCode=None → 가이드 DataFrame (axis, label, description, example, group)
        - axis="등급" 또는 None+stockCode → 종합 등급 dict

          grade : str - dCR 등급 (예: "dCR-AA+")
          score : float - 위험 점수 (0=최우량, 100=최위험) (점)
          healthScore : float - 건전성 점수 (100-score) (점)
          axes : list[dict] - 7축 상세 (name, score, weight, metrics)
          eCR : str | None - 현금흐름등급
          outlook : str - 전망 ("안정적"/"긍정적"/"부정적")

        - axis=축이름 → 해당 축 dict

          axis : str - 축 풀네임
          score : float - 해당 축 위험 점수 (점)
          weight : int - 가중치 (%)
          metrics : list[dict] - 개별 지표 (name, value, score)

    Examples
    --------
    >>> import dartlab
    >>> dartlab.credit("005930")                # 삼성전자 종합
    >>> dartlab.credit("005930", "채무상환")     # 채무상환 축만
    >>> dartlab.credit()                        # 가이드 DataFrame

    Raises
    ------
    ValueError
        축 이름이 등록되지 않은 경우.

    Notes
    -----
    3-Track 모델(일반/금융/지주) + Notch Adjustment + CHS 시장 보정.
    79개사 검증: 대기업 87%, 중대형 82%. DART 공시 기반, API 키 불필요.

    Requires:
        - L1 raw: DART 정기보고서 (자동 다운로드) 또는 EDGAR 10-K/10-Q
        - L1.5 frame: 재무제표 가공 frame

    Guide
    -----
    AI 역할: AI는 credit을 상환능력·재무건전성 판단 엔진으로 보고 부채, 현금흐름, 이자보상, 만기 근거를 요구한다.
    When: 종목의 부도 위험·재무 건전성을 독립 평가할 때.
    How: credit 단독으로 종합 등급 확인 → analysis(안정성, 현금흐름) 와 함께 심층 진단.
        story credit 타입이 credit + analysis(안정성) + analysis(현금흐름) + analysis(자금조달) 순서로 조합.
    Verified:
        - credit 단독 → dCR 등급 + 7축 위험점수 + PD 추정 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
        - credit + analysis(안정성,현금흐름) → 부도 위험 종합 진단 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

    See Also
    --------
    analysis : 재무 심층 분석 - 안정성·현금흐름 축이 credit 과 상호 보완.
    scan : 전종목 재무건전성 비교.

    LLM Specifications:
        AntiPatterns:
            - axis 영문 ("repayment") 사용 시 한글 alias 함께 - 한글 우선 권장
            - 종합 score 단독 인용 (grade + 7 축 dict 함께)
            - "부도 위험 높음" 단정 X (등급 + outlook + 시계열 함께)
        OutputSchema:
            - grade : str - dCR 등급 (dCR-AAA ~ dCR-D)
            - score : float - 위험 점수 (0~100, 0 = 최우량)
            - healthScore : float - 건전성 점수 (100 - score)
            - axes : list[dict] - 7 축 (name / score / weight / metrics)
            - eCR : str | None - 현금흐름등급
            - outlook : str - 안정적 / 긍정적 / 부정적
        Prerequisites:
            - finance + report 데이터 (자동 다운로드)
        Freshness:
            정기보고서 마감 후 30~45 일.
        Dataflow:
            stockCode → engine.evaluate → 7 축 calc (repayment/leverage/
            liquidity/cashFlow/businessStability/reliability/disclosureRisk)
            → 가중 점수 합산 → CHS notch → grade 변환 → dict 조립.
        TargetMarkets:
            - KR (DART)
    """
    # gather 표준 axis-first 정규화 + 옛 id-first swap (quant 패턴).
    if axis is not None and (axis in _AXIS_REGISTRY or axis in _ALIASES or axis in _GRADE_ALIASES):
        stockCode = target  # 신형: credit("채무상환","005930")
    elif axis is not None and target is not None:
        import warnings

        warnings.warn(
            f'dartlab.credit("{axis}", "{target}") 호출은 deprecated - '
            f'dartlab.credit("{target}", "{axis}") (axis-first) 를 사용하세요.',
            DeprecationWarning,
            stacklevel=2,
        )
        stockCode, axis = axis, target  # 옛형 swap
    else:
        stockCode, axis = axis, None  # credit() 가이드 / credit("005930") 종합등급

    if stockCode is None:
        return guide()

    # "등급"/"grade" 등 종합 alias는 axis로 처리하지 않음 (전체 결과)
    if axis is not None and axis in _GRADE_ALIASES:
        axis = None

    from dartlab.company import Company
    from dartlab.credit.engine import evaluateCompany

    company = Company(stockCode)
    result = evaluateCompany(company, detail=True, basePeriod=basePeriod)
    if result is None:
        if axis is not None:
            return None
        from dartlab.credit.product import blockedCreditResult

        return blockedCreditResult(
            company,
            reason="해당 시장에는 검증된 dCR calibration이 없거나 필수 재무 근거가 부족합니다.",
            basePeriod=basePeriod,
        )

    if axis is not None:
        return _filterAxis(result, axis)

    from dartlab.credit.product import attachCreditProduct

    return attachCreditProduct(company, result, basePeriod=basePeriod)


def creditCompany(
    company,
    axis: str | None = None,
    *,
    detail: bool = False,
    basePeriod: str | None = None,
    overrides: dict | None = None,
) -> dict | "pl.DataFrame" | None:
    """Company 객체로 신용등급 산출 (Company-bound용).

    Capabilities:
        ``credit()`` 의 Company-bound 변형. DartCompany / EdgarCompany 인스턴스를 받아 동일
        7 축 + 종합 등급 산출. ``overrides`` 지원 - AI / 사용자가 시나리오 가정 (예: 부채비율
        150% 가정) 을 주입해 stress / what-if 분석 가능.

    Parameters
    ----------
    company : Company
        DartCompany 또는 EdgarCompany 인스턴스.
    axis : str | None
        None → 가이드 DataFrame (self-discovery).
        "등급"/"grade" → 종합 등급 dict.
        "채무상환"/"자본구조" 등 → 해당 축 dict.
    detail : bool
        True이면 7축 상세 + 서사 + 시계열 포함.
    basePeriod : str | None
        분석 기준 기간 (예: "2024"). None이면 최신.
    overrides : dict | None
        AI/사용자 시나리오 가정 교체. core/overrides.py CREDIT_KEYS 참조.
        예: ``{"debtRatio": 150}`` → 부채비율을 150%로 가정한 시나리오.

    Returns
    -------
    DataFrame | dict | None
        axis=None → 가이드 DataFrame.
        axis 지정 시 → 해당 축 또는 종합 등급 dict.
        overrides 적용 시 결과 dict에 ``assumptions`` 키가 추가됨.

    Examples
    --------
    >>> c = dartlab.Company("005930")
    >>> c.credit("등급")                      # 종합
    >>> c.credit("채무상환", detail=True)      # 채무상환 축 상세

    Raises:
        ValueError: ``axis`` 가 등록되지 않은 이름인 경우 ``_filterAxis`` 에서.

    Guide:
        ``Company.credit`` 의 위임 대상. overrides 사용 시 ``assumptions`` 키가 결과 dict 에
        추가 - UI / 답변에 "가정 명시" 단서 인용 권장.

    When:
        Company 객체에 binding 된 신용 분석. AI/사용자가 stress 시나리오 (부채비율 가정 등) 를
        주입할 때.

    How:
        ``credit.engine.evaluateCompany`` 위임 → ``overrides`` 전달 → 축 필터 (optional) →
        ``synth.overrides.buildAssumptions`` 로 가정 투명화.

    Requires:
        - Company 객체 (DartCompany / EdgarCompany)
        - L1 raw: 회사별 재무 데이터 접근 가능

    See Also:
        - ``dartlab.credit.credit`` : stockCode 버전
        - ``dartlab.synth.overrides.buildAssumptions`` : 가정 투명화

    AIContext:
        AI 가 시나리오 / what-if 분석 ("부채비율이 X% 였다면") 답변 시 ``overrides`` 키 직접 사용.
        답변에 ``assumptions`` 필드 인용 의무.
    """
    if axis is None:
        return guide()

    from dartlab.credit.engine import evaluateCompany

    # "등급"/"grade" 등 종합 alias는 axis로 처리하지 않음
    if axis in _GRADE_ALIASES:
        axis_filter: str | None = None
    else:
        axis_filter = axis

    result = evaluateCompany(
        company,
        detail=True,
        basePeriod=basePeriod,
        overrides=overrides,
    )
    if result is None:
        if axis_filter is not None:
            return None
        from dartlab.credit.product import blockedCreditResult

        return blockedCreditResult(
            company,
            reason="해당 시장에는 검증된 dCR calibration이 없거나 필수 재무 근거가 부족합니다.",
            basePeriod=basePeriod,
        )

    if axis_filter is not None:
        result = _filterAxis(result, axis_filter)

    # assumptions 투명화 - 4 엔진 공통 utility (core/overrides.py)
    if isinstance(result, dict):
        from dartlab.synth.overrides import buildAssumptions

        appliedOverrides = result.get("appliedOverrides") if isinstance(result.get("appliedOverrides"), dict) else None
        assumptions = buildAssumptions(result, engine="credit", overrides=appliedOverrides)
        if assumptions:
            result["assumptions"] = assumptions

    if axis_filter is None and isinstance(result, dict):
        from dartlab.credit.product import attachCreditProduct

        result = attachCreditProduct(company, result, basePeriod=basePeriod)

    return result


def axes() -> dict[str, str]:
    """가용한 7축 목록.

    Returns
    -------
    dict[str, str]
        키 : str - 축 이름 (예: "repayment", "leverage").
        값 : str - 한글 레이블 (예: "채무상환능력", "자본구조").

    Raises:
        없음.

    Requires:
        - 외부 데이터 불필요 (정적 dict 복사 반환).
    """
    return dict(_CREDIT_AXES)
