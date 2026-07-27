"""어댑터 dispatch 표의 정합성 회귀.

`_buildKindSpecView` 안에 47 갈래짜리 `elif adapter_name == ...` 사슬이 있었다. 갈래마다
하는 일은 사실 같았다. adapters 의 빌더 하나를 부르고 결과 dict 의 몇 키를 view 로 옮기는
것이다. 갈리는 것은 셋뿐이다. 어느 빌더냐, 인자가 회사냐 종목코드냐 정규화 표냐, 결과를
통째로 합치냐 특정 키만 옮기냐.

사슬은 길어질수록 옆 갈래를 복사해 붙이게 된다. 실제로 categories/series 를 옮기는 갈래
스물몇 개 중 일부만 options 병합을 하고 있었고, 그 차이가 의도인지 누락인지 코드만 봐서는
알 수 없었다. 표로 적으면 그 셋이 한눈에 정렬돼 보인다.

이 파일이 지키는 것은 표의 성질이다. 표에 적힌 빌더가 실재하는지, 인자 종류와 병합 방식이
정해진 값인지, 정규화 표가 필요한 어댑터 목록이 표에서 도출되는지.
"""

from __future__ import annotations

import pytest

from dartlab.viz.adapterPlans import ADAPTER_PLANS, ALWAYS, NORM_ADAPTERS, PRESENT

pytestmark = [pytest.mark.unit]


def testEveryPlanNamesAnExistingBuilder() -> None:
    """표가 없는 함수를 가리키면 그 카드는 호출 순간 죽는다."""

    from dartlab.viz.display import adapters

    missing = sorted(name for name, plan in ADAPTER_PLANS.items() if not hasattr(adapters, plan.builder))

    assert not missing, f"빌더가 없는 어댑터: {missing}"


@pytest.mark.parametrize("name", sorted(ADAPTER_PLANS))
def testArgKindIsKnown(name: str) -> None:
    """인자 종류가 셋 중 하나가 아니면 dispatch 가 조용히 잘못된 인자를 넘긴다."""

    assert ADAPTER_PLANS[name].arg in {"company", "stockCode", "norm"}


@pytest.mark.parametrize("name", sorted(ADAPTER_PLANS))
def testMergeShapeIsCoherent(name: str) -> None:
    """통째로 합치는 계획은 옮길 키를 따로 적지 않는다. 둘 다 적으면 하나가 죽은 선언이다."""

    plan = ADAPTER_PLANS[name]

    if plan.full:
        assert plan.fields == ()
    else:
        assert plan.fields, "합치는 방식도 옮길 키도 없으면 이 어댑터는 아무 일도 안 한다"
        for _key, mode, _default in plan.fields:
            assert mode in {ALWAYS, PRESENT}


def testNormAdaptersAreDerivedFromTheTable() -> None:
    """정규화 표가 필요한 목록을 따로 관리하면 표와 어긋난다."""

    declared = {name for name, plan in ADAPTER_PLANS.items() if plan.needsNorm}

    assert declared <= NORM_ADAPTERS
    assert {"kpiFromNorm", "diffFromNorm"} <= NORM_ADAPTERS


def testCatalogAdaptersAreAllDispatchable() -> None:
    """카탈로그가 쓰는 어댑터 이름이 표에도 개별 처리에도 없으면 그 카드는 빈 껍데기가 된다."""

    from dartlab.viz.builder import _SPEC_DRIVEN_ADAPTERS
    from dartlab.viz.catalog import CATALOG

    used = {
        (entry.get("dataSpec") or {}).get("adapter")
        for entry in CATALOG.values()
        if (entry.get("dataSpec") or {}).get("adapter")
    }
    unknown = sorted(used - set(ADAPTER_PLANS) - _SPEC_DRIVEN_ADAPTERS)

    assert not unknown, f"dispatch 할 수 없는 어댑터: {unknown}"


def testPlanTableIsNotEmptyAndCoversBothArgKinds() -> None:
    """표가 비거나 한쪽 인자만 있으면 옮기다 만 것이다."""

    args = {plan.arg for plan in ADAPTER_PLANS.values()}

    assert len(ADAPTER_PLANS) > 30
    assert {"company", "stockCode", "norm"} <= args
