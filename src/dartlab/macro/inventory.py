"""매크로 재고순환 분석 — ISM 재고사이클 + 자산배분 바로미터.

투자전략 7: 재고 흐름이 예상하지 못한 성과를 결정한다
투자전략 8: 재고순환지표로 주가 상승을 예측하자
투자전략 13: ISM지수가 세계 자산배분의 바로미터다
투자전략 34: ISM제조업지수가 55를 하회하면 미국 금리인상 종결
"""

from __future__ import annotations

from dartlab.core.finance.inventoryCycle import classifyInventoryPhase, ismBarometer
from dartlab.core.finance.sentiment import ismAssetAllocation


def _fetch_ism_data(market: str) -> dict[str, float | None]:
    """gather에서 ISM/재고 지표 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    data: dict[str, float | None] = {}

    if market.upper() == "US":
        # ISM PMI
        for label, sid in [
            ("ism_pmi", "NAPM"),
            ("ism_new_orders", "NAPMNOI"),
            ("ism_inventories", "NAPMII"),
            ("new_orders", "NEWORDER"),
            ("inventories", "BUSINV"),
        ]:
            try:
                df = g.macro(sid)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls()
                    if len(vals) > 0:
                        data[label] = float(vals[-1])
                        # 이전 기간 값도 저장 (모멘텀용)
                        if len(vals) > 1:
                            data[f"{label}_prev"] = float(vals[-2])
            except Exception:
                pass
    else:
        # KR: 광공업생산(출하 프록시) + BSI(재고판단 프록시)
        # ECOS에서 출하/재고지수 직접 미제공(KOSIS 전용)
        for label, sid in [
            ("manufacturing", "MANUFACTURING"),  # 광공업생산 = 출하 프록시
            ("bsi", "BSI_ALL"),  # BSI 전산업 = 재고판단 프록시 (50 기준)
        ]:
            try:
                df = g.macro(sid)
                if df is not None and len(df) > 0:
                    vals = df.get_column("value").drop_nulls()
                    if len(vals) > 0:
                        data[label] = float(vals[-1])
                        if len(vals) > 1:
                            data[f"{label}_prev"] = float(vals[-2])
            except Exception:
                pass

    return data


def analyze_inventory(*, market: str = "US", **kwargs) -> dict:
    """재고순환 종합 분석.

    Returns:
        dict: inventoryPhase, ismBarometer, ismAllocation, timeseries
    """
    data = _fetch_ism_data(market)
    result: dict = {"market": market.upper()}

    if market.upper() == "US":
        # ISM 기반 재고순환
        new_orders = data.get("ism_new_orders")
        inventories = data.get("ism_inventories")
        if new_orders is not None and inventories is not None:
            prev_no = data.get("ism_new_orders_prev")
            prev_inv = data.get("ism_inventories_prev")
            prev_ratio = (prev_no / prev_inv) if prev_no and prev_inv and prev_inv > 0 else None
            phase = classifyInventoryPhase(new_orders, inventories, prev_ratio)
            result["inventoryPhase"] = {
                "phase": phase.phase,
                "phaseLabel": phase.phaseLabel,
                "ratio": phase.ratio,
                "ratioMom": phase.ratioMom,
                "equityImplication": phase.equityImplication,
                "equityLabel": phase.equityLabel,
                "description": phase.description,
            }
        else:
            # fallback: 제조업 신규수주/재고
            no = data.get("new_orders")
            inv = data.get("inventories")
            if no is not None and inv is not None and inv > 0:
                prev_no2 = data.get("new_orders_prev")
                prev_inv2 = data.get("inventories_prev")
                prev_ratio2 = (prev_no2 / prev_inv2) if prev_no2 and prev_inv2 and prev_inv2 > 0 else None
                phase = classifyInventoryPhase(no, inv, prev_ratio2)
                result["inventoryPhase"] = {
                    "phase": phase.phase,
                    "phaseLabel": phase.phaseLabel,
                    "ratio": phase.ratio,
                    "ratioMom": phase.ratioMom,
                    "equityImplication": phase.equityImplication,
                    "equityLabel": phase.equityLabel,
                    "description": phase.description,
                    "source": "manufacturing_orders",
                }
            else:
                result["inventoryPhase"] = None

        # ISM 바로미터
        ism = data.get("ism_pmi")
        if ism is not None:
            ism_prev = data.get("ism_pmi_prev")
            barometer = ismBarometer(ism, ism_prev)
            result["ismBarometer"] = {
                "level": barometer.level,
                "zone": barometer.zone,
                "zoneLabel": barometer.zoneLabel,
                "equityStance": barometer.equityStance,
                "equityLabel": barometer.equityLabel,
                "rateImplication": barometer.rateImplication,
                "rateLabel": barometer.rateLabel,
                "description": barometer.description,
            }

            # ISM 자산배분 (투자전략 13)
            alloc = ismAssetAllocation(ism)
            result["ismAllocation"] = {
                "stance": alloc.stance,
                "stanceLabel": alloc.stanceLabel,
                "equityWeight": alloc.equityWeight,
                "bondWeight": alloc.bondWeight,
                "description": alloc.description,
            }
        else:
            result["ismBarometer"] = None
            result["ismAllocation"] = None

    else:
        # KR: 광공업생산 모멘텀(출하 프록시) + BSI(재고판단 프록시)
        mfg = data.get("manufacturing")
        bsi = data.get("bsi")
        if mfg is not None and bsi is not None:
            mfg_prev = data.get("manufacturing_prev")
            bsi_prev = data.get("bsi_prev")
            # 광공업생산 = 출하 프록시 (수준), BSI = 재고 판단 (50 기준)
            # BSI > 100 = 긍정, < 100 = 부정. 재고 해소 = 출하 대비 재고 감소
            # classifyInventoryPhase에 맞게: 생산(수요 프록시) vs BSI 역수(재고 프록시)
            # BSI 높으면 기업 낙관 = 재고 적극 보충 → 재고 증가
            # 200 - BSI = BSI 역수 (100 기준 대칭). 생산 / (200-BSI) ≈ 수요/재고
            inv_proxy = 200.0 - bsi  # BSI 역수: 높을수록 재고 과잉
            prev_ratio = None
            if mfg_prev is not None and bsi_prev is not None:
                inv_prev = 200.0 - bsi_prev
                if inv_prev > 0:
                    prev_ratio = mfg_prev / inv_prev
            phase = classifyInventoryPhase(mfg, inv_proxy, prev_ratio)
            result["inventoryPhase"] = {
                "phase": phase.phase,
                "phaseLabel": phase.phaseLabel,
                "ratio": phase.ratio,
                "ratioMom": phase.ratioMom,
                "equityImplication": phase.equityImplication,
                "equityLabel": phase.equityLabel,
                "description": phase.description,
                "source": "kr_manufacturing_bsi_proxy",
            }
        else:
            result["inventoryPhase"] = None

        result["ismBarometer"] = None
        result["ismAllocation"] = None

    # 시계열
    from dartlab.macro._helpers import recent_timeseries

    ts: dict = {}
    try:
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        if market.upper() == "US":
            for label, sid in [("ism_pmi", "NAPM"), ("new_orders", "NAPMNOI"), ("inventories", "NAPMII")]:
                ts[label] = recent_timeseries(g.macro(sid))
        else:
            for label, sid in [("manufacturing", "MANUFACTURING"), ("bsi", "BSI_ALL")]:
                ts[label] = recent_timeseries(g.macro(sid))
    except Exception:
        pass
    result["timeseries"] = ts

    return result
