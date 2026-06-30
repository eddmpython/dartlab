"""왓처 토픽 러너 회귀 — eval_new_ipo·eval_new_orders 매치 구조·dedup slug·필터·sanitize.

df 를 주입(FakeDF)해 dartlab.scan 실호출 없이 검증(polars·dartlab 불요). slug = 매치 id(허브 sentNonce
last-seen set 키): IPO=rcept, orders=stockCode.
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
    assert len(items) == 1
    m = items[0]
    assert m["topic"] == "newIpo"
    assert m["slug"] == "20260626000715"  # rcept = 매치 id(dedup)
    assert "기도산업" in m["notification"]["title"]
    assert "공모가" in m["notification"]["body"]
    assert "청약" in m["notification"]["body"]
    assert m["notification"]["tag"] == "ipo:20260626000715"
    assert m["notification"]["url"] == "/terminal"  # 자기 라우트


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


def test_eval_new_ipo_dedup_slug_stable():
    """같은 rcept = 같은 slug → 허브 nonce 동일 → 재실행 시 409(멱등)."""
    row = {"corpName": "A", "rcept": "R1"}
    a = watch.eval_new_ipo(FakeDF([row]))[0]
    b = watch.eval_new_ipo(FakeDF([row]))[0]
    assert a["slug"] == b["slug"] == "R1"


# ── eval_new_orders ─────────────────────────────────────────────────
def test_eval_new_orders_threshold_and_guards():
    df = FakeDF(
        [
            {
                "stockCode": "111111",
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
    assert "book-to-bill" in m["notification"]["body"]
    assert "현대차" in m["notification"]["body"]
    assert m["notification"]["tag"] == "orders:111111"


def test_eval_new_orders_custom_threshold():
    df = FakeDF([{"stockCode": "555555", "bookToBill": 1.5, "recentRevenue": 1e12, "nContract": 3}])
    assert watch.eval_new_orders(df, min_book_to_bill=2.0) == []  # 임계 상향 → 제외
    assert len(watch.eval_new_orders(df, min_book_to_bill=1.0)) == 1
