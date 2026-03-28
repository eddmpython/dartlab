"""감사 리스크 종합 스코어 — 의견 + 감사인 변경 + 특기사항."""

from __future__ import annotations

import polars as pl

from dartlab.scan._helpers import scan_parquets

_OPINION_RISK = {
    "의견거절": 3,
    "부적정의견": 3,
    "한정의견": 2,
    "적정의견": 0,
}


def scanAudit() -> pl.DataFrame:
    """종목별 감사 리스크 종합 분석.

    컬럼: stockCode, opinion, auditor, auditorChanged, hasSpecialMatter, riskLevel
    """
    raw = scan_parquets(
        "auditOpinion",
        ["stockCode", "year", "quarter", "adt_opinion", "adtor", "adt_reprt_spcmnt_matter"],
    )
    if raw.is_empty():
        return pl.DataFrame()

    # Q4(사업보고서) 우선, 없으면 가장 큰 분기
    years = sorted(raw["year"].unique().to_list(), reverse=True)
    if not years:
        return pl.DataFrame()

    # 최신 2개 연도 필요 (감사인 변경 감지용)
    validYears = years[:2] if len(years) >= 2 else years

    rows: list[dict] = []
    for code in raw["stockCode"].unique().to_list():
        sub = raw.filter(pl.col("stockCode") == code)

        # 최신 연도 데이터
        latestSub = sub.filter(pl.col("year") == validYears[0])
        if latestSub.is_empty():
            continue

        # Q4 우선 선택
        q4 = latestSub.filter(pl.col("quarter") == "4분기")
        best = q4 if not q4.is_empty() else latestSub
        row = best.row(0, named=True)

        opinion = row.get("adt_opinion", "")
        auditor = row.get("adtor", "")
        specialMatter = row.get("adt_reprt_spcmnt_matter", "")

        # 감사인 변경 감지
        auditorChanged = False
        if len(validYears) >= 2:
            prevSub = sub.filter(pl.col("year") == validYears[1])
            if not prevSub.is_empty():
                prevQ4 = prevSub.filter(pl.col("quarter") == "4분기")
                prevBest = prevQ4 if not prevQ4.is_empty() else prevSub
                prevAuditor = prevBest.row(0, named=True).get("adtor", "")
                if prevAuditor and auditor and prevAuditor != auditor:
                    auditorChanged = True

        # 특기사항 유무
        hasSpecialMatter = bool(
            specialMatter and str(specialMatter).strip() not in ("", "-", "해당사항없음", "해당없음", "해당사항 없음")
        )

        # 종합 리스크 레벨
        opinionRisk = _OPINION_RISK.get(str(opinion).strip(), 1)
        riskScore = opinionRisk
        if auditorChanged:
            riskScore += 1
        if hasSpecialMatter:
            riskScore += 1

        if riskScore >= 3:
            riskLevel = "고위험"
        elif riskScore >= 2:
            riskLevel = "주의"
        elif riskScore >= 1:
            riskLevel = "관찰"
        else:
            riskLevel = "안전"

        rows.append(
            {
                "stockCode": code,
                "opinion": str(opinion).strip() if opinion else None,
                "auditor": str(auditor).strip() if auditor else None,
                "auditorChanged": auditorChanged,
                "hasSpecialMatter": hasSpecialMatter,
                "riskLevel": riskLevel,
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()
