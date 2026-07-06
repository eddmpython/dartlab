"""팩터 레지스트리 SSOT : 등록/해제·변화식·base점수 인식 + 자동흡수 end-to-end (순수 유닛).

Covers:
- register/unregister 멱등 + 하류 조회(factorNames·factorBetaMap) 즉시 반영.
- macroChange: level=차분, price=수익률.
- baseScoreExpr: baseScore|score|consensus 인식 + 부재 오류.
- 자동흡수 end-to-end: 팩터 1행 등록 → macroDaily 열 + macroBetaByCodeWide 베타 열 자동 (하류 수정 0).
"""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from dartlab.simulate import factors as fx


def _cleanup(name: str):
    """테스트 등록 팩터 정리 (레지스트리 전역 오염 방지)."""
    fx.unregisterMacroFactor(name)


def testRegisterUnregisterIdempotent():
    n0 = len(fx.factorNames())
    mf = fx.MacroFactor("copper", "testSrc", "COPPER", "price", "구리")
    try:
        fx.registerMacroFactor(mf)
        fx.registerMacroFactor(mf)  # 재등록 = 교체 (중복 없음)
        assert fx.factorNames().count("copper") == 1
        assert fx.factorBetaMap()["copper"] == "copperBeta"  # 규약 컬럼명
        assert len(fx.factorNames()) == n0 + 1
    finally:
        _cleanup("copper")
    assert "copper" not in fx.factorNames()  # 해제 대칭


def testMacroChangeKinds():
    lvl = pl.DataFrame({"rate": [3.0, 3.5]}).select(d=fx.macroChange("rate"))
    assert abs(lvl["d"][1] - 0.5) < 1e-12  # level = 차분 (%p)
    px = pl.DataFrame({"oil": [100.0, 110.0]}).select(d=fx.macroChange("oil"))
    assert abs(px["d"][1] - 0.10) < 1e-12  # price = 수익률


def testBaseScoreExprDetection():
    for col in ("baseScore", "score", "consensus"):
        df = pl.DataFrame({"code": ["a"], col: [1.5]})
        assert df.select(v=fx.baseScoreExpr(df))["v"][0] == 1.5
    with pytest.raises(ValueError):
        fx.baseScoreExpr(pl.DataFrame({"code": ["a"]}))


def testAutoAbsorbNewFactorEndToEnd(tmp_path, monkeypatch):
    # 자동흡수: 팩터 1행 등록 + 소스 parquet 존재 → macroDaily 열 + 베타 열이 하류 수정 0 으로 등장
    from dartlab.simulate import table

    d = [(date(2026, 1, 1) + timedelta(days=i)) for i in range(60)]
    src = tmp_path / "macro/testSrc"
    src.mkdir(parents=True)
    pl.DataFrame({"seriesId": ["COPPER"] * 60, "date": d, "value": [100.0 + i for i in range(60)]}).write_parquet(
        src / "observations.parquet"
    )
    dates = [x.strftime("%Y%m%d") for x in d]
    px = pl.DataFrame(
        {
            "date": dates * 1,
            "code": ["a"] * 60,
            "close": [1000.0 * (1 + 0.02 * i) for i in range(60)],
            "shares": [1.0] * 60,
            "mktcap": [1.0] * 60,
        }
    )
    monkeypatch.setattr(table, "dailyPrices", lambda baseDir=None: px)
    try:
        fx.registerMacroFactor(fx.MacroFactor("copper", "testSrc", "COPPER", "price", "구리"))
        macro = table.macroDaily(tmp_path)
        assert "copper" in macro.columns  # 패널 자동흡수 (macroDaily 수정 0)
        betas = table.macroBetaByCodeWide(dates[-1], baseDir=tmp_path)
        assert "copperBeta" in betas.columns  # 베타 열 자동흡수 (macroBetaByCodeWide 수정 0)
    finally:
        _cleanup("copper")
