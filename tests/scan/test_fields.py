"""scan fields catalog and spec screening contract."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_scan_fields_lists_all_sources():
    """scan("fields") exposes every planned source family."""
    import dartlab

    df = dartlab.scan("fields")

    assert {"field", "label", "source", "kind", "unit", "operatorSet", "coverage", "example", "notes"} <= set(
        df.columns
    )
    assert {"finance", "report", "docs", "krx", "krxIndex"} <= set(df["source"].to_list())


def test_scan_fields_searches_korean_and_english():
    """Field discovery supports both Korean labels and English field keys."""
    import dartlab

    roe = dartlab.scan("fields", "roe")
    sales = dartlab.scan("fields", "매출")

    assert "finance.ratio.roe" in roe["field"].to_list()
    assert any("sales" in field or "revenue" in field for field in sales["field"].to_list())


def test_screen_spec_filters_selects_and_sorts(monkeypatch):
    """screen(spec=...) applies where/select/sort using field value frames."""
    from dartlab.scan.builders.kr import fields as scan_fields
    from dartlab.scan.screen import scanScreen

    values = {
        "finance.ratio.roe": pl.DataFrame({"stockCode": ["000001", "000002"], "finance.ratio.roe": [12.0, 4.0]}),
        "valuation.pbr": pl.DataFrame({"stockCode": ["000001", "000002"], "valuation.pbr": [0.8, 1.5]}),
        "krx.marketCap": pl.DataFrame({"stockCode": ["000001", "000002"], "krx.marketCap": [1000, 2000]}),
    }

    monkeypatch.setattr(scan_fields, "_loadFieldValues", lambda field, spec: values[field])

    df = scanScreen(
        spec={
            "where": [{"field": "finance.ratio.roe", "op": ">", "value": 10}],
            "select": ["valuation.pbr", "krx.marketCap"],
            "sort": {"field": "valuation.pbr", "desc": False},
            "limit": 10,
        },
        verbose=False,
    )

    assert df.to_dicts() == [
        {
            "stockCode": "000001",
            "finance.ratio.roe": 12.0,
            "valuation.pbr": 0.8,
            "krx.marketCap": 1000,
        }
    ]


def test_screen_spec_rejects_unknown_op(monkeypatch):
    """Unsupported operators fail with a field-specific message."""
    from dartlab.scan.builders.kr import fields as scan_fields
    from dartlab.scan.screen import scanScreen

    monkeypatch.setattr(
        scan_fields,
        "_loadFieldValues",
        lambda field, spec: pl.DataFrame({"stockCode": ["000001"], field: [12.0]}),
    )

    with pytest.raises(ValueError, match="지원하지 않습니다"):
        scanScreen(
            spec={"where": [{"field": "finance.ratio.roe", "op": "startswith", "value": 10}]},
            verbose=False,
        )


def test_screen_spec_rejects_unit_mismatch():
    """Condition unit must match the catalog unit."""
    from dartlab.scan.screen import scanScreen

    with pytest.raises(ValueError, match="단위"):
        scanScreen(
            spec={"where": [{"field": "finance.ratio.roe", "op": ">", "value": 10, "unit": "원"}]},
            verbose=False,
        )


def test_screen_spec_rejects_missing_field():
    """Unknown fields point users back to scan('fields')."""
    from dartlab.scan.screen import scanScreen

    with pytest.raises(ValueError, match="scan\\('fields'\\)"):
        scanScreen(spec={"where": [{"field": "missing.field", "op": ">", "value": 1}]}, verbose=False)


def test_docs_condition_uses_search_hits(monkeypatch):
    """docs conditions summarize search index hits by stockCode."""
    import importlib

    search_mod = importlib.import_module("dartlab.providers.dart.search")
    from dartlab.scan.screen import scanScreen

    def fake_search(query, *, topK=10, scope="auto", **kwargs):
        return pl.DataFrame(
            {
                "stock_code": ["000001", "000001", "000002"],
                "score": [2.0, 1.0, 0.5],
                "text": ["HBM 투자", "HBM 증설", "기타"],
                "dartUrl": ["u1", "u2", "u3"],
            }
        )

    monkeypatch.setattr(search_mod, "search", fake_search)

    df = scanScreen(
        spec={"where": [{"field": "docs.content", "op": "contains", "value": "HBM"}], "limit": 5},
        verbose=False,
    )

    rows = sorted(df.to_dicts(), key=lambda row: row["stockCode"])
    assert rows[0]["stockCode"] == "000001"
    assert rows[0]["docsHitCount"] == 2
    assert rows[0]["docsBestScore"] == 2.0


def test_krx_index_is_select_context(monkeypatch):
    """krxIndex fields attach scalar market context and cannot filter stocks."""
    from dartlab.scan.builders.kr import fields as scan_fields
    from dartlab.scan.screen import scanScreen

    monkeypatch.setattr(
        scan_fields,
        "_loadFieldValues",
        lambda field, spec: pl.DataFrame({"stockCode": ["000001"], field: [12.0]}),
    )
    monkeypatch.setattr(scan_fields, "_loadKrxIndexScalar", lambda field, spec: 3000.0)

    df = scanScreen(
        spec={
            "where": [{"field": "finance.ratio.roe", "op": ">", "value": 10}],
            "select": ["krxIndex.KOSPI.close"],
        },
        verbose=False,
    )

    assert df["krxIndex.KOSPI.close"].to_list() == [3000.0]

    with pytest.raises(ValueError, match="시장 컨텍스트"):
        scanScreen(
            spec={"where": [{"field": "krxIndex.KOSPI.close", "op": ">", "value": 3000}]},
            verbose=False,
        )


def _roeFrame(monkeypatch, values):
    """finance.ratio.roe 값을 주입하되 @파생 참조는 실제 derivedValues 로 위임하는 헬퍼."""
    from dartlab.scan.builders.kr import fields as scan_fields

    codes = [f"{i:06d}" for i in range(len(values))]
    frame = pl.DataFrame({"stockCode": codes, "finance.ratio.roe": [float(v) for v in values]})

    def fake(field, spec):
        if field.startswith("@"):
            return (spec or {}).get("_derivedValues", {})[field[1:]]
        return frame

    monkeypatch.setattr(scan_fields, "_loadFieldValues", fake)
    return codes


def test_define_scalar_weighting_mul(monkeypatch):
    """리터럴 스칼라 곱은 가중치로 작동하고 base 단위를 보존한다 (가중 팩터 합성 핵심)."""
    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, [10.0, 20.0])
    df = scanScreen(
        spec={
            "define": {"w": {"op": "mul", "left": 0.5, "right": "finance.ratio.roe"}},
            "select": ["@w"],
            "sort": {"field": "@w", "desc": False},
        },
        verbose=False,
    )
    assert df["@w"].to_list() == [5.0, 10.0]


def test_define_scalar_offset_addsub(monkeypatch):
    """필드 ± 리터럴 오프셋 (임계 상대화). 필드÷스칼라 도 허용."""
    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, [10.0, 15.0])
    df = scanScreen(
        spec={
            "define": {"d": {"op": "sub", "left": "finance.ratio.roe", "right": 15.0}},
            "select": ["@d"],
            "sort": {"field": "@d", "desc": False},
        },
        verbose=False,
    )
    assert df["@d"].to_list() == [-5.0, 0.0]


def test_define_scalar_left_div_rejected(monkeypatch):
    """리터럴 ÷ 필드 는 역수 단위라 거부 (단위 대수 보호)."""
    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, [10.0])
    with pytest.raises(ValueError, match="역수 단위"):
        scanScreen(
            spec={"define": {"d": {"op": "div", "left": 1.0, "right": "finance.ratio.roe"}}, "select": ["@d"]},
            verbose=False,
        )


def test_define_both_literal_rejected(monkeypatch):
    """양변 리터럴은 무의미하므로 거부."""
    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, [10.0])
    with pytest.raises(ValueError, match="양변 리터럴"):
        scanScreen(
            spec={"define": {"d": {"op": "add", "left": 1.0, "right": 2.0}}, "select": ["@d"]},
            verbose=False,
        )


def test_define_winsorize_clips_universe_tails(monkeypatch):
    """winsorize 는 유니버스 분위 [lower,upper] 로 꼬리를 절단한다 (아웃라이어 z 지배 방어)."""
    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, list(range(101)))  # 0..100
    df = scanScreen(
        spec={
            "define": {"w": {"op": "winsorize", "field": "finance.ratio.roe", "lower": 0.1, "upper": 0.9}},
            "select": ["@w"],
        },
        verbose=False,
    )
    vs = df["@w"].to_list()
    assert min(vs) >= 10.0 - 1e-6
    assert max(vs) <= 90.0 + 1e-6


def test_define_clip_absolute_bounds(monkeypatch):
    """clip 은 절대 경계 [min,max] 로 제한한다."""
    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, [-5.0, 50.0, 200.0])
    df = scanScreen(
        spec={
            "define": {"c": {"op": "clip", "field": "finance.ratio.roe", "min": 0.0, "max": 100.0}},
            "select": ["@c"],
            "sort": {"field": "@c", "desc": False},
        },
        verbose=False,
    )
    assert df["@c"].to_list() == [0.0, 50.0, 100.0]


def test_define_nan_does_not_poison_zscore_or_winsorize(monkeypatch):
    """NaN 1개가 group mean/std·quantile 을 오염시켜 전 종목 NaN 이 되면 안 된다 (조용한 오답 차단).

    polars is_not_null() 은 NaN 을 안 거른다. krx.roc12 처럼 지표 window 부족으로 NaN 이 섞이면
    zscore/winsorize 가 전멸했었다. _finiteOnly 가 비유한값을 null 로 승격해 해당 종목만 gap 이 된다.
    """
    import math

    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, [1.0, 2.0, 3.0, 4.0, float("nan")])
    df = scanScreen(
        spec={
            "define": {
                "z": {"op": "zscore", "field": "finance.ratio.roe"},
                "w": {"op": "winsorize", "field": "@z", "lower": 0.1, "upper": 0.9},
            },
            "select": ["@w"],
        },
        verbose=False,
    )
    vals = df["@w"].to_list()
    finite = [v for v in vals if v is not None and not math.isnan(v)]
    assert len(finite) == 4  # NaN 종목만 탈락, 나머지 4개는 유한한 z
    assert all(math.isfinite(v) for v in finite)


def test_define_abs_and_log(monkeypatch):
    """abs 는 절대값, log 는 양수만 자연로그 (비양수 null)."""
    from dartlab.scan.screen import scanScreen

    _roeFrame(monkeypatch, [-4.0, 9.0])
    dfAbs = scanScreen(
        spec={
            "define": {"a": {"op": "abs", "field": "finance.ratio.roe"}},
            "select": ["@a"],
            "sort": {"field": "@a", "desc": False},
        },
        verbose=False,
    )
    assert dfAbs["@a"].to_list() == [4.0, 9.0]

    dfLog = scanScreen(
        spec={"define": {"l": {"op": "log", "field": "finance.ratio.roe"}}, "select": ["@l"]},
        verbose=False,
    )
    # -4 -> null (비양수), 9 -> ln 9
    logs = sorted([v for v in dfLog["@l"].to_list() if v is not None])
    assert len(logs) == 1
    assert abs(logs[0] - 2.1972245773) < 1e-6


class TestScreenUniverseIndexName:
    """indexName 은 받아만 두는 키가 아니라 실제로 시장을 좁힌다.

    실측(2026-08-06). 코스피만 요구한 스크리닝이 코스닥을 섞어 돌려줬다. 이 모듈은
    "조건을 못 읽었으면 빈 결과가 아니라 못 읽었다고 말해야 한다" 는 계약으로 지어졌는데
    이 키만 읽은 척하고 버리고 있었다. 조용히 틀린 답이 가장 나쁘다.
    """

    @staticmethod
    def _listing() -> pl.DataFrame:
        return pl.DataFrame(
            {
                "종목코드": ["005930", "000660", "247540", "217270"],
                "시장구분": ["유가", "유가", "코스닥", "코넥스"],
            }
        )

    def test코스피만남긴다(self, monkeypatch):
        """섞여 나오면 사용자는 코스닥 종목을 코스피로 읽는다."""
        import dartlab
        from dartlab.scan.builders.kr.report import fields

        monkeypatch.setattr(dartlab, "listing", self._listing)

        assert sorted(fields._screenUniverse("KOSPI")["stockCode"].to_list()) == ["000660", "005930"]

    def test코스닥과코넥스도가른다(self, monkeypatch):
        """시장 이름 하나만 되면 나머지는 못 쓰는 것과 같다."""
        import dartlab
        from dartlab.scan.builders.kr.report import fields

        monkeypatch.setattr(dartlab, "listing", self._listing)

        assert fields._screenUniverse("KOSDAQ")["stockCode"].to_list() == ["247540"]
        assert fields._screenUniverse("KONEX")["stockCode"].to_list() == ["217270"]

    def test지정없으면전부남긴다(self, monkeypatch):
        """기본은 전 상장이다. 말없이 좁히는 것도 같은 종류의 거짓말이다."""
        import dartlab
        from dartlab.scan.builders.kr.report import fields

        monkeypatch.setattr(dartlab, "listing", self._listing)

        assert len(fields._screenUniverse()["stockCode"].to_list()) == 4

    def test모르는이름은조용히무시하지않는다(self, monkeypatch):
        """무시하면 전 상장 결과가 그 시장 결과인 척 나간다."""
        import dartlab
        from dartlab.scan.builders.kr.report import fields

        monkeypatch.setattr(dartlab, "listing", self._listing)

        with pytest.raises(ValueError, match="indexName"):
            fields._screenUniverse("NASDAQ")
