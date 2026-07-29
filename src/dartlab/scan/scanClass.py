"""Scan 클래스 + 그룹 accessor — router 위에 얹힌 사용자 facade (P-S9).

router.py 는 registry / aliases / resolver 만, scanClass.py 는 사용자가 직접
호출하는 ``Scan`` 와 ``Scan.financial`` 같은 그룹 accessor 를 담는다.

dartlab.__init__.py 가 lazy 로 ``Scan()`` 을 생성해 ``dartlab.scan`` 에 노출.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.scan.rename import _enrichWithKorean
from dartlab.scan.router import (
    _AXIS_REGISTRY,
    _SCAN_GROUPS,
    _AxisEntry,
    _edgarDispatch,
    _resolveAxis,
    _resolveGroup,
)


class Scan:
    """시장 전체 횡단분석 -- 22축, 전부 Polars DataFrame.

    Capabilities:
        - governance: 최대주주 지분, 사외이사, 보수비율, 감사의견, 소액주주 분산 + 등급
        - workforce: 임직원 수, 평균급여, 인건비율, 1인당부가가치, 성장률
        - capital: 배당, 자사주(취득/처분/소각), 증자/감자, 환원 분류
        - debt: 사채만기, 부채비율, ICR, 위험등급
        - account: 전종목 단일 계정 시계열 (매출액, 영업이익 등)
        - ratio: 전종목 단일 재무비율 시계열 (ROE, 부채비율 등)
        - network: 상장사 관계 네트워크 (출자/지분/계열)
        - cashflow: OCF/ICF/FCF + 현금흐름 패턴 분류 (8종)
        - audit: 감사의견, 감사인변경, 특기사항, 감사독립성
        - insider: 최대주주 지분변동, 자기주식, 경영권 안정성
        - quality: Accrual Ratio + CF/NI -- 이익의 현금 뒷받침
        - liquidity: 유동비율 + 당좌비율 -- 단기 지급능력
        - growth: 매출/영업이익/순이익 CAGR + 성장 패턴 분류
        - profitability: 영업이익률/순이익률/ROE/ROA + 등급
        - efficiency: 자산/재고/매출채권 회전율 + CCC + 등급
        - valuation: PER/PBR/PSR + 시가총액 + 등급 (네이버 실시간)
        - dividendTrend: DPS 시계열 + 패턴 (연속증가/안정/감소/시작/중단)
        - macroBeta: 전종목 GDP/금리/환율 베타 횡단면 (OLS)
        - fields: 조건형 스크리닝 필드 카탈로그
        - screen: 멀티팩터 프리셋 + spec 조건형 스크리닝
        - disclosureRisk: 공시 변화 기반 선행 리스크 (우발부채/감사변경/계열/사업전환)
        - orders: 신규수주 flow (book-to-bill/모멘텀/계약상대 집중도) -- 단일판매·공급계약 선행지표

    Requires:
        데이터: 축별로 다름 (prebuild 또는 collect 데이터)
        - governance/workforce/capital/debt/audit/insider: report
        - account/ratio: finance
        - network: panel; disclosureRisk: changes; orders: allFilings(런타임 직독)

    AIContext:
        시장 전체 비교/순위 질문에 사용. 개별 종목 분석은 Company 메서드 사용.

    Guide:
        - "다른 회사랑 비교 가능해?" -> scan("account") 또는 scan("ratio") 안내
        - "거버넌스 좋은 회사?" -> scan("governance")로 등급 A 필터
        - "배당 많이 주는 회사?" -> scan("capital")로 배당수익률 정렬
        - "ROE 높은 회사?" -> scan("ratio", "roe")로 전종목 비교
        - "조건으로 종목 찾아줘" -> scan("fields")로 필드 확인 후 scan("screen", spec=...)
        - "삼성전자랑 SK하이닉스 비교" -> scan("account", "sales", code="005930,000660")
        - API 키 불필요. 사전 다운로드 데이터만으로 동작.

    SeeAlso:
        - analysis: 개별 종목 14축 전략분석
        - Company.insights: 단일 종목 7영역 종합 분석
        - gather: 주가/수급 데이터 (모멘텀 보완)

    Args:
        axis: 축 이름. None이면 22축 가이드 반환.
        target: 축별 대상 (종목코드, 항목, 비율명 등).
        **kwargs: 축별 옵션 (freq, fsPref, market 등).

    Returns
    -------
    pl.DataFrame
        전종목 횡단 데이터. axis=None이면 가이드 DataFrame.
        공통 컬럼: 종목코드 (str), 종목명 (str) + 축별 지표 컬럼.

    Example::

        import dartlab
        dartlab.scan()                           # 가이드
        dartlab.scan("governance")               # 전종목 지배구조
        dartlab.scan("account", "매출액")          # 전종목 매출액
        dartlab.scan("ratio", "roe")             # 전종목 ROE
        dartlab.scan("fields", "roe")            # 조건형 스크리닝 필드 검색
        dartlab.scan("screen", spec={"where": [{"field": "finance.ratio.roe", "op": ">", "value": 10}]})
    """

    def __call__(
        self,
        axis: str | None = None,
        target: str | None = None,
        *,
        freq: str = "Q",
        **kwargs: Any,
    ) -> pl.DataFrame | Any:
        """축(axis)별 전종목 횡단분석.

        2-level 호출도 지원한다::

            scan("financial")              # 재무 8축 가이드
            scan("financial", "수익성")     # financial 그룹 내 수익성 축
            scan("profitability")          # 기존 flat 호출도 그대로 동작

        Returns
        -------
        pl.DataFrame
            axis=None (가이드):
                axis : str — 축 이름
                label : str — 한글 레이블
                description : str — 설명
                example : str — 사용 예시
            axis="profitability":
                종목코드 : str — 6자리 종목코드
                종목명 : str — 회사명
                영업이익률 : float — 영업이익률 (%)
                순이익률 : float — 순이익률 (%)
                ROE : float — 자기자본이익률 (%)
                ROA : float — 총자산이익률 (%)
                등급 : str — 수익성 등급
            axis="account" (target="매출액"):
                종목코드 : str — 6자리 종목코드
                종목명 : str — 회사명
                2024, 2023, ... : float — 연도별 값 (원 단위)
            axis="ratio" (target="roe"):
                종목코드 : str — 6자리 종목코드
                종목명 : str — 회사명
                2024, 2023, ... : float — 연도별 비율값 (%, 배)
            axis="fields":
                field : str — screen spec 에 넣는 정규 필드 키
                label : str — 표시명
                source : str — finance/report/docs/krx/krxIndex 등 원천
                kind : str — number/text/boolean/context
                unit : str — 원/%/배/건/일/점/주/텍스트/없음
                operatorSet : str — 허용 연산자 목록
                coverage : str — 로컬 prebuild 기준 커버리지
            기타 축: 종목코드 + 종목명 + 축별 지표 컬럼

        Raises
        ------
        ValueError
            axis 또는 target 이 등록되지 않은 경우.
            그룹 호출 시 target 이 해당 그룹에 속하지 않는 경우.

        Examples
        --------
        >>> dartlab.scan()                              # 전체 축 가이드
        >>> dartlab.scan("profitability")               # 전종목 수익성
        >>> dartlab.scan("account", "매출액")            # 전종목 매출액 시계열
        >>> dartlab.scan("ratio", "roe")                # 전종목 ROE 시계열
        >>> dartlab.scan("fields", "매출")               # 스크리닝 필드 검색
        >>> dartlab.scan("screen", spec={"where": [{"field": "finance.ratio.roe", "op": ">", "value": 10}]})
        >>> dartlab.scan("financial")                   # 재무 8축 가이드
        >>> dartlab.scan("financial", "수익성")          # 재무 그룹 내 수익성

        Notes
        -----
        사전 빌드 parquet 기반. 첫 호출 시 HuggingFace 에서 자동 다운로드.
        전종목 데이터를 한 번에 로드하므로 메모리 ~200MB 소비.

        Guide
        -----
        AI 역할: AI는 scan을 전종목 횡단 비교와 스크리닝 엔진으로 보고 universe, metric, 기간, rank 근거를 만든다.
        데이터 기본기: scan 경로는 universe, metric, period, rank, table 을 먼저
            evidence 로 남긴다. 조건 검색은 scan("fields") 로 가능한 field 를
            확인한 뒤 scan("screen") 으로 구성한다.
        When: 특정 종목 심층 분석 전, 업종·시장 내 상대 위치를 파악할 때.
        How: scan 으로 전체 분포를 보고 → analysis 로 개별 종목 심층 분석.
            story credit/governance/audit 타입에서 scan 데이터를 동종업계 비교로 활용.
            조건형 종목 발굴은 scan("fields") → scan("screen", spec=...) → Company/analysis 순서.
            단일 지표 하나만으로 후보 추천을 끝내지 말고 finance/report/docs/krx 중 최소 3관점 교차 검증.
            단일 종목 결론은 scan 후보/rank 에서 끝내지 말고 Company 원자료와
            analysis/credit 로 후속 검증한다.
        Verified:
            - scan("재무건전성") → 업종 비교 테이블, 해석 약간 부족 (observed weak via ai-ask, 2026-04-25 — 정식 Phase 판정 아님)

        See Also
        --------
        analysis : 개별 종목 재무 심층 분석.
        quant : 가격 기반 정량 신호.
        credit : 개별 종목 신용 분석.

        LLM Specifications:
            AntiPatterns:
                - axis 추측 (가용 axis 는 scan() 무인자 호출 결과 가이드 확인)
                - account/ratio 호출 시 target 누락 (둘 다 target 필수)
                - "growth" 결과 상위 그대로 추천 (매출 규모·기간 필터 없으면 micro-cap 잡음)
            OutputSchema:
                - 모든 axis 공통: 종목코드 (str) + 종목명 (str) + 축별 컬럼
                - account: 연도별 컬럼 (원 단위)
                - ratio: 연도별 컬럼 (% / 배)
                - growth: 매출 CAGR / 영업이익 CAGR / 순이익 CAGR + 등급
                - profitability: 영업이익률 / 순이익률 / ROE / ROA + 등급
                - fields: field / label / source / kind / unit / coverage
            Prerequisites:
                - HuggingFace prebuild parquet 자동 다운로드 (첫 호출 시간 + ~200 MB)
            Freshness:
                prebuild parquet 빌드 시점. 분기 마감 후 30~45 일.
            Dataflow:
                scan(axis) → 후보 → Company(stockCode).analysis(...) 또는 .panel(...)
            TargetMarkets:
                - KR (DART)
        """
        if axis is None:
            return self._guide()

        # ── 2-level: 그룹 호출 ──
        group = _resolveGroup(axis)
        if group is not None:
            if target is None:
                return self._financialGuide() if group == "financial" else self._guide()
            # target을 그룹 내 축으로 resolve
            try:
                resolvedTarget = _resolveAxis(target)
            except ValueError:
                members = ", ".join(_SCAN_GROUPS[group])
                raise ValueError(f"'{target}'은(는) '{group}' 그룹에 속하지 않습니다. 가용 축: {members}")
            if resolvedTarget not in _SCAN_GROUPS[group]:
                members = ", ".join(_SCAN_GROUPS[group])
                raise ValueError(f"'{target}'은(는) '{group}' 그룹에 속하지 않습니다. 가용 축: {members}")
            # 그룹 내 축이면 flat 호출로 위임 (나머지 kwargs 전달)
            return self(resolvedTarget, **kwargs)

        resolved = _resolveAxis(axis)
        entry = _AXIS_REGISTRY[resolved]

        # target 없으면 목록 반환 (targetRequired 축)
        if entry.targetRequired and target is None:
            return self._listForAxis(resolved, entry)

        # target → 파라미터 변환
        callKwargs: dict[str, Any] = dict(kwargs)
        if entry.targetParam and target is not None:
            callKwargs[entry.targetParam] = target
        # freq 는 account/ratio 등 Company 엔진과 기간 단위를 공유하는 축에만 의미
        if resolved in ("account", "ratio"):
            callKwargs["freq"] = freq

        # 현재 공개 scan 축은 과거 시점 고정을 구현하지 않는다. 예전에는 EDGAR의
        # ``**kwargs`` 경로가 asOf를 받아 놓고 현재 자료를 반환해 시점이 맞는 것처럼
        # 보였다. 지원 전까지는 어느 시장에서도 명시적으로 거부한다.
        if callKwargs.get("asOf") is not None:
            raise ValueError(f"scan 축 '{resolved}'은(는) asOf 시점 고정을 지원하지 않습니다.")

        # 시장은 registry 계약에 있는 값만 받는다. 예전에는 알 수 없는 값이나
        # US 미지원 축도 KR 구현으로 조용히 떨어져 다른 시장 결과를 반환했다.
        market = callKwargs.pop("market", None)
        normalizedMarket: str | None = None
        if market is not None:
            if not isinstance(market, str):
                raise ValueError(f"market 은 문자열이어야 합니다: {market!r}")
            marketAliases = {"KR": "KR", "DART": "KR", "US": "US", "EDGAR": "US"}
            normalizedMarket = marketAliases.get(market.strip().upper())
            if normalizedMarket is None:
                raise ValueError(f"지원하지 않는 market: {market!r}. KR 또는 US 만 사용하세요.")
            if normalizedMarket not in entry.universeMarkets:
                supported = ", ".join(entry.universeMarkets) or "없음"
                raise ValueError(
                    f"scan 축 '{resolved}'은(는) market={normalizedMarket}을 지원하지 않습니다. 지원: {supported}"
                )

        # EDGAR market 디스패치 — XBRL 기반 축은 EDGAR 전용 구현으로 분기
        if normalizedMarket == "US":
            result = _edgarDispatch(resolved, callKwargs)
            if result is None:
                raise RuntimeError(f"scan 축 '{resolved}'의 US dispatcher가 등록되지 않았습니다.")
        else:
            # lazy import + 호출
            mod = importlib.import_module(entry.module)
            fn = getattr(mod, entry.fn)
            result = fn(**callKwargs)

        # stockCode 필터 (target이 있고 targetParam이 None인 축)
        if target and entry.targetParam is None and isinstance(result, pl.DataFrame):
            for col in ("종목코드", "stockCode"):
                if col in result.columns:
                    result = result.filter(pl.col(col) == target)
                    break

        # 종목 필터 후 빈 결과면 사유 안내
        if target and isinstance(result, pl.DataFrame) and result.height == 0 and entry.targetParam is None:
            _MISSING_HINTS = {
                "liquidity": "금융업(은행/보험/증권)은 유동자산/유동부채 계정이 없어 유동성 분석 불가",
                "debt": "해당 종목에 사채/부채 데이터 없음",
                "audit": "해당 종목에 감사의견 데이터 없음",
            }
            hint = _MISSING_HINTS.get(resolved, f"'{target}'에 해당 데이터 없음")
            return pl.DataFrame({"info": [hint]})

        # 최종 사용자 반환: 한글 컬럼 + 종목명
        if isinstance(result, pl.DataFrame) and "stockCode" in result.columns:
            result = _enrichWithKorean(result)

        return result

    def docsSections(
        self,
        *,
        sectionTitle: str | None = None,
        year: int | None = None,
        stockCodes: list[str] | None = None,
        onlyWithContent: bool = False,
        limit: int = 100,
        market: str = "KR",
        engine: str | None = None,
    ) -> pl.DataFrame:
        """공시 본문 섹션 메타 cross-company 조회 — 슬림 인덱스 경유 (P3, 룰 8+9).

        ``data/{provider}/scan/docsIndex.parquet`` lazy scan + filter. raw 2918 parquet
        glob 패턴 (STATUS_STACK_BUFFER_OVERRUN 사고 원인) 차단.

        Args:
            sectionTitle: 섹션 제목 부분 일치 필터 (예 "신용평가").
            year: 보고연도 필터.
            stockCodes: 종목코드 list 필터.
            onlyWithContent: True 면 contentLength=0 placeholder (헤더-only) 제외.
            limit: 최대 반환 row 수 (룰 8 강제. 0 = 무제한, 권장 X).
            market: KR (dart) / US (edgar) / JP (edinet). P3.5 에서 multi-market.
            engine: M6 cross-scan 엔진. None (기본) = 환경변수
                ``DARTLAB_CROSS_SCAN_ENGINE`` 또는 ``"polars"`` (streaming).
                ``"duckdb"`` 명시 시 OOC SQL 위임 (대용량 cross-company).

        Returns:
            pl.DataFrame · 11 컬럼 (stockCode/corpName/year/reportType/periodKey/
            sectionOrder/sectionTitle/sectionUrl/contentLength/hasTable/docId).

        Raises:
            FileNotFoundError: docsIndex.parquet 미빌드. ``prebuildData.py --target docsIndex`` 실행 필요.
            ValueError: market 미지원 값.

        Example:
            >>> import dartlab
            >>> df = dartlab.scan.docsSections(sectionTitle="신용평가", year=2024, onlyWithContent=True, limit=50)
            >>> df.select(["stockCode", "corpName", "contentLength"]).head()
            >>> # M6: cross-company × 대용량은 DuckDB OOC 위임
            >>> df = dartlab.scan.docsSections(year=2024, engine="duckdb", limit=10000)

        Capabilities:
            - market 별 (KR/US/JP) docsIndex.parquet lazy scan + 4 필터 (sectionTitle 부분 일치 /
              year / stockCodes / onlyWithContent) + ``pickCrossScanEngine`` 위임. 룰 8 (limit) +
              룰 9 (raw cross-scan 차단) 강제.

        AIContext:
            Agent 가 "X 섹션 가진 회사" cross-company 질문 시 본 메서드 dispatch. 본문이 아닌 메타
            인덱스라 1~2 초 응답 (RSS <100 MB). 본문이 필요하면 :func:`Company.section` 으로 후속.

        Guide:
            - market KR/US/JP 의 docsIndex.parquet 미빌드면 FileNotFoundError — prebuild 단계 점검.
            - limit=0 무제한 — 권장 X (메모리/페이로드 폭증).

        When:
            cross-company 섹션 보유 회사 검색 시. AI agent dispatch 가장 빈번.

        How:
            market → docsIndex.parquet 경로 결정 → lazy scan + 4 필터 → ``pickCrossScanEngine`` 으로
            polars/duckdb 위임 → collect.

        Requires:
            - 로컬 ``data/{provider}/scan/docsIndex.parquet`` (``buildDocsIndex`` 산출)

        SeeAlso:
            - :meth:`iterDocsSections` — 본 메서드의 streaming pair (룰 10)
            - :func:`dartlab.scan.builders.kr.docsIndex.buildDocsIndex` — source 빌더
        """
        from dartlab.core.dataLoader import _dataDir, _getDataRoot
        from dartlab.scan.io.cross import pickCrossScanEngine

        if market not in ("KR", "US", "JP"):
            raise ValueError(f"지원 안 함 market: {market}. KR/US/JP 만.")

        # market 별 인덱스 path (P3 KR, P3.5 US/JP)
        if market == "KR":
            indexPath = Path(_dataDir("scan")) / "docsIndex.parquet"
        elif market == "US":
            indexPath = _getDataRoot() / "edgar" / "scan" / "docsIndex.parquet"
        else:  # JP
            indexPath = _getDataRoot() / "edinet" / "scan" / "docsIndex.parquet"

        if not indexPath.exists():
            raise FileNotFoundError(
                f"docsIndex.parquet 미빌드: {indexPath}. "
                "uv run python -X utf8 .github/scripts/prebuildData.py --target docsIndex 실행 필요."
            )

        lf = pl.scan_parquet(str(indexPath))
        if sectionTitle:
            lf = lf.filter(pl.col("sectionTitle").str.contains(sectionTitle))
        if year is not None:
            lf = lf.filter(pl.col("year") == year)
        if stockCodes:
            lf = lf.filter(pl.col("stockCode").is_in(stockCodes))
        if onlyWithContent:
            lf = lf.filter(pl.col("contentLength") > 0)
        # M6: cross-scan engine dispatcher — polars (streaming) 또는 duckdb (OOC)
        return pickCrossScanEngine(engine=engine).aggregate(  # type: ignore[arg-type]
            lf, limit=limit if limit and limit > 0 else None
        )

    def iterDocsSections(
        self,
        *,
        sectionTitle: str | None = None,
        year: int | None = None,
        stockCodes: list[str] | None = None,
        onlyWithContent: bool = False,
        market: str = "KR",
    ) -> "Iterator[dict[str, Any]]":
        """docsSections 의 streaming iterator (룰 10 — pair).

        Args:
            sectionTitle: 부분 일치 필터.
            year: 보고연도 필터.
            stockCodes: 종목코드 list.
            onlyWithContent: contentLength=0 제외.
            market: KR/US/JP.

        Yields:
            dict — docsIndex 1 row.

        Raises:
            FileNotFoundError: docsIndex.parquet 미빌드.
            ValueError: market 미지원.

        Example:
            >>> for row in dartlab.scan.iterDocsSections(sectionTitle="신용평가", year=2024):
            ...     print(row["stockCode"], row["corpName"])

        Capabilities:
            - :meth:`docsSections` 결과를 메모리에 모두 모으지 않고 row dict 로 한 개씩 yield.
              대량 cross-company 처리에 메모리 안전.

        AIContext:
            Agent 가 streaming 처리 (예: 1000+ row 를 score 후 sort 만 필요) 시 본 메서드 사용.
            limit 인자 없음 — 전체 순회.

        Requires:
            - :meth:`docsSections` 와 동일

        SeeAlso:
            - :meth:`docsSections` — 본 메서드의 DataFrame pair (룰 10)
        """
        df = self.docsSections(
            sectionTitle=sectionTitle,
            year=year,
            stockCodes=stockCodes,
            onlyWithContent=onlyWithContent,
            limit=0,  # iterator 는 limit 없음 (사용자가 break 로 제어)
            market=market,
        )
        yield from df.iter_rows(named=True)

    def _guide(self) -> pl.DataFrame:
        """축 목록 + 사용법 가이드.

        Returns
        -------
        pl.DataFrame
            축별 메타데이터 테이블. 컬럼:

            - axis : str — 정규 축 키 (예: ``"governance"``, ``"profitability"``).
            - label : str — 한글 축 이름 (예: ``"거버넌스"``, ``"수익성"``).
            - group : str — 데이터 그룹 (``"DART"``, ``"DART+EDGAR"``, ``"financial"``).
            - description : str — 축이 수행하는 분석 한 줄 설명.
            - example : str — 호출 예시 코드 문자열.
            - apiKey : str — 필요한 API 키 (scan은 전부 불필요).
        """
        from dartlab.core.utils.axisGuide import buildAxisGuideDataFrame

        financial_axes = set(_SCAN_GROUPS.get("financial", []))

        def _group(key: str, _entry) -> str:
            if key in financial_axes:
                return "financial"
            if "US" in _entry.universeMarkets:
                return "DART+EDGAR"
            return "DART"

        return buildAxisGuideDataFrame(
            _AXIS_REGISTRY,
            groupExtractor=_group,
            columnOrder=["axis", "label", "group", "description", "example", "apiKey"],
        )

    def _financialGuide(self) -> pl.DataFrame:
        """financial 그룹 8축 가이드."""
        rows = []
        for axisKey in _SCAN_GROUPS["financial"]:
            entry = _AXIS_REGISTRY[axisKey]
            rows.append(
                {
                    "axis": axisKey,
                    "label": entry.label,
                    "description": entry.description,
                    "example": f'scan("financial", "{axisKey}")',
                }
            )
        return pl.DataFrame(rows)

    def _listForAxis(self, axis: str, entry: _AxisEntry) -> pl.DataFrame | list:
        """target 필수 축의 가용 목록 반환."""
        if entry.listModule and entry.listFn:
            mod = importlib.import_module(entry.listModule)
            fn = getattr(mod, entry.listFn)
            result = fn()
            if isinstance(result, list) and result and isinstance(result[0], dict):
                return pl.DataFrame(result)
            return result
        return pl.DataFrame({"info": [f"scan('{axis}', '<target>') 형태로 사용하세요."]})

    def __getattr__(self, name):
        """accessor 패턴: scan.governance(), scan.financial.profitability() 등."""
        # 그룹 이름 확인 (financial 등)
        group = _resolveGroup(name)
        if group is not None:
            return _ScanGroupAccessor(self, group)

        # 직접 축 이름 확인 (governance, workforce 등)
        try:
            resolved = _resolveAxis(name)
        except ValueError:
            raise AttributeError(f"Scan에 '{name}' 속성이 없습니다")

        def _boundAxis(target=None, **kwargs):
            return self(resolved, target, **kwargs)

        _boundAxis.__name__ = name
        _boundAxis.__doc__ = f'scan("{resolved}")'
        return _boundAxis

    def __repr__(self) -> str:
        n = len(_AXIS_REGISTRY)
        lines = [f"Scan — {n}축 시장 횡단분석"]
        lines.append("")

        for key, entry in _AXIS_REGISTRY.items():
            lines.append(f"  {key:20s} {entry.label} — {entry.description}")

        lines.append("")
        lines.append("━━━ 빠른 시작 ━━━")
        lines.append("  dartlab.scan()                              # 이 가이드")
        lines.append('  dartlab.scan("governance")                  # 지배구조 전종목')
        lines.append('  dartlab.scan("financial", "profitability")  # 수익성 (financial 그룹)')
        lines.append('  dartlab.scan("screen", "value")             # 멀티팩터 스크리닝')
        lines.append('  c.scan("governance")                        # Company-bound')
        lines.append("")
        lines.append("━━━ 데이터 ━━━")
        lines.append("  DART : 프리빌드 parquet (자동 다운로드, API 키 불필요)")
        lines.append("  EDGAR: XBRL 기반 (자동 다운로드, API 키 불필요)")
        lines.append("")
        lines.append("노트북: https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/03_scan.py")
        return "\n".join(lines)


class _ScanGroupAccessor:
    """scan.financial 등 그룹 accessor."""

    def __init__(self, scanInstance: Scan, group: str):
        self._scan = scanInstance
        self._group = group

    def __call__(self, target=None, **kwargs):
        """그룹 가이드 또는 그룹 내 축 실행."""
        return self._scan(self._group, target, **kwargs)

    def __getattr__(self, name):
        """scan.financial.profitability() 패턴."""
        try:
            resolved = _resolveAxis(name)
        except ValueError:
            raise AttributeError(f"'{self._group}' 그룹에 '{name}' 축이 없습니다")

        members = _SCAN_GROUPS.get(self._group, [])
        if resolved not in members:
            raise AttributeError(f"'{name}' 축은 '{self._group}' 그룹에 속하지 않습니다")

        def _boundAxis(target=None, **kwargs):
            return self._scan(resolved, target, **kwargs)

        _boundAxis.__name__ = name
        _boundAxis.__doc__ = f'scan("{resolved}")'
        return _boundAxis

    def __repr__(self) -> str:
        members = _SCAN_GROUPS.get(self._group, [])
        lines = [f"Scan.{self._group} -- {len(members)}축"]
        for key in members:
            entry = _AXIS_REGISTRY.get(key)
            if entry:
                lines.append(f"  {key:12s} {entry.label} -- {entry.description}")
        return "\n".join(lines)
