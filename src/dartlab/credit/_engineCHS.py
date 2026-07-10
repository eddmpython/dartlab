"""CHS (Campbell-Hilscher-Szilagyi) 부도확률 보정 헬퍼 — engine.py 의 evaluateCompany 호출.

_chsSkip: 데이터 결손 시 structured unavailable dict 반환.
_calcCHSAdjustment: 주가 + 재무 입력 → synth.distress.calcCHS 호출 → 기본 점수 ±2 notch 보정.

분리 사유: engine.py god module 분리 (1174줄 → 단계적 감축).
"""

from __future__ import annotations

from dartlab.credit._engineConfig import _CHS_PD_BRACKETS, _CONFIG


def _chsPdToScore(pd: float) -> int:
    """CHS 부도확률 → 0-100 스코어 매핑."""
    for threshold, score in _CHS_PD_BRACKETS:
        if pd <= threshold:
            return score
    return 80


def _chsSkip(reason: str) -> dict:
    """CHS 보정 스킵 결과 — 호출부가 사유 추적 가능하도록 structured dict 반환."""
    return {"status": "unavailable", "reason": reason, "adjustedScore": None, "adjustment": 0}


def _calcCHSAdjustment(company, baseScore: float) -> dict:
    """CHS 부도확률 모델로 기본 점수를 ±2 notch 범위 보정.

    Returns
    -------
    dict
        status : str — "ok" 면 보정 적용, "unavailable" 이면 데이터·계산 실패.
        reason : str — unavailable 시 사유 (price_insufficient / finance_missing / shares_unknown 등).
        adjustedScore : float | None — ok 시 보정 후 점수, unavailable 시 None.
        chsScore : float — ok 시 PD → 점수 환산값.
        chsPd : float — ok 시 부도확률.
        adjustment : float — ok 시 적용 조정치 (0 if unavailable).
    """
    try:
        from dartlab.synth.distress import calcCHS

        # 시세를 못 얻는 환경이 있다. 브라우저(pyodide)는 스레드를 못 띄워 gather 가 RuntimeError
        # 를 내고, 오프라인에서는 OSError 가 난다. CHS 보정은 부가 기능이므로 그때는 보정만
        # 건너뛴다. 여기서 예외가 새면 credit 호출 전체가 죽는다.
        try:
            priceData = company.gather("price") if hasattr(company, "gather") else None
        except (RuntimeError, OSError, ImportError, ValueError, KeyError, AttributeError):
            return _chsSkip("price_unavailable")
        if priceData is None or len(priceData) < 20:
            return _chsSkip("price_insufficient")

        bs = company.select("BS", ["자산총계", "부채총계", "현금및현금성자산", "현금및예치금"])
        is_ = company.select("IS", ["당기순이익"])
        from dartlab.core.utils.helpers import toDictBySnakeId

        bsParsed = toDictBySnakeId(bs)
        isParsed = toDictBySnakeId(is_)
        if not bsParsed or not isParsed:
            return _chsSkip("finance_missing")

        bsData, periods = bsParsed
        isData, _ = isParsed

        # 최신 기간
        p = sorted(periods, reverse=True)[0] if periods else None
        if not p:
            return _chsSkip("no_period")

        ta = (bsData.get("자산총계", {}) or {}).get(p)
        tl = (bsData.get("부채총계", {}) or {}).get(p)
        cash = (bsData.get("현금및현금성자산", {}) or bsData.get("현금및예치금", {}) or {}).get(p)
        ni = (isData.get("당기순이익", {}) or {}).get(p)

        if not all(v is not None and v != 0 for v in [ta, tl]):
            return _chsSkip("assets_or_liabilities_missing")

        # 주가 데이터에서 시가총액, 변동성, 수익률 추출
        prices = priceData.sort("date") if "date" in priceData.columns else priceData
        closeCol = "close" if "close" in prices.columns else "종가"
        if closeCol not in prices.columns:
            return _chsSkip("close_column_missing")

        closes = prices[closeCol].drop_nulls().to_list()
        if len(closes) < 20:
            return _chsSkip("close_series_too_short")

        latestPrice = closes[-1]
        if latestPrice <= 0:
            return _chsSkip("latest_price_nonpositive")

        # 주식수 추정: EPS 역산 (가장 신뢰)
        shares = None
        try:
            epsData = company.select("IS", ["기본주당이익", "당기순이익"])
            if epsData is not None:
                from dartlab.core.utils.helpers import toDictBySnakeId

                epsParsed = toDictBySnakeId(epsData)
                if epsParsed:
                    epsDict, epsPeriods = epsParsed
                    eps = (epsDict.get("기본주당이익", {}) or {}).get(epsPeriods[0] if epsPeriods else "")
                    niForEps = (epsDict.get("당기순이익", {}) or {}).get(epsPeriods[0] if epsPeriods else "")
                    if eps and abs(eps) > 0 and niForEps:
                        shares = abs(niForEps / eps)
        except (TypeError, ValueError, KeyError, AttributeError, ZeroDivisionError):
            pass

        # fallback: 자본/주가
        if not shares:
            eq = ta - tl if ta and tl else None
            shares = eq / latestPrice if eq and latestPrice > 0 else None
        if not shares or shares <= 0:
            return _chsSkip("shares_unknown")

        marketCap = shares * latestPrice

        # 변동성 (연환산 일별 수익률 표준편차)
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes)) if closes[i - 1] != 0]
        if len(returns) < 10:
            return _chsSkip("returns_series_too_short")
        mean_r = sum(returns) / len(returns)
        var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        sigma = (var_r**0.5) * (252**0.5)

        exret = (closes[-1] / closes[0] - 1) if closes[0] != 0 else 0

        chsResult = calcCHS(
            netIncome=ni,
            totalLiabilities=tl,
            cash=cash,
            totalAssets=ta,
            marketCap=marketCap,
            equityVolatility=sigma,
            excessReturn=exret,
            stockPrice=latestPrice,
        )

        if chsResult is None:
            return _chsSkip("chs_model_returned_none")

        # CHS PD → 점수 매핑 (0-100 스케일)
        chsPd = chsResult.probability
        chsScore = _chsPdToScore(chsPd)

        # PD 기반 비대칭 조정 — 안전 기업 상향, 위험 기업 하향
        diff = chsScore - baseScore
        if chsPd <= 0.001:  # 극안전 (AAA급 PD)
            adj = max(-5.0, diff * 0.3)
        elif chsPd <= 0.01:  # 투자적격 확실 — 상향만 허용
            adj = max(-3.0, min(0, diff * 0.2))
        elif chsPd > 0.10:  # 부실 신호 — 하향만
            adj = min(5.0, max(0, diff * 0.2))
        else:  # 중간 대역
            adj = max(min(diff * 0.15, 3.0), -3.0)
        # 안전장치: BB 이하(score>40)이면 CHS 상향 제한
        if baseScore > 40:
            adj = max(adj, -3.0)
        # 안전장치: AA 이상(score<10)이면 CHS 하향 최대 +1점 (우량 기업 보호)
        if baseScore < 10 and adj > 0:
            adj = min(adj, _CONFIG["chs_safe_max_down"])

        return {
            "status": "ok",
            "adjustedScore": round(baseScore + adj, 2),
            "chsScore": chsScore,
            "chsPd": chsPd,
            "adjustment": round(adj, 2),
        }
    except (ImportError, TypeError, ValueError, KeyError, AttributeError, ZeroDivisionError) as exc:
        return _chsSkip(f"calc_error:{type(exc).__name__}")


__all__ = ["_calcCHSAdjustment", "_chsSkip"]
