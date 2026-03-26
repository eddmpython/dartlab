"""주주총회 등에 관한 사항 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.providers.dart.docs.finance.shareholderMeeting.parser import parseMeetingAgenda
from dartlab.providers.dart.docs.finance.shareholderMeeting.types import ShareholderMeetingResult


def shareholderMeeting(stockCode: str) -> ShareholderMeetingResult | None:
    """주주총회 등에 관한 사항 분석."""
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
            if "주주총회" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                agendas = parseMeetingAgenda(content)
                if agendas:
                    agendaDf = pl.DataFrame(agendas)
                    return ShareholderMeetingResult(
                        corpName=corpName,
                        nYears=1,
                        agendas=agendas,
                        agendaDf=agendaDf,
                    )

                if len(content) > 200:
                    return ShareholderMeetingResult(
                        corpName=corpName,
                        nYears=1,
                        textOnly=True,
                    )
    return None
