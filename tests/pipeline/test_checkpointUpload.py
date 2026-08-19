"""checkpoint HF 업로드가 배치 단위인지 고정한다 (2026-08-19 O(n^2) 회귀 가드).

`hfUpload` 는 `changedFiles` 인자가 없으면 누적 매니페스트 `dist/changed_{cat}.txt` 를 읽는다.
checkpoint 업로더가 배치 목록을 명시하지 않으면 100 종목마다 지금까지 모은 전량을 다시 올려
소요가 제곱으로 늘어난다. 실측: 업로드 대상이 1000 개에서 1500 개로 늘며 checkpoint 간격이
3 분 41 초에서 12 분 14 초로 벌어졌고 90 분 job timeout 에 잘렸다.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def _loadSyncRecent():
    path = ROOT / ".github" / "scripts" / "sync" / "syncRecent.py"
    spec = importlib.util.spec_from_file_location("syncRecent_undertest", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _runUploader(monkeypatch, tmp_path, batches: list[list[str]]) -> list[dict]:
    """checkpoint 업로더를 batches 순서대로 호출하고 각 호출의 관측치를 반환한다."""
    mod = _loadSyncRecent()
    monkeypatch.chdir(tmp_path)

    calls: list[dict] = []

    class _Result:
        returncode = 0

    def fakeRun(cmd, env=None, check=False):
        changedFile = (env or {}).get("SYNC_CHANGED_FILE")
        payload = {
            "category": (env or {}).get("SYNC_CATEGORY"),
            "changedFile": changedFile,
            "batch": [],
            "cumulative": [],
        }
        if changedFile and Path(changedFile).exists():
            payload["batch"] = [x for x in Path(changedFile).read_text(encoding="utf-8").splitlines() if x]
        cat = payload["category"]
        cumPath = Path("dist") / f"changed_{cat}.txt"
        if cumPath.exists():
            payload["cumulative"] = [x for x in cumPath.read_text(encoding="utf-8").splitlines() if x]
        calls.append(payload)
        return _Result()

    # `_makeCheckpointUploader` 는 함수 안에서 subprocess 를 lazy import 하므로
    # sys.modules 의 전역 모듈을 patch 해야 잡힌다.
    import subprocess as _sp

    monkeypatch.setattr(_sp, "run", fakeRun)
    upload = mod._makeCheckpointUploader("report")
    for codes in batches:
        upload(codes)
    return calls


def test_checkpoint_uploads_only_current_batch(monkeypatch, tmp_path) -> None:
    """두 번째 checkpoint 는 첫 배치를 다시 올리지 않는다."""
    calls = _runUploader(
        monkeypatch,
        tmp_path,
        [["000001", "000002"], ["000003", "000004", "000005"]],
    )

    assert len(calls) == 2
    assert calls[0]["batch"] == ["000001.parquet", "000002.parquet"]
    assert calls[1]["batch"] == ["000003.parquet", "000004.parquet", "000005.parquet"], (
        f"두 번째 checkpoint 가 배치 밖 파일을 올린다: {calls[1]['batch']}"
    )


def test_checkpoint_passes_explicit_manifest_to_uploader(monkeypatch, tmp_path) -> None:
    """SYNC_CHANGED_FILE 이 설정돼야 hfUpload 가 누적 매니페스트를 읽지 않는다."""
    calls = _runUploader(monkeypatch, tmp_path, [["000001"]])

    changedFile = calls[0]["changedFile"]
    assert changedFile, "SYNC_CHANGED_FILE 미설정 시 hfUpload 가 누적 매니페스트를 읽어 전량 재업로드한다"
    assert Path(changedFile).name == "changed_report_checkpoint.txt"
    assert calls[0]["category"] == "report"


def test_checkpoint_still_accumulates_category_manifest(monkeypatch, tmp_path) -> None:
    """누적 매니페스트는 그대로 쌓인다. 워크플로 최종 업로드 스텝이 잔여분을 잡는 근거다."""
    calls = _runUploader(
        monkeypatch,
        tmp_path,
        [["000001", "000002"], ["000003"]],
    )

    assert calls[0]["cumulative"] == ["000001.parquet", "000002.parquet"]
    assert calls[1]["cumulative"] == ["000001.parquet", "000002.parquet", "000003.parquet"]


def test_checkpoint_noop_on_empty_batch(monkeypatch, tmp_path) -> None:
    """빈 배치는 업로드를 호출하지 않는다."""
    calls = _runUploader(monkeypatch, tmp_path, [[]])
    assert calls == []


def test_upload_shim_reads_explicit_manifest(monkeypatch, tmp_path) -> None:
    """uploadData shim 이 SYNC_CHANGED_FILE 을 읽어 changedFiles 로 넘긴다."""
    path = ROOT / ".github" / "scripts" / "sync" / "uploadData.py"
    spec = importlib.util.spec_from_file_location("uploadData_undertest", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    manifest = tmp_path / "batch.txt"
    manifest.write_text("000001.parquet\n000002.parquet\n", encoding="utf-8")

    captured: dict = {}

    import dartlab.pipeline.hfUpload as hfUpload

    monkeypatch.setattr(
        hfUpload,
        "uploadCategoryToHf",
        lambda category, **kwargs: captured.update(category=category, **kwargs) or 0,
    )
    monkeypatch.setenv("SYNC_CATEGORY", "report")
    monkeypatch.setenv("SYNC_CHANGED_FILE", str(manifest))
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr("sys.argv", ["uploadData.py", "--target", "hf"])

    mod.main()

    assert captured["category"] == "report"
    assert captured["changedFiles"] == ["000001.parquet", "000002.parquet"]


def test_upload_shim_falls_back_to_cumulative_manifest(monkeypatch, tmp_path) -> None:
    """SYNC_CHANGED_FILE 이 없으면 기존대로 None 을 넘겨 누적 매니페스트 경로를 쓴다."""
    path = ROOT / ".github" / "scripts" / "sync" / "uploadData.py"
    spec = importlib.util.spec_from_file_location("uploadData_undertest2", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    captured: dict = {}

    import dartlab.pipeline.hfUpload as hfUpload

    monkeypatch.setattr(
        hfUpload,
        "uploadCategoryToHf",
        lambda category, **kwargs: captured.update(category=category, **kwargs) or 0,
    )
    monkeypatch.setenv("SYNC_CATEGORY", "finance")
    monkeypatch.delenv("SYNC_CHANGED_FILE", raising=False)
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr("sys.argv", ["uploadData.py", "--target", "hf"])

    mod.main()

    assert captured["category"] == "finance"
    assert captured["changedFiles"] is None
