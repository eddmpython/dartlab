import importlib.util
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _loadGovBuild():
    path = ROOT / ".github" / "scripts" / "sync" / "buildGovData.py"
    spec = importlib.util.spec_from_file_location("buildGovData", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.unit
def testGovBuildUsesSharedHfRetryForReadAndWrites():
    text = (ROOT / ".github" / "scripts" / "sync" / "buildGovData.py").read_text(encoding="utf-8")
    assert "retryHfCall(\n            hf_hub_download" in text
    assert "retryHfCall(create_repo" in text
    assert "retryHfCall(\n        api.upload_folder" in text
    assert "retryHfCall(upload)" in text


@pytest.mark.unit
@pytest.mark.parametrize("workflow", ["buildGovPriceData.yml", "buildGovIndexData.yml"])
def testGovWorkflowSeparatesRerunCacheAndBoundsRetries(workflow):
    text = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    assert "github.run_id }}-${{ github.run_attempt" in text
    assert 'DARTLAB_GOV_RETRY_ATTEMPTS: "5"' in text
    assert 'DARTLAB_HF_RETRY_MAX_SINGLE_WAIT_SECONDS: "300"' in text


@pytest.mark.unit
def testGovDailySkipsApiWhenLookbackAlreadyCollected(monkeypatch, tmp_path):
    """첫 슬롯이 수집한 lookback은 backstop 슬롯에서 외부 API를 다시 호출하지 않는다."""
    mod = _loadGovBuild()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DARTLAB_GOV_MIN_COMPLETE_ROWS", "1")
    dateDir = tmp_path / "data" / "gov" / "prices" / "date"
    dateDir.mkdir(parents=True)
    pl.DataFrame(
        {
            "BAS_DD": ["20260813", "20260812", "20260811", "20260810"],
            "ISU_CD": ["A000001", "A000001", "A000001", "A000001"],
        }
    ).write_parquet(dateDir / "2026.parquet")

    import dartlab.gather.gov.govApi as govApi

    monkeypatch.setattr(govApi, "fetchGovBydd", lambda *_args, **_kwargs: pytest.fail("API 재호출 금지"))
    monkeypatch.setattr(mod, "_deployFolder", lambda *_args, **_kwargs: pytest.fail("HF 재발행 금지"))

    assert mod.daily(apiKey="key", hfToken="token", basDt="20260813", lookbackDays=4) == 0


@pytest.mark.unit
def testGovCollectedDatesRejectsPartialShard(monkeypatch, tmp_path):
    """행 수가 너무 적은 날짜는 완료로 오인하지 않아 다음 슬롯이 다시 복구한다."""
    mod = _loadGovBuild()
    monkeypatch.setenv("DARTLAB_GOV_MIN_COMPLETE_ROWS", "2")
    dateDir = tmp_path / "date"
    dateDir.mkdir()
    pl.DataFrame(
        {
            "BAS_DD": ["20260813", "20260812", "20260812"],
            "ISU_CD": ["A000001", "A000001", "A000002"],
        }
    ).write_parquet(dateDir / "2026.parquet")

    assert mod._collectedPriceDates(["20260813", "20260812"], dateDir) == {"20260812"}
