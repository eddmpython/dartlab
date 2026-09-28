"""syncGdeltBackfill 슬롯 단위 격리 계약 (네트워크/HF 무관).

2026-09 GDELT Sync 는 불량 GKG 파일 1 개(SourceUnavailableError)가 run 전체를 중단시켜 같은 창의
나머지 슬롯까지 버렸고, forward 창(D-2~D-1)이 같은 슬롯을 다시 받아 이틀 연속 실패했다.
실패 슬롯은 경고로 남기고 계속 진행하며, 모든 슬롯이 실패할 때만 0 이 아닌 종료코드를 낸다.
스크립트라 importlib 경유. fetch 와 parquet 쓰기는 대역으로 바꾼다.
"""

from __future__ import annotations

import importlib.util
from datetime import date, datetime
from pathlib import Path

import polars as pl
import pytest

from dartlab.gather.sources import gdelt, newsIo
from dartlab.gather.types import SourceUnavailableError

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "scripts" / "sync" / "syncGdeltBackfill.py"
# 하루 6 시간 간격 = 4 슬롯 (00/06/12/18시).
_ARGV = ["--start", "2026-09-13", "--end", "2026-09-13", "--step-minutes", "360", "--sleep", "0"]
_ALL_SLOTS = ["20260913000000", "20260913060000", "20260913120000", "20260913180000"]
_BAD_SLOT = "20260913060000"


def _loadModule():
    spec = importlib.util.spec_from_file_location("syncGdeltBackfillForTest", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _slotId(slot: datetime) -> str:
    return slot.strftime("%Y%m%d%H%M%S")


def _slotFrame(slot: datetime) -> pl.DataFrame:
    """슬롯 1 개 fetch 결과 대역 (KR 1 행, 슬롯마다 url 다름)."""
    return pl.DataFrame({"date": [slot.date()], "market": ["KR"], "url": [f"https://yna.co.kr/{_slotId(slot)}"]})


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """스크립트 모듈 + 호출 기록. parquet 쓰기는 기록만 하고 dist 매니페스트는 tmp 로 격리."""
    mod = _loadModule()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    calls: dict[str, list] = {"fetched": [], "written": []}

    def _write(df: pl.DataFrame, **kwargs):
        calls["written"].append((kwargs["market"], kwargs["day"], sorted(df["url"].to_list())))
        return tmp_path / "written.parquet", df.height, df.height

    monkeypatch.setattr(newsIo, "writeDailyParquet", _write)
    return mod, calls


def test_failing_slot_does_not_stop_other_slots(harness, monkeypatch, tmp_path, capsys, caplog) -> None:
    """한 슬롯 실패는 경고로 남고, 뒤 슬롯까지 계속 받아 저장하며 종료코드 0."""
    mod, calls = harness

    def _fetch(slot: datetime, *, markets=None) -> pl.DataFrame:
        calls["fetched"].append(_slotId(slot))
        if _slotId(slot) == _BAD_SLOT:
            raise SourceUnavailableError(f"GDELT GKG CSV를 해석할 수 없습니다: {_BAD_SLOT}") from (
                pl.exceptions.ComputeError("invalid utf-8 sequence")
            )
        return _slotFrame(slot)

    monkeypatch.setattr(gdelt, "fetchGdeltGkg", _fetch)

    rc = mod.main(_ARGV)

    assert rc == 0
    assert calls["fetched"] == _ALL_SLOTS  # 실패 슬롯 뒤도 계속 처리
    okUrls = sorted(f"https://yna.co.kr/{s}" for s in _ALL_SLOTS if s != _BAD_SLOT)
    assert calls["written"] == [("KR", date(2026, 9, 13), okUrls)]  # 나머지 3 슬롯은 버려지지 않음
    out = capsys.readouterr().out
    warnings = [line for line in out.splitlines() if line.startswith("::warning::")]
    assert len(warnings) == 1 and _BAD_SLOT in warnings[0]
    assert "ComputeError: invalid utf-8 sequence" in warnings[0]  # 원인까지 한 줄로 남김
    assert "::error::" not in out
    assert "실패 슬롯 1/4" in caplog.text and _BAD_SLOT in caplog.text  # run 끝 요약
    manifest = (tmp_path / "dist" / "changed_newsGdelt.txt").read_text(encoding="utf-8")
    assert manifest.split() == ["KR/2026-09-13.parquet"]  # 업로드 매니페스트 기존 동작 유지


def test_all_slots_failing_returns_nonzero(harness, monkeypatch, tmp_path, capsys, caplog) -> None:
    """모든 슬롯 실패는 실제 공급 장애. 전부 시도한 뒤 0 이 아닌 종료코드, 저장·매니페스트 없음."""
    mod, calls = harness

    def _fetch(slot: datetime, *, markets=None) -> pl.DataFrame:
        calls["fetched"].append(_slotId(slot))
        raise SourceUnavailableError(f"GDELT GKG 슬롯을 가져올 수 없습니다: {_slotId(slot)}")

    monkeypatch.setattr(gdelt, "fetchGdeltGkg", _fetch)

    rc = mod.main(_ARGV)

    assert rc != 0
    assert calls["fetched"] == _ALL_SLOTS
    assert calls["written"] == []
    out = capsys.readouterr().out
    assert sum(line.startswith("::warning::") for line in out.splitlines()) == 4
    assert any(line.startswith("::error::") for line in out.splitlines())
    assert "실패 슬롯 4/4" in caplog.text
    assert not (tmp_path / "dist" / "changed_newsGdelt.txt").exists()


def test_programming_error_is_not_swallowed(harness, monkeypatch) -> None:
    """격리 대상은 공급 실패(SourceUnavailableError)뿐. 그 밖의 예외는 그대로 전파한다."""
    mod, calls = harness

    def _fetch(slot: datetime, *, markets=None) -> pl.DataFrame:
        calls["fetched"].append(_slotId(slot))
        raise KeyError("market")

    monkeypatch.setattr(gdelt, "fetchGdeltGkg", _fetch)

    with pytest.raises(KeyError):
        mod.main(_ARGV)
    assert calls["fetched"] == _ALL_SLOTS[:1]
    assert calls["written"] == []
