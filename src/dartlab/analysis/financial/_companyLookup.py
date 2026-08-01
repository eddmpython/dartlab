"""Company 객체에서 업종 정보를 꺼내는 조회 primitive SSOT.

예측신호 네 갈래(``_signalsCorporate`` · ``_signalsDirection`` · ``_signalsMacroBreak`` ·
``_signalsPeer``)와 ``predictionSignals`` 가 업종 키를 얻는 같은 아홉 줄을 각자 갖고
있었고, forecast 입력과 valuation 입력이 sectorParams 를 얻는 같은 네 줄을 각자 갖고
있었다. 한쪽만 고치면 같은 회사를 두 축이 다른 업종으로 읽는다.

실패 규약: 업종을 못 읽으면 예외 대신 None 이다. 업종 미상과 조회 실패를 구분할 방법이
원래부터 없고, 부르는 쪽 전부가 None 을 "업종 미상" 으로 처리한다.

``_IG_TO_SECTOR_KEY`` 는 ``valuation`` 이 소유하므로 함수 안에서 늦게 import 한다.
모듈 최상단으로 올리면 valuation 과 순환이 된다.

주의: ``_signalsMacroSensitivity._getSectorKey`` 는 이름만 같은 다른 함수다. 그쪽은
``getattr`` 로 sector 를 읽고 ImportError 를 잡지 않아 실패 모양이 다르다. 합치면
동작이 바뀌므로 그대로 둔다.
"""

from __future__ import annotations

import re
from typing import Any


def _getSectorKey(company) -> str | None:
    """Company 의 산업분류에서 밸류에이션 업종 키를 얻는다. 미상이면 None."""
    try:
        from dartlab.analysis.financial.valuation import _IG_TO_SECTOR_KEY

        sectorInfo = company.sector
        if sectorInfo is not None:
            igName = sectorInfo.industryGroup.name
            return _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError, ImportError):
        pass
    return None


def _getSectorParams(company: Any):
    """Company 에 붙은 SectorParams 를 꺼낸다. 없으면 None."""
    try:
        return getattr(company, "sectorParams", None)
    except AttributeError:
        return None


def _periodEndDate(basePeriod: str) -> str | None:
    """재무 기간 라벨을 비교 가능한 기간 말일로 바꾼다."""
    annual = re.fullmatch(r"(\d{4})", basePeriod)
    if annual:
        return f"{annual.group(1)}-12-31"
    quarter = re.fullmatch(r"(\d{4})Q([1-4])", basePeriod)
    if not quarter:
        return None
    month_day = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}
    return f"{quarter.group(1)}-{month_day[quarter.group(2)]}"


def _getSharesOutstandingInput(company: Any, basePeriod: str | None = None) -> dict | None:
    """공시된 보통주 수와 실제 선택한 보고 기간을 함께 얻는다."""
    try:
        import polars as pl

        report = getattr(company, "_report", None)
        df = report.extract("stockTotal") if report is not None else None
        if df is not None and len(df) > 0 and "se" in df.columns and "istc_totqy" in df.columns:
            common = df.filter(pl.col("se") == "보통주")
            period_end = _periodEndDate(basePeriod) if basePeriod else None
            if basePeriod is not None and period_end is None:
                return None
            if period_end and "stlm_dt" in common.columns:
                common = common.filter(pl.col("stlm_dt") <= period_end)
            if len(common) > 0:
                if "stlm_dt" in common.columns:
                    common = common.sort("stlm_dt", descending=True)
                value = common["istc_totqy"][0]
                if value is not None and float(value) > 0:
                    period = common["stlm_dt"][0] if "stlm_dt" in common.columns else None
                    return {
                        "value": int(float(value)),
                        "period": period,
                        "source": "report.stockTotal",
                    }
    except (AttributeError, KeyError, IndexError, OSError, RuntimeError, TypeError, ValueError):
        pass

    # 과거 기준 계산에서 최신 profile 값으로 조용히 대체하면 미래 정보가 섞인다.
    if basePeriod is not None:
        return None
    accessor = getattr(company, "_profileAccessor", None)
    if accessor is None:
        return None
    try:
        value = accessor.sharesOutstanding
    except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
        return None
    if not value:
        return None
    return {"value": int(value), "period": None, "source": "profile.latest"}


def _getSharesOutstanding(company: Any, basePeriod: str | None = None) -> int | None:
    """공시된 발행주식수를 얻는다. 못 얻으면 None.

    주당 지표를 내는 자리 넷(애널리스트·밸류에이션 입력·매출 예측 입력·현금흐름 가치평가
    도구)이 각자 주식수를 구하고 있었다. 옛 이름 ``company.profile.sharesOutstanding`` 은
    표면에 없어 넷 다 늘 None 이었다.

    공급원은 회사 자기 정기보고서의 주식총수 현황이고 값 컬럼은 ``istc_totqy`` (발행주식의
    총수) 다. 이름이 비슷한 ``isu_stock_totqy`` 는 정관상 발행할 주식의 총수, 곧 수권주식수라
    실제 발행량의 서너 배다.

    한때 ``capital`` 축을 거쳤는데 그 축은 전종목 스캔이라 회사당 8 초가 들고 시장 프레임을
    통째로 메모리에 올린다. 한 회사의 주식수를 알자고 시장을 훑을 이유가 없다.

    Returns:
        발행주식수 (유통 보통주). 보고서가 없거나 값이 비면 None.
    """
    resolved = _getSharesOutstandingInput(company, basePeriod=basePeriod)
    return resolved["value"] if resolved else None
