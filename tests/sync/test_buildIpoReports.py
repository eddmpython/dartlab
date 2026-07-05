"""buildIpoReports 베이크 회귀 (HF·DART 무의존, 순수 로직).

_discover 발행사 그룹핑(최신 FULL + 확정 doc, FULL 없으면 제외) + build 산출 parquet 이 왓치 소비용
scan 호환 스칼라 + reportJson(전체 IpoReport) 컬럼을 담는지. listFilings·buildIpoReport 는 mock.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "sync" / "buildIpoReports.py"


def _load():
    spec = importlib.util.spec_from_file_location("buildIpoReports", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _listDf(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(
        rows,
        schema={
            "corp_code": pl.Utf8,
            "corp_name": pl.Utf8,
            "corp_cls": pl.Utf8,
            "stock_code": pl.Utf8,
            "report_nm": pl.Utf8,
            "rcept_no": pl.Utf8,
            "rcept_dt": pl.Utf8,
        },
    )


def test_discover_groups_full_and_confirmation(monkeypatch):
    mod = _load()
    df = _listDf(
        [
            {
                "corp_code": "C1",
                "corp_name": "레몬헬스케어",
                "corp_cls": "E",
                "stock_code": "",
                "report_nm": "증권신고서(지분증권)",
                "rcept_no": "20260508000400",
                "rcept_dt": "20260508",
            },
            {
                "corp_code": "C1",
                "corp_name": "레몬헬스케어",
                "corp_cls": "E",
                "stock_code": "",
                "report_nm": "[기재정정]증권신고서(지분증권)",
                "rcept_no": "20260612000375",
                "rcept_dt": "20260612",
            },
            {
                "corp_code": "C1",
                "corp_name": "레몬헬스케어",
                "corp_cls": "E",
                "stock_code": "",
                "report_nm": "[발행조건확정]증권신고서(지분증권)",
                "rcept_no": "20260623000235",
                "rcept_dt": "20260623",
            },
            {
                "corp_code": "C1",
                "corp_name": "레몬헬스케어",
                "corp_cls": "E",
                "stock_code": "",
                "report_nm": "투자설명서",
                "rcept_no": "20260618000073",
                "rcept_dt": "20260618",
            },
            {
                "corp_code": "C2",
                "corp_name": "기도산업",
                "corp_cls": "E",
                "stock_code": "",
                "report_nm": "증권신고서(지분증권)",
                "rcept_no": "20260626000715",
                "rcept_dt": "20260626",
            },
            {
                "corp_code": "C3",
                "corp_name": "확정만",
                "corp_cls": "E",
                "stock_code": "",
                "report_nm": "[발행조건확정]증권신고서(지분증권)",
                "rcept_no": "20260601000001",
                "rcept_dt": "20260601",
            },
        ]
    )
    monkeypatch.setattr("dartlab.gather.dart.disclosure.listFilings", lambda *a, **k: df)
    out = mod._discover(client=object(), dateFrom=None, verbose=False)
    byCorp = {it["full"]["corp_code"]: it for it in out}
    assert set(byCorp) == {"C1", "C2"}  # C3 은 FULL 없음(확정만) → 제외
    assert byCorp["C1"]["full"]["rcept_no"] == "20260612000375"  # 확정 doc 아닌 최신 FULL(정정본)
    assert byCorp["C1"]["conf"]["rcept_no"] == "20260623000235"
    assert byCorp["C2"]["conf"] is None


def test_build_emits_scan_compatible_and_reportjson(monkeypatch, tmp_path):
    mod = _load()
    monkeypatch.setattr("dartlab.config.dataDir", str(tmp_path))
    monkeypatch.setattr("dartlab.core.dartClient.DartClient", lambda *a, **k: object())
    monkeypatch.setattr(
        mod,
        "_discover",
        lambda client, dateFrom, verbose: [
            {
                "full": {
                    "rcept_no": "20260626000715",
                    "corp_code": "C2",
                    "corp_name": "기도산업",
                    "rcept_dt": "20260626",
                    "report_nm": "증권신고서(지분증권)",
                    "_isSpac": False,
                },
                "conf": None,
            }
        ],
    )

    def _fakeBuild(rcept, *, corpName=None, confirmationRcept=None):
        return {
            "title": f"{corpName} 공모분석",
            "summary": {
                "priceBand": [24800, 28400],
                "subscription": "2026.08.11 ~ 08.12",
                "peerPer": 10.01,
                "isLoss": False,
            },
            "sections": [{"title": "공모 개요", "badge": "✓ 검증", "rows": [["희망공모가", "24,800원 ~ 28,400원"]]}],
            "markdown": "# 기도산업 공모분석",
        }

    monkeypatch.setattr("dartlab.story.ipoReport.buildIpoReport", _fakeBuild)

    dest = mod.build(verbose=False)
    df = pl.read_parquet(dest)
    assert df.height == 1
    row = df.row(0, named=True)
    # 왓치 eval_new_ipo 소비용 scan 호환 스칼라
    assert row["rcept"] == "20260626000715" and row["corpName"] == "기도산업"
    assert row["priceBandLow"] == 24800.0 and row["priceBandHigh"] == 28400.0
    assert row["subscription"] == "2026.08.11 ~ 08.12" and row["appliedPer"] == 10.01
    assert row["isSpac"] is False
    # 터미널 ipoReportSource 직독용 전체 리포트 JSON round-trip
    report = json.loads(row["reportJson"])
    assert report["title"] == "기도산업 공모분석"
    assert report["sections"][0]["title"] == "공모 개요"
