"""복합축 승격 필드(axis.*) 테스트 + 컬럼 드리프트 가드.

레지스트리 정합·raw 스캐너 해소·캐시·컬럼부재·실패 흡수를 합성 데이터로 검증하고,
requires_data 로 실 스캐너 출력에 선언 컬럼이 실재하는지(드리프트) 검증한다.
"""

from __future__ import annotations

import importlib

import polars as pl
import pytest

import dartlab.scan.builders.kr.report.fields as F
from dartlab.scan.builders.kr.report.fieldCatalog import _COMPOSITE_AXIS_FIELDS, _catalog


@pytest.mark.unit
class TestRegistry:
    def test_modules_and_fns_importable(self):
        for field, r in _COMPOSITE_AXIS_FIELDS.items():
            mod = importlib.import_module(r["module"])
            assert hasattr(mod, r["fn"]), f"{field}: {r['module']}.{r['fn']} 없음"
            assert r["kind"] in ("number", "text")
            assert r["col"] and r["label"] and r["unit"]

    def test_registered_in_catalog(self):
        cat = _catalog()
        axisFields = set(cat.filter(pl.col("source") == "axis")["field"].to_list())
        assert axisFields == set(_COMPOSITE_AXIS_FIELDS), "카탈로그 axis 필드와 레지스트리 불일치"


@pytest.mark.unit
class TestLoadCompositeAxis:
    def test_resolves_native_column_and_caches(self, monkeypatch):
        import dartlab.scan.debt as debtmod

        fake = pl.DataFrame({"stockCode": ["A", "B"], "ICR": [5.0, 1.5], "위험등급": ["안전", "고위험"]})
        calls = {"n": 0}

        def fakeScan(**k):
            calls["n"] += 1
            return fake

        monkeypatch.setattr(debtmod, "scanDebt", fakeScan)
        spec = {"_axisCache": {}}
        out = F._loadCompositeAxis("axis.debt.icr", spec)
        assert out.columns == ["stockCode", "axis.debt.icr"]
        assert dict(zip(out["stockCode"].to_list(), out["axis.debt.icr"].to_list(), strict=True)) == {
            "A": 5.0,
            "B": 1.5,
        }
        # 같은 스캐너 두 번째 필드는 캐시 재사용 (scanDebt 1회만 호출)
        out2 = F._loadCompositeAxis("axis.debt.riskGrade", spec)
        assert dict(zip(out2["stockCode"].to_list(), out2["axis.debt.riskGrade"].to_list(), strict=True)) == {
            "A": "안전",
            "B": "고위험",
        }
        assert calls["n"] == 1

    def test_korean_stockcol_handled(self, monkeypatch):
        import dartlab.scan.audit as auditmod

        fake = pl.DataFrame({"종목코드": ["A"], "opinion": ["적정의견"]})
        monkeypatch.setattr(auditmod, "scanAudit", lambda **k: fake)
        out = F._loadCompositeAxis("axis.audit.opinion", {"_axisCache": {}})
        assert out.columns == ["stockCode", "axis.audit.opinion"]
        assert out["axis.audit.opinion"][0] == "적정의견"

    def test_missing_column_returns_empty(self, monkeypatch):
        import dartlab.scan.financial.quality as qmod

        monkeypatch.setattr(qmod, "scanQuality", lambda **k: pl.DataFrame({"stockCode": ["A"]}))
        out = F._loadCompositeAxis("axis.quality.cfToNi", {"_axisCache": {}})
        assert out.height == 0
        assert out.columns == ["stockCode", "axis.quality.cfToNi"]

    def test_scanner_failure_absorbed(self, monkeypatch):
        import dartlab.scan.audit as auditmod

        def boom(**k):
            raise ValueError("data missing")

        monkeypatch.setattr(auditmod, "scanAudit", boom)
        out = F._loadCompositeAxis("axis.audit.riskLevel", {"_axisCache": {}})
        assert out.height == 0


@pytest.mark.requires_data
@pytest.mark.heavy
class TestColumnDrift:
    def test_native_columns_present_in_scanner_output(self):
        import gc
        from collections import defaultdict

        byScanner: dict[tuple, list[tuple[str, str]]] = defaultdict(list)
        for field, r in _COMPOSITE_AXIS_FIELDS.items():
            byScanner[(r["module"], r["fn"])].append((field, r["col"]))
        # 스캐너 하나씩 로드/검증/해제 (Polars 네이티브 메모리 누적 회피).
        for (module, fn), fields in byScanner.items():
            mod = importlib.import_module(module)
            df = getattr(mod, fn)(verbose=False)
            cols = set(df.columns)
            for field, col in fields:
                assert col in cols, f"{field}: 컬럼 {col!r} 드리프트. {fn} 출력={sorted(cols)}"
            del df
            gc.collect()
