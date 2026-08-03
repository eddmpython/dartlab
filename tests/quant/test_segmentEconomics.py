"""P1c 세그먼트 경제성 게이트 — peer-reconcile 부문마진 배분 (offline 결정론).

segment economics의 현재 실행 계약을 검증한다.
de-gate: 부문 OI 미공시 시 마진 스킵 → 연결 OI 를 peer 마진 구조로 배분(reconcile, Σ=OI_total).
본 파일 = 순수 배분 수식 검증. company-level peer fetch 배선은 CI(data) — 02c §5.
"""

from __future__ import annotations

from dartlab.analysis.financial._segmentEconomics import reconcileSegmentMargins


def test_reconcile_sums_to_total_oi():
    r = reconcileSegmentMargins({"A": 100.0, "B": 50.0}, 30.0, {"A": 0.25, "B": 0.10})
    assert r is not None
    total = sum(v["oiDerived"] for v in r.values())
    assert abs(total - 30.0) < 1.0, "Σ 도출 OI = 연결 OI (reconcile 제약)"


def test_reconcile_preserves_margin_rank():
    r = reconcileSegmentMargins({"A": 100.0, "B": 100.0}, 40.0, {"A": 0.30, "B": 0.10})
    assert r["A"]["marginDerived"] > r["B"]["marginDerived"], "고마진 peer → 고마진 도출(순위 보존)"


def test_reconcile_range_scaled_by_k():
    r = reconcileSegmentMargins({"A": 100.0}, 25.0, {"A": 0.25}, {"A": (0.20, 0.30)})
    rng = r["A"]["marginRange"]
    assert rng is not None and len(rng) == 2 and rng[0] < rng[1], "peer 범위 → reconcile 마진 범위"


def test_reconcile_none_on_no_match():
    assert reconcileSegmentMargins({"A": 100.0}, 30.0, {}) is None, "peer 매칭 0 → None(도출 불가)"
    assert reconcileSegmentMargins({}, 30.0, {"A": 0.25}) is None, "부문 매출 0 → None"


def test_reconcile_loss_segment_excluded_from_k():
    # 적자부문(음수 peer margin)은 k 분모서 제외(부호 왜곡 방지, R3) — 양수 부문으로 k 산출.
    r = reconcileSegmentMargins({"A": 100.0, "B": 50.0}, 20.0, {"A": 0.25, "B": -0.10})
    assert r is not None and "A" in r and r["B"]["marginDerived"] < 0, "적자부문 도출 손실 + 양수부문 k 보존"
