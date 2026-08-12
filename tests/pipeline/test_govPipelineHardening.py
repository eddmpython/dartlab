from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


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
