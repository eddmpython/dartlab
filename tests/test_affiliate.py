"""affiliate 패키지 검증 테스트 — 015 실험의 40개 시나리오를 pytest로 전환."""

from __future__ import annotations

from collections import Counter

import pytest

from tests.conftest import requires_samsung

pytestmark = requires_samsung

# 느린 파이프라인 → 모듈 수준에서 한번만 실행
_data = None
_full = None
_gc = None


def _ensure_data():
    global _data, _full, _gc
    if _data is not None:
        return
    from dartlab.engines.dart.affiliate import build_graph, export_full

    _data = build_graph(verbose=False)
    _full = export_full(_data)
    _gc = Counter(_data["code_to_group"][n] for n in _data["all_node_ids"])


@pytest.fixture(scope="module", autouse=True)
def affiliate_data():
    _ensure_data()
    yield _data


# ── 그룹 크기 범위 (10) ──────────────────────────────────


@pytest.mark.parametrize(
    "group,lo,hi",
    [
        ("삼성", 15, 25),
        ("현대차", 15, 25),
        ("SK", 15, 25),
        ("LG", 8, 15),
        ("한화", 10, 15),
        ("롯데", 8, 15),
        ("현대백화점", 10, 15),
        ("KT", 5, 15),
        ("효성", 8, 15),
        ("HD현대", 5, 10),
    ],
)
def test_group_size_range(group, lo, hi):
    _ensure_data()
    actual = _gc.get(group, 0)
    assert lo <= actual <= hi, f"{group}: {actual} not in [{lo}, {hi}]"


# ── 필수 소속 (18) ───────────────────────────────────────


@pytest.mark.parametrize(
    "code,name,expected_group",
    [
        ("005930", "삼성전자", "삼성"),
        ("006400", "삼성SDI", "삼성"),
        ("032830", "삼성생명", "삼성"),
        ("207940", "삼성바이오로직스", "삼성"),
        ("005380", "현대자동차", "현대차"),
        ("000270", "기아", "현대차"),
        ("012330", "현대모비스", "현대차"),
        ("001450", "현대해상", "현대차"),
        ("034730", "SK", "SK"),
        ("000660", "SK하이닉스", "SK"),
        ("003550", "LG", "LG"),
        ("066570", "LG전자", "LG"),
        ("000880", "한화에어로스페이스", "한화"),
        ("088350", "한화생명", "한화"),
        ("023530", "롯데지주", "롯데"),
        ("004800", "효성", "효성"),
        ("329180", "HD현대", "HD현대"),
        ("035720", "카카오", "카카오"),
    ],
)
def test_must_belong(code, name, expected_group):
    _ensure_data()
    actual = _data["code_to_group"].get(code, "?")
    assert actual == expected_group, f"{name}({code}): {actual} != {expected_group}"


# ── 금지 소속 (5) ────────────────────────────────────────


@pytest.mark.parametrize(
    "code,name,forbidden_group",
    [
        ("240810", "원익IPS", "삼성"),
        ("222800", "심텍", "삼성"),
        ("002390", "한독", "삼성"),
        ("010060", "OCI홀딩스", "삼성"),
    ],
)
def test_must_not_belong(code, name, forbidden_group):
    _ensure_data()
    actual = _data["code_to_group"].get(code, "?")
    assert actual != forbidden_group, f"{name}({code}): 오분류 {actual}"


def test_hyundai_marine_not_independent():
    """현대해상은 독립이면 안 됨."""
    _ensure_data()
    code = "001450"
    group = _data["code_to_group"].get(code, "?")
    name = _data["code_to_name"].get(code, code)
    assert group != name, f"현대해상이 독립으로 분류됨: {group}"


# ── 독립 비율 ────────────────────────────────────────────


def test_independence_ratio():
    _ensure_data()
    indep = sum(1 for c in _gc.values() if c == 1)
    ratio = indep / len(_data["all_node_ids"])
    assert 0.40 <= ratio <= 0.60, f"독립 비율 {ratio:.1%} (범위: 40~60%)"


# ── 그룹 수 ──────────────────────────────────────────────


def test_group_count():
    _ensure_data()
    multi = sum(1 for c in _gc.values() if c >= 2)
    assert 150 <= multi <= 250, f"2명+ 그룹: {multi} (범위: 150~250)"


# ── 순환출자 ─────────────────────────────────────────────


def test_cycle_count():
    _ensure_data()
    assert len(_data["cycles"]) >= 50, f"순환출자: {len(_data['cycles'])} (최소: 50)"


def test_hyundai_cycle_exists():
    _ensure_data()
    has_hyundai = any("005380" in c or "000270" in c for c in _data["cycles"])
    assert has_hyundai, "현대차 내부 순환출자 없음"


# ── 데이터 무결성 ────────────────────────────────────────


def test_all_nodes_have_group():
    _ensure_data()
    assert all(n in _data["code_to_group"] for n in _data["all_node_ids"])


def test_no_empty_group_name():
    _ensure_data()
    assert all(_data["code_to_group"].get(n, "") != "" for n in _data["all_node_ids"])


def test_node_count():
    _ensure_data()
    assert len(_data["all_node_ids"]) >= 1500, f"노드 수: {len(_data['all_node_ids'])}"


# ── export 품질 ──────────────────────────────────────────


def test_full_json_size():
    """full JSON 크기 제한 (2MB 이하)."""
    import json

    _ensure_data()
    text = json.dumps(_full, ensure_ascii=False, separators=(",", ":"))
    size_mb = len(text) / (1024 * 1024)
    assert size_mb <= 2.0, f"full JSON: {size_mb:.1f}MB (최대: 2MB)"


def test_ego_enrichment():
    """독립 회사 ego가 최소 2노드 이상."""
    from dartlab.engines.dart.affiliate import export_ego

    _ensure_data()
    # 독립 회사 몇 개 샘플
    indep_codes = [n for n in _data["all_node_ids"] if _gc[_data["code_to_group"][n]] == 1][:20]
    for code in indep_codes:
        ego = export_ego(_data, _full, code, hops=1)
        assert ego["meta"]["nodeCount"] >= 2, f"{code}: ego 1노드 (보강 실패)"


def test_industry_clusters():
    """업종 클러스터 존재."""
    _ensure_data()
    assert _full["meta"]["industryCount"] >= 100, f"업종: {_full['meta']['industryCount']}"
