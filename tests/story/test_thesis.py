"""P2 thesis 빌더 게이트 — ROIC−WACC 지속성 → 구조화 인과논거 (offline 결정론).

현재 계약: docs/handbook/architecture/analysisProducts.md.
정규식 산문 폐기 — 메커니즘 1문장(데이터 섞이면 조건부 정직). 본 파일 = 순수 합성 헬퍼
(_spreadPersistence·_composeCentral·_composeTriggers) + company 실패 시 conclusion 폴백.
calcRoicTimeline 의존 end-to-end 는 CI.
"""

from __future__ import annotations

from types import SimpleNamespace

from dartlab.story.thesis import _composeCentral, _composeTriggers, _spreadPersistence, buildThesis

# ── 스프레드 지속성 (최신순 history, None roic 제외) ──


def test_persistence_skips_incomplete_year_and_computes():
    hist = [
        {"roic": None, "spread": None, "waccEstimate": 8.72},  # 미완 현재연도
        {"roic": 9.9, "spread": 1.18, "waccEstimate": 8.72},
        {"roic": 6.71, "spread": -2.01, "waccEstimate": 8.72},
        {"roic": 12.0, "spread": 3.3, "waccEstimate": 8.72},
    ]
    sig = _spreadPersistence(hist)
    assert sig["roicLatest"] == 9.9, "미완연도 건너뛰고 최신 유효값"
    assert sig["years"] == 3
    assert sig["posRatio"] == round(2 / 3, 2)
    assert sig["spreadLatest"] == 1.18


def test_persistence_none_on_empty():
    assert _spreadPersistence([{"roic": None, "spread": None}]) is None


# ── 중심논거 (메커니즘·조건부 정직) ──


def test_central_strong_moat():
    sig = {
        "roicLatest": 25.0,
        "waccLatest": 8.0,
        "mean": 15.0,
        "posRatio": 1.0,
        "years": 7,
        "trend": "stable",
        "spreadLatest": 17.0,
    }
    c = _composeCentral(sig, "")
    assert "상회" in c and "방어" in c, "고스프레드·고지속 = 단정적 가치창출"


def test_central_conditional_when_mixed():
    sig = {
        "roicLatest": 9.9,
        "waccLatest": 8.7,
        "mean": 0.5,
        "posRatio": 0.5,
        "years": 7,
        "trend": "stable",
        "spreadLatest": 1.18,
    }
    c = _composeCentral(sig, "")
    assert "조건부" in c, "섞인 데이터(사이클) = 조건부 정직(과장 금지)"


def test_central_underperform():
    sig = {
        "roicLatest": 4.0,
        "waccLatest": 9.0,
        "mean": -3.0,
        "posRatio": 0.2,
        "years": 6,
        "trend": "narrowing",
        "spreadLatest": -5.0,
    }
    c = _composeCentral(sig, "")
    assert "미회수" in c, "자본비용 미회수 = 가치창출 미확인"


def test_central_fallback_to_conclusion():
    assert _composeCentral(None, "기존 결론") == "기존 결론"


# ── 트리거 (정량 결박) ──


def test_triggers_narrowing_and_warnings():
    sig = {"trend": "narrowing", "spreadLatest": -1.5, "posRatio": 0.3}
    t = _composeTriggers(sig, ["부채 급증", "마진 압박"])
    assert any("narrowing" in x for x in t)
    assert any("ROIC < WACC" in x for x in t), "posRatio<0.5 트리거"
    assert "부채 급증" in t
    assert len(t) <= 5


# ── buildThesis 폴백 (company 실패 시) ──


def test_build_thesis_fallback_without_roic():
    # 더미 company → calcRoicTimeline 실패 → conclusion 폴백.
    card = SimpleNamespace(conclusion="자본 가치 창출", strengths=["FCF 흑자"], warnings=["사이클 변동"])
    th = buildThesis(object(), card, {"intrinsic": 196337, "current": 80000})
    assert th is not None
    assert th["central"] == "자본 가치 창출", "ROIC 실패 시 conclusion 폴백"
    assert th["call"] is not None and "196,337" in th["call"]
    assert "사이클 변동" in th["triggers"]


def test_build_thesis_none_when_no_material():
    assert buildThesis(object(), SimpleNamespace(conclusion="", strengths=[], warnings=[]), None) is None
