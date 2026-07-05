"""왓처 토픽 러너 회귀 — eval_new_ipo·eval_new_orders 매치 구조·dedup slug·필터·sanitize.

df 를 주입(FakeDF)해 dartlab.scan 실호출 없이 검증(polars·dartlab 불요). slug = 매치 id(허브 sentNonce
last-seen set 키): IPO=corpCode(발행사 안정키, 기재정정 재발화 방지) + 확정공모가 corpCode:conf, orders=stockCode.
실행: uv run python -X utf8 -m pytest .github/scripts/notify/
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import watch  # noqa: E402


class FakeDF:
    """polars df 대용 — iter_rows(named=True) 만 제공(eval 함수가 쓰는 인터페이스)."""

    def __init__(self, rows: list[dict]):
        self._rows = rows

    def iter_rows(self, named: bool = True):
        return iter(self._rows)


# ── eval_new_ipo ────────────────────────────────────────────────────
def test_eval_new_ipo_basic():
    df = FakeDF(
        [
            {
                "corpCode": "00126380",
                "corpName": "기도산업",
                "rcept": "20260626000715",
                "subscription": "2026.08.11 ~ 2026.08.12",
                "priceBandLow": 24800.0,
                "priceBandHigh": 28400.0,
                "appliedPer": 10.01,
                "isSpac": False,
            }
        ]
    )
    items = watch.eval_new_ipo(df)
    assert len(items) == 1  # confirmationRcept 없음 → 등장 신호 1개만
    m = items[0]
    assert m["topic"] == "newIpo"
    assert m["slug"] == "00126380"  # corpCode = 발행사 안정키(기재정정 재발화 방지)
    assert "기도산업" in m["notification"]["title"]
    assert "공모가" in m["notification"]["body"]
    assert "청약" in m["notification"]["body"]
    assert m["notification"]["tag"] == "ipo:00126380"
    assert m["notification"]["url"] == "/terminal?ipo=1"  # 자기 라우트 + IPO 다이얼로그 딥링크


def test_eval_new_ipo_spac_label_and_skip_no_rcept():
    df = FakeDF(
        [
            {"corpName": "엔에이치스팩", "rcept": "20260601000001", "isSpac": True},
            {"corpName": "노접수", "rcept": None},  # rcept 없으면 skip(매치 id 불가)
        ]
    )
    items = watch.eval_new_ipo(df)
    assert len(items) == 1
    assert "(스팩)" in items[0]["notification"]["title"]


def test_eval_new_ipo_slug_stable_across_amendments():
    """같은 corpCode = 같은 slug → 기재정정으로 rcept 바뀌어도 재발화 없음(발행사별 1회)."""
    a = watch.eval_new_ipo(FakeDF([{"corpCode": "C1", "corpName": "A", "rcept": "R1"}]))[0]
    b = watch.eval_new_ipo(FakeDF([{"corpCode": "C1", "corpName": "A", "rcept": "R2"}]))[0]
    assert a["slug"] == b["slug"] == "C1"  # rcept R1->R2 바뀌어도 slug 불변


def test_eval_new_ipo_no_corpcode_falls_back_to_rcept():
    """corpCode 결측(scan 폴백 등)이면 rcept 로 안전 폴백."""
    m = watch.eval_new_ipo(FakeDF([{"corpName": "A", "rcept": "R1"}]))[0]
    assert m["slug"] == "R1"


def test_eval_new_ipo_confirmation_second_signal():
    """confirmationRcept 있으면 등장 + 확정공모가 2 신호(각 slug 구분, 발행사별 각 1회)."""
    df = FakeDF([{"corpCode": "C1", "corpName": "레몬", "rcept": "R1", "confirmationRcept": "R9"}])
    items = watch.eval_new_ipo(df)
    assert len(items) == 2
    assert {m["slug"] for m in items} == {"C1", "C1:conf"}
    titles = " ".join(m["notification"]["title"] for m in items)
    assert "신규상장" in titles and "공모가확정" in titles


# ── eval_new_orders ─────────────────────────────────────────────────
def test_eval_new_orders_threshold_and_guards():
    df = FakeDF(
        [
            {
                "stockCode": "111111",
                "corpName": "테스트조선",
                "bookToBill": 2.1,
                "recentRevenue": 5.0e11,
                "nContract": 4,
                "grade": "A",
                "topCounterparty": "현대차",
            },  # 통과
            {"stockCode": "222222", "bookToBill": 0.7, "recentRevenue": 1.0e11, "nContract": 2},  # b2b<1 skip
            {
                "stockCode": "333333",
                "bookToBill": 9.9,
                "recentRevenue": None,
                "nContract": 1,
            },  # 매출 없음(micro-cap) skip
            {"stockCode": "444444", "bookToBill": 3.0, "recentRevenue": 2.0e11, "nContract": 0},  # 계약 0 skip
        ]
    )
    items = watch.eval_new_orders(df)
    assert [m["slug"] for m in items] == ["111111"]  # 통과는 하나
    m = items[0]
    assert m["topic"] == "newOrders"
    assert "테스트조선" in m["notification"]["title"]  # 코드 아니라 회사명(가독)
    assert "book-to-bill" in m["notification"]["body"]
    assert "현대차" in m["notification"]["body"]
    assert m["notification"]["url"] == "/terminal?sym=111111"  # 딥링크(해당 종목 오픈)
    assert m["notification"]["tag"] == "orders:111111"


def test_eval_new_orders_no_corpname_falls_back_to_code():
    """corpName 결측(과거 스캔 스키마)이면 '종목 {code}' 로 안전 폴백 · url 은 여전히 딥링크."""
    df = FakeDF([{"stockCode": "111111", "bookToBill": 2.1, "recentRevenue": 5e11, "nContract": 4}])
    m = watch.eval_new_orders(df)[0]
    assert "종목 111111" in m["notification"]["title"]
    assert m["notification"]["url"] == "/terminal?sym=111111"


def test_eval_new_orders_custom_threshold():
    df = FakeDF([{"stockCode": "555555", "bookToBill": 1.5, "recentRevenue": 1e12, "nContract": 3}])
    assert watch.eval_new_orders(df, min_book_to_bill=2.0) == []  # 임계 상향 → 제외
    assert len(watch.eval_new_orders(df, min_book_to_bill=1.0)) == 1


# ── 발송 위생: 토픽별 cap (조용한 절단 금지) ──────────────────────────
def test_cap_matches_per_topic_order_preserved():
    ms = [{"topic": "newIpo", "slug": str(i)} for i in range(5)] + [
        {"topic": "newOrders", "slug": str(i)} for i in range(4)
    ]
    kept, dropped = watch.cap_matches(ms, caps={"newIpo": 3, "newOrders": 2})
    assert [m["slug"] for m in kept if m["topic"] == "newIpo"] == ["0", "1", "2"]  # 앞 3개(관련도순) 유지
    assert sum(1 for m in kept if m["topic"] == "newOrders") == 2
    assert len(dropped) == 4  # ipo 2 + orders 2 초과


def test_cap_matches_under_cap_keeps_all():
    ms = [{"topic": "newIpo", "slug": "a"}, {"topic": "newOrders", "slug": "b"}]
    kept, dropped = watch.cap_matches(ms)
    assert len(kept) == 2 and dropped == []


# ── stateful 라우팅 (threshold_cross /active set-diff) ────────────────
def test_new_orders_is_stateful():
    """newOrders 는 stateful(/active 커서), newIpo 는 stateless(/send 영구 nonce)."""
    assert "newOrders" in watch._STATEFUL_TOPICS
    assert "newIpo" not in watch._STATEFUL_TOPICS


def test_send_stateful_maps_matches_to_active(monkeypatch):
    """stateful 발송은 전체 매치 set 을 key+notification 으로 /active 에 전달(허브가 diff)."""
    captured = {}

    def fake_post_active(hub, token, topic, matches, ts):
        captured["topic"] = topic
        captured["matches"] = matches
        return 200, {"entered": 1, "sent": 1, "failed": 0}

    monkeypatch.setattr(watch, "post_active", fake_post_active)
    problems = watch._send_stateful(
        "h", "tok", "newOrders", [{"topic": "newOrders", "slug": "005930", "notification": {"title": "x"}}], 123
    )
    assert problems == []
    assert captured["topic"] == "newOrders"
    assert captured["matches"] == [{"key": "005930", "notification": {"title": "x"}}]


def test_send_stateful_total_fail_is_problem(monkeypatch):
    """전건 발송 실패(entered>0, sent=0, failed>0)는 problem(RED)."""
    monkeypatch.setattr(watch, "post_active", lambda *a: (200, {"entered": 2, "sent": 0, "failed": 5}))
    problems = watch._send_stateful("h", "tok", "newOrders", [{"slug": "A", "notification": {}}], 1)
    assert len(problems) == 1
