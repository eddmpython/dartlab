"""screen spec `define` 파생 필드 AST 테스트.

합성 필드 값을 monkeypatch 로 주입해 파생 산술·단위전파·위상정렬·순환·div0·회귀를
결정적으로 검증한다 (네트워크·prebuild 불요).
"""

from __future__ import annotations

import polars as pl
import pytest

import dartlab.scan.builders.kr.report.fields as F
from dartlab.scan.builders.kr.report.fields import (
    _computeDerived,
    _deriveUnit,
    _topoSortDefines,
    executeScreenSpec,
)

pytestmark = pytest.mark.unit

# 합성 필드 우주 (stockCode A/B/C). (프레임, 단위).
_FIELDS: dict[str, tuple[pl.DataFrame, str]] = {
    "finance.account.cash": (
        pl.DataFrame({"stockCode": ["A", "B", "C"], "finance.account.cash": [100.0, 50.0, None]}),
        "원",
    ),
    "finance.account.debt": (
        pl.DataFrame({"stockCode": ["A", "B", "C"], "finance.account.debt": [40.0, 80.0, 10.0]}),
        "원",
    ),
    "krx.marketCap": (pl.DataFrame({"stockCode": ["A", "B", "C"], "krx.marketCap": [200.0, 200.0, 200.0]}), "원"),
    "finance.ratio.debtRatio": (
        pl.DataFrame({"stockCode": ["A", "B", "C"], "finance.ratio.debtRatio": [50.0, 150.0, 20.0]}),
        "%",
    ),
    "finance.account.op": (
        pl.DataFrame({"stockCode": ["A", "B", "C"], "finance.account.op": [100.0, 100.0, 100.0]}),
        "원",
    ),
    "finance.account.interest": (
        pl.DataFrame({"stockCode": ["A", "B", "C"], "finance.account.interest": [10.0, 0.0, 5.0]}),
        "원",
    ),
}


@pytest.fixture
def patched(monkeypatch):
    def fakeLoad(field, spec):
        field = F._normalizeField(field)
        if field.startswith("@"):
            return (spec or {}).get("_derivedValues", {})[field[1:]]
        if field in _FIELDS:
            return _FIELDS[field][0]
        raise ValueError(f"unknown field {field}")

    def fakeMeta(field, spec=None):
        if field.startswith("@"):
            unit = (spec or {}).get("_derivedUnits", {})[field[1:]]
            return {"field": field, "kind": "number", "unit": unit, "operatorSet": F._NUMERIC_OPS}
        if field in _FIELDS:
            return {"field": field, "kind": "number", "unit": _FIELDS[field][1], "operatorSet": F._NUMERIC_OPS}
        raise ValueError(f"unknown field {field}")

    monkeypatch.setattr(F, "_loadFieldValues", fakeLoad)
    monkeypatch.setattr(F, "_fieldMeta", fakeMeta)


def _asDict(df, col):
    return dict(zip(df["stockCode"].to_list(), df[col].to_list(), strict=True))


class TestDeriveUnit:
    def test_div_same_unit_dimensionless(self):
        assert _deriveUnit("div", "원", "원", "x") == "배"

    def test_div_diff_unit(self):
        assert _deriveUnit("div", "원", "주", "x") == "원/주"

    def test_sub_same_unit(self):
        assert _deriveUnit("sub", "원", "원", "x") == "원"

    def test_add_mismatch_raises(self):
        with pytest.raises(ValueError, match="단위 불일치"):
            _deriveUnit("add", "원", "%", "x")

    def test_mul_with_dimensionless(self):
        assert _deriveUnit("mul", "원", "배", "x") == "원"


class TestTopoSort:
    def test_orders_deps_first(self):
        order = _topoSortDefines(
            {
                "b": {"op": "div", "left": "@a", "right": "krx.marketCap"},
                "a": {"op": "sub", "left": "finance.account.cash", "right": "finance.account.debt"},
            }
        )
        assert order.index("a") < order.index("b")

    def test_cycle_raises(self):
        with pytest.raises(ValueError, match="순환"):
            _topoSortDefines(
                {
                    "a": {"op": "div", "left": "@b", "right": "krx.marketCap"},
                    "b": {"op": "div", "left": "@a", "right": "krx.marketCap"},
                }
            )

    def test_undefined_ref_raises(self):
        with pytest.raises(ValueError, match="미정의"):
            _topoSortDefines({"a": {"op": "div", "left": "@missing", "right": "krx.marketCap"}})


class TestComputeDerived:
    def test_sub_and_div_chain(self, patched):
        spec = {
            "define": {
                "netCash": {"op": "sub", "left": "finance.account.cash", "right": "finance.account.debt"},
                "netCashToCap": {"op": "div", "left": "@netCash", "right": "krx.marketCap"},
            }
        }
        vals, units = _computeDerived(spec)
        assert units["netCash"] == "원"
        assert units["netCashToCap"] == "배"  # 원/원 -> 배(무차원)
        nc = _asDict(vals["netCash"], "@netCash")
        assert nc["A"] == 60.0 and nc["B"] == -30.0
        assert nc["C"] is None  # cash None -> null 전파
        ncc = _asDict(vals["netCashToCap"], "@netCashToCap")
        assert ncc["A"] == pytest.approx(0.3)

    def test_div_by_zero_is_null(self, patched):
        spec = {"define": {"icr": {"op": "div", "left": "finance.account.op", "right": "finance.account.interest"}}}
        vals, _ = _computeDerived(spec)
        icr = _asDict(vals["icr"], "@icr")
        assert icr["A"] == 10.0  # 100/10
        assert icr["B"] is None  # 100/0 -> null
        assert icr["C"] == 20.0  # 100/5

    def test_unit_mismatch_add_raises(self, patched):
        spec = {"define": {"bad": {"op": "add", "left": "finance.account.cash", "right": "finance.ratio.debtRatio"}}}
        with pytest.raises(ValueError, match="단위 불일치"):
            _computeDerived(spec)

    def test_bad_op_raises(self, patched):
        spec = {"define": {"x": {"op": "pow", "left": "finance.account.cash", "right": "finance.account.debt"}}}
        with pytest.raises(ValueError, match="지원하지 않는 define op"):
            _computeDerived(spec)

    def test_empty_define(self):
        assert _computeDerived({}) == ({}, {})
        assert _computeDerived({"where": []}) == ({}, {})


class TestExecuteScreenSpecDefine:
    def test_define_in_where_select_sort(self, patched):
        spec = {
            "define": {
                "netCash": {"op": "sub", "left": "finance.account.cash", "right": "finance.account.debt"},
                "netCashToCap": {"op": "div", "left": "@netCash", "right": "krx.marketCap"},
            },
            "where": [
                {"field": "@netCashToCap", "op": ">", "value": 0.2},
                {"field": "finance.ratio.debtRatio", "op": "<", "value": 100},
            ],
            "select": ["@netCash"],
            "sort": {"field": "@netCashToCap", "desc": True},
            "limit": 10,
        }
        out = executeScreenSpec(spec)
        assert out["stockCode"].to_list() == ["A"]  # B netCashToCap<0, C null
        assert "@netCashToCap" in out.columns and "@netCash" in out.columns

    def test_no_define_regression(self, patched):
        spec = {"where": [{"field": "finance.ratio.debtRatio", "op": "<", "value": 100}]}
        out = executeScreenSpec(spec)
        assert set(out["stockCode"].to_list()) == {"A", "C"}
        assert "_derivedValues" not in spec  # 원본 spec 무변경


class TestLoadNote:
    def test_note_item_resolution(self, monkeypatch):
        import dartlab.scan.note as notemod

        df = pl.DataFrame(
            {
                "stockCode": ["A", "A", "B"],
                "account": ["재공품", "상품", "재공품"],
                "label": ["재공품", "상품", "재공품"],
                "period": ["2024", "2024", "2024"],
                "value": ["100", "50", "200"],
                "valueNum": [100.0, 50.0, 200.0],
            }
        )
        monkeypatch.setattr(notemod, "scanNote", lambda concept, **k: df)
        out = F._loadNote("note.inventory@재공품")
        d = _asDict(out, "note.inventory@재공품")
        assert d["A"] == 100.0 and d["B"] == 200.0

    def test_note_requires_item(self):
        with pytest.raises(ValueError, match="항목 지정"):
            F._loadNote("note.inventory")
