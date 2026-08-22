"""syncRecent 의 (bsns_year, reprt_code) 단위 누락 판정 회귀. 네트워크 0.

2026-08-21 실측: DART 재무 API 는 분기당 최신 본문 버전 rcept 하나만 돌려준다. rcept 단위 판정은
원본과 정정이 함께 있는 분기를 매 run 재수집하고 "잔여 누락 207건" 으로 찍었다(데이터는 다 있었다).
"""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def _loadSyncRecent():
    path = ROOT / ".github" / "scripts" / "sync" / "syncRecent.py"
    spec = importlib.util.spec_from_file_location("syncRecent", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(rceptNo: str, reportNm: str, rceptDt: str) -> dict:
    return {"rcept_no": rceptNo, "report_nm": reportNm, "rcept_dt": rceptDt}


ORIGINAL = _row("20260814003797", "반기보고서 (2026.06)", "20260814")
CORRECTION = _row("20260819000055", "[기재정정]반기보고서 (2026.06)", "20260819")
ATTACHMENT = _row("20260820000011", "[첨부정정]반기보고서 (2026.06)", "20260820")
TODAY = datetime(2026, 8, 22)


def test_key_satisfied_when_any_version_present():
    """카카오 사례: parquet 은 정정 rcept 만 들고 있어도 그 분기는 충족. 원본 rcept 를 쫓지 않는다."""
    mod = _loadSyncRecent()
    assert mod._keyMissingRows([ORIGINAL, CORRECTION], {"20260819000055"}, today=TODAY) == []
    assert mod._keyMissingRows([ORIGINAL], {"20260814003797"}, today=TODAY) == []


def test_key_missing_when_no_version_present():
    mod = _loadSyncRecent()
    missing = mod._keyMissingRows([ORIGINAL, CORRECTION], {"20250514000001"}, today=TODAY)
    assert [r["rcept_no"] for r in missing] == ["20260814003797", "20260819000055"]


def test_fresh_body_correction_is_recollected_within_grace_only():
    """parquet 이 원본만 들고 있는데 기재정정이 7일 안에 올라오면 그 행만 재수집. 7일이 지나면 더 쫓지 않는다."""
    mod = _loadSyncRecent()
    fresh = mod._keyMissingRows([ORIGINAL, CORRECTION], {"20260814003797"}, today=TODAY)
    assert [r["rcept_no"] for r in fresh] == ["20260819000055"]
    stale = mod._keyMissingRows([ORIGINAL, CORRECTION], {"20260814003797"}, today=datetime(2026, 9, 10))
    assert stale == []


def test_attachment_only_correction_never_triggers_recollect():
    """첨부정정·첨부추가는 본문 버전을 바꾸지 않으므로 재수집 대상이 아니다."""
    mod = _loadSyncRecent()
    assert mod._keyMissingRows([ORIGINAL, ATTACHMENT], {"20260814003797"}, today=TODAY) == []


def test_verify_mode_ignores_correction_lag():
    """수집 뒤 검증(correctionGrace=False)은 버전을 따지지 않는다. API 가 안 주는 버전은 누락이 아니다."""
    mod = _loadSyncRecent()
    assert mod._keyMissingRows([ORIGINAL, CORRECTION], {"20260814003797"}, today=TODAY, correctionGrace=False) == []


def test_non_periodic_rows_keep_rcept_rule():
    mod = _loadSyncRecent()
    other = _row("20260801000001", "주요사항보고서", "20260801")
    assert mod._keyMissingRows([other], set(), today=TODAY) == [other]
    assert mod._keyMissingRows([other], {"20260801000001"}, today=TODAY) == []


def test_verify_collected_rcepts_accepts_correction_version(tmp_path):
    """실제 parquet 로: 정정 rcept 만 있어도 검증 잔여 누락 0."""
    mod = _loadSyncRecent()
    from dartlab.core.dataConfig import DATA_RELEASES

    financeDir = tmp_path / DATA_RELEASES["finance"]["dir"]
    financeDir.mkdir(parents=True)
    pl.DataFrame({"rcept_no": ["20260819000055"], "bsns_year": ["2026"], "reprt_code": ["11012"]}).write_parquet(
        financeDir / "035720.parquet"
    )
    targetFilings = {"035720": {"finance": [ORIGINAL, CORRECTION], "report": []}}

    assert mod._verifyCollectedRcepts(targetFilings, str(tmp_path), ["finance"]) == []

    pl.DataFrame({"rcept_no": ["20250514000001"], "bsns_year": ["2025"], "reprt_code": ["11013"]}).write_parquet(
        financeDir / "035720.parquet"
    )
    failures = mod._verifyCollectedRcepts(targetFilings, str(tmp_path), ["finance"])
    assert sorted(f["rceptNo"] for f in failures) == ["20260814003797", "20260819000055"]
