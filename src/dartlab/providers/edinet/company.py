"""EDINET 엔진 내부 Company 본체.

DART/EDGAR Company 와 동일한 단일 진입 (``c.show(topic)``) 사상.
``c.BS`` / ``c.finance`` / ``c.timeseries`` 같은 namespace · 단축 property 는
Plan v10 정합성 위해 제공하지 않는다 — 모든 접근은 ``c.show()`` 경유.

사용법::

    from dartlab.providers.edinet import Company

    c = Company("E00001")           # EDINET 코드
    c.corpName                      # "トヨタ自動車株式会社"
    c.panel("riskFactors")          # sections 기반 topic DataFrame
    c.show("riskFactors")           # 사업等のリスク
    c.show("BS")                    # 재무상태표 (XBRL 정규화)
"""

from __future__ import annotations

from typing import Any

import polars as pl

_FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS"})

# topic 단축 alias
_TOPIC_ALIASES: dict[str, str] = {
    "business": "businessDescription",
    "risk": "riskFactors",
    "md&a": "mdAndA",
    "mdna": "mdAndA",
    "governance": "corporateGovernance",
    "employee": "employee",
    "esg": "sustainability",
    "segments": "segments",
    "facilities": "facilities",
    "dividend": "dividendPolicy",
    "officers": "officers",
    "shareholders": "majorShareholders",
    "history": "history",
    "accounting": "accountingPolicies",
}

# 유가증권보고서 chapter/label 매핑
_YUHO_LABELS: dict[str, tuple[str, str]] = {
    "companyOverview": ("企業の概況", "企業の概況"),
    "keyMetrics": ("企業の概況", "主要な経営指標等の推移"),
    "history": ("企業の概況", "沿革"),
    "businessDescription": ("企業の概況", "事業の内容"),
    "subsidiaries": ("企業の概況", "関係会社の状況"),
    "employee": ("企業の概況", "従業員の状況"),
    "managementPolicy": ("事業の状況", "経営方針"),
    "sustainability": ("事業の状況", "サステナビリティ"),
    "riskFactors": ("事業の状況", "事業等のリスク"),
    "mdAndA": ("事業の状況", "経営者による分析"),
    "majorContracts": ("事業の状況", "重要な契約"),
    "researchAndDevelopment": ("事業の状況", "研究開発活動"),
    "capitalExpenditure": ("設備の状況", "設備投資等の概要"),
    "majorFacilities": ("設備の状況", "主要な設備"),
    "facilityPlan": ("設備の状況", "設備の新設・除却計画"),
    "shareInformation": ("提出会社の状況", "株式等の状況"),
    "dividendPolicy": ("提出会社の状況", "配当政策"),
    "corporateGovernance": ("提出会社の状況", "コーポレート・ガバナンス"),
    "officers": ("提出会社の状況", "役員の状況"),
    "majorShareholders": ("提出会社の状況", "大株主の状況"),
    "consolidatedBS": ("経理の状況", "連結貸借対照表"),
    "consolidatedIS": ("経理の状況", "連結損益計算書"),
    "consolidatedCF": ("経理の状況", "連結キャッシュ・フロー計算書"),
    "segments": ("経理の状況", "セグメント情報"),
    "relatedPartyTransaction": ("経理の状況", "関連当事者情報"),
    "accountingPolicies": ("経理の状況", "重要な会計方針"),
    "subsequentEvents": ("経理の状況", "重要な後発事象"),
}

_FINANCE_LABELS: dict[str, tuple[str, str]] = {
    "BS": ("財務諸表", "貸借対照表"),
    "IS": ("財務諸表", "損益計算書"),
    "CF": ("財務諸表", "キャッシュ・フロー計算書"),
    "CIS": ("財務諸表", "包括利益計算書"),
    "ratios": ("財務諸表", "財務比率"),
}


class _DocsNamespace:
    """docs namespace — pure docs source.

    내부 보조 namespace. 외부 사용자는 ``c._docs.X`` 직접 접근 대신
    ``c.show(topic)`` 또는 ``c.panel(topic)`` 사용.
    """

    def __init__(self, company: Company):
        self._company = company
        self._sections: pl.DataFrame | None = None

    @property
    def sections(self) -> pl.DataFrame:
        """docs 수평화 sections DataFrame (lazy).

        Capabilities:
            - lazy load — 첫 호출 시 ``_loadSections`` 실행 + cache.

        Returns:
            pl.DataFrame — sections wide DataFrame.

        Guide:
            - "EDINET docs sections" → ``c.panel``.

        SeeAlso:
            - ``_loadSections`` (모듈 private) — 본 함수 본체.

        Requires:
            - polars.

        AIContext:
            EDINET 작업 패스 영역. AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 빈 DataFrame 반환 — caller 가 empty 분기 의무.
                - sections 접근 빈도 가정 X — 본 함수가 lazy load, 첫 호출만 비용.
            OutputSchema:
                - sections wide DataFrame [topic, period, text, sourceLabel].
            Prerequisites:
                - docs parquet 수집 (구현 후).
            Freshness:
                - docs 수집 시점.
            Dataflow:
                - docs parquet → _loadSections → 본 함수.
            TargetMarkets:
                - JP (EDINET) 한정.

        Raises:
            없음.

        Example:
            >>> sections(...)
        """
        if self._sections is None:
            self._sections = self._loadSections()
        return self._sections

    def _loadSections(self) -> pl.DataFrame:
        """docs parquet → sections 수평화."""
        # 초기 스캐폴딩: 빈 DataFrame 반환
        # 실제 구현은 데이터 수집 후
        return pl.DataFrame(
            schema={
                "topic": pl.Utf8,
                "period": pl.Utf8,
                "text": pl.Utf8,
                "sourceLabel": pl.Utf8,
            }
        )


class Company:
    """EDINET Company — 단일 진입 ``c.show(topic)``.

    Args:
        edinetCode: EDINET 코드 (예: "E00001") 또는 증권코드 (예: "7203").
    """

    def __init__(self, edinetCode: str):
        self.edinetCode = edinetCode
        self.market = "JP"
        self.currency = "JPY"
        self._corpName: str | None = None
        self._securitiesCode: str | None = None

        self.docs = _DocsNamespace(self)
        self._financeTimeseries: dict[str, pl.DataFrame] | None = None

    def __repr__(self) -> str:
        name = self._corpName or self.edinetCode
        return f"Company('{name}', market='JP')"

    # ── P7: Company context manager + 메모리-safe surface (룰 11 + MemorySafeProvider) ──

    def __enter__(self) -> "Company":
        """context manager 진입 — OomTripwire 시작.

        Example:
            with Company("7203") as c:
                c.show("IS")

        Returns:
            self.

        Raises:
            RuntimeError: 같은 Company context에 중첩 진입할 때.
        """
        from dartlab.core.memory import MemoryScope

        scope = getattr(self, "_memoryScope", None)
        if scope is None:
            scope = MemoryScope()
            self._memoryScope = scope
        scope.enter()
        return self

    def __exit__(self, _excType: object, _excVal: object, _excTb: object) -> None:
        """context manager 종료 — OomTripwire 정지 + 캐시 evict.

        Args:
            excType: 예외 type.
            excVal: 예외 인스턴스.
            excTb: traceback.

        Raises:
            BaseExceptionGroup: 본문 예외와 정리 실패가 함께 발생했을 때.
            Exception: tripwire 정지 또는 cache 정리가 실패했을 때.
        """
        from dartlab.core.memory import MemoryScope

        scope = getattr(self, "_memoryScope", None)
        if not isinstance(scope, MemoryScope):
            raise RuntimeError("Company memory scope가 시작되지 않았습니다")
        bodyError = _excVal if isinstance(_excVal, BaseException) else None
        scope.exit(
            cleanup=self.cleanupCache,
            bodyError=bodyError,
        )

    def cleanupCache(self) -> int:
        """캐시 evict + cleanupBetweenCompanies.

        EDINET 은 BoundedCache 사용 안 함 — _financeTimeseries dict 만 비움.

        Returns:
            비운 entry 수 (0 또는 1).

        Example:
            >>> c = Company("7203")
            >>> c.cleanupCache()
            0

        Raises:
            Exception: Python GC가 낸 예외를 그대로 전달한다.

        Capabilities:
            - ``self._financeTimeseries`` 참조 해제와 Python 순환 참조 회수. dart/edgar와
              같은 명시적 회사 수명주기 경계.

        Guide:
            - "다음 회사 진입 전 메모리 회수" → 본 함수 또는 ``with Company(c):``.

        AIContext:
            JP 다종목 batch 안 본 함수 의무 호출. 다음 회사 전 DataFrame 참조 수명을 끝낸다.

        LLM Specifications:
            AntiPatterns:
                - 호출 없이 다종목 순회 → Company가 보유한 DataFrame 참조 누적.
            OutputSchema:
                - int — 비운 entry 수 (0 또는 1).
            Prerequisites:
                - 인스턴스 활성 상태.
            Freshness:
                - 호출 시점.
            Dataflow:
                - self._financeTimeseries → None → cleanupBetweenCompanies(label).
            TargetMarkets:
                - JP (EDINET) — 본 클래스 인스턴스.

        SeeAlso:
            - ``memorySnapshot`` — 호출 전/후 RSS 비교.
            - ``__exit__`` — context manager 자동 호출.

        Requires:
            - polars
        """
        from dartlab.core.memory import cleanupBetweenCompanies

        evicted = 1 if self._financeTimeseries else 0
        self._financeTimeseries = None
        cleanupBetweenCompanies(label=f"{self.edinetCode}_exit")
        return evicted

    def memorySnapshot(self) -> dict[str, int]:
        """현 메모리 snapshot.

        Returns:
            keys: "cacheSize" (0 또는 1), "rssMb".

        Example:
            >>> c = Company("7203")
            >>> c.memorySnapshot()
            {'cacheSize': 0, 'rssMb': 250}

        Raises:
            없음.

        Capabilities:
            - ``_financeTimeseries`` 캐시 size + 현 프로세스 RSS dict 합산. MemorySafeProvider entry.

        Guide:
            - "이 회사 메모리 얼마" → 본 함수.

        AIContext:
            OOM tripwire 시 회사별 메모리 분포 확인 + AI cleanup 결정.

        LLM Specifications:
            AntiPatterns:
                - RSS 절대값 환경 간 비교 X.
            OutputSchema:
                - dict {"cacheSize": int, "rssMb": int}.
            Prerequisites:
                - Windows psapi 또는 Linux procfs.
            Freshness:
                - 호출 시점.
            Dataflow:
                - OS RSS 관측 + _financeTimeseries 상태 → 본 함수.
            TargetMarkets:
                - JP (EDINET).

        SeeAlso:
            - ``cleanupCache`` — 본 함수 보여준 RSS 회수.

        Requires:
            - polars
        """
        from dartlab.core.memory import getMemoryMb

        cacheSize = 1 if self._financeTimeseries else 0
        return {"cacheSize": cacheSize, "rssMb": int(getMemoryMb())}

    @property
    def corpName(self) -> str | None:
        """회사명 (한자 정식명).

        Returns:
            str | None — ``_corpName`` 그대로. 미수집 시 None.

        LLM Specifications:
            AntiPatterns:
                - 미수집 상태 (None) 를 빈 문자열로 변환 X — None 분기 명시.
            OutputSchema:
                - 1 str 또는 None.
            Prerequisites:
                - EDINET 메타 1 회 이상 수집.
            Freshness:
                - 메타 수집 시점.
            Dataflow:
                - EDINET API → _corpName → 본 함수.
            TargetMarkets:
                - JP (EDINET) 한정.

        Raises:
            없음.

        Example:
            >>> corpName(...)
        """
        return self._corpName

    @property
    def securitiesCode(self) -> str | None:
        """4 자리 증권코드 (東証 코드).

        Returns:
            str | None — 4 자리 증권코드 또는 None.

        LLM Specifications:
            AntiPatterns:
                - EDINET 코드 ("E00001") 와 증권코드 ("7203") 혼동 X — 본 함수는 후자만.
            OutputSchema:
                - 1 str (4 자리) 또는 None.
            Prerequisites:
                - EDINET 메타 수집.
            Freshness:
                - 메타 수집 시점.
            Dataflow:
                - EDINET API → _securitiesCode → 본 함수.
            TargetMarkets:
                - JP (EDINET) 한정.

        Raises:
            없음.

        Example:
            >>> securitiesCode(...)
        """
        return self._securitiesCode

    # ── 공개 인터페이스 ──

    def _loadFinanceTimeseries(self) -> dict[str, pl.DataFrame]:
        """재무제표 시계열 (XBRL 정규화) lazy 로드.

        초기 스캐폴딩: 빈 dict. 데이터 수집 완료 후 ``BS/IS/CF/CIS`` key 의
        ``pl.DataFrame`` 으로 채움. 외부 사용자는 ``c.show("BS")`` 로 접근.
        """
        if self._financeTimeseries is None:
            self._financeTimeseries = {}
        return self._financeTimeseries

    @property
    def panel(self):
        """EDINET panel facade — 현 단계 ``show`` 호환 callable.

        공개 sections facade 는 폐기됐고, 사용자는 ``c.panel(topic)`` 으로
        진입한다. EDINET 본 수집/패널 artifact 는 후속 단계라 현재는 ``show`` 경로를
        같은 호출계약으로 감싼다.

        Args:
            없음 — 반환된 callable 에 topic 을 전달한다.

        Returns:
            CallableAccessor — ``c.panel(topic)`` 호출 표면.

        Raises:
            없음.

        Example:
            >>> c = Company("7203")
            >>> panel = c.panel
            >>> callable(panel)
            True
        """
        from dartlab.core.dualAccess import CallableAccessor

        return CallableAccessor(self._panelImpl, name="panel")

    def _panelImpl(self, topic: str | None = None, **_kw: Any) -> pl.DataFrame | None:
        """panel callable 본체 — topic 없으면 내부 docs wide, topic 있으면 show alias."""
        if topic is None:
            return self.docs.sections
        return self.show(topic)

    def show(self, topic: str) -> pl.DataFrame | None:
        """topic별 데이터 표시.

        Args:
            topic: topicId 또는 alias (예: "BS", "riskFactors", "risk").

        Returns:
            DataFrame 또는 None.

        Capabilities:
            - finance topic (BS/IS/CF/CIS) → _loadFinanceTimeseries dispatch. 그 외 docs sections filter.
              현 단계 빈 (EDINET API 미연결).

        Guide:
            - "BS / 리스크 / 사업내용" → ``c.show(topic)``.

        AIContext:
            CompanyProtocol 충족 stub — AI 가 호출 시 None / 빈 결과. EDINET API 부재 명시 의무.

        LLM Specifications:
            AntiPatterns:
                - 결과 None 을 "topic 없음" 단정 X — EDINET API 미연결 상태일 수 있음.
                - alias 추측 X — ``_TOPIC_ALIASES`` 명시 매핑.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - sections / financeTimeseries 수집 (구현 후).
            Freshness:
                - sections / finance 수집 시점.
            Dataflow:
                - topic → alias resolve → finance/docs 분기 → 본 함수.
            TargetMarkets:
                - JP (EDINET).

        SeeAlso:
            - ``select`` / ``trace`` — show 결과의 필터/origin.

        Requires:
            - polars

        Raises:
            없음.
        """
        resolved = _TOPIC_ALIASES.get(topic, topic)

        # finance topic — XBRL 시계열 dispatch
        if resolved in _FINANCE_TOPICS:
            return self._loadFinanceTimeseries().get(resolved)

        # docs topic
        secs = self.docs.sections
        if secs.is_empty():
            return None
        filtered = secs.filter(pl.col("topic") == resolved)
        return filtered if not filtered.is_empty() else None

    @property
    def index(self) -> pl.DataFrame:
        """수평화 보드 — 전체 topic 요약 (chapter/label/topic/periods).

        Capabilities:
            - sections 의 unique topic list 추출.
            - 각 topic → (chapter, label) 매핑 (``_YUHO_LABELS`` + ``_FINANCE_LABELS``).
            - period unique count = 시계열 길이.

        Returns:
            pl.DataFrame — 컬럼 chapter/label/topic/periods. sections empty 시 빈 schema.

        Guide:
            - "EDINET 회사 index 매트릭스" → ``c.index``.

        SeeAlso:
            - ``sections`` — 본 함수의 input source.
            - ``_YUHO_LABELS`` / ``_FINANCE_LABELS`` — chapter/label 매핑.

        Requires:
            - polars.

        AIContext:
            EDINET 작업 패스 영역. AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - sections empty 시 빈 schema 반환 — caller height==0 분기 의무.
            OutputSchema:
                - chapter/label/topic/periods.
            Prerequisites:
                - sections 수집.
            Freshness:
                - sections 시점.
            Dataflow:
                - sections → 본 함수 → AI.
            TargetMarkets:
                - JP (EDINET) 한정.

        Raises:
            없음.

        Example:
            >>> index(...)
        """
        secs = self.docs.sections
        if secs.is_empty():
            return pl.DataFrame(
                schema={
                    "chapter": pl.Utf8,
                    "label": pl.Utf8,
                    "topic": pl.Utf8,
                    "periods": pl.UInt32,
                }
            )

        topics = secs.select("topic").unique().to_series().to_list()
        rows: list[dict[str, Any]] = []

        for topic in sorted(topics):
            labels = {**_YUHO_LABELS, **_FINANCE_LABELS}
            chapter, label = labels.get(topic, ("기타", topic))
            count = secs.filter(pl.col("topic") == topic).select("period").n_unique()
            rows.append(
                {
                    "chapter": chapter,
                    "label": label,
                    "topic": topic,
                    "periods": count,
                }
            )

        return pl.DataFrame(rows)

    def trace(self, topic: str) -> dict[str, Any]:
        """source provenance 추적 — finance / docs source 구분 + market 메타.

        Capabilities:
            - ``_TOPIC_ALIASES`` 매핑 후 source 분기.
            - finance topic (BS/IS/CF/CIS) → source="finance".
            - 그 외 → source="docs".

        Args:
            topic: topicId 또는 alias.

        Returns:
            dict — topic / source / market / edinetCode 메타.

        Guide:
            - "EDINET 회사 topic trace" → ``c.trace("BS")``.

        SeeAlso:
            - ``show`` — 본 함수의 짝 (실제 데이터 반환).
            - ``_TOPIC_ALIASES`` (모듈 상수) — alias 매핑.

        Requires:
            - 외부 의존 없음.

        AIContext:
            EDINET 작업 패스 영역. AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - resolved topic 이 alias 통과 후 ID 라 가정 — 실 origin (docs/finance) 분기는 source 필드.
            OutputSchema:
                - dict — 4 키.
            Prerequisites:
                - EDINET Company instance.
            Freshness:
                - 본 함수 호출 시점 (정적).
            Dataflow:
                - alias map → 본 함수 → AI 디버그.
            TargetMarkets:
                - JP (EDINET) 한정.

        Raises:
            없음.

        Example:
            >>> trace(...)
        """
        resolved = _TOPIC_ALIASES.get(topic, topic)
        return {
            "topic": resolved,
            "source": "finance" if resolved in _FINANCE_TOPICS else "docs",
            "market": self.market,
            "edinetCode": self.edinetCode,
        }

    def select(
        self,
        topic: str,
        indList: str | list[str] | None = None,
        colList: str | list[str] | None = None,
    ) -> pl.DataFrame | None:
        """topic 데이터에서 행/열 선택 (P8 — CompanyProtocol 충족).

        EDINET 은 select 본 구현 미흡 — show 결과에 indList/colList 만큼 필터링.
        Phase 후속에서 dart/edgar 와 동등한 cascade 매칭 구현 예정.

        Args:
            topic: BS/IS/CF/CIS/ratios 등.
            indList: 행 (계정명) 필터.
            colList: 열 (기간) 필터.

        Returns:
            필터된 DataFrame 또는 None.

        Raises:
            없음 (show 가 None 반환 시 None 그대로).

        Example:
            >>> c = Company("7203")
            >>> c.select("IS", indList="매출액")

        Capabilities:
            - show() 결과에 indList/colList 단순 필터 (account 컬럼 + 컬럼명 in cols). EDINET 본 구현 미완 —
              dart/edgar cascade 매칭 후속 phase.

        Guide:
            - "EDINET 회사 행/열 필터" → 본 함수 (현재 단순).

        AIContext:
            CompanyProtocol 충족 stub. 본 구현 미완 — 결과 불완전 가능.

        LLM Specifications:
            AntiPatterns:
                - show() None → None 그대로 (caller None 분기 의무).
                - cascade 매칭 가정 X — 현재 단순 in_ 필터.
            OutputSchema:
                - pl.DataFrame (필터된) 또는 None.
            Prerequisites:
                - show(topic) 결과.
            Freshness:
                - show 와 동일.
            Dataflow:
                - show(topic) → indList/colList filter → 본 함수.
            TargetMarkets:
                - JP (EDINET).

        SeeAlso:
            - ``show`` — 본 함수의 입력 source.

        Requires:
            - polars
        """
        df = self.show(topic)
        if df is None:
            return None
        if indList is not None:
            inds = [indList] if isinstance(indList, str) else list(indList)
            if "account" in df.columns:
                df = df.filter(pl.col("account").is_in(inds))
        if colList is not None:
            cols = [colList] if isinstance(colList, str) else list(colList)
            keep = [c for c in df.columns if c in cols or c == "account"]
            if keep:
                df = df.select(keep)
        return df

    @property
    def topics(self) -> pl.DataFrame:
        """사용 가능한 topic 목록 (CompanyProtocol 충족).

        Returns:
            ``topic`` 컬럼만 가진 DataFrame.

        Example:
            >>> c = Company("7203")
            >>> c.topics.head()

        Raises:
            없음.

        Capabilities:
            - sections 의 unique topic 정렬 list 반환. 현 단계 빈 DataFrame (sections empty).

        Guide:
            - "어떤 topic 있나" → 본 property.

        AIContext:
            CompanyProtocol 충족 stub — AI 가 topic 라우팅 결정 시 본 함수 카탈로그.

        LLM Specifications:
            AntiPatterns:
                - 결과 empty 를 "data 없음" 단정 X — EDINET API 미연결 상태일 수 있음.
            OutputSchema:
                - pl.DataFrame [topic] (1 column).
            Prerequisites:
                - sections 수집 (구현 후).
            Freshness:
                - sections 수집 시점.
            Dataflow:
                - sections → unique → sort → 본 property.
            TargetMarkets:
                - JP (EDINET).

        SeeAlso:
            - ``sections`` / ``index`` — 더 상세한 메타.

        Requires:
            - polars
        """
        secs = self.docs.sections
        if secs.is_empty():
            return pl.DataFrame(schema={"topic": pl.Utf8})
        return secs.select("topic").unique().sort("topic")

    # ── filings ──

    def filings(self) -> pl.DataFrame | None:
        """공시 목록 (초기 스캐폴딩: 빈 DataFrame, CompanyProtocol 충족).

        Returns:
            빈 DataFrame (EDINET filings 본 구현 후속 phase).

        Example:
            >>> c = Company("7203")
            >>> c.filings()

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return pl.DataFrame(
            schema={
                "docId": pl.Utf8,
                "filerName": pl.Utf8,
                "submittedAt": pl.Utf8,
                "docTypeCode": pl.Utf8,
            }
        )

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간 간 텍스트 변화 감지 (CompanyProtocol 충족 stub).

        EDINET 본 구현 미완 — 현재 None 반환. 후속 phase 에서 docs sections 의
        period 차이 diff 빌더 추가 예정.

        Args:
            topic: 비교 대상 topic.
            fromPeriod: 시작 period.
            toPeriod: 종료 period.

        Returns:
            현재 None.

        Example:
            >>> c.diff("riskFactors", fromPeriod="2023", toPeriod="2024")

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return None

    def disclosure(
        self,
        start: str | None = None,
        end: str | None = None,
        *,
        days: int = 365,
        type: str | None = None,
        keyword: str | None = None,
        finalOnly: bool = False,
    ) -> pl.DataFrame:
        """실시간 공시 검색 (CompanyProtocol 충족 stub).

        EDINET 본 구현 미완 — 현재 빈 DataFrame. 후속 phase 에서
        ``edinet/openapi/client.listDocuments`` 위임 예정.

        Args:
            start: 시작일 (YYYY-MM-DD).
            end: 종료일.
            days: 기간 (start/end 미지정 시).
            type: 서류 유형 필터.
            keyword: 키워드 필터.
            finalOnly: 최종본만.

        Returns:
            빈 DataFrame (현재).

        Example:
            >>> c.disclosure(days=90)

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return pl.DataFrame(
            schema={
                "docId": pl.Utf8,
                "filerName": pl.Utf8,
                "submittedAt": pl.Utf8,
                "docTypeCode": pl.Utf8,
            }
        )

    def liveFilings(
        self,
        start: str | None = None,
        end: str | None = None,
        *,
        days: int | None = None,
        limit: int = 20,
        keyword: str | None = None,
        forms: list[str] | tuple[str, ...] | None = None,
        finalOnly: bool = False,
    ) -> pl.DataFrame:
        """실시간 공시 목록 — EDINET OpenAPI 위임 (CompanyProtocol 충족 stub).

        EDINET 본 구현 미완 — 현재 빈 DataFrame. 후속 phase 에서 client.listDocuments
        위임 + form/type 매핑 예정.

        Args:
            start: 시작일.
            end: 종료일.
            days: 기간.
            limit: 최대 행 수.
            keyword: 키워드 필터.
            forms: form 유형 리스트.
            finalOnly: 최종본만.

        Returns:
            빈 DataFrame (현재).

        Example:
            >>> c.liveFilings(days=30, limit=10)

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return pl.DataFrame()

    def readFiling(
        self,
        filing: Any,
        *,
        maxChars: int | None = None,
    ) -> dict[str, Any]:
        """공시 원문 읽기 (CompanyProtocol 충족 stub).

        EDINET 본 구현 미완 — 현재 빈 dict. 후속 phase 에서 ``downloadDocument`` +
        XBRL 파싱 위임 예정.

        Args:
            filing: filing dict 또는 docId.
            maxChars: 최대 문자 수.

        Returns:
            빈 dict (현재).

        Example:
            >>> c.readFiling({"docId": "S100T1HW"})

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return {}

    def view(self, *, port: int = 8400) -> None:
        """브라우저 뷰어 실행 (CompanyProtocol 충족 stub).

        EDINET 본 구현 미완 — 현재 no-op. 후속 phase 에서 dart/edgar 와 동등한
        local launchViewer 위임 예정.

        Args:
            port: 로컬 서버 포트.

        Returns:
            None.

        Example:
            >>> c.view()

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return None

    def quant(
        self,
        metric: str | None = None,
        **kwargs: Any,
    ) -> dict | pl.DataFrame | None:
        """기술적 분석 (CompanyProtocol 충족 stub).

        EDINET 본 구현 미완 — 현재 None. 후속 phase 에서 일본 시장 OHLCV
        (yahoo finance JP) 위임 예정.

        Args:
            metric: 지표 이름 (None 이면 종합).
            **kwargs: 추가 옵션.

        Returns:
            현재 None.

        Example:
            >>> c.quant("rsi")

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return None

    def ask(
        self,
        question: str,
        *,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | Any:
        """LLM 에게 기업 분석 질문 (CompanyProtocol 충족 stub).

        EDINET 본 구현 미완 — 현재 안내 메시지 반환. 후속 phase 에서 dartlab.ai.kernel
        위임 + JP-EDINET 컨텍스트 패키지 추가 예정.

        Args:
            question: 자연어 질문.
            include: 컨텍스트 포함 키.
            exclude: 제외 키.
            provider: LLM provider.
            model: 모델명.
            stream: 스트리밍 여부.
            **kwargs: provider 별 옵션.

        Returns:
            안내 메시지 (현재).

        Example:
            >>> c.ask("최근 리스크는?")

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 현 단계 stub — 빈 결과를 "데이터 없음" 단정 X. EDINET API 미연결 상태.
                - dart/edgar 동등 결과 가정 X — 후속 phase 까지 placeholder.
            OutputSchema:
                - dart/edgar 동등 컬럼 (현재 빈 schema 또는 빈 dict).
            Prerequisites:
                - EDINET API 연결 (후속 phase).
            Freshness:
                - 후속 phase 에서 EDINET API 갱신 시점.
            Dataflow:
                - 현재 빈 → 후속 EDINET API → 본 함수.
            TargetMarkets:
                - JP (EDINET) — 본 phase 미구현 stub.
        """
        return (
            "EDINET Company.ask 본 구현 미완 — 후속 phase 에서 dartlab.ai.kernel 위임 + "
            "JP-EDINET 컨텍스트 패키지 추가 예정. dart/edgar Company.ask 와 동등 surface."
        )
