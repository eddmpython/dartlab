"""IPO 공모분석 리포트 — 증권신고서(지분증권) 파싱 결과 → 읽을 수 있는 narrative 리포트.

회사 재무 시계열 story 엔진(ReportModel·company panel)은 corp_cls=E(상장 전 IPO)에 데이터원이 없다.
따라서 별 perspective 분기 대신 *자족형* IPO 리포트를 만든다 — 파싱 결과(:func:`parseIpoProspectus`
+ :func:`parseOfferingConfirmation`)를 6 카테고리 섹션 + 항등식 검증 배지 + 비교기업 대비 좌표로 조립한다.

순수 렌더(:func:`renderIpoReport`, fetch 0·테스트 용이)와 fetch 래퍼(:func:`buildIpoReport`)로 분리.
GitHub Discussion #70 의 "IPO 공모분석 리포트 한 편" 요청을 라이브 산출로 충족.
"""

from __future__ import annotations

from dartlab.providers.dart.securitiesRegistration import parseIpoProspectus, parseOfferingConfirmation

__all__ = ["renderIpoReport", "buildIpoReport"]

_BADGE = {True: "✓ 검증", False: "✗ 미검증"}


def _won(v: float | None) -> str:
    """원 → 사람 단위(조/억/만). None 은 '-'."""
    if not v:
        return "-"
    v = float(v)
    if abs(v) >= 1e12:
        return f"{v / 1e12:,.2f}조원"
    if abs(v) >= 1e8:
        return f"{v / 1e8:,.0f}억원"
    if abs(v) >= 1e4:
        return f"{v / 1e4:,.0f}만원"
    return f"{v:,.0f}원"


def _price(v: float | None) -> str:
    return f"{v:,.0f}원" if v else "-"


def _pair(t: tuple | None, fmt=_price, sep=" ~ ") -> str:
    if not t:
        return "-"
    a, b = min(t), max(t)
    return fmt(a) if a == b else f"{fmt(a)}{sep}{fmt(b)}"


def renderIpoReport(
    parsed: dict,
    *,
    corpName: str | None = None,
    rcept: str | None = None,
    rceptDt: str | None = None,
    confirmation: dict | None = None,
) -> dict:
    """파싱 결과 → IPO 공모분석 리포트 (구조화 섹션 + markdown).

    Args:
        parsed: :func:`parseIpoProspectus` 반환 dict.
        corpName: 발행사명 (제목).
        rcept: 접수번호 (원문근거 링크).
        rceptDt: 접수일 (YYYYMMDD).
        confirmation: :func:`parseOfferingConfirmation` 반환(확정공모가) 또는 None.

    Returns:
        dict
            title : str — "{회사명} 공모분석".
            sections : list[dict] — {title, rows[(label,value)], badge}.
            markdown : str — 터미널/랜딩 표시용 전체 리포트.

    Capabilities:
        - 6 카테고리(개요·일정·밸류·유통물량/보호예수·재무·리스크)를 항등식 배지와 함께 리포트화.
        - IPO 자체 implied 멀티플 vs 비교기업 멀티플 좌표, 확정가 vs 밴드 신호.

    Guide:
        - fetch 포함 원스텝은 :func:`buildIpoReport`. 본 함수는 순수(파싱 dict in).

    SeeAlso:
        - :func:`buildIpoReport` — rcept → fetch → 본 렌더.
        - :func:`dartlab.providers.dart.securitiesRegistration.parseIpoProspectus`.

    Requires:
        - parsed dict (parseIpoProspectus 결과).

    AIContext:
        Agent 가 "OO 공모 분석 리포트 보여줘" 류 요청 시 단건 리포트 산출.

    LLM Specifications:
        AntiPatterns:
            - badge 미검증(✗)인 섹션 수치를 확정값으로 단정.
            - implied PER 를 절대 고/저평가 단정 (비교군 기준 좌표).
        OutputSchema:
            - dict: title(str) / sections(list) / markdown(str).
        Prerequisites:
            - parseIpoProspectus 결과 dict.
        Freshness:
            - 신고서 접수 시점 (+ 확정가는 발행조건확정 시점).
        Dataflow:
            - parseIpoProspectus → renderIpoReport → 리포트.
        TargetMarkets:
            - KR (DART 증권신고서 지분증권).
    """
    off = parsed.get("offering", {})
    val = parsed.get("valuation", {})
    fin = parsed.get("financials", {})
    flt = parsed.get("float", {})
    mult = parsed.get("multiples", {})
    ids = parsed.get("identities", {})
    name = corpName or "발행사"
    confirmedPrice = (confirmation or {}).get("confirmedPrice")

    sections: list[dict] = []

    # 1. 공모 개요 + 예상 시가총액
    band = off.get("priceBand")
    bandStr = _pair(band)
    if confirmedPrice and band:
        loc = (
            "밴드 상단" if confirmedPrice >= max(band) else ("밴드 하단" if confirmedPrice <= min(band) else "밴드 내")
        )
        bandStr += f"  → 확정 {confirmedPrice:,.0f}원 ({loc})"
    sections.append(
        {
            "title": "공모 개요",
            "badge": _BADGE.get(ids.get("offeringRawQtyOk")) if "offeringRawQtyOk" in ids else None,
            "rows": [
                ("희망공모가", bandStr),
                ("모집주식수", f"{ids.get('sharesRecovered'):,.0f}주" if ids.get("sharesRecovered") else "-"),
                ("모집총액", _won(off.get("offerTotal"))),
                ("예상 시가총액", _pair(mult.get("marketCap"), fmt=_won)),
            ],
        }
    )

    # 2. 공모 일정
    sections.append(
        {
            "title": "공모 일정",
            "badge": None,
            "rows": [("청약기일", off.get("subscription") or "-"), ("납입기일", off.get("payDate") or "-")],
        }
    )

    # 3. 밸류에이션 (implied vs 비교기업)
    peer = val.get("peerMultiple")
    impPer = mult.get("per")
    perCmp = "-"
    if impPer and peer:
        perCmp = f"{_pair(impPer, fmt=lambda x: f'{x:.1f}배')} (비교기업 {peer:.1f}배 대비 {'저' if max(impPer) < peer else '고'}평가 좌표)"
    sections.append(
        {
            "title": "밸류에이션",
            "badge": _BADGE.get(ids.get("valuationChain")) if "valuationChain" in ids else None,
            "rows": [
                ("적용 평가모형", val.get("model") or "-"),
                ("비교기업 적용 PER", f"{peer:.2f}배" if peer else "-"),
                ("주당 평가가액", _price(val.get("perShareValue"))),
                ("할인율", _pair(val.get("discount"), fmt=lambda x: f"{x:.1f}%")),
                ("IPO implied PER", perCmp),
                (
                    "implied PSR / PBR",
                    f"{_pair(mult.get('psr'), fmt=lambda x: f'{x:.2f}')} / {_pair(mult.get('pbr'), fmt=lambda x: f'{x:.2f}')}",
                ),
            ],
        }
    )

    # 4. 유통가능물량 · 보호예수
    lockups = flt.get("lockups", [])
    lockStr = ", ".join(f"{lu['holder'][:10]} {lu['period']}" for lu in lockups[:4]) + (
        " …" if len(lockups) > 4 else ""
    )
    sections.append(
        {
            "title": "유통가능물량 · 보호예수",
            "badge": _BADGE.get(ids.get("floatBalance")) if "floatBalance" in ids else None,
            "rows": [
                (
                    "상장 직후 유통가능비율",
                    f"{flt.get('freeFloatPct'):.2f}% ({flt.get('freeFloatShares'):,.0f}주)"
                    if flt.get("freeFloatPct")
                    else "-",
                ),
                ("매각제한(보호예수) 물량", f"{flt.get('lockedShares'):,.0f}주" if flt.get("lockedShares") else "-"),
                ("보호예수 해제 일정", lockStr or "-"),
            ],
        }
    )

    # 5. 재무 (최근 연간)
    rows = fin.get("rows", {})
    periods = fin.get("periods", [])
    finRows = []
    if periods:
        finRows.append(("기준 기간", mult.get("annualPeriod") or periods[0]))
    for label in ("매출액", "영업이익", "당기순이익"):
        vals = rows.get(label)
        if vals:
            finRows.append((label, _won(vals[0] * fin.get("unit", 1.0)) if vals[0] is not None else "-"))
    if mult.get("isLoss"):
        finRows.append(("⚠ 리스크", "최근 연간 적자"))
    sections.append(
        {
            "title": "재무 (요약)",
            "badge": _BADGE.get(ids.get("financialsBalance")) if "financialsBalance" in ids else None,
            "rows": finRows or [("재무", "-")],
        }
    )

    # 6. 리스크
    risk = parsed.get("risk", {})
    sections.append(
        {
            "title": "투자위험",
            "badge": None,
            "rows": [("위험 섹션", f"{risk.get('count', 0)}개 ({', '.join(risk.get('sections', [])[:4])})")],
        }
    )

    # ── markdown ──
    lines = [f"# {name} 공모분석", ""]
    src = "증권신고서(지분증권)" + (f" · 접수 {rceptDt}" if rceptDt else "")
    if rcept:
        src += f" · 원문 DART {rcept}"
    lines += [f"> {src}", ""]
    for sec in sections:
        head = f"## {sec['title']}"
        if sec.get("badge"):
            head += f"  〔{sec['badge']}〕"
        lines.append(head)
        for label, value in sec["rows"]:
            lines.append(f"- {label}: {value}")
        lines.append("")
    lines.append(
        "모든 수치는 접수번호 원문에서 직접 추출, 원문 자체 관계식으로 자기검증(〔검증〕 배지). "
        "implied 멀티플·할인율은 비교군 기준 좌표 — 고/저평가 단정 아님."
    )

    return {"title": f"{name} 공모분석", "sections": sections, "markdown": "\n".join(lines)}


def buildIpoReport(rcept: str, *, corpName: str | None = None, confirmationRcept: str | None = None) -> dict:
    """rcept → 증권신고서 본문 fetch → 파싱 → IPO 공모분석 리포트 (원스텝).

    Args:
        rcept: FULL 증권신고서(지분증권) 접수번호. (``[발행조건확정]`` 아님 — confirmationRcept 로 별도.)
        corpName: 발행사명 (제목). 미지정 시 "발행사".
        confirmationRcept: ``[발행조건확정]`` doc 접수번호 (확정공모가 병합) 또는 None.

    Returns:
        dict — :func:`renderIpoReport` 와 동일 (title/sections/markdown). 본문 fetch 실패 시
        markdown 에 사유.

    Capabilities:
        - 단일 rcept → 6 카테고리 IPO 공모분석 리포트 라이브 산출 (원문근거 동반).

    Guide:
        - 전 상장사 횡단 발굴은 :func:`dartlab.scan.ipo.scanIpo`, 본 함수는 단건 deep 리포트.
        - 확정공모가를 합치려면 ``listFilings('발행조건확정')`` 에서 같은 발행사 rcept 를 confirmationRcept 로.

    SeeAlso:
        - :func:`renderIpoReport` — 순수 렌더.
        - :func:`dartlab.scan.ipo.scanIpo` — 횡단 발굴.

    Requires:
        - DART_API_KEYS, ``gather.dart.allFilingsCollector._collectOneRaw``.

    AIContext:
        Agent 가 "OO IPO 공모분석/증권신고서 리포트" 단건 요청 시 dispatch.

    LLM Specifications:
        AntiPatterns:
            - ``[발행조건확정]`` rcept 를 rcept 인자로 (6 섹션 없음 — confirmationRcept 로).
        OutputSchema:
            - dict: title / sections / markdown.
        Prerequisites:
            - FULL 증권신고서 rcept + DART_API_KEYS.
        Freshness:
            - 접수 시점.
        Dataflow:
            - rcept → _collectOneRaw → parseIpoProspectus → renderIpoReport.
        TargetMarkets:
            - KR.
    """
    from dartlab.core.dartClient import DartClient
    from dartlab.gather.dart.allFilingsCollector import _collectOneRaw

    client = DartClient()
    content, status = _collectOneRaw(client, rcept)
    if status != "ok" or not content:
        return {
            "title": f"{corpName or '발행사'} 공모분석",
            "sections": [],
            "markdown": f"# 리포트 생성 실패\n본문 fetch 실패(status={status}).",
        }
    parsed = parseIpoProspectus(content)
    confirmation = None
    if confirmationRcept:
        cContent, cStatus = _collectOneRaw(client, confirmationRcept)
        if cStatus == "ok" and cContent:
            confirmation = parseOfferingConfirmation(cContent)
    return renderIpoReport(parsed, corpName=corpName, rcept=rcept, confirmation=confirmation)
