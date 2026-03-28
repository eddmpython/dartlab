"""EDINET 엔진 내부 Company 본체.

DART/EDGAR Company와 동일한 구조를 제공한다.

- docs: sections 수평화 (topic × period), filings
- finance: BS/IS/CF/timeseries/ratios
- 공개 인터페이스: index / show / trace

사용법::

    from dartlab.providers.edinet import Company

    c = Company("E00001")           # EDINET 코드
    c.corpName                      # "トヨタ自動車株式会社"
    c.sections                      # sections 수평화 DataFrame
    c.show("riskFactors")           # 사업等のリスク
    c.show("BS")                    # 재무상태표
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
    """docs namespace — pure docs source."""

    def __init__(self, company: Company):
        self._company = company
        self._sections: pl.DataFrame | None = None

    @property
    def sections(self) -> pl.DataFrame:
        """docs 수평화 sections DataFrame."""
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


class _FinanceNamespace:
    """finance namespace — XBRL 재무 정규화."""

    def __init__(self, company: Company):
        self._company = company
        self._timeseries: dict[str, pl.DataFrame] | None = None

    def _loadTimeseries(self) -> dict[str, pl.DataFrame]:
        # 초기 스캐폴딩: 빈 dict 반환
        return {}

    @property
    def timeseries(self) -> dict[str, pl.DataFrame]:
        """재무제표별 시계열 dict."""
        if self._timeseries is None:
            self._timeseries = self._loadTimeseries()
        return self._timeseries

    @property
    def BS(self) -> pl.DataFrame | None:
        """재무상태표."""
        return self.timeseries.get("BS")

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서."""
        return self.timeseries.get("IS")

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표."""
        return self.timeseries.get("CF")


class Company:
    """EDINET Company — docs/finance/profile namespace.

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
        self.finance = _FinanceNamespace(self)

    def __repr__(self) -> str:
        name = self._corpName or self.edinetCode
        return f"Company('{name}', market='JP')"

    @property
    def corpName(self) -> str | None:
        """회사명."""
        return self._corpName

    @property
    def securitiesCode(self) -> str | None:
        """4자리 증권코드 (東証 코드)."""
        return self._securitiesCode

    # ── sections (merged view) ──

    @property
    def sections(self) -> pl.DataFrame:
        """profile.sections — docs.sections 기반 merged view."""
        return self.docs.sections

    # ── 공개 인터페이스 ──

    def show(self, topic: str) -> pl.DataFrame | None:
        """topic별 데이터 표시.

        Args:
            topic: topicId 또는 alias (예: "BS", "riskFactors", "risk").

        Returns:
            DataFrame 또는 None.
        """
        resolved = _TOPIC_ALIASES.get(topic, topic)

        # finance topic
        if resolved in _FINANCE_TOPICS:
            return getattr(self.finance, resolved, None)

        # docs topic
        secs = self.sections
        if secs.is_empty():
            return None
        filtered = secs.filter(pl.col("topic") == resolved)
        return filtered if not filtered.is_empty() else None

    @property
    def index(self) -> pl.DataFrame:
        """수평화 보드 — 전체 topic 요약."""
        secs = self.sections
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
        """source provenance 추적."""
        resolved = _TOPIC_ALIASES.get(topic, topic)
        return {
            "topic": resolved,
            "source": "finance" if resolved in _FINANCE_TOPICS else "docs",
            "market": self.market,
            "edinetCode": self.edinetCode,
        }

    # ── filings ──

    def filings(self) -> list[dict[str, Any]]:
        """공시 목록 (초기 스캐폴딩: 빈 리스트)."""
        return []

    # ── finance 바로가기 ──

    @property
    def BS(self) -> pl.DataFrame | None:
        """재무상태표."""
        return self.finance.BS

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서."""
        return self.finance.IS

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표."""
        return self.finance.CF
