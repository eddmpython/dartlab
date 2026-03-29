"""감사 리스크 종합 스코어 — 의견 + 감사인 변경 + 특기사항 + 감사독립성."""

from __future__ import annotations

import polars as pl

from dartlab.scan._helpers import parse_num, scan_parquets

_OPINION_RISK = {
    "의견거절": 3,
    "부적정의견": 3,
    "한정의견": 2,
    "적정의견": 0,
}


def _numericYears(years: list) -> list[str]:
    """숫자 연도만 필터링 후 내림차순 정렬 (한국 회계연도 포맷 제외)."""
    numeric = [str(y) for y in years if str(y).strip().isdigit()]
    return sorted(numeric, key=lambda y: int(y), reverse=True)


def _sortedYears(years: list) -> list[str]:
    """모든 연도를 정렬: 숫자 연도 우선 (내림차순), 그 다음 한국 회계연도 (문자열 내림차순)."""
    numeric = []
    other = []
    for y in years:
        s = str(y).strip()
        if s.isdigit():
            numeric.append(s)
        elif s and s != "-":
            other.append(s)
    return sorted(numeric, key=lambda y: int(y), reverse=True) + sorted(other, reverse=True)


def _scanAuditFees() -> dict[str, dict]:
    """auditContract + nonAuditContract → {종목코드: {감사보수, 비감사보수, 독립성비율}}."""
    audit = scan_parquets(
        "auditContract",
        ["stockCode", "year", "quarter", "mendng"],
    )
    nonAudit = scan_parquets(
        "nonAuditContract",
        ["stockCode", "year", "quarter", "servc_mendng"],
    )

    # 감사보수: 최신 연도 Q4 기준
    auditFees: dict[str, float] = {}
    if not audit.is_empty():
        years = _numericYears(audit["year"].unique().to_list())
        for y in years:
            sub = audit.filter(pl.col("year") == y)
            q4 = sub.filter(pl.col("quarter") == "4분기")
            target = q4 if not q4.is_empty() else sub
            valid = target.filter(pl.col("mendng").is_not_null() & (pl.col("mendng") != "-"))
            if valid.shape[0] >= 50:
                for code, group in valid.group_by("stockCode"):
                    val = parse_num(group.row(0, named=True).get("mendng"))
                    if val and val > 0:
                        auditFees[code[0]] = val
                break

    # 비감사보수: 최신 연도
    nonAuditFees: dict[str, float] = {}
    if not nonAudit.is_empty():
        years = _numericYears(nonAudit["year"].unique().to_list())
        for y in years:
            sub = nonAudit.filter(pl.col("year") == y)
            q4 = sub.filter(pl.col("quarter") == "4분기")
            target = q4 if not q4.is_empty() else sub
            valid = target.filter(pl.col("servc_mendng").is_not_null() & (pl.col("servc_mendng") != "-"))
            if valid.shape[0] >= 10:
                for code, group in valid.group_by("stockCode"):
                    total = 0.0
                    for row in group.iter_rows(named=True):
                        val = parse_num(row.get("servc_mendng"))
                        if val and val > 0:
                            total += val
                    if total > 0:
                        nonAuditFees[code[0]] = total
                break

    # 독립성비율 = 비감사보수 / 감사보수 (높을수록 독립성 위험)
    result: dict[str, dict] = {}
    allCodes = set(auditFees) | set(nonAuditFees)
    for code in allCodes:
        af = auditFees.get(code, 0.0)
        naf = nonAuditFees.get(code, 0.0)
        ratio = (naf / af * 100) if af > 0 else None
        result[code] = {
            "감사보수": af,
            "비감사보수": naf,
            "독립성비율": ratio,
        }
    return result


def scanAudit() -> pl.DataFrame:
    """종목별 감사 리스크 종합 분석.

    컬럼: stockCode, opinion, auditor, auditorChanged, hasSpecialMatter,
          auditFee, nonAuditFee, independenceRatio, riskLevel
    """
    raw = scan_parquets(
        "auditOpinion",
        ["stockCode", "year", "quarter", "adt_opinion", "adtor", "adt_reprt_spcmnt_matter"],
    )
    if raw.is_empty():
        return pl.DataFrame()

    # 감사독립성 데이터 수집
    feeMap = _scanAuditFees()

    rows: list[dict] = []
    for code in raw["stockCode"].unique().to_list():
        sub = raw.filter(pl.col("stockCode") == code)

        # 종목별 연도 정렬 (숫자 우선, 한국 회계연도 포함)
        codeYears = _sortedYears(sub["year"].unique().to_list())
        if not codeYears:
            continue

        # 최신 연도 데이터
        latestSub = sub.filter(pl.col("year") == codeYears[0])
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
        if len(codeYears) >= 2:
            prevSub = sub.filter(pl.col("year") == codeYears[1])
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

        # 감사독립성 데이터
        fees = feeMap.get(code, {})
        auditFee = fees.get("감사보수", 0.0)
        nonAuditFee = fees.get("비감사보수", 0.0)
        independenceRatio = fees.get("독립성비율")

        # 종합 리스크 레벨
        opinionRisk = _OPINION_RISK.get(str(opinion).strip(), 1)
        riskScore = opinionRisk
        if auditorChanged:
            riskScore += 1
        if hasSpecialMatter:
            riskScore += 1
        # 비감사보수가 감사보수의 50% 이상이면 독립성 리스크
        if independenceRatio is not None and independenceRatio >= 50:
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
                "auditFee": auditFee,
                "nonAuditFee": nonAuditFee,
                "independenceRatio": round(independenceRatio, 1) if independenceRatio is not None else None,
                "riskLevel": riskLevel,
            }
        )

    if not rows:
        return pl.DataFrame()
    schema = {
        "stockCode": pl.Utf8,
        "opinion": pl.Utf8,
        "auditor": pl.Utf8,
        "auditorChanged": pl.Boolean,
        "hasSpecialMatter": pl.Boolean,
        "auditFee": pl.Float64,
        "nonAuditFee": pl.Float64,
        "independenceRatio": pl.Float64,
        "riskLevel": pl.Utf8,
    }
    return pl.DataFrame(rows, schema=schema)
