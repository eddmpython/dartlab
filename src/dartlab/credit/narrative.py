"""7축 신용평가 서사 생성 엔진.

지표값 + 업종 기준표 위치를 조합하여 신평사 수준의 해석 문장을 생성한다.
숫자 나열이 아니라, "왜 이 등급인가"를 읽을 수 있는 문장으로 설명한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AxisNarrative:
    """축별 서사."""

    axisName: str
    summary: str
    details: list[str] = field(default_factory=list)
    severity: str = "adequate"  # strong | adequate | weak | critical

    def toParagraph(self) -> str:
        """details를 연결된 문단으로 조합."""
        if not self.details:
            return self.summary
        # 첫 문장 + details를 자연스럽게 연결
        sentences = [self.summary] + self.details
        return " ".join(sentences)

    @property
    def severityKr(self) -> str:
        return {"strong": "우수", "adequate": "양호", "weak": "주의", "critical": "위험"}.get(
            self.severity, self.severity
        )


def _severity(score: float | None) -> str:
    if score is None:
        return "adequate"
    if score < 10:
        return "strong"
    if score < 25:
        return "adequate"
    if score < 45:
        return "weak"
    return "critical"


def _fmt(v, suffix="", decimals=1) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return f"{v:.{decimals}f}{suffix}"
    return f"{v}{suffix}"


def _fmtTril(v) -> str:
    """금액을 조/억 단위로 변환."""
    if v is None:
        return "N/A"
    absV = abs(v)
    sign = "-" if v < 0 else ""
    if absV >= 1e12:
        return f"{sign}{absV / 1e12:,.1f}조원"
    if absV >= 1e8:
        return f"{sign}{absV / 1e8:,.0f}억원"
    return f"{sign}{absV:,.0f}원"


# ═══════════════════════════════════════════════════════════
# 축별 서사 생성
# ═══════════════════════════════════════════════════════════


def narrateRepayment(latest: dict, axisScore: float | None, sectorLabel: str) -> AxisNarrative:
    """축 1: 채무상환능력."""
    details = []
    sev = _severity(axisScore)

    # 금액 맥락
    ebitda = latest.get("ebitda")
    totalBorrowing = latest.get("totalBorrowing")
    revenue = latest.get("revenue")

    if ebitda is not None and revenue is not None:
        if ebitda > 0:
            details.append(f"매출 {_fmtTril(revenue)} 기반 EBITDA {_fmtTril(ebitda)}을 창출한다.")
        elif ebitda < 0:
            details.append(
                f"매출 {_fmtTril(revenue)} 대비 EBITDA {_fmtTril(ebitda)}로 본업에서 적자다. "
                f"다만 이는 지주사/특수 구조에서는 배당수입 등 영업외 현금흐름으로 보완될 수 있다."
            )

    icr = latest.get("ebitdaInterestCoverage")
    if icr is not None:
        if icr >= 100:
            # 이자비용이 극소 — "999배"보다 의미 있는 표현
            if totalBorrowing:
                details.append(
                    f"총차입금 {_fmtTril(totalBorrowing)} 대비 이자 부담이 사실상 없어 무차입에 준하는 재무구조다."
                )
            else:
                details.append("이자 부담이 사실상 없어 무차입에 준하는 재무구조다.")
        elif icr > 10:
            details.append(f"이자보상배율 {_fmt(icr)}배로 충분한 이자 지급 여력을 보유한다.")
        elif icr > 5:
            details.append(f"이자보상배율 {_fmt(icr)}배로 양호한 채무상환 여력이 있다.")
        elif icr > 2:
            details.append(f"이자보상배율 {_fmt(icr)}배로 이자 지급은 가능하나 여유는 제한적이다.")
        elif icr > 1:
            details.append(f"이자보상배율 {_fmt(icr)}배로 이자 지급 여력이 빠듯하다. 수익성 악화 시 위험.")
        else:
            details.append(f"이자보상배율 {_fmt(icr)}배로 이자 지급 능력이 부족하다.")

    de = latest.get("debtToEbitda")
    if de is not None:
        if de < 1:
            details.append(f"Debt/EBITDA {_fmt(de)}배로 차입금을 1년 내 상환 가능한 수준이다.")
        elif de < 3:
            details.append(f"Debt/EBITDA {_fmt(de)}배로 차입금 부담이 적정하다.")
        elif de < 5:
            details.append(f"Debt/EBITDA {_fmt(de)}배로 차입금 부담이 다소 높다.")
        else:
            details.append(f"Debt/EBITDA {_fmt(de)}배로 차입금 상환에 장기간이 소요된다.")

    ffo = latest.get("ffoToDebt")
    if ffo is not None and ffo < 999:
        if ffo > 40:
            details.append(f"FFO/총차입금 {_fmt(ffo, '%', 0)}로 우수한 내부 현금 창출력을 보인다.")
        elif ffo > 20:
            details.append(f"FFO/총차입금 {_fmt(ffo, '%', 0)}로 양호한 부채상환 능력이다.")
        elif ffo > 10:
            details.append(f"FFO/총차입금 {_fmt(ffo, '%', 0)}로 부채상환 능력이 제한적이다.")
        elif ffo > 0:
            details.append(f"FFO/총차입금 {_fmt(ffo, '%', 0)}로 부채상환 능력이 취약하다.")

    summary = f"채무상환능력은 {sectorLabel} 업종 기준 "
    if sev == "strong":
        summary += "매우 우수하다."
    elif sev == "adequate":
        summary += "양호한 수준이다."
    elif sev == "weak":
        summary += "보통 이하 수준으로 모니터링이 필요하다."
    else:
        summary += "취약하여 즉각적인 개선이 요구된다."

    return AxisNarrative("채무상환능력", summary, details, sev)


def narrateCapitalStructure(latest: dict, axisScore: float | None) -> AxisNarrative:
    """축 2: 자본구조."""
    details = []
    sev = _severity(axisScore)

    dr = latest.get("debtRatio")
    if dr is not None:
        if dr < 50:
            details.append(f"부채비율 {_fmt(dr, '%', 0)}로 재무구조가 매우 보수적이다.")
        elif dr < 100:
            details.append(f"부채비율 {_fmt(dr, '%', 0)}로 건전한 재무구조를 유지한다.")
        elif dr < 200:
            details.append(f"부채비율 {_fmt(dr, '%', 0)}로 적정 수준의 레버리지를 활용한다.")
        elif dr < 300:
            details.append(f"부채비율 {_fmt(dr, '%', 0)}로 레버리지가 다소 높은 편이다.")
        else:
            details.append(f"부채비율 {_fmt(dr, '%', 0)}로 과도한 레버리지를 사용하고 있다.")

    bd = latest.get("borrowingDependency")
    if bd is not None:
        if bd > 30:
            details.append(f"차입금의존도 {_fmt(bd, '%', 0)}로 외부 자금 의존도가 높다.")
        elif bd > 15:
            details.append(f"차입금의존도 {_fmt(bd, '%', 0)}로 적정 수준이다.")

    nde = latest.get("netDebtToEbitda")
    if nde is not None:
        if nde < 0:
            details.append("순차입금이 마이너스(순현금 포지션)로 실질적 부채 부담이 없다.")
        elif nde < 2:
            details.append(f"순차입금/EBITDA {_fmt(nde)}배로 실질 부채 부담이 낮다.")

    summary = "자본구조는 "
    if sev == "strong":
        summary += "매우 건전하다."
    elif sev == "adequate":
        summary += "양호하다."
    elif sev == "weak":
        summary += "레버리지 부담이 있다."
    else:
        summary += "과도한 부채로 구조적 위험이 존재한다."

    return AxisNarrative("자본구조", summary, details, sev)


def narrateLiquidity(latest: dict, axisScore: float | None) -> AxisNarrative:
    """축 3: 유동성."""
    details = []
    sev = _severity(axisScore)

    cr = latest.get("currentRatio")
    if cr is not None:
        if cr > 200:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 매우 우수하다.")
        elif cr > 150:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 양호하다.")
        elif cr > 100:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 적정하다.")
        else:
            details.append(f"유동비율 {_fmt(cr, '%', 0)}로 단기 유동성이 부족하다.")

    stdr = latest.get("shortTermDebtRatio")
    if stdr is not None and stdr > 50:
        details.append(f"단기차입금 비중 {_fmt(stdr, '%', 0)}로 차환 리스크가 존재한다.")

    cashR = latest.get("cashRatio")
    if cashR is not None and cashR > 30:
        details.append(f"현금비율 {_fmt(cashR, '%', 0)}로 즉시 동원 가능한 현금이 충분하다.")

    # 유동성 지표 모순 설명: 유동비율/현금비율은 좋은데 단기차입금비중이 높은 경우
    if cr is not None and cr > 150 and stdr is not None and stdr > 50:
        details.append(
            f"유동비율({_fmt(cr, '%', 0)})과 현금비율은 우수하나, "
            f"단기차입금 비중({_fmt(stdr, '%', 0)})이 높아 차환 시점의 유동성 관리가 필요하다. "
            f"현금 보유량이 충분하므로 실질적 차환 위험은 낮다."
        )

    summary = "유동성은 "
    if sev == "strong":
        summary += "매우 충분하다."
    elif sev == "adequate":
        summary += "적정 수준이다."
    elif sev == "weak":
        summary += "주의가 필요한 수준이다."
    else:
        summary += "부족하여 차환/유동성 위험이 높다."

    return AxisNarrative("유동성", summary, details, sev)


def narrateCashFlow(latest: dict, axisScore: float | None, metrics: dict) -> AxisNarrative:
    """축 4: 현금흐름."""
    details = []
    sev = _severity(axisScore)

    os = latest.get("ocfToSales")
    if os is not None:
        if os > 100:
            # 지주사 등: 매출 < OCF (배당수입/지분법이 OCF에 포함)
            details.append(
                f"OCF/매출 {_fmt(os, '%')}로 자체 매출 대비 현금흐름이 매우 크다. "
                f"이는 자회사 배당수입 등 영업외 현금이 포함된 것으로 판단된다."
            )
        elif os > 15:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 매출 대비 현금 창출력이 우수하다.")
        elif os > 5:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 현금 창출이 양호하다.")
        elif os > 0:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 현금 창출이 제한적이다.")
        else:
            details.append(f"OCF/매출 {_fmt(os, '%')}로 영업에서 현금이 유출되고 있다.")

    fcf = latest.get("fcf")
    if fcf is not None:
        if fcf > 0:
            details.append("투자 이후에도 잉여현금흐름(FCF)이 양수로 자체 성장 여력이 있다.")
        else:
            details.append("투자 부담으로 잉여현금흐름(FCF)이 음수이다.")

    # OCF 추세
    history = metrics.get("history", [])
    if len(history) >= 3:
        ocfs = [h.get("ocf") for h in history[:3]]
        if all(o is not None and o > 0 for o in ocfs):
            details.append("영업현금흐름이 3기 연속 양수로 안정적이다.")

    summary = "현금흐름 창출 능력은 "
    if sev == "strong":
        summary += "우수하다."
    elif sev == "adequate":
        summary += "양호하다."
    elif sev == "weak":
        summary += "보통 수준이다."
    else:
        summary += "취약하여 외부 조달 의존도가 높다."

    return AxisNarrative("현금흐름", summary, details, sev)


def narrateBusinessStability(biz: dict, axisScore: float | None) -> AxisNarrative:
    """축 5: 사업 안정성."""
    details = []
    sev = _severity(axisScore)

    revCV = biz.get("revenueCV")
    if revCV is not None:
        if revCV < 10:
            details.append(f"매출 변동계수 {_fmt(revCV, '%')}로 매출이 매우 안정적이다.")
        elif revCV < 20:
            details.append(f"매출 변동계수 {_fmt(revCV, '%')}로 적정한 안정성을 보인다.")
        else:
            details.append(f"매출 변동계수 {_fmt(revCV, '%')}로 실적 변동성이 크다.")

    latestRev = biz.get("latestRevenue")
    if latestRev is not None:
        revTril = latestRev / 1e12
        if revTril > 10:
            details.append(f"매출 규모 {revTril:.0f}조원으로 대형 기업의 사업 안정성을 보유한다.")
        elif revTril > 1:
            details.append(f"매출 규모 {revTril:.1f}조원 수준이다.")

    hhi = biz.get("segmentHHI")
    if hhi is not None:
        if hhi < 1500:
            details.append("사업 부문이 분산되어 다각화 효과가 있다.")
        elif hhi > 5000:
            details.append("사업이 단일 부문에 집중되어 있어 분산 효과가 제한적이다.")

    summary = "사업 안정성은 "
    if sev == "strong":
        summary += "매우 높다."
    elif sev == "adequate":
        summary += "양호한 수준이다."
    else:
        summary += "변동성이 존재한다."

    return AxisNarrative("사업안정성", summary, details, sev)


def narrateReliability(rel: dict, auditOpinion: str | None, axisScore: float | None) -> AxisNarrative:
    """축 6: 재무 신뢰성."""
    details = []
    sev = _severity(axisScore)

    m = rel.get("beneishMScore")
    if m is not None:
        if m < -2.22:
            details.append("Beneish M-Score 기준 이익 조작 가능성이 낮다.")
        elif m > -1.78:
            details.append("Beneish M-Score가 조작 가능성 구간에 해당하여 주의가 필요하다.")

    f = rel.get("piotroskiFScore")
    if f is not None:
        if f >= 7:
            details.append(f"Piotroski F-Score {f}/9로 재무 펀더멘탈이 강건하다.")
        elif f <= 3:
            details.append(f"Piotroski F-Score {f}/9로 재무 펀더멘탈이 취약하다.")

    if auditOpinion:
        if "적정" in auditOpinion and "부적정" not in auditOpinion and "한정" not in auditOpinion:
            details.append("감사의견은 적정으로 재무제표 신뢰성에 문제가 없다.")
        elif "한정" in auditOpinion:
            details.append("감사의견이 한정으로 재무제표 일부 항목에 대한 신뢰성 우려가 있다.")
        elif "부적정" in auditOpinion or "의견거절" in auditOpinion:
            details.append("감사의견이 비적정으로 재무제표 전반의 신뢰성에 심각한 문제가 있다.")

    summary = "재무 신뢰성은 "
    if sev == "strong":
        summary += "우수하다."
    elif sev == "adequate":
        summary += "양호하다."
    else:
        summary += "주의가 필요하다."

    return AxisNarrative("재무신뢰성", summary, details, sev)


def narrateDisclosureRisk(dr: dict | None, axisScore: float | None) -> AxisNarrative:
    """축 7: 공시 리스크."""
    details = []
    sev = _severity(axisScore)

    if dr is None:
        return AxisNarrative(
            "공시리스크", "공시 리스크 신호가 감지되지 않았다.", ["scan 데이터 범위 내 특이 신호 없음."], "strong"
        )

    chronic = dr.get("chronicYears") or dr.get("chronic_years", 0)
    if chronic >= 3:
        details.append(f"우발부채가 {chronic}년 연속 증가하여 만성화 징후가 있다.")
    elif chronic >= 1:
        details.append("우발부채가 증가 추세이나 아직 만성 수준은 아니다.")

    risk = dr.get("riskKeyword") or dr.get("risk_keyword", 0)
    if risk > 0:
        details.append(f"리스크 키워드(횡령/배임/과징금 등)가 {risk}건 감지되었다.")

    if not details:
        details.append("특이한 공시 리스크 신호는 감지되지 않았다.")

    summary = "공시 리스크는 "
    if sev == "strong":
        summary += "낮은 수준이다."
    elif sev == "adequate":
        summary += "양호하다."
    else:
        summary += "모니터링이 필요하다."

    return AxisNarrative("공시리스크", summary, details, sev)


# ═══════════════════════════════════════════════════════════
# 통합
# ═══════════════════════════════════════════════════════════


def buildNarratives(result: dict) -> list[AxisNarrative]:
    """engine.py evaluateCompany 결과에서 7축 전체 서사 생성."""
    axes = result.get("axes", [])
    latest = {}
    metricsHistory = result.get("metricsHistory", [])
    if metricsHistory:
        latest = metricsHistory[0]

    biz = result.get("businessStability", {})
    rel = result.get("reliability", {})
    audit = result.get("auditOpinion")
    dr = result.get("disclosureRisk")
    sector = result.get("sector", "")

    def _axisScore(name):
        for a in axes:
            if a.get("name") == name:
                return a.get("score")
        return None

    return [
        narrateRepayment(latest, _axisScore("채무상환능력"), sector),
        narrateCapitalStructure(latest, _axisScore("자본구조")),
        narrateLiquidity(latest, _axisScore("유동성")),
        narrateCashFlow(latest, _axisScore("현금흐름"), {"history": metricsHistory}),
        narrateBusinessStability(biz or {}, _axisScore("사업안정성")),
        narrateReliability(rel or {}, audit, _axisScore("재무신뢰성")),
        narrateDisclosureRisk(dr, _axisScore("공시리스크")),
    ]


def narrateProfile(profile: dict | None, segments: dict | None, rank: dict | None) -> str:
    """기업 개요 서사 — 이 회사가 뭘 하는 회사인가."""
    parts = []

    # 업종 + 주요제품
    if profile:
        sector = profile.get("sector", "")
        products = profile.get("products", "")
        if sector:
            parts.append(sector.replace("섹터: ", ""))
        if products:
            parts.append(products.replace("주요제품: ", "주요 사업: "))

    # 부문 구성
    if segments and segments.get("segments"):
        segs = segments["segments"]
        total = segments.get("totalRevenue", 0)
        if total > 0 and segs:
            segParts = []
            for s in segs[:3]:
                name = s.get("name", "")
                rev = s.get("revenue", 0)
                share = rev / total * 100 if total > 0 else 0
                if share > 5:
                    margin = s.get("opMargin")
                    marginStr = f"(영업이익률 {margin:.1f}%)" if margin is not None else ""
                    segParts.append(f"{name} {share:.0f}%{marginStr}")
            if segParts:
                parts.append("부문 구성: " + ", ".join(segParts))

    # 업종 내 순위
    if rank:
        sectorRank = rank.get("revenueRankInSector")
        sectorTotal = rank.get("revenueSectorTotal")
        sizeClass = rank.get("sizeClass", "")
        if sectorRank and sectorTotal:
            sizeKr = {"large": "대형", "mid": "중형", "small": "소형"}.get(sizeClass, "")
            parts.append(f"업종 내 매출 {sectorRank}/{sectorTotal}위 ({sizeKr})")

    return " | ".join(parts) if parts else ""


def narrateTrend(history: list[dict]) -> str:
    """전기 대비 추세 해석 — 핵심 지표의 개선/악화."""
    if len(history) < 2:
        return ""

    h0, h1 = history[0], history[1]
    parts = []

    # 매출 전년비
    rev0, rev1 = h0.get("revenue"), h1.get("revenue")
    if rev0 and rev1 and rev1 != 0:
        chg = (rev0 - rev1) / abs(rev1) * 100
        direction = "증가" if chg > 0 else "감소"
        parts.append(f"매출 전년비 {'+' if chg > 0 else ''}{chg:.0f}% {direction}")

    # 영업이익 전년비
    oi0, oi1 = h0.get("operatingIncome"), h1.get("operatingIncome")
    if oi0 and oi1 and oi1 != 0:
        chg = (oi0 - oi1) / abs(oi1) * 100
        if abs(chg) > 30:
            direction = "대폭 개선" if chg > 0 else "대폭 악화"
            parts.append(f"영업이익 {'+' if chg > 0 else ''}{chg:.0f}% ({direction})")

    # Debt/EBITDA 변화
    de0, de1 = h0.get("debtToEbitda"), h1.get("debtToEbitda")
    if de0 is not None and de1 is not None:
        if de0 < de1:
            parts.append(f"Debt/EBITDA {de1:.1f}→{de0:.1f}배로 개선")
        elif de0 > de1 * 1.2:
            parts.append(f"Debt/EBITDA {de1:.1f}→{de0:.1f}배로 악화")

    # 부채비율 변화
    dr0, dr1 = h0.get("debtRatio"), h1.get("debtRatio")
    if dr0 is not None and dr1 is not None:
        delta = dr0 - dr1
        if abs(delta) > 5:
            direction = "상승" if delta > 0 else "하락"
            parts.append(f"부채비율 {dr1:.0f}%→{dr0:.0f}%로 {direction}")

    if not parts:
        return "전기 대비 핵심 지표 변동이 제한적이다."

    # 3~5년 시계열 스토리 추가
    if len(history) >= 4:
        deList = [h.get("debtToEbitda") for h in history[:5]]
        validDe = [(i, v) for i, v in enumerate(deList) if v is not None]
        if len(validDe) >= 3:
            values = [v for _, v in validDe]
            peak = max(values)
            trough = min(values)
            peakIdx = values.index(peak)
            troughIdx = values.index(trough)
            periods = [h.get("period", "") for h in history[:5]]

            if peak > trough * 2 and peakIdx > troughIdx:
                # 악화 후 개선 (V자)
                parts.append(
                    f"Debt/EBITDA가 {periods[troughIdx]}년 {trough:.1f}배에서 "
                    f"{periods[peakIdx]}년 {peak:.1f}배까지 악화 후 "
                    f"{periods[0]}년 {values[0]:.1f}배로 회복."
                )
            elif all(values[i] >= values[i + 1] for i in range(len(values) - 1)):
                parts.append(f"Debt/EBITDA가 {len(values)}개년 연속 개선 추세.")
            elif all(values[i] <= values[i + 1] for i in range(len(values) - 1)):
                parts.append(f"Debt/EBITDA가 {len(values)}개년 연속 악화 추세.")

    return " ".join(parts) + "."


def narrateBorrowings(borrowingsDetail: list[dict] | None, latest: dict | None) -> str:
    """차입금 구성 분석 — 만기/종류별."""
    if latest is None:
        return ""

    totalBorrowing = latest.get("totalBorrowing")
    cashVal = latest.get("cash") if "cash" in (latest or {}) else None
    # cash가 latest에 없으면 history에서 추출 시도
    if cashVal is None:
        # netDebt = totalBorrowing - cash → cash = totalBorrowing - netDebt
        netDebt = latest.get("netDebt")
        if totalBorrowing and netDebt is not None:
            cashVal = totalBorrowing - netDebt

    if not totalBorrowing or totalBorrowing <= 0:
        return "차입금이 없거나 극소하여 부채 구성 분석이 불필요하다."

    parts = []
    parts.append(f"총차입금 {_fmtTril(totalBorrowing)}.")

    # 단기/장기 비중
    stRatio = latest.get("shortTermDebtRatio")
    if stRatio is not None:
        ltRatio = 100 - stRatio
        stAmt = totalBorrowing * stRatio / 100
        ltAmt = totalBorrowing * ltRatio / 100
        parts.append(f"단기 {stRatio:.0f}%({_fmtTril(stAmt)}), 장기 {ltRatio:.0f}%({_fmtTril(ltAmt)}).")

    # 현금 대비
    if cashVal and cashVal > 0:
        ratio = cashVal / totalBorrowing
        if ratio > 2:
            parts.append(f"현금 보유({_fmtTril(cashVal)})가 총차입금의 {ratio:.1f}배로 차환 위험이 매우 낮다.")
        elif ratio > 1:
            parts.append(f"현금({_fmtTril(cashVal)})이 총차입금을 상회하여 차환 여력이 있다.")
        else:
            parts.append(f"현금({_fmtTril(cashVal)})이 총차입금의 {ratio:.0%}로 차환 시 외부 조달이 필요할 수 있다.")

    return " ".join(parts)


def narrateCausalChain(latest: dict, result: dict) -> str:
    """6막 인과 연결 — dartlab 핵심 사상을 credit에 적용.

    매출 → 이익 → 현금 → 안정성 → 등급의 인과 체인.
    앞이 뒤의 원인이다.

    지주사/영업적자 등 특수 케이스를 별도 처리한다.
    """
    parts = []
    grade = result.get("grade", "?")
    isHolding = result.get("holding", False)

    rev = latest.get("revenue")
    oi = latest.get("operatingIncome")
    ebitda = latest.get("ebitda")
    ocf = latest.get("ocf")
    netDebt = latest.get("netDebt")
    debtRatio = latest.get("debtRatio")

    # 지주사 특수 경로: 매출이 작고 OCF가 배당/지분법 중심
    if isHolding and rev and ocf and ocf > rev * 0.5:
        parts.append(f"지주사로서 자체 매출 {_fmtTril(rev)}")
        if ocf > 0:
            parts.append(f"자회사 배당 등으로 OCF {_fmtTril(ocf)} 확보")
        if netDebt is not None and netDebt <= 0:
            parts.append("순현금 포지션으로 재무 안정성이 높다.")
        elif debtRatio is not None:
            parts.append(f"부채비율 {debtRatio:.0f}%.")
        if parts:
            chain = ", ".join(parts)
            return f"인과 요약: {chain} 종합 {grade}."
        return ""

    # 일반 기업 경로
    # 1막→2막: 매출 → 이익
    if rev and rev > 0:
        parts.append(f"매출 {_fmtTril(rev)}")
        if oi is not None:
            margin = oi / rev * 100
            if oi < 0:
                parts.append(f"영업적자(이익률 {margin:.0f}%)로 본업 수익성이 부진하나")
            elif margin > 15:
                parts.append(f"영업이익률 {margin:.0f}%로 수익성이 높아")
            elif margin > 5:
                parts.append(f"영업이익률 {margin:.0f}%로")
            else:
                parts.append(f"영업이익률 {margin:.0f}%에 불과하여")

    # 2막→3막: 이익 → 현금
    if ocf is not None:
        if ebitda is not None and ebitda > 0 and ocf > 0:
            if ocf > ebitda:
                parts.append(f"EBITDA {_fmtTril(ebitda)} 이상의 현금(OCF {_fmtTril(ocf)})을 창출하고")
            else:
                parts.append(f"OCF {_fmtTril(ocf)}를 창출하며")
        elif ocf > 0:
            parts.append(f"OCF {_fmtTril(ocf)}를 확보하고")
        else:
            parts.append("영업에서 현금이 유출되어")

    # 3막→4막: 현금 → 안정성
    if netDebt is not None:
        if netDebt <= 0:
            parts.append("순현금 포지션을 유지한다.")
        elif debtRatio is not None and debtRatio < 100:
            parts.append(f"부채비율 {debtRatio:.0f}%로 안정적이다.")
        elif debtRatio is not None:
            parts.append(f"부채비율 {debtRatio:.0f}%로 레버리지 부담이 있다.")

    # 결론
    if parts:
        chain = " → ".join(parts[:2]) + ", " + " → ".join(parts[2:]) if len(parts) > 2 else " → ".join(parts)
        return f"인과 요약: {chain} 종합 {grade}."

    return ""


def buildOverallNarrative(result: dict, narratives: list[AxisNarrative]) -> str:
    """등급 근거 종합 서사 — 강점/약점 구분."""
    grade = result.get("grade", "?")
    score = result.get("score", 0)

    strengths = [n for n in narratives if n.severity == "strong"]
    weaknesses = [n for n in narratives if n.severity in ("weak", "critical")]

    parts = [f"종합 신용등급 {grade} (점수 {score:.1f}/100)."]

    if strengths:
        names = ", ".join(n.axisName for n in strengths)
        parts.append(f"핵심 강점은 {names}이다.")

    if weaknesses:
        names = ", ".join(n.axisName for n in weaknesses)
        parts.append(f"주요 약점은 {names}으로 등급 하방 압력 요인이다.")

    if result.get("captiveFinance"):
        parts.append("캡티브 금융 복합기업으로 연결 재무제표의 구조적 왜곡이 존재한다.")

    if result.get("holding"):
        parts.append("지주사 구조로 지분법손익이 실적에 영향을 미친다.")

    return " ".join(parts)
