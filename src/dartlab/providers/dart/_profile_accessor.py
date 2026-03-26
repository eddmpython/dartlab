"""docs spine + finance/report authoritative merge accessor.

company.py에서 분리된 accessor 클래스.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.providers.dart._utils import _isPeriodColumn

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company


class _ProfileAccessor:
    """docs spine + finance/report authoritative merge."""

    _CANONICAL_TOPIC_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

    _PREFERRED_TOPIC_ORDER = [
        "BS",
        "IS",
        "CIS",
        "CF",
        "SCE",
        "ratios",
        "dividend",
        "employee",
        "majorHolder",
        "executive",
        "audit",
        "capitalChange",
        "treasuryStock",
        "stockTotal",
        "investedCompany",
        "majorHolderChange",
        "minorityHolder",
        "outsideDirector",
        "publicOfferingUsage",
        "privateOfferingUsage",
        "corporateBond",
        "shortTermBond",
        "auditContract",
        "nonAuditContract",
    ]

    _REPORT_AUTHORITATIVE_TOPICS = {
        "dividend",
        "employee",
        "majorHolder",
        "executive",
        "audit",
        "capitalChange",
        "treasuryStock",
        "stockTotal",
        "investedCompany",
        "majorHolderChange",
        "minorityHolder",
        "outsideDirector",
        "publicOfferingUsage",
        "privateOfferingUsage",
        "corporateBond",
        "shortTermBond",
        "auditContract",
        "nonAuditContract",
        "executivePayAllTotal",
        "executivePayIndividual",
        "unregisteredExecutivePay",
        "topPay",
        "debtSecurities",
        "commercialPaper",
        "hybridSecurities",
        "contingentCapital",
        "executivePayTotal",
        "executivePayByType",
    }

    def __init__(self, company: "Company"):
        self._company = company

    @classmethod
    def _isProfileTopic(cls, topic: Any) -> bool:
        if not isinstance(topic, str) or not topic:
            return False
        return bool(cls._CANONICAL_TOPIC_RE.fullmatch(topic))

    @property
    def facts(self) -> pl.DataFrame | None:
        cacheKey = "_profileFacts"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        frames: list[pl.DataFrame] = []

        annual = self._company.finance.annual
        if annual is not None:
            series, years = annual
            for sj in ("BS", "IS", "CF"):
                stmt = series.get(sj, {})
                if not stmt:
                    continue
                rows = []
                for item, values in stmt.items():
                    for idx, year in enumerate(years):
                        value = values[idx] if idx < len(values) else None
                        if value is None:
                            continue
                        rows.append(
                            {
                                "topic": sj,
                                "period": str(year),
                                "source": "finance",
                                "valueType": "number",
                                "valueKey": item,
                                "value": value,
                                "payloadRef": f"finance:{sj}:{item}",
                                "priority": 300,
                                "summary": f"{item}={value}",
                            }
                        )
                if rows:
                    frames.append(pl.DataFrame(rows))

        cisAnnual = self._company._financeCisAnnual()
        if cisAnnual is not None:
            cisSeries, years = cisAnnual
            rows = []
            for item, values in cisSeries.get("CIS", {}).items():
                for idx, year in enumerate(years):
                    value = values[idx] if idx < len(values) else None
                    if value is None:
                        continue
                    rows.append(
                        {
                            "topic": "CIS",
                            "period": str(year),
                            "source": "finance",
                            "valueType": "number",
                            "valueKey": item,
                            "value": value,
                            "payloadRef": f"finance:CIS:{item}",
                            "priority": 300,
                            "summary": f"{item}={value}",
                        }
                    )
            if rows:
                frames.append(pl.DataFrame(rows))

        sce = self._company._sceSeriesAnnual()
        if sce is not None:
            sceSeries, years = sce
            for item, values in sceSeries.get("SCE", {}).items():
                rows = []
                for idx, year in enumerate(years):
                    value = values[idx] if idx < len(values) else None
                    if value is None:
                        continue
                    rows.append(
                        {
                            "topic": "SCE",
                            "period": str(year),
                            "source": "finance",
                            "valueType": "number",
                            "valueKey": item,
                            "value": value,
                            "payloadRef": f"finance:SCE:{item}",
                            "priority": 300,
                            "summary": f"{item}={value}",
                        }
                    )
                if rows:
                    frames.append(pl.DataFrame(rows))

        if self._company.report is not None:
            for apiType in self._company.report.apiTypes:
                df = self._company.report.extractAnnual(apiType)
                if df is None or df.is_empty():
                    continue
                rows = []
                for row in df.iter_rows(named=True):
                    year = row.get("year")
                    quarter = row.get("quarter")
                    summaryParts = []
                    for key, value in row.items():
                        if key in {"stockCode", "year", "quarter", "quarterNum", "apiType", "stlm_dt"}:
                            continue
                        if value is None:
                            continue
                        summaryParts.append(f"{key}={value}")
                        rows.append(
                            {
                                "topic": self._canonicalReportTopic(apiType),
                                "period": str(year),
                                "source": "report",
                                "valueType": "field",
                                "valueKey": key,
                                "value": str(value),
                                "payloadRef": f"report:{apiType}:{quarter}",
                                "priority": 200,
                                "summary": None,
                            }
                        )
                    if rows and summaryParts:
                        summary = "; ".join(summaryParts[:6])
                        for item in rows[-len(summaryParts) :]:
                            item["summary"] = summary
                if rows:
                    frames.append(pl.DataFrame(rows))

        docsBlocks = self._company.docs.retrievalBlocks
        if docsBlocks is not None and not docsBlocks.is_empty():
            # topic = coalesce(detailTopic, semanticTopic, topic)
            topicExpr = pl.col("topic")
            if "semanticTopic" in docsBlocks.columns:
                topicExpr = pl.coalesce(pl.col("semanticTopic"), topicExpr)
            if "detailTopic" in docsBlocks.columns:
                topicExpr = pl.coalesce(pl.col("detailTopic"), topicExpr)

            valueKeyExpr = topicExpr.cast(pl.Utf8)
            if "rawTitle" in docsBlocks.columns:
                valueKeyExpr = pl.coalesce(pl.col("rawTitle"), valueKeyExpr)
            if "blockLabel" in docsBlocks.columns:
                valueKeyExpr = pl.coalesce(pl.col("blockLabel"), valueKeyExpr)

            payloadExpr = pl.concat_str(
                [pl.lit("docs:"), topicExpr.cast(pl.Utf8), pl.lit(":"), pl.col("period").cast(pl.Utf8)]
            )
            if "cellKey" in docsBlocks.columns:
                payloadExpr = pl.coalesce(pl.col("cellKey"), payloadExpr)

            docsDf = (
                docsBlocks.filter(
                    pl.col("period").is_not_null() & pl.col("blockText").is_not_null() & (pl.col("blockText") != "")
                )
                .with_columns(topicExpr.alias("_topic"))
                .filter(pl.col("_topic").is_not_null())
                .select(
                    [
                        pl.col("_topic").cast(pl.Utf8).alias("topic"),
                        pl.col("period").cast(pl.Utf8).alias("period"),
                        pl.lit("docs").alias("source"),
                        (pl.col("blockType") if "blockType" in docsBlocks.columns else pl.lit("text")).alias(
                            "valueType"
                        ),
                        valueKeyExpr.alias("valueKey"),
                        pl.col("blockText").cast(pl.Utf8).alias("value"),
                        payloadExpr.alias("payloadRef"),
                        pl.lit(100).alias("priority"),
                        pl.col("blockText").cast(pl.Utf8).str.slice(0, 400).alias("summary"),
                    ]
                )
            )
            if docsDf.height > 0:
                frames.append(docsDf)

        result = pl.concat(frames, how="vertical_relaxed") if frames else None
        self._company._cache[cacheKey] = result
        return result

    @property
    def sections(self) -> pl.DataFrame | None:
        return self._company._get_primary("sections")

    @property
    def availableTopics(self) -> list[str]:
        topics = set()
        if self.sections is not None and "topic" in self.sections.columns:
            topics.update(self.sections["topic"].to_list())
        facts = self.facts
        if facts is not None and "topic" in facts.columns:
            topics.update(facts["topic"].unique().to_list())
        return sorted(str(t) for t in topics if t is not None)

    def get(self, topic: str) -> Any:
        import warnings

        warnings.warn("profile.get(topic) → show(topic) 경로 권장", DeprecationWarning, stacklevel=2)
        if topic in {"BS", "IS", "CF", "CIS"}:
            return getattr(self._company.finance, topic)
        if topic == "SCE":
            return self._company.finance.sce
        if topic in self._REPORT_AUTHORITATIVE_TOPICS and self._company.report is not None:
            if topic == "audit":
                return self._company.report.audit
            return getattr(self._company.report, topic, None)
        sections = self.sections
        if sections is None:
            return None
        return sections.filter(pl.col("topic") == topic)

    def trace(self, topic: str, period: str | None = None) -> pl.DataFrame | dict[str, Any] | None:
        from dartlab.providers.dart.docs.sections import rawPeriod

        requestedPeriod = rawPeriod(period) if isinstance(period, str) else period
        facts = self.facts
        docsSections = self._company.docs.sections

        sources: list[dict[str, Any]] = []

        if facts is not None:
            traced = facts.filter(pl.col("topic") == topic)
            if requestedPeriod is not None:
                traced = traced.filter(pl.col("period") == requestedPeriod)
            if not traced.is_empty():
                grouped = traced.group_by("source").agg(
                    [
                        pl.len().alias("rows"),
                        pl.col("payloadRef").first().alias("payloadRef"),
                        pl.col("summary").first().alias("summary"),
                        pl.col("priority").max().alias("priority"),
                    ]
                )
                sources.extend(grouped.iter_rows(named=True))

        if docsSections is not None and topic in docsSections["topic"].to_list():
            row = docsSections.filter(pl.col("topic") == topic)
            if not row.is_empty():
                periodCols = [c for c in docsSections.columns if _isPeriodColumn(c)]
                if requestedPeriod is not None and requestedPeriod in periodCols:
                    value = row.item(0, requestedPeriod)
                    if value is not None:
                        sources.append(
                            {
                                "source": "docs",
                                "rows": 1,
                                "payloadRef": f"docs-sections:{topic}:{requestedPeriod}",
                                "summary": str(value)[:400],
                                "priority": 100,
                            }
                        )

        if not sources:
            return None

        sources.sort(key=lambda r: (r.get("priority", 0), r.get("source", "")), reverse=True)
        primary = sources[0]
        return {
            "topic": topic,
            "period": requestedPeriod,
            "primarySource": primary.get("source"),
            "fallbackSources": [r.get("source") for r in sources[1:]],
            "selectedPayloadRef": primary.get("payloadRef"),
            "availableSources": sources,
            "whySelected": f"{self._sourcePriority(topic)} authoritative priority",
        }

    def _canonicalReportTopic(self, apiType: str) -> str:
        if apiType == "auditOpinion":
            return "audit"
        return apiType

    def _sourcePriority(self, topic: str) -> str:
        if topic in {"BS", "IS", "CIS", "CF", "SCE"}:
            return "finance"
        if topic in self._REPORT_AUTHORITATIVE_TOPICS:
            return "report"
        return "docs"
