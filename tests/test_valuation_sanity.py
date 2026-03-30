"""밸류에이션 합리성 검증 (sanity check).

대표 기업 10개의 종합 적정가가 합리적 범위에 있는지 검증한다.
수정할 때마다 "고쳤는데 다른 데 틀어짐"을 바로 잡기 위한 가드레일.

기준: 적정가/현재가 비율이 10~1000% 범위 (극단적 이상값 방지)
- 10% 미만: 모델이 완전히 고장 (DCF 25원 같은 사례)
- 1000% 이상: 연결 멀티플 과대, DDM 폭주 등

모델 수: 최소 2개 이상 합성에 참여해야 함
"""

import gc

import pytest

# 실제 데이터 필요 — requires_data 마커
pytestmark = [pytest.mark.requires_data, pytest.mark.slow]

# (종목코드, 기업명, 참고 현재가, 최소 비율%, 최대 비율%, 최소 모델 수)
SANITY_CASES = [
    ("005930", "삼성전자", 175400, 10, 500, 2),
    ("000660", "SK하이닉스", 194300, 10, 500, 2),
    ("000270", "기아", 150300, 30, 500, 2),
    ("004020", "현대제철", 34300, 10, 800, 2),
    ("042660", "한화오션", 123200, 5, 500, 1),  # 적자 턴어라운드 — 넓은 범위
    ("017670", "SK텔레콤", 59400, 30, 500, 2),
    ("055550", "신한지주", 93500, 20, 400, 2),
    ("034730", "SK", 334000, 10, 1000, 2),  # 지주사 — 넓은 범위
    ("051910", "LG화학", 235000, 10, 1000, 2),  # 적자 화학 — 넓은 범위
    ("036570", "엔씨소프트", 230000, 10, 500, 2),
]


@pytest.fixture(scope="module")
def syntheses():
    """10개 기업 종합 밸류에이션 결과를 한 번만 계산."""
    import dartlab
    from dartlab.analysis.financial.valuation import calcValuationSynthesis

    results = {}
    for code, name, price, *_ in SANITY_CASES:
        c = dartlab.Company(code)
        r = calcValuationSynthesis(c)
        results[code] = (r, price)
        del c
        gc.collect()
    return results


@pytest.mark.parametrize(
    "code,name,price,minRatio,maxRatio,minModels",
    SANITY_CASES,
    ids=[f"{c[0]}_{c[1]}" for c in SANITY_CASES],
)
def test_valuationSanity(syntheses, code, name, price, minRatio, maxRatio, minModels):
    """적정가가 합리적 범위 내에 있는지 검증."""
    result, _ = syntheses[code]

    assert result is not None, f"{name}({code}): calcValuationSynthesis 결과 None"

    wfv = result.get("weightedFairValue")
    estimates = result.get("estimates", [])

    # 모델 수 검증
    assert len(estimates) >= minModels, (
        f"{name}({code}): 합성 모델 {len(estimates)}개 < 최소 {minModels}개. "
        f"포함된 모델: {[e['method'] for e in estimates]}"
    )

    # 적정가 존재 검증
    assert wfv is not None and wfv > 0, f"{name}({code}): 종합 적정가 없음 또는 0 이하"

    # 비율 범위 검증
    ratio = wfv / price * 100
    assert minRatio <= ratio <= maxRatio, (
        f"{name}({code}): 적정가/현재가 = {ratio:.0f}% "
        f"(범위: {minRatio}~{maxRatio}%). "
        f"적정가={wfv:,.0f}, 현재가={price:,}"
    )
