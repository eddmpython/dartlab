"""Implied Equity Risk Premium. 현재 비발행 (가격 SSOT 부재).

Gordon 역산 ERP 는 분모가 *시가총액*이어야 한다.

    ImpliedERP ~= (E/P) + g - Rf

dartlab 이 전종목으로 집계할 수 있는 것은 자본총계(장부가) 합산뿐이라, 예전 구현의
``E / 자본총계`` 는 E/P 가 아니라 aggregate ROE 였다. P/B > 1 인 시장에서 이 값은 ERP 를
체계적으로 과대평가했고, 상한 클램프에 걸려 한국 ERP 를 12.0% (성숙시장 4.6% 대비) 로
발행한 캐시가 실제로 남아 있었다. 그 값은 ``calcDFV`` 의 WACC 로 흘러 모든 DCF 결과를
왜곡한다. 지수 레벨을 받아 놓고 산술에는 쓰지 않으면서 ``method="gordon_simple"`` 라벨을
붙인 것도 실제 계산과 달랐다.

이름만 원모형인 값을 계속 보정하는 대신, 공용 입력으로 원식을 재현할 수 없는 모델은
발행하지 않는다 (L0-03 비정규 부실·조작 모델 비발행 계약과 같은 규칙). 호환 키는
그대로 두되 ``impliedERP`` 는 항상 ``None`` 이고 호출자는 큐레이션된 정적 ERP 로
정상 degrade 한다.

재활성화 조건: 유니버스 시가총액 SSOT (가격 x 상장주식수) 확보. 그 뒤 배당·자사주
yield 와 payout 을 갖춘 원식으로 복원한다.

근거: Damodaran, *Equity Risk Premiums: Determinants, Estimates and Implications* (annual).
https://pages.stern.nyu.edu/~adamodar/pc/datasets/histimpl.html
"""

from __future__ import annotations

from typing import Any


def calcImpliedERP(
    country: str = "KR",
    *,
    asOfDate: str | None = None,
    useCache: bool = True,
) -> dict[str, Any]:
    """정적 ERP 를 반환한다. Implied ERP 역산은 현재 비발행이다.

    Capabilities:
        ``loadDamodaranERP`` 의 정적 ERP 를 같은 스키마로 돌려주되, 역산 sub-key 는
        발행하지 않는다 (``impliedERP=None``, ``method="none"``,
        ``source="fallback_historical"``, ``sampleCount=0``). 소비자는 정적 ERP 와
        역산 ERP 를 값 모양이 아니라 이 세 키로 구분한다.

    Args:
        country: ``"KR"``/``"US"``. ISO 2-letter.
        asOfDate: 역산 재활성화 시 사용할 기준일. 비발행 동안은 동작에 영향이 없다.
        useCache: 역산 재활성화 시 사용할 분기 cache 스위치. 비발행 동안은 동작에
            영향이 없다. 옛 구현이 남긴 편향된 cache 도 읽지 않는다.

    Returns:
        dict: ``loadDamodaranERP`` 와 같은 정적 10 키 +
            ``impliedERP`` (항상 ``None``) · ``method`` (``"none"``) ·
            ``sampleCount`` (``0``).

    Raises:
        없음.

    Example:
        >>> r = calcImpliedERP("KR")
        >>> r["impliedERP"] is None and r["method"] == "none"
        True

    Guide:
        역산 값이 필요하면 ``impliedERP`` 가 ``None`` 인지 먼저 보고, None 이면
        정적 ERP 로 답한다. 0 이나 임의 상수로 대체하지 않는다.

    SeeAlso:
        - ``loadDamodaranERP``: 정적 ERP (Damodaran 1 월/7 월 업데이트)
        - ``calcDFV``: WACC 산출 시 본 ERP 사용

    Requires:
        ``dartlab.synth.riskPremiums.loadDamodaranERP``.

    AIContext:
        시장 내재 프리미엄을 물어도 현재는 역산값이 없다. 정적 ERP 임을 밝히고
        추정한 내재 프리미엄을 지어내지 않는다.

    LLM Specifications:
        AntiPatterns:
            - ``impliedERP`` 가 None 인데 정적 ``totalERP`` 를 "시장 내재" 라고 인용.
            - 비발행 상태를 0 또는 임의 상수로 대체.
        OutputSchema:
            정적 10 키 + ``impliedERP``/``method``/``sampleCount``.
        Prerequisites:
            ``loadDamodaranERP`` 호출 가능.
        Freshness:
            정적 ERP 의 갱신 주기를 따른다.
        Dataflow:
            country -> loadDamodaranERP -> 비발행 표시 부착 -> dict 반환.
        TargetMarkets: KR, US.
    """
    from dartlab.synth.riskPremiums import loadDamodaranERP

    fallback = loadDamodaranERP(countryCode=country)
    fallback["source"] = "fallback_historical"
    fallback["impliedERP"] = None
    fallback["method"] = "none"
    fallback["sampleCount"] = 0
    return fallback
