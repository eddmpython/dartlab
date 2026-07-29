"""mergeAliasRows row-level semantic 가드 (적대적 검토 HIGH-2).

``SNAKEID_ALIASES`` 는 5 소비처에서 양립불가하게 쓰인다 — DART pivot 행축소
(``financeMappers``) / calc 양방향복제(``helpers``) / EDGAR pivot fixpoint(``edgar/pivot``)
/ show forward-only / koreanLabels 전파. 그 중 *공유 함수* ``mergeAliasRows`` 의
행축소 의미(alias 제거 + canonical not-null 채움 + metaCols 분기)를 합성 입력으로
직접 박제 — equivalence golden 이 안 잡는 row-level 출력을 고정한다.
"""

from __future__ import annotations

import pytest

from dartlab.core.accounts import SNAKEID_ALIASES, mergeAliasRows
from dartlab.core.accounts.aliases import _compileAliasGraph

pytestmark = pytest.mark.unit

# 명확한 alias→canonical 전제 (런타임 검증)
_ALIAS = "cash_flows_from_operating_activities"
_CANON = "operating_cashflow"


def test_alias_premise() -> None:
    """전제 — _ALIAS 가 SNAKEID_ALIASES 에서 _CANON 으로 매핑."""
    assert SNAKEID_ALIASES.get(_ALIAS) == _CANON


def test_alias_row_removed_and_canonical_filled() -> None:
    """alias 는 머지 대상으로 분류, canonical 의 None 셀만 alias not-null 로 채움."""
    rowMap = {
        _CANON: {"snakeId": _CANON, "2024": None, "2023": 100.0},
        _ALIAS: {"snakeId": _ALIAS, "2024": 50.0, "2023": 999.0},
    }
    merged = mergeAliasRows(rowMap)
    assert _ALIAS in merged  # 제거 대상 (DART pivot 이 이걸로 행 삭제)
    assert rowMap[_CANON]["2024"] == 50.0  # None 이던 셀 → alias 값
    assert rowMap[_CANON]["2023"] == 100.0  # 원래 not-null → 덮어쓰기 안 함
    assert rowMap[_CANON]["snakeId"] == _CANON  # metaCol 보존


def test_metacols_default_skips_meta_columns() -> None:
    """default metaCols 는 snakeId/항목/_level/_sort 머지 제외 (DART pivot 모드)."""
    rowMap = {
        _CANON: {"snakeId": _CANON, "항목": None, "value": None},
        _ALIAS: {"snakeId": _ALIAS, "항목": "현금흐름", "value": 5.0},
    }
    mergeAliasRows(rowMap)
    assert rowMap[_CANON]["항목"] is None  # metaCol — 머지 안 됨
    assert rowMap[_CANON]["value"] == 5.0  # 일반 col — 머지됨


def test_metacols_empty_merges_all_columns() -> None:
    """metaCols=set() 는 전 컬럼 머지 (calc 모드 — toDictBySnakeId)."""
    rowMap = {
        _CANON: {"snakeId": _CANON, "x": None},
        _ALIAS: {"snakeId": _ALIAS, "x": 7.0},
    }
    mergeAliasRows(rowMap, metaCols=set())
    assert rowMap[_CANON]["x"] == 7.0


def test_no_canonical_row_no_merge() -> None:
    """canonical row 부재 시 머지·제거 없음 (alias 단독 생존)."""
    rowMap = {_ALIAS: {"snakeId": _ALIAS, "value": 1.0}}
    merged = mergeAliasRows(rowMap)
    assert _ALIAS not in merged
    assert _ALIAS in rowMap


def test_no_alias_row_no_merge() -> None:
    """alias row 부재 시 canonical 무변경."""
    rowMap = {_CANON: {"snakeId": _CANON, "value": 1.0}}
    merged = mergeAliasRows(rowMap)
    assert _CANON not in merged
    assert rowMap[_CANON]["value"] == 1.0


def test_snakeid_aliases_single_object_identity() -> None:
    """SNAKEID_ALIASES 가 owner·labels facade·edgar 에서 단일 객체 (5 semantic 공유 전제)."""
    from dartlab.core.accounts.aliases import SNAKEID_ALIASES as fromOwner
    from dartlab.core.utils.labels import SNAKEID_ALIASES as fromLabels
    from dartlab.providers.edgar.finance.mapper import EDGAR_TO_DART_ALIASES as fromEdgar

    assert fromOwner is fromLabels is fromEdgar


def test_alias_graph_compiles_transitive_chain_to_terminal() -> None:
    """다단계 alias는 중간 행 삭제 순서와 무관하게 terminal로 평탄화한다."""

    compiled = _compileAliasGraph({"a": "b", "b": "c"})

    assert compiled == {"a": "c", "b": "c"}


def test_alias_graph_rejects_cycle() -> None:
    """서로를 가리키는 alias는 import 시점에 명시적으로 실패해야 한다."""

    with pytest.raises(ValueError, match="순환 참조"):
        _compileAliasGraph({"a": "b", "b": "a"})


def test_total_equity_and_parent_equity_remain_distinct() -> None:
    """총자본은 비지배지분을 포함하므로 지배주주지분과 합치면 안 된다."""

    assert SNAKEID_ALIASES.get("total_equity") == "total_stockholders_equity"
    assert SNAKEID_ALIASES.get("equity_including_nci") == "total_stockholders_equity"
    assert "total_stockholders_equity" not in SNAKEID_ALIASES
    assert "owners_of_parent_equity" not in SNAKEID_ALIASES

    rowMap = {
        "total_stockholders_equity": {"2025": 4_921.0},
        "owners_of_parent_equity": {"2025": 4_021.0},
    }
    merged = mergeAliasRows(rowMap, metaCols=set())

    assert not merged
    assert rowMap["total_stockholders_equity"]["2025"] == 4_921.0
    assert rowMap["owners_of_parent_equity"]["2025"] == 4_021.0
