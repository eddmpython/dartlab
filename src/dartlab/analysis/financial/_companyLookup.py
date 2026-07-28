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
