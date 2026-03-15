"""위험관리 및 파생거래 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.finance.riskDerivative.parser import (
    detectUnit,
    parseDerivativeContracts,
    parseFxSensitivity,
)
from dartlab.engines.dart.docs.finance.riskDerivative.types import RiskDerivativeResult


def _buildDerivativeDf(
    rows: list[dict],
    headers: list[str] | None = None,
) -> pl.DataFrame | None:
    """파생상품 행 목록을 DataFrame으로 변환."""
    if not rows:
        return None

    maxVals = max(len(r["values"]) for r in rows)
    data: dict[str, list] = {"label": [r["label"] for r in rows]}
    for i in range(maxVals):
        colName = headers[i] if headers and i < len(headers) else f"v{i + 1}"
        if colName in data:
            colName = f"{colName}_{i + 1}"
        data[colName] = [r["values"][i] if i < len(r["values"]) else None for r in rows]

    schema = {"label": pl.Utf8}
    for col in data:
        if col != "label":
            schema[col] = pl.Int64

    return pl.DataFrame(data, schema=schema)


def riskDerivative(stockCode: str) -> RiskDerivativeResult | None:
    """위험관리 및 파생거래 분석."""
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
            if ("위험관리" in title and "파생" in title) or ("파생" in title and "거래" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                unit = detectUnit(content)
                fxSensitivity = parseFxSensitivity(content)
                derivatives, derivHeaders = parseDerivativeContracts(content)

                if not fxSensitivity and not derivatives:
                    if "없습니다" in content[:500] or "해당사항" in content[:500] or len(content) < 300:
                        return RiskDerivativeResult(
                            corpName=corpName,
                            nYears=1,
                            unit=unit,
                            noData=True,
                        )
                    hasRisk = any(k in content for k in ("환율", "이자율", "시장위험", "신용위험"))
                    if hasRisk:
                        return RiskDerivativeResult(
                            corpName=corpName,
                            nYears=1,
                            unit=unit,
                            textOnly=True,
                        )
                    continue

                fxDf = None
                if fxSensitivity:
                    fxDf = pl.DataFrame(
                        {
                            "currency": [f["currency"] for f in fxSensitivity],
                            "upImpact": [f.get("upImpact") for f in fxSensitivity],
                            "downImpact": [f.get("downImpact") for f in fxSensitivity],
                        },
                        schema={
                            "currency": pl.Utf8,
                            "upImpact": pl.Int64,
                            "downImpact": pl.Int64,
                        },
                    )

                return RiskDerivativeResult(
                    corpName=corpName,
                    nYears=1,
                    unit=unit,
                    fxSensitivity=fxSensitivity,
                    derivatives=derivatives,
                    fxDf=fxDf,
                    derivativeDf=_buildDerivativeDf(derivatives, derivHeaders),
                )

    return None
