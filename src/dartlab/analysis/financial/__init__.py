"""재무제표 완전 분석 통합 진입점.

scan()이 시장 전체를 횡단하듯, analysis()는 단일 종목을 심층 분석한다.

사용법::

    import dartlab

    dartlab.analysis()                              # 전체 가이드
    dartlab.analysis("financial", "수익구조")         # 수익구조 분석 항목 목록
    dartlab.analysis("financial", "수익구조", c)      # 삼성전자 수익구조 분석 실행
    dartlab.analysis("financial", "이익품질", c)      # 삼성전자 이익의 질 분석

    c.analysis()                                    # 가이드
    c.analysis("financial", "수익성")                 # 수익성 분석
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any

import polars as pl

from dartlab.analysis.financial._registry import (
    _ALIASES,
    _AXIS_REGISTRY,
    _AXIS_TO_GROUP,
    _GROUPS,
    _AxisEntry,
    _CalcEntry,
    _resolveAxis,
)

# ── axis warm-up - calc 간 공유 accessor 선제 빌드 ──


def _warmupFinanceAccessors(company: Any) -> None:
    """축 실행 전 IS/BS/CF 공통 accessor 를 선제 빌드해 calc 간 공유.

    14축 × 50+ calc 가 각자 ``company.select("IS", ...)`` / ``company._finance.BS``
    를 독립 접근하면 accessor 캐시가 BoundedCache evict 뒤 재빌드되며
    loadData 반복 호출을 유발한다. 축 실행 직전에 한 번 빌드해 Company.
    _cache 의 ``_financeStmt_{sjDiv}_Q_consolidated`` key 를 미리 적재하면
    이후 calc 들은 전부 cache-hit 로 수렴한다.

    금융업 CF 부재 같은 정상 예외는 조용히 무시 - 해당 calc 가 내부에서
    None 반환으로 처리한다.
    """
    stmt = getattr(company, "_financeStmt", None)
    if stmt is None:
        return
    for sjDiv in ("IS", "BS", "CF"):
        try:
            stmt(sjDiv, freq="Q", scope="consolidated")
        except (AttributeError, KeyError, ValueError, TypeError):
            pass


# ── basePeriod 지원 여부 검사 (캐싱) ──

_BP_CACHE: dict[str, bool] = {}
_OV_CACHE: dict[str, bool] = {}


def _acceptsBasePeriod(fn) -> bool:
    """calc 함수가 basePeriod 파라미터를 받는지 확인 (결과 캐싱)."""
    key = f"{fn.__module__}.{fn.__qualname__}"
    cached = _BP_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        sig = inspect.signature(fn)
        result = "basePeriod" in sig.parameters
    except (ValueError, TypeError):
        result = False
    _BP_CACHE[key] = result
    return result


def _acceptsOverrides(fn) -> bool:
    """calc 함수가 overrides 파라미터를 받는지 확인 (결과 캐싱)."""
    key = f"{fn.__module__}.{fn.__qualname__}"
    cached = _OV_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        sig = inspect.signature(fn)
        result = "overrides" in sig.parameters
    except (ValueError, TypeError):
        result = False
    _OV_CACHE[key] = result
    return result


# ── 엔진 가정 투명화 (assumptions aggregation) ──
#
# AI 가 엔진 결과를 조율(override)하려면 "엔진이 무슨 값을 썼는지" 알아야 한다.
# 각 calc 결과에 흩어진 discountRate/baseWacc/assumedMargin 등을 표준 키로 모아
# `results["assumptions"]` 에 주입. autoEnrich 가 이걸 _summary 에 반영.

# _aggregateAssumptions → core/overrides.buildAssumptions 로 이전 (4 엔진 공통).
# 엔진별 특수 추출은 core/overrides._extractAnalysisSpecific.


# ── Group Accessor ──


class _GroupAccessor:
    """analysis.financial, analysis.valuation 등 그룹 accessor."""

    def __init__(self, analysisInstance: "Analysis", group: str) -> None:
        self._analysis = analysisInstance
        self._group = group

    def __call__(self, company=None, *, stockCode=None, basePeriod=None, overrides=None) -> object:
        """그룹 가이드 또는 그룹 전체 실행. `stockCode` / `company` 호환."""
        return self._analysis(
            self._group,
            company=company,
            stockCode=stockCode,
            basePeriod=basePeriod,
            overrides=overrides,
        )

    def __getattr__(self, name: str) -> object:
        """analysis.financial.profitability() 패턴."""
        try:
            resolved = _resolveAxis(name)
        except ValueError:
            raise AttributeError(f"'{self._group}' 그룹에 '{name}' 축이 없습니다")

        if resolved not in _GROUPS.get(self._group, []):
            raise AttributeError(f"'{name}' 축은 '{self._group}' 그룹에 속하지 않습니다")

        def _boundAxis(company=None, *, stockCode=None, basePeriod=None, overrides=None):
            """그룹 내 특정 축 실행 바인딩. `stockCode` / `company` 호환."""
            return self._analysis(
                self._group,
                resolved,
                company=company,
                stockCode=stockCode,
                basePeriod=basePeriod,
                overrides=overrides,
            )

        _boundAxis.__name__ = name
        _boundAxis.__doc__ = f'analysis("{self._group}", "{resolved}")'
        return _boundAxis

    def __repr__(self) -> str:
        axes = _GROUPS.get(self._group, [])
        lines = [f"Analysis.{self._group} -- {len(axes)}축"]
        for key in axes:
            entry = _AXIS_REGISTRY.get(key)
            if entry:
                lines.append(f"  {key:8s} {entry.description}")
        return "\n".join(lines)


# ── Analysis Class ──


class Analysis:
    """재무제표 완전 분석 - 20축, 단일 종목 심층.

    Capabilities:
        Part 1 - 사업구조: 수익구조, 자금조달, 자산구조, 현금흐름
        Part 2 - 핵심비율: 수익성, 성장성, 안정성, 효율성, 종합평가
        Part 3 - 심화분석: 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
        Part 4 - 가치평가: DCF, DDM, 상대가치, RIM, 목표주가, 역내재성장률, 민감도
        Part 5 - 비재무 심화: 지배구조, 공시변화감지, 비교분석
        Part 6 - 전망분석: 매출전망, 예측신호
        - 각 축은 Company를 받아 dict를 반환하는 순수 함수 집합
        - story()가 이 결과를 소비하여 구조화 보고서 생성

    Requires:
        데이터: finance (자동 다운로드)

    AIContext:
        - ask() (dartlab.ask) 가 analysis 결과를 tool 로 소비해 AI 해석 생성
        - ask()에서 재무분석 컨텍스트로 활용
        - 70개 calc* 함수의 개별 결과를 LLM에 주입 가능

    Guide:
        - AI 역할: AI는 analysis를 단일 기업 재무·가치·리스크 해석 엔진으로 보고 axis/subaxis와 필요한 재무 evidence를 선택한다.
        - "이 회사 수익구조?" -> analysis("financial", "수익구조") - 매출원가율, 판관비율 등
        - "재무 건전한가?" -> analysis("financial", "안정성") - 부채비율, 유동비율, ICR
        - "이익이 진짜야?" -> analysis("financial", "이익품질") - 발생주의 비율, OCF/NI
        - "적정가치?" -> analysis("valuation", "가치평가") - DCF/DDM/상대/RIM/목표가
        - "전체 종합?" -> analysis("financial", "종합평가") - 15축 통합 스코어
        - 15축 전부 보고 싶으면 story() 사용 권장

    SeeAlso:
        - story: analysis 결과를 구조화 보고서로 렌더링
        - scan: 전종목 비교 (analysis는 단일 종목 심층)
        - Company.insights: 7영역 인사이트 등급 (빠른 요약)

    Args:
        axis: 축 이름 ("수익구조", "수익성" 등). None이면 15축 가이드.
        company: Company 객체. None이면 해당 축의 분석 항목 목록.
        **kwargs: 축별 옵션.

    Returns:
        axis=None → pl.DataFrame (15축 가이드)
        company=None → pl.DataFrame (해당 축 calc 목록)
        둘 다 있으면 → dict (분석 결과)

    Example::

        import dartlab
        dartlab.analysis()                              # 전체 가이드
        dartlab.analysis("financial", "수익구조")                       # 항목 목록
        c = dartlab.Company("005930")
        dartlab.analysis("financial", "수익구조", company=c)            # 삼성전자 수익구조
        dartlab.analysis("financial", "수익구조", stockCode="005930")   # 종목코드 단독
        c.analysis("financial", "수익성")                               # Company 바인딩
    """

    def __call__(
        self,
        axis: str | None = None,
        sub: Any | None = None,
        *,
        company: Any | None = None,
        stockCode: str | None = None,
        basePeriod: str | None = None,
        overrides: dict | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame | dict:
        """재무 심층 분석 - 5 그룹 22 축 인과 분석 + 가치평가 + 전망.

        2단계 호출: analysis("그룹", "축") 또는 analysis("축") 단축형.

        Parameters
        ----------
        axis : str, optional
            분석 축 또는 그룹. None 이면 가이드 DataFrame 반환.
            그룹: "financial", "valuation", "governance", "forecast", "macro".
            축: "수익구조", "수익성", "성장성", "안정성", "현금흐름", "자본배분",
            "투자효율", "가치평가", "매출전망", "이익전망" 등 22 축.
        sub : str, optional
            그룹 호출 시 하위 축 지정. analysis("financial", "수익성").
        stockCode : str, optional
            종목코드. company 없이 단독 호출 시 사용.
        basePeriod : str, optional
            기준 기간 (예: "2024Q4"). 생략 시 최신 기간 자동.
        overrides : dict, optional
            calc 함수 입력값 재지정 (what-if 시나리오).

        Returns
        -------
        dict
            축별 분석 결과. 공통 키:
                period : str - 기준 기간
                items : list[dict] - 개별 지표 목록
                    name : str - 지표명
                    value : float | str - 값
                    unit : str - 단위 (%, 원, 배, 일, 점)
                    trend : str - 추세 (상승/하락/유지)
            축별 추가 키:
                marginTrend : list - 마진 시계열 (수익성)
                debtMetrics : dict - 부채 지표 (안정성)
                fcfHistory : list - FCF 시계열 (현금흐름)
                targetPrice : float - 적정 주가 (가치평가, 원)
                forecastRevenue : list - 매출 전망 (매출전망)
        pl.DataFrame
            axis=None: 가이드 - 축 목록 + 설명 + 예시.
            그룹만 지정 시: 그룹 내 축 목록.

        Raises
        ------
        ValueError
            축이 그룹에 속하지 않는 경우 (예: analysis("valuation", "수익성")).
            등록되지 않은 축 이름.

        Examples
        --------
        >>> c.analysis()                              # 전체 축 가이드
        >>> c.analysis("financial", "수익성")          # 그룹 + 축
        >>> c.analysis("수익성")                       # 단축형
        >>> c.analysis("가치평가")                     # 적정 주가
        >>> dartlab.analysis("수익성", stockCode="005930")  # 종목코드 단독

        Notes
        -----
        DART 공시 재무제표 기반. API 키 불필요.
        분기별 비교 가능성이 핵심 - 모든 축이 시계열 추이를 포함.

        Guide
        -----
        When: 개별 종목의 재무 인과를 심층 분석할 때.
        How: 6막 인과 순서 - 수익구조 → 수익성 → 성장성 → 안정성 → 현금흐름 → 자본배분.
            story full/executive 타입이 이 순서로 조합.
            credit 분석 시 안정성 + 현금흐름 먼저, credit 엔진과 함께 사용.
            valuation 분석 시 수익성 + 성장성 → 가치평가 + 매출전망 순서.

        See Also
        --------
        credit : 독립 신용 분석 - analysis(안정성) 와 함께 사용.
        scan : 전종목 횡단 비교 - 상대 위치 파악 후 심층 분석.
        quant : 가격 기반 정량 신호 - analysis 재무 + quant 기술 조합.
        macro : 거시 환경 - 기업 분석의 매크로 컨텍스트.

        LLM Specifications:
            AntiPatterns:
                - axis 영문 ("profitability") 사용 (실제는 한글 - "수익성")
                - "valuation" 그룹에 "수익성" 같이 다른 그룹 sub 전달 (그룹별 sub 다름)
                - overrides 키 추측 (axis 별 다름 - calc 함수 시그니처 확인)
            OutputSchema:
                - period : str - 기준 기간
                - items : list[dict] - 지표 (name / value / unit / trend)
                - axis 별 추가: marginTrend (수익성), debtMetrics (안정성), fcfHistory
                  (현금흐름), targetPrice (가치평가), forecastRevenue (매출전망)
                - dataAsOf : dict - latestPeriod / retrievedAt
            Prerequisites:
                - finance 데이터 (자동 다운로드)
            Freshness:
                finance 분기 - 마감 후 30~45 일.
            Dataflow:
                analysis(axis) → 결과 dict → review/story 가 보고서로 조립
            TargetMarkets:
                - KR (DART)
        """
        if axis is None:
            return self._guide()

        # sub가 Company 객체면 legacy 호환: analysis("financial", "수익성", company)
        if sub is not None and hasattr(sub, "stockCode"):
            company = sub
            sub = None

        # stockCode 인자 수용 - 일관성 규약 (종목 = stockCode).
        # company 없고 stockCode 있으면 Company 생성.
        if company is None and stockCode is not None:
            from dartlab.company import Company

            company = Company(stockCode)

        # 그룹 해석 - 직접 그룹명 또는 한글 그룹 alias
        group = axis if axis in _GROUPS else _ALIASES.get(axis) if _ALIASES.get(axis) in _GROUPS else None

        if group is not None:
            # 2단계: analysis("financial", "수익성")
            if sub is None:
                return self._groupGuide(group)
            resolved = _resolveAxis(sub)
            # R24-1: 축이 그룹에 속하는지 명시적 검증.
            # 이전엔 `analysis("valuation", "수익성")` 같은 그룹/축 mismatch 가
            # silent 로 잘못된 그룹의 결과를 반환했다.
            if resolved not in _GROUPS.get(group, []):
                group_axes = _GROUPS.get(group, [])
                axes_str = ", ".join(group_axes) if group_axes else "(없음)"
                raise ValueError(
                    f"'{resolved}' 축은 '{group}' 그룹에 속하지 않습니다. "
                    f"'{group}' 그룹의 가용 축: {axes_str}\n"
                    f"  사용법: c.analysis('{group}') 로 그룹의 축 목록을 확인하거나, "
                    f"c.analysis('{resolved}') 로 축만 직접 호출하세요."
                )
            entry = _AXIS_REGISTRY[resolved]
            if company is None:
                return self._listCalcs(resolved, entry)
            return self._run(company, entry, basePeriod=basePeriod, overrides=overrides)

        # 그룹 없이 축만 전달된 경우 → 자동 추론
        resolved = _resolveAxis(axis)
        entry = _AXIS_REGISTRY[resolved]

        if company is None:
            return self._listCalcs(resolved, entry)

        return self._run(company, entry, basePeriod=basePeriod, overrides=overrides)

    def _groupGuide(self, group: str) -> pl.DataFrame:
        """그룹 내 축 목록."""
        axes = _GROUPS.get(group, [])
        rows = []
        for key in axes:
            entry = _AXIS_REGISTRY.get(key)
            if entry:
                rows.append({"축": key, "파트": entry.partId, "설명": entry.description})
        if not rows:
            return pl.DataFrame()
        return pl.DataFrame(rows)

    def _guide(self) -> pl.DataFrame:
        """축 가이드 - 5엔진 통일 컬럼 (axis, label, description, example, group, items, apiKey).

        Returns
        -------
        pl.DataFrame
            axis : str - 축 이름
            label : str - 한글 레이블
            description : str - 설명
            example : str - 사용 예시
            group : str - 소속 그룹 (entry.section)
            items : int - calc 함수 개수
            apiKey : str - 필요한 API 키 ("불필요" - 모든 축이 DART 공시 기반)
        """
        from dartlab.synth.axisGuide import buildAxisGuideDataFrame

        return buildAxisGuideDataFrame(
            _AXIS_REGISTRY,
            groupExtractor=lambda k, e: e.section,
            extraColumns={"items": lambda k, e: len(e.calcs)},
        )

    def _listCalcs(self, axis: str, entry: _AxisEntry) -> pl.DataFrame:
        """해당 축의 분석 항목 목록."""
        rows = []
        for calc in entry.calcs:
            rows.append(
                {
                    "blockKey": calc.blockKey,
                    "함수": calc.fn,
                    "label": calc.label,
                }
            )
        return pl.DataFrame(rows)

    def _run(
        self,
        company: Any,
        entry: _AxisEntry,
        *,
        basePeriod: str | None = None,
        overrides: dict | None = None,
    ) -> dict:
        """해당 축의 calc* 함수 전부 실행.

        Parameters
        ----------
        overrides : dict | None
            AI/사용자가 지정한 가정 override. overrides 파라미터를
            받는 calc 함수에만 전달된다.
        """
        _warmupFinanceAccessors(company)
        results: dict[str, Any] = {}
        appliedOverrides: dict[str, Any] = {}
        calculationErrors: dict[str, str] = {}
        for calc in entry.calcs:
            try:
                mod = importlib.import_module(calc.module)
                fn = getattr(mod, calc.fn)
                kw: dict[str, Any] = {}
                if _acceptsBasePeriod(fn):
                    kw["basePeriod"] = basePeriod
                if overrides and _acceptsOverrides(fn):
                    kw["overrides"] = overrides
                    appliedOverrides.update(overrides)
                results[calc.blockKey] = fn(company, **kw)
            except (
                KeyError,
                ValueError,
                TypeError,
                AttributeError,
                ArithmeticError,
                ImportError,
                RuntimeError,
                OSError,
            ) as exc:
                results[calc.blockKey] = None
                calculationErrors[calc.blockKey] = type(exc).__name__
            except Exception as exc:
                from dartlab.gather.types import isOptionalSourceError

                if not isOptionalSourceError(exc):
                    raise
                results[calc.blockKey] = None
                calculationErrors[calc.blockKey] = type(exc).__name__

        usableBlocks = [
            calc.blockKey
            for calc in entry.calcs
            if results.get(calc.blockKey) is not None
            and not (
                isinstance(results.get(calc.blockKey), dict)
                and results[calc.blockKey].get("status") in {"blocked", "unavailable"}
            )
        ]
        expectedBlocks = [calc.blockKey for calc in entry.calcs]
        if len(usableBlocks) == len(expectedBlocks):
            assessmentStatus = "usable"
        elif usableBlocks:
            assessmentStatus = "partial"
        else:
            assessmentStatus = "blocked"
        results["assessmentStatus"] = assessmentStatus
        results["coverage"] = {
            "observedBlocks": len(usableBlocks),
            "totalBlocks": len(expectedBlocks),
            "usableBlockKeys": usableBlocks,
            "missingBlockKeys": [key for key in expectedBlocks if key not in usableBlocks],
        }
        if calculationErrors:
            results["calculationErrors"] = calculationErrors

        # 엔진 투명성 - 4 엔진 공통 utility (core/overrides.py)
        from dartlab.synth.overrides import buildAssumptions

        assumptions = buildAssumptions(results, engine="analysis", overrides=appliedOverrides or None)
        if assumptions:
            results["assumptions"] = assumptions

        # Phase 15 B2: dataAsOf 자동 주입 - 각 calc history 의 최신 period + 호출 시각
        try:
            from dartlab.core.utils.period import resolveLatestPeriod

            periods_pool: set[str] = set()
            blockPeriods: dict[str, list[str]] = {}
            blockLatestPeriods: dict[str, str] = {}

            def _collectPeriods(value: Any, target: set[str]) -> None:
                if isinstance(value, dict):
                    period = value.get("period")
                    if isinstance(period, str) and period:
                        target.add(period)
                    for child in value.values():
                        _collectPeriods(child, target)
                elif isinstance(value, list):
                    for child in value:
                        _collectPeriods(child, target)

            for calc in entry.calcs:
                found: set[str] = set()
                _collectPeriods(results.get(calc.blockKey), found)
                if found:
                    blockPeriods[calc.blockKey] = sorted(found)
                    blockLatest = resolveLatestPeriod(list(found))
                    if blockLatest:
                        blockLatestPeriods[calc.blockKey] = blockLatest
                    periods_pool.update(found)
            latest = resolveLatestPeriod(list(periods_pool)) if periods_pool else None
            if latest or basePeriod:
                import datetime as _dt

                results["dataAsOf"] = {
                    "latestPeriod": latest or basePeriod,
                    "earliestPeriod": min(periods_pool) if periods_pool else basePeriod,
                    "periods": sorted(periods_pool),
                    "blockPeriods": blockPeriods,
                    "blockLatestPeriods": blockLatestPeriods,
                    "mixedPeriods": len(set(blockLatestPeriods.values())) > 1,
                    "retrievedAt": _dt.datetime.now().date().isoformat(),
                }
        except (ImportError, AttributeError, KeyError, TypeError):
            pass

        if entry.section == "종합평가":
            from dartlab.analysis.financial.representative import buildAnalysisProduct

            results["product"] = buildAnalysisProduct(company, results, basePeriod=basePeriod)
        return results

    def __getattr__(self, name: str) -> "_GroupAccessor":
        """accessor 패턴: analysis.financial, analysis.valuation 등."""
        group = name if name in _GROUPS else _ALIASES.get(name) if _ALIASES.get(name) in _GROUPS else None
        if group is not None:
            return _GroupAccessor(self, group)
        raise AttributeError(f"Analysis에 '{name}' 속성이 없습니다")

    def __repr__(self) -> str:
        total_calcs = sum(len(e.calcs) for e in _AXIS_REGISTRY.values())
        lines = [
            f"Analysis - {len(_AXIS_REGISTRY)}축 · {total_calcs}개 분석 함수 | 단일 종목 재무 심층 분석",
            "",
            "━━━ 분석 축 ━━━",
        ]
        # 그룹별로 묶어 표시
        _GROUP_LABELS = {
            "financial": "Part 1~3 - 재무분석",
            "valuation": "Part 4 - 가치평가",
            "governance": "Part 5 - 비재무 심화",
            "forecast": "Part 6 - 전망분석",
            "macro": "Part 6 - 매크로 연결",
        }
        for group, axes in _GROUPS.items():
            lines.append(f"  [{_GROUP_LABELS.get(group, group)}]")
            for key in axes:
                entry = _AXIS_REGISTRY.get(key)
                if entry:
                    lines.append(f"    {key:10s} {entry.description} ({len(entry.calcs)}항목)")
            lines.append("")
        lines.append("━━━ 빠른 시작 ━━━")
        lines.append("  c.analysis()                            # 이 가이드")
        lines.append('  c.analysis("수익구조")                    # 수익구조 분석')
        lines.append('  c.analysis("financial", "수익성")         # 그룹+축 지정')
        lines.append('  c.analysis("종합평가")                    # 재무 스코어카드')
        lines.append('  c.analysis("가치평가")                    # DCF/DDM/RIM/상대가치')
        lines.append("")
        lines.append("━━━ 데이터 ━━━")
        lines.append("  DART 전자공시 기반 재무제표 - API 키 불필요 (자동 다운로드)")
        lines.append("  전체 결과를 보고서로 → c.story()")
        lines.append("")
        lines.append(
            "노트북: https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_quickstart.ipynb"
        )
        return "\n".join(lines)
