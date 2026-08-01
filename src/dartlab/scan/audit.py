"""감사 리스크 종합 스코어 — 의견 + 감사인 변경 + 특기사항 + 감사독립성."""

from __future__ import annotations

import polars as pl

from dartlab.providers._common.auditOpinion import auditOpinionStatus, normalizeAuditOpinion
from dartlab.scan.io.parquet import scanParquets

_OPINION_RISK = {
    "의견거절": 3,
    "부적정의견": 3,
    "한정의견": 2,
    "적정의견": 0,
    "적정": 0,
}


def _normalizeOpinion(raw: str | None) -> str | None:
    """감사의견 정규화 — 다양한 표기를 통일.

    Parameters
    ----------
    raw : str | None
        DART 원본 감사의견 문자열. 공백·줄바꿈 포함 가능.

    Returns
    -------
    str | None
        정규화된 감사의견. 다음 중 하나:
        - ``"적정의견"`` — 적정 계열
        - ``"한정의견"`` — 한정 계열
        - ``"부적정의견"`` — 부적정 계열
        - ``"의견거절"`` — 의견거절 계열
        - ``None`` — 감사의견 대상 아님 (해당없음, 반기검토 등)
        - 원본 문자열 — 위 범주에 해당하지 않는 기타 의견
    """
    normalized = normalizeAuditOpinion(raw)
    if normalized is not None:
        return normalized
    if auditOpinionStatus(raw) == "ambiguous":
        return str(raw).strip()
    return None


def _sortedYears(years: list) -> list[str]:
    """모든 연도를 정렬: 숫자 연도 우선 (내림차순), 그 다음 한국 회계연도 (문자열 내림차순).

    Parameters
    ----------
    years : list
        연도 값 리스트. 숫자 문자열(``"2024"``)과 한국 회계연도(``"제55기"``) 혼재 가능.

    Returns
    -------
    list[str]
        정렬된 연도 문자열 리스트. 숫자 연도 내림차순 → 기타 문자열 내림차순 순서.
    """
    numeric = []
    other = []
    for y in years:
        s = str(y).strip()
        if s.isdigit():
            numeric.append(s)
        elif s and s != "-":
            other.append(s)
    return sorted(numeric, key=lambda y: int(y), reverse=True) + sorted(other, reverse=True)


def scanAudit(*, verbose: bool = True) -> pl.DataFrame:
    """종목별 감사 리스크 종합 분석.

    프리빌드 auditOpinion parquet에서 전종목 감사의견·감사인·특기사항을 추출하고,
    감사인 변경 여부와 결합하여 종합 리스크 등급을 산출한다.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        opinion : str — 정규화된 감사의견 (적정의견/한정의견/부적정의견/의견거절)
        auditor : str — 감사인명
        auditorChanged : bool — 직전 연도 대비 감사인 변경 여부
        hasSpecialMatter : bool — 감사보고서 특기사항 존재 여부
        riskLevel : str, 종합 리스크 등급 (안전/관찰/주의/고위험).
            감사의견을 읽지 못한 종목은 판정 대신 ``"자료부족"``.

    Raises
    ------
    polars.PolarsError
        auditOpinion report parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("audit")
    >>> df.filter(pl.col("위험등급") == "고위험").select(["종목코드", "감사의견"])

    Capabilities:
        - 전종목 auditOpinion report parquet 에서 종목별 최신 감사의견 + 감사인 + 특기사항 추출
          후 감사인 변경 여부와 결합 → 종합 리스크 등급 (안전/관찰/주의/고위험).
        - 의견 누락 종목은 최신 연도 감사인 정보만으로 partial row.

    AIContext:
        Agent 가 ``dartlab.scan("audit")`` 호출 시 본 함수가 dispatch. 감사 리스크 횡단 비교
        (한정/부적정/거절 의견 회사 등) 또는 1 사 위험등급 컨텍스트 source.

    Guide:
        - 의견 분류 SSOT: ``_normalizeOpinion`` (적정/한정/부적정/거절 표준화).
        - 감사인 변경 = 최근 2 개 연도 비교. 변경 있으면 riskLevel 상승.
        - Q4 (분기) 우선 → 분기 없으면 전체 연 단위 fallback.

    When:
        대시보드 / 화면 audit 카드 빌드 시. cross-company 스크리닝 (한정 의견 종목 추적) 시.

    How:
        ``scanParquets("auditOpinion", ...)`` lazy load → 종목별 그룹 → 최신 연 + Q4 우선 →
        ``_normalizeOpinion`` + auditorChanged + hasSpecialMatter 결합 → riskLevel 분기 → wide row.

    Requires:
        - 로컬 ``data/dart/scan/report/auditOpinion.parquet`` (``buildReport`` 산출)
        - 한글 컬럼 → camelCase mapping (router 가 자동)

    SeeAlso:
        - :func:`dartlab.scan.builders.kr.core.buildReport` — auditOpinion source 빌드
        - :func:`dartlab.scan.io.parquet.scanParquets` — apiType lazy 로더
        - :func:`dartlab.scan.disclosureRisk.scanDisclosureRisk` — 보완적 리스크 axis
    """
    raw = scanParquets(
        "auditOpinion",
        ["stockCode", "year", "quarter", "adt_opinion", "adtor", "adt_reprt_spcmnt_matter"],
    )
    if raw.is_empty():
        return pl.DataFrame()

    rows: list[dict] = []
    for code in raw["stockCode"].unique().to_list():
        sub = raw.filter(pl.col("stockCode") == code)

        # 종목별 연도 정렬 (숫자 우선, 한국 회계연도 포함)
        codeYears = _sortedYears(sub["year"].unique().to_list())
        if not codeYears:
            continue

        # opinion이 있는 행을 우선 탐색 (최신 연도부터)
        opinion = None
        auditor = None
        specialMatter = None
        bestYear = None
        for y in codeYears:
            ySub = sub.filter(pl.col("year") == y)
            # Q4 우선
            q4 = ySub.filter(pl.col("quarter") == "4분기")
            candidate = q4 if not q4.is_empty() else ySub
            for r in candidate.iter_rows(named=True):
                normalized = _normalizeOpinion(r.get("adt_opinion"))
                if normalized:
                    opinion = normalized
                    auditor = r.get("adtor", "")
                    specialMatter = r.get("adt_reprt_spcmnt_matter", "")
                    bestYear = y
                    break
            if opinion:
                break

        # opinion 못 찾으면 최신 연도에서 auditor라도 가져옴
        if opinion is None:
            latestSub = sub.filter(pl.col("year") == codeYears[0])
            q4 = latestSub.filter(pl.col("quarter") == "4분기")
            best = q4 if not q4.is_empty() else latestSub
            if not best.is_empty():
                row = best.row(0, named=True)
                auditor = row.get("adtor", "")
                specialMatter = row.get("adt_reprt_spcmnt_matter", "")
            bestYear = codeYears[0]

        # 감사인 변경 감지: bestYear 직전 연도와 비교
        auditorChanged = False
        bestIdx = codeYears.index(bestYear) if bestYear in codeYears else 0
        if bestIdx + 1 < len(codeYears):
            prevSub = sub.filter(pl.col("year") == codeYears[bestIdx + 1])
            if not prevSub.is_empty():
                prevQ4 = prevSub.filter(pl.col("quarter") == "4분기")
                prevBest = prevQ4 if not prevQ4.is_empty() else prevSub
                prevAuditor = prevBest.row(0, named=True).get("adtor", "")
                if prevAuditor and auditor and str(prevAuditor).strip() != str(auditor).strip():
                    auditorChanged = True

        # 특기사항 유무
        hasSpecialMatter = bool(
            specialMatter and str(specialMatter).strip() not in ("", "-", "해당사항없음", "해당없음", "해당사항 없음")
        )

        # 종합 리스크 레벨. 감사의견을 읽지 못하면 종합 판정을 만들지 않는다.
        # 예전에는 의견 부재와 표준 범주 밖 문자열(각주 마커 등)이 모두 위험점수 1을
        # 받아 "관찰"이라는 실질 판정으로 나갔다. 자료 부재는 판정이 아니므로 형제 축
        # (insider·cashflow·growth)과 같은 정직 gap 라벨로 남긴다.
        opinionRisk = _OPINION_RISK.get(opinion) if opinion else None
        if opinionRisk is None:
            riskLevel = "자료부족"
        else:
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
                "opinion": opinion,
                "auditor": str(auditor).strip() if auditor else None,
                "auditorChanged": auditorChanged,
                "hasSpecialMatter": hasSpecialMatter,
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
        "riskLevel": pl.Utf8,
    }
    return pl.DataFrame(rows, schema=schema)
