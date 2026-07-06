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


# ── Phase 3: 시계열(temporal) 노드 ──


def _series(rows: dict[str, list], k: int) -> pl.DataFrame:
    data: dict[str, list] = {"stockCode": list(rows)}
    for i in range(k):
        data[f"_t{i}"] = [rows[s][i] for s in rows]
    return pl.DataFrame(data)


@pytest.fixture
def temporal(monkeypatch):
    # 오래된→최신 순 [t0,t1,t2]. 최근 n 개를 슬라이스해 위치 컬럼으로.
    full = {
        "finance.account.sales": {"A": [20.0, 30.0, 60.0], "B": [None, None, 50.0], "C": [10.0, 10.0, 10.0]},
        "finance.account.operating_profit": {"A": [10.0, 20.0, 30.0], "B": [5.0, None, 15.0], "C": [-1.0, 2.0, 3.0]},
    }

    def fakeSeries(field, n):
        rows = full[field]
        k = min(n, 3)
        sliced = {s: v[-k:] for s, v in rows.items()}
        return _series(sliced, k), k

    def fakeMeta(field, spec=None):
        return {"field": field, "kind": "number", "unit": "원", "operatorSet": F._NUMERIC_OPS}

    monkeypatch.setattr(F, "_loadFieldSeries", fakeSeries)
    monkeypatch.setattr(F, "_fieldMeta", fakeMeta)


class TestTemporal:
    def test_mean_min_max(self, temporal):
        op = "finance.account.operating_profit"
        m = _asDict(F._evalTemporalNode("m", {"op": "mean", "field": op, "years": 3}, {})[0], "@m")
        assert m["A"] == 20.0 and m["B"] == 10.0 and m["C"] == pytest.approx(4 / 3)
        mn = _asDict(F._evalTemporalNode("m", {"op": "min", "field": op, "years": 3}, {})[0], "@m")
        assert mn["A"] == 10.0 and mn["B"] == 5.0 and mn["C"] == -1.0
        mx = _asDict(F._evalTemporalNode("m", {"op": "max", "field": op, "years": 3}, {})[0], "@m")
        assert mx["A"] == 30.0 and mx["B"] == 15.0 and mx["C"] == 3.0

    def test_cagr_needs_positive_endpoints(self, temporal):
        df, unit = F._evalTemporalNode("g", {"op": "cagr", "field": "finance.account.sales", "years": 3}, {})
        g = _asDict(df, "@g")
        assert unit == "배"
        assert g["A"] == pytest.approx(3**0.5 - 1)  # (60/20)^(1/2)-1
        assert g["B"] is None  # 시작 결측
        assert g["C"] == pytest.approx(0.0)  # 10→10

    def test_yoy_last_two(self, temporal):
        y = _asDict(F._evalTemporalNode("y", {"op": "yoy", "field": "finance.account.operating_profit"}, {})[0], "@y")
        assert y["A"] == pytest.approx(0.5)  # (30-20)/20
        assert y["C"] == pytest.approx(0.5)  # (3-2)/2
        assert y["B"] is None  # 직전 결측

    def test_slope_ols_skips_null(self, temporal):
        s = _asDict(
            F._evalTemporalNode("s", {"op": "slope", "field": "finance.account.operating_profit", "years": 3}, {})[0],
            "@s",
        )
        assert s["A"] == pytest.approx(10.0)  # 10,20,30 완전 직선
        assert s["B"] == pytest.approx(5.0)  # (5@0, 15@2) → 기울기 5
        assert s["C"] == pytest.approx(2.0)  # -1,2,3

    def test_years_min_two(self, temporal):
        with pytest.raises(ValueError, match="years 는 2 이상"):
            F._evalTemporalNode("x", {"op": "mean", "field": "finance.account.sales", "years": 1}, {})

    def test_field_must_be_source(self, temporal):
        with pytest.raises(ValueError, match="원천 시계열 필드"):
            F._evalTemporalNode("x", {"op": "cagr", "field": "@ref"}, {})

    def test_non_series_source_raises(self):
        with pytest.raises(ValueError, match="finance.account"):
            F._loadFieldSeries("valuation.pbr", 3)


# ── Phase 3: 상대(relative) 노드 ──


class TestRelative:
    def test_percentile_whole_universe(self, patched):
        df, unit = F._evalRelativeNode("p", {"op": "percentile", "field": "finance.ratio.debtRatio"}, {}, {}, {})
        d = _asDict(df, "@p")
        assert unit == "백분위"
        # 20(C)<50(A)<150(B) → 0 / 50 / 100
        assert d["C"] == 0.0 and d["A"] == 50.0 and d["B"] == 100.0

    def test_zscore_whole_universe(self, patched):
        df, unit = F._evalRelativeNode("z", {"op": "zscore", "field": "finance.ratio.debtRatio"}, {}, {}, {})
        d = _asDict(df, "@z")
        assert unit == "표준편차"
        assert d["A"] == pytest.approx(-0.3428, abs=1e-3)
        assert d["B"] == pytest.approx(1.1263, abs=1e-3)
        assert d["C"] == pytest.approx(-0.7835, abs=1e-3)

    def test_percentile_by_industry(self, patched, monkeypatch):
        monkeypatch.setattr(
            F, "_industryMap", lambda: pl.DataFrame({"stockCode": ["A", "B", "C"], "_grp": ["g1", "g1", "g2"]})
        )
        df, _ = F._evalRelativeNode(
            "p", {"op": "percentile", "field": "finance.ratio.debtRatio", "by": "industry"}, {}, {}, {}
        )
        d = _asDict(df, "@p")
        assert d["A"] == 0.0 and d["B"] == 100.0  # g1: 50<150
        assert d["C"] is None  # g2 단독 → 순위 불가(null)

    def test_industry_unprovisioned_raises(self, patched, monkeypatch):
        monkeypatch.setattr(F, "_industryMap", lambda: pl.DataFrame({"stockCode": [], "_grp": []}))
        with pytest.raises(ValueError, match="업종 매핑"):
            F._evalRelativeNode(
                "p", {"op": "percentile", "field": "finance.ratio.debtRatio", "by": "industry"}, {}, {}, {}
            )

    def test_bad_by_raises(self, patched):
        with pytest.raises(ValueError, match="지원하지 않는 by"):
            F._evalRelativeNode("p", {"op": "percentile", "field": "finance.ratio.debtRatio", "by": "대충"}, {}, {}, {})

    def test_missing_field_raises(self, patched):
        with pytest.raises(ValueError, match="field"):
            F._evalRelativeNode("p", {"op": "percentile"}, {}, {}, {})

    def test_relative_of_derived_ref(self, patched):
        # 파생 @nc 위에 상대 백분위 (topo 순 의존 해소).
        spec = {
            "define": {
                "nc": {"op": "sub", "left": "finance.account.cash", "right": "finance.account.debt"},
                "ncPct": {"op": "percentile", "field": "@nc"},
            }
        }
        vals, units = _computeDerived(spec)
        assert units["ncPct"] == "백분위"
        d = _asDict(vals["ncPct"], "@ncPct")
        # nc: A=60, B=-30, C=null(cash 결측) → 비결측 2점 -30(B)<60(A)
        assert d["B"] == 0.0 and d["A"] == 100.0
        assert "C" not in d  # null operand 제외


class TestExecuteScreenSpecPhase3:
    def test_temporal_in_where(self, temporal):
        spec = {
            "define": {"opMin": {"op": "min", "field": "finance.account.operating_profit", "years": 3}},
            "where": [{"field": "@opMin", "op": ">", "value": 0}],
            "select": ["@opMin"],
            "sort": {"field": "@opMin", "desc": True},
        }
        out = executeScreenSpec(spec)
        assert set(out["stockCode"].to_list()) == {"A", "B"}  # C min=-1 제외
        assert out["stockCode"].to_list()[0] == "A"  # min 큰 순 정렬


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
