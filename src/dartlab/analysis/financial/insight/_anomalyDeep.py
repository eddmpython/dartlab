"""anomaly.py 심층 detector 분리. Trend/CCC/Audit/Benford/RevenueQuality.

분리 이유: insight/anomaly.py 941 줄. 5 개 detector (Trend/CCC/Audit/Benford/
RevenueQuality) + _isBig4 helper + _BIG4_KEYWORDS 가 약 480 줄. 별도 모듈로 빼서
anomaly.py 의 facade 책임 (룰 진입점 + 가벼운 detector 7 개) 만 유지.

BC: anomaly 모듈에서 5 detector + _isBig4 모두 import 가능 (re-export).
순환 import 회피: _yoyChange 는 anomaly.py 의 정의를 함수 내부에서 lazy import.
"""

from __future__ import annotations

import math

from dartlab.analysis.financial._seriesMath import _latestNotNone
from dartlab.analysis.financial.insight.types import Anomaly, AuditDataForAnomaly
from dartlab.core.utils.extract import getAnnualValues
from dartlab.providers._common.auditOpinion import normalizeAuditOpinion

_BIG4_KEYWORDS = ["삼일", "PwC", "삼정", "KPMG", "한영", "EY", "안진", "Deloitte"]


def _annualValuesWithFallback(aSeries: dict, sjDiv: str, *snakeIds: str) -> list:
    """계정 별칭 목록을 순서대로 훑어 처음 잡히는 시계열을 돌려준다.

    같은 개념이 파서/공시 표기에 따라 다른 snakeId 로 들어와서 (net_profit vs
    net_income 등) detector 마다 2 단 fallback 이 반복되고 있었다.
    """
    values: list = []
    for snakeId in snakeIds:
        values = getAnnualValues(aSeries, sjDiv, snakeId)
        if values:
            return values
    return values


def _trailingNegativeStreak(values: list) -> int:
    """최신부터 거슬러 올라가며 음수가 끊기지 않고 이어진 기수."""
    streak = 0
    for v in reversed(values):
        if v is not None and v < 0:
            streak += 1
        else:
            break
    return streak


def _trailingRiseStreak(series: list) -> int:
    """최신부터 거슬러 올라가며 직전기 대비 상승이 이어진 기수 (None 이면 끊긴다)."""
    streak = 0
    for i in range(len(series) - 1, 0, -1):
        if series[i] is not None and series[i - 1] is not None and series[i] > series[i - 1]:
            streak += 1
        else:
            break
    return streak


def detectTrendDeterioration(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    """시계열 악화 패턴 탐지: 연속적자, ICR<1, 부채비율 상승.

    Capabilities:
        - 순이익/영업CF 연속 적자 + ICR<1 연속 + 부채비율 연속 상승 4 패턴 감지.

    실험 084/006 검증 결과 기반.
    severity: 4기+ danger, 3기 warning, 2기 info.

    Parameters
    ----------
    aSeries : dict
        finance.timeseries 시계열 dict.
    isFinancial : bool
        금융업 여부.

    Returns
    -------
    list[Anomaly]
        감지된 악화 패턴 목록.

    Guide:
        급격한 단일 사건이 아닌 ‘연속성’ 신호. 디폴트 1~2 년 선행 지표.

    When:
        runAnomalyDetection 7 번째 룰. 비금융은 4 패턴, 금융은 2 패턴.

    How:
        시계열 reversed loop 로 연속 streak 카운트 → 임계 기준 severity 매핑.

    Requires:
        aSeries IS/CF/BS 연간 시계열 ≥ 4 년 권장.

    Raises:
        없음.

    Example:
        >>> detectTrendDeterioration(aSeries)
        [Anomaly('danger', 'trendDeterioration', '순이익 4기 연속 적자')]

    See Also:
        - detectEarningsQuality: 단일 분기 신호
        - calcDistress: 종합 부실 모델

    AIContext:
        ‘N 기 연속’ 표현은 추세적 악화 컨텍스트로 직접 인용. 단기 변동과 구분.
    """
    anomalies: list[Anomaly] = []

    # 순이익·영업CF 연속 적자는 계정과 라벨만 다른 같은 판정이라 한 루프로 묶는다.
    for label, values in (
        ("순이익", _annualValuesWithFallback(aSeries, "IS", "net_profit", "net_income")),
        ("영업CF", getAnnualValues(aSeries, "CF", "operating_cashflow")),
    ):
        streak = _trailingNegativeStreak(values)
        if streak >= 2:
            sev = "danger" if streak >= 4 else "warning" if streak >= 3 else "info"
            anomalies.append(Anomaly(sev, "trendDeterioration", f"{label} {streak}기 연속 적자", float(streak)))

    if isFinancial:
        return anomalies  # ICR, 부채비율 추이는 금융업 구조적 왜곡

    for detected in (_interestCoverageStreak(aSeries), _debtRatioRiseStreak(aSeries)):
        if detected is not None:
            anomalies.append(detected)

    return anomalies


def _interestCoverageStreak(aSeries: dict) -> Anomaly | None:
    """ICR<1 이 2 기 이상 이어졌는지. 금융업은 호출자가 걸러낸다."""
    opVals = _annualValuesWithFallback(aSeries, "IS", "operating_profit", "operating_income")
    fcVals = _annualValuesWithFallback(aSeries, "IS", "finance_costs", "interest_expense")
    if not (opVals and fcVals):
        return None

    n = min(len(opVals), len(fcVals))
    streak = 0
    for i in range(n - 1, -1, -1):
        opV = opVals[i]
        fcV = fcVals[i]
        if opV is not None and fcV is not None and fcV > 0 and opV / fcV < 1:
            streak += 1
        else:
            break
    if streak < 2:
        return None
    sev = "danger" if streak >= 3 else "warning"
    return Anomaly(sev, "trendDeterioration", f"ICR<1 {streak}기 연속", float(streak))


def _debtRatioRiseStreak(aSeries: dict) -> Anomaly | None:
    """부채비율이 3 기 이상 연속 상승했는지."""
    tlVals = getAnnualValues(aSeries, "BS", "total_liabilities")
    eqVals = _annualValuesWithFallback(aSeries, "BS", "owners_of_parent_equity", "total_stockholders_equity")
    if not (tlVals and eqVals):
        return None

    n = min(len(tlVals), len(eqVals))
    drSeries = []
    for i in range(n):
        if tlVals[i] is not None and eqVals[i] is not None and eqVals[i] > 0:
            drSeries.append(tlVals[i] / eqVals[i] * 100)
        else:
            drSeries.append(None)

    streak = _trailingRiseStreak(drSeries)
    if streak < 3:
        return None
    sev = "warning" if streak >= 4 else "info"
    return Anomaly(sev, "trendDeterioration", f"부채비율 {streak}기 연속 상승", float(streak))


def detectCCCDeterioration(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    """CCC(현금전환주기) 악화 탐지.

    Capabilities:
        - DSO + DIO - DPO 시계열 → 3 기 연속 확대 streak 탐지.

    실험 084/007 검증 결과 기반.
    CCC 3기+ 연속 확대 시 운전자본 경색 경고.
    금융업 제외 (DSO/DIO/CCC 비적용).

    Parameters
    ----------
    aSeries : dict
        finance.timeseries 시계열 dict.
    isFinancial : bool
        금융업 여부 (True이면 빈 리스트 반환).

    Returns
    -------
    list[Anomaly]
        CCC 악화 이상 신호 목록.

    Guide:
        CCC 확대 = 현금 회수 지연 → 단기 유동성 압박. 4 기+ 는 warning.

    When:
        runAnomalyDetection 8 번째 룰. 비금융업만 실행.

    How:
        매출/매출원가/매출채권/재고/매입채무 5 계정 시계열 → CCC 산출 → 연속 증가.

    Requires:
        aSeries IS/BS 연간 ≥ 4 년 + 매출/COGS/AR/INV/AP 비결측.

    Raises:
        없음.

    Example:
        >>> detectCCCDeterioration(aSeries)
        [Anomaly('warning', 'cccDeterioration', 'CCC 4기 연속 확대 ...')]

    See Also:
        - detectWorkingCapitalAnomaly: 단일 사건 신호
        - calcCCC: 정량 산출

    AIContext:
        ‘N 기 연속 CCC 확대’ 표현은 운전자본 경색 컨텍스트로 인용.
    """
    if isFinancial:
        return []

    anomalies: list[Anomaly] = []
    revVals = _annualValuesWithFallback(aSeries, "IS", "sales", "revenue")
    recVals = getAnnualValues(aSeries, "BS", "trade_and_other_receivables")
    invVals = getAnnualValues(aSeries, "BS", "inventories")
    payVals = getAnnualValues(aSeries, "BS", "trade_and_other_payables")
    cogsVals = getAnnualValues(aSeries, "IS", "cost_of_sales")

    n = (
        min(len(revVals), len(recVals), len(invVals), len(payVals))
        if revVals and recVals and invVals and payVals
        else 0
    )
    if n < 3:
        return anomalies

    cccSeries: list[float | None] = []
    for i in range(n):
        rv = revVals[i]
        rc = recVals[i]
        iv = invVals[i]
        pa = payVals[i]
        co = cogsVals[i] if cogsVals and i < len(cogsVals) else rv

        if rv and rv > 0 and rc is not None and iv is not None and pa is not None and co and co > 0:
            dso = rc / rv * 365
            dio = iv / co * 365
            dpo = pa / co * 365
            cccSeries.append(dso + dio - dpo)
        else:
            cccSeries.append(None)

    # 연속 확대 탐지
    streak = _trailingRiseStreak(cccSeries)

    if streak >= 3:
        latest = cccSeries[-1]
        sev = "warning" if streak >= 4 else "info"
        anomalies.append(
            Anomaly(
                sev,
                "cccDeterioration",
                f"CCC {streak}기 연속 확대 (최신 {latest:.0f}일)" if latest else f"CCC {streak}기 연속 확대",
                float(streak),
            )
        )

    return anomalies


def _isBig4(auditor: str | None) -> bool:
    """감사인이 Big4인지 판정.

    Parameters
    ----------
    auditor : str | None
        감사인 이름.

    Returns
    -------
    bool
        Big4 여부. None이면 False.
    """
    if not auditor:
        return False
    return any(kw in auditor for kw in _BIG4_KEYWORDS)


def detectAuditRedFlags(auditData: AuditDataForAnomaly | None) -> list[Anomaly]:
    """감사 Red Flag 탐지. PCAOB AS 3101, ISA 570/701/705, SOX 302/404.

    Capabilities:
        - 감사인 교체 패턴 + 감사보수 ±30% + 계속기업/내부통제 약점 + 비적정 의견 +
          KAM 급증 6 종 룰 통합.

    6개 항목: 감사인 교체, 감사보수 급변, 계속기업 불확실성,
    내부통제 취약점, 감사의견 비적정, KAM 급증.

    Parameters
    ----------
    auditData : AuditDataForAnomaly | None
        감사 데이터. None이면 빈 리스트 반환.

    Returns
    -------
    list[Anomaly]
        감사 관련 이상 신호 목록.

    Guide:
        세계 표준 감사 프레임 (PCAOB/ISA/SOX) 기반. ‘계속기업 의문’ 은 디폴트 직전 신호.

    When:
        runAnomalyDetection 내부에서 호출 (analyzeFinancial 가 auditData 추출).

    How:
        auditors/fees/opinions/kamCounts 시계열을 6 룰 분기.

    Requires:
        AuditDataForAnomaly dataclass (auditors/fees/opinions/kamCounts/플래그) 사전 구축.

    Raises:
        없음.

    Example:
        >>> detectAuditRedFlags(audit)
        [Anomaly('danger', 'audit', '계속기업 불확실성 ...')]

    See Also:
        - analyzeAudit: 단독 진입점
        - runAnomalyDetection: 11 룰 통합 실행

    AIContext:
        ISA/PCAOB 표준 인용으로 신뢰도 강화. ‘감사인 교체’ + ‘비적정 의견’ 조합은 최우선 알림.
    """
    if auditData is None:
        return []

    # 6 룰은 서로 독립이라 각자 자기 게이트를 들고 Anomaly 또는 None 을 낸다.
    # 3·4 번은 플래그 한 줄이라 그대로 둔다. 나열 순서가 곧 반환 순서다.
    anomalies: list[Anomaly] = []
    for detected in (_auditorChangeFlag(auditData.auditors), _auditFeeSwingFlag(auditData.fees)):
        if detected is not None:
            anomalies.append(detected)

    # 3. 계속기업 불확실성 (ISA 570)
    if auditData.hasGoingConcern:
        anomalies.append(Anomaly("danger", "audit", "계속기업 불확실성. 감사인 보고 (ISA 570)", 1.0))

    # 4. 내부통제 취약점 (SOX 302/404)
    if auditData.hasInternalControlWeakness:
        anomalies.append(Anomaly("danger", "audit", "내부회계관리제도 취약점 보고 (SOX 302/404)", 1.0))

    for detected in (_auditOpinionFlag(auditData.opinions), _kamSurgeFlag(auditData.kamCounts)):
        if detected is not None:
            anomalies.append(detected)

    return anomalies


def _auditorChangeFlag(auditors: list) -> Anomaly | None:
    """룰 1: 감사인 비정상 교체 (PCAOB AS 3101)."""
    if len(auditors) < 2:
        return None
    # 고유 감사인 수 (None 제외)
    unique = [a for a in auditors if a is not None]
    changes = []
    for i in range(1, len(unique)):
        if unique[i] != unique[i - 1]:
            changes.append((i, unique[i - 1], unique[i]))

    if len(changes) >= 3:
        return Anomaly(
            "danger",
            "audit",
            f"감사인 {len(changes)}회 교체 (5년 내). 빈번 교체 Red Flag",
            float(len(changes)),
        )
    if len(changes) >= 2:
        return Anomaly("danger", "audit", "감사인 2년 이내 재교체. Red Flag", float(len(changes)))
    if len(changes) == 1:
        _, prev, curr = changes[0]
        if _isBig4(prev) and not _isBig4(curr):
            return Anomaly("warning", "audit", f"Big4→비Big4 교체 ({prev} → {curr})", 1.0)
    return None


def _auditFeeSwingFlag(fees: list) -> Anomaly | None:
    """룰 2: 감사보수 급변 (ISA 260, ±30% YoY)."""
    if len(fees) < 2:
        return None
    validFees = [(i, f) for i, f in enumerate(fees) if f is not None and f > 0]
    if len(validFees) < 2:
        return None
    _, prevFee = validFees[-2]
    _, currFee = validFees[-1]
    feeChange = (currFee - prevFee) / prevFee * 100
    if abs(feeChange) <= 30:
        return None
    direction = "급증" if feeChange > 0 else "급감"
    return Anomaly("warning", "audit", f"감사보수 {direction} ({feeChange:+.0f}%)", feeChange)


def _auditOpinionFlag(opinions: list) -> Anomaly | None:
    """룰 5: 감사의견 비적정 (ISA 705)."""
    if not opinions:
        return None
    latest = _latestNotNone(opinions)
    normalized = normalizeAuditOpinion(latest)
    if normalized is None or normalized == "적정의견":
        return None
    return Anomaly("danger", "audit", f"감사의견 비적정: {normalized} (ISA 705)", 1.0)


def _kamSurgeFlag(kamCounts: list) -> Anomaly | None:
    """룰 6: KAM 급증 (ISA 701). 직전 대비 3 건 이상 늘면 감사인 위험 인식 확대."""
    if len(kamCounts) < 2:
        return None
    validKam = [(i, k) for i, k in enumerate(kamCounts) if k is not None]
    if len(validKam) < 2:
        return None
    _, prevKam = validKam[-2]
    _, currKam = validKam[-1]
    if currKam <= prevKam + 2:
        return None
    return Anomaly(
        "info",
        "audit",
        f"KAM 급증 ({prevKam}건 → {currKam}건). 감사인 위험 인식 확대",
        float(currKam - prevKam),
    )


def detectBenfordAnomaly(aSeries: dict) -> list[Anomaly]:
    """Benford's Law 이상치 탐지. 회계 조작 의심 신호.

    Capabilities:
        - 재무제표 모든 IS/BS/CF 값 첫 자릿수 분포 → Benford 기대분포 χ² 검정.

    Nigrini (1996), AICPA 공식 감사 절차.
    재무제표 수치의 첫째 유효 자릿수 분포를 Benford 기대 분포와 비교.
    χ² > 15.51 (df=8, p<0.05) → warning, χ² > 20.09 (p<0.01) → danger.

    Parameters
    ----------
    aSeries : dict
        finance.timeseries 시계열 dict.

    Returns
    -------
    list[Anomaly]
        Benford 분포 이탈 이상 신호 목록.

    Guide:
        통계적 정황 신호이지 단독 증거 아님. 다른 anomaly 와 결합해야 의미 있음.

    When:
        runAnomalyDetection 10 번째 룰. 모든 산업 호출. 최소 50 개 숫자 필요.

    How:
        IS/BS/CF 모든 값 첫 자릿수 추출 → 기대 분포 P(d)=log10(1+1/d) χ² 비교.

    Requires:
        aSeries 시계열 ≥ 4 년치 데이터 (≥ 50 숫자 확보).

    Raises:
        없음.

    Example:
        >>> detectBenfordAnomaly(aSeries)
        [Anomaly('warning', 'benford', 'χ²=18.5 ...')]

    See Also:
        - detectAuditRedFlags: 정성적 신호
        - detectRevenueQuality: 매출 인식 이상

    AIContext:
        ‘회계 조작 의심’ 단정 금지. ‘통계적 정황 신호’ 로 인용.
    """
    anomalies: list[Anomaly] = []

    # 모든 IS/BS/CF 값에서 첫째 유효 자릿수 추출
    digits: list[int] = []
    for sjDiv in ("IS", "BS", "CF"):
        section = aSeries.get(sjDiv, {})
        for _key, vals in section.items():
            if not isinstance(vals, list):
                continue
            for v in vals:
                if v is None or not isinstance(v, (int, float)):
                    continue
                if v == 0 or not math.isfinite(v):
                    continue
                # 첫째 유효 자릿수 추출
                absV = abs(v)
                d = int(str(absV).lstrip("0").lstrip(".").lstrip("0")[:1]) if absV != 0 else 0
                if 1 <= d <= 9:
                    digits.append(d)

    # 최소 50개 이상 숫자 필요
    if len(digits) < 50:
        return anomalies

    n = len(digits)
    # Benford 기대 분포: P(d) = log10(1 + 1/d)
    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    observed = {d: 0 for d in range(1, 10)}
    for d in digits:
        observed[d] += 1

    # χ² 검정
    chi2 = 0.0
    for d in range(1, 10):
        exp_count = expected[d] * n
        obs_count = observed[d]
        if exp_count > 0:
            chi2 += (obs_count - exp_count) ** 2 / exp_count

    # df=8, p<0.01 → 20.09, p<0.05 → 15.51
    if chi2 > 20.09:
        anomalies.append(
            Anomaly(
                "danger",
                "earningsQuality",
                f"Benford's Law 위반 (χ²={chi2:.1f}, p<0.01). 회계 수치 분포 이상",
                chi2,
            )
        )
    elif chi2 > 15.51:
        anomalies.append(
            Anomaly(
                "warning",
                "earningsQuality",
                f"Benford's Law 이탈 (χ²={chi2:.1f}, p<0.05). 회계 수치 분포 주의",
                chi2,
            )
        )

    return anomalies


def detectRevenueQuality(aSeries: dict) -> list[Anomaly]:
    """매출 품질 탐지. Dechow & Dichev (2002).

    Capabilities:
        - OCF/Revenue 비율 < 0 + 3 기 연속 하락 + AR 성장 vs 매출 성장 1.5× 초과
          3 룰 통합.

    OCF/Revenue 비율 추세: 매출이 늘어도 현금이 안 들어오면 의심.
    - OCF/Revenue < 0 (매출 흑자인데 영업CF 적자) → danger
    - OCF/Revenue 3기 연속 하락 → warning
    - 매출채권 증가율 > 매출 증가율 × 1.5 (3기 연속) → warning

    Parameters
    ----------
    aSeries : dict
        finance.timeseries 시계열 dict.

    Returns
    -------
    list[Anomaly]
        매출 품질 이상 신호 목록.

    Guide:
        Dechow & Dichev (2002) accrual quality 학술 프레임. 발생주의 왜곡 정공법.

    When:
        runAnomalyDetection 11 번째 룰. 모든 산업 호출.

    How:
        매출/영업CF/매출채권 시계열 → OCF/Revenue 비율 + AR vs 매출 성장 비교.

    Requires:
        aSeries IS (sales) + CF (operating_cashflow) + BS (AR) 연간 시계열 ≥ 4 년.

    Raises:
        없음.

    Example:
        >>> detectRevenueQuality(aSeries)
        [Anomaly('warning', 'revenueQuality', 'OCF/Revenue 3기 연속 하락 ...')]

    See Also:
        - detectEarningsQuality: 이익 품질 단일 분기
        - detectWorkingCapitalAnomaly: 운전자본 단일 사건

    AIContext:
        ‘매출 인식 vs 현금 회수 괴리’ 컨텍스트로 인용. Dechow 학술 출처 가능.
    """
    anomalies: list[Anomaly] = []

    revVals = getAnnualValues(aSeries, "IS", "sales")
    cfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")
    arVals = getAnnualValues(aSeries, "BS", "trade_and_other_receivables")

    # OCF/Revenue 비율 시계열을 한 번 만들고 룰 1·2 가 함께 읽는다.
    ocfRevRatios = _ocfRevenueRatios(revVals, cfVals)

    # 룰 1: OCF/Revenue < 0 (최신기, 매출 흑자인데 영업CF 적자)
    latest = _latestNotNone(ocfRevRatios)
    if latest is not None and latest < 0:
        anomalies.append(
            Anomaly(
                "danger",
                "earningsQuality",
                f"매출 대비 영업CF 적자 (OCF/Revenue={latest:.1%}). 매출 품질 의심",
                latest * 100,
            )
        )

    # 룰 2: OCF/Revenue 3기 연속 하락
    validRatios = [r for r in ocfRevRatios if r is not None]
    if len(validRatios) >= 3:
        decline = _trailingDeclineStreak(validRatios)
        if decline >= 3:
            anomalies.append(
                Anomaly(
                    "warning",
                    "earningsQuality",
                    f"OCF/Revenue {decline}기 연속 하락. 매출 품질 악화 추세",
                    float(decline),
                )
            )

    # 룰 3: 매출채권 증가율 > 매출 증가율 × 1.5 (3기 연속)
    receivable = _receivableGrowthFlag(arVals, revVals)
    if receivable is not None:
        anomalies.append(receivable)

    return anomalies


def _ocfRevenueRatios(revVals: list, cfVals: list) -> list:
    """매출 대비 영업CF 비율 시계열. 분모가 없거나 0 이하면 그 기는 None."""
    n = min(len(revVals), len(cfVals)) if revVals and cfVals else 0
    ratios: list[float | None] = []
    for i in range(n):
        rv = revVals[i]
        cf = cfVals[i]
        if rv is not None and cf is not None and rv > 0:
            ratios.append(cf / rv)
        else:
            ratios.append(None)
    return ratios


def _trailingDeclineStreak(values: list) -> int:
    """최신부터 거슬러 올라가며 직전기 대비 하락이 이어진 기수 (결측 없는 시계열 전제)."""
    streak = 0
    for i in range(len(values) - 1, 0, -1):
        if values[i] < values[i - 1]:
            streak += 1
        else:
            break
    return streak


def _receivableGrowthFlag(arVals: list, revVals: list) -> Anomaly | None:
    """룰 3: 매출채권 증가율이 매출 증가율의 1.5 배를 3 기 연속 넘었는지."""
    if not (arVals and revVals and len(arVals) >= 3 and len(revVals) >= 3):
        return None

    n = min(len(arVals), len(revVals))
    arGrowths: list[float | None] = []
    revGrowths: list[float | None] = []
    for i in range(1, n):
        arPrev, arCurr = arVals[i - 1], arVals[i]
        rvPrev, rvCurr = revVals[i - 1], revVals[i]
        if arPrev and arPrev > 0 and arCurr is not None:
            arGrowths.append((arCurr - arPrev) / arPrev * 100)
        else:
            arGrowths.append(None)
        if rvPrev and rvPrev > 0 and rvCurr is not None:
            revGrowths.append((rvCurr - rvPrev) / rvPrev * 100)
        else:
            revGrowths.append(None)

    # 최근 3기 매출채권 증가 > 매출 × 1.5
    streak = 0
    for i in range(len(arGrowths) - 1, -1, -1):
        ag = arGrowths[i]
        rg = revGrowths[i]
        if ag is not None and rg is not None and rg >= 0 and ag > rg * 1.5 and ag > 10:
            streak += 1
        else:
            break
    if streak < 3:
        return None
    return Anomaly(
        "warning",
        "earningsQuality",
        f"매출채권 증가율 > 매출 증가율×1.5 {streak}기 연속. 수금 품질 의심",
        float(streak),
    )
