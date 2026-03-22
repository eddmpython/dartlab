"""감사제도에 관한 사항 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.finance.auditSystem.parser import (
    parseAuditActivity,
    parseAuditCommittee,
)
from dartlab.engines.company.dart.docs.finance.auditSystem.types import AuditSystemResult


def auditSystem(stockCode: str) -> AuditSystemResult | None:
    """감사제도에 관한 사항 분석."""
    try:
        df = loadData(stockCode)
    except FileNotFoundError:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if "감사" in title and ("제도" in title or "기구" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                committee = parseAuditCommittee(content)
                activity = parseAuditActivity(content)

                if committee or activity:
                    committeeDf = pl.DataFrame(committee) if committee else None
                    activityDf = pl.DataFrame(activity) if activity else None

                    return AuditSystemResult(
                        corpName=corpName,
                        nYears=1,
                        committee=committee,
                        activity=activity,
                        committeeDf=committeeDf,
                        activityDf=activityDf,
                    )

                if len(content) > 200:
                    return AuditSystemResult(
                        corpName=corpName,
                        nYears=1,
                        textOnly=True,
                    )
    return None
