"""DART 금액·단위 정규화 SSOT 회귀."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.providers.dart.parse.amount import (
    detectUnitLabel,
    detectUnitScale,
    parseAmount,
    parseAmountExpr,
    unitScaleToWon,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,234", 1234.0),
        ("△500", -500.0),
        ("▲ 500", -500.0),
        ("(1,234)", -1234.0),
        ("-12.5", -12.5),
        ("+12.5", 12.5),
        (0, 0.0),
        ("-", None),
        ("(주30)", None),
        ("매출액 123", None),
        ("1,2", None),
        ("", None),
        (float("nan"), None),
    ],
)
def test_parse_amount(raw, expected) -> None:
    assert parseAmount(raw) == expected


def test_parse_amount_expr_matches_scalar_contract() -> None:
    raw = ["1,234", "△500", "(1,234)", "-12.5", "+12.5", "-", "(주30)", "매출액 123", "1,2", None]
    result = pl.DataFrame({"raw": raw}).select(parseAmountExpr("raw").alias("value"))["value"].to_list()

    assert result == [parseAmount(value) for value in raw]


@pytest.mark.parametrize(
    ("caption", "label", "scale"),
    [
        ("(단위: 원)", "원", 1),
        ("단위 : 천원", "천원", 1_000),
        ("(단위: 백만원, %)", "백만원", 1_000_000),
        ("(단위: 억원, %)", "억원", 100_000_000),
        ("(단위: 십억원)", "십억원", 1_000_000_000),
        ("(단위: 조원)", "조원", 1_000_000_000_000),
        ("<TABLE>단위 : 원</TABLE>", "원", 1),
    ],
)
def test_unit_label_and_scale_share_one_mapping(caption: str, label: str, scale: int) -> None:
    assert detectUnitLabel(caption) == label
    assert unitScaleToWon(label) == scale
    assert detectUnitScale(caption) == scale


def test_unknown_unit_needs_explicit_default() -> None:
    assert detectUnitLabel("(단위: 광년)") is None
    assert detectUnitScale("(단위: 광년)") is None
    assert detectUnitScale("(단위: 광년)", defaultUnit="백만원") == 1_000_000
