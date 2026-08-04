"""gather/edgar/bulk.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.core.edgarClient  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_convert_bulk_to_parquets_callable() -> None:
    """convertBulkToParquets() callable smoke."""
    from dartlab.core.edgarClient import convertBulkToParquets

    assert callable(convertBulkToParquets)


def test_download_companyfacts_bulk_callable() -> None:
    """downloadCompanyfactsBulk() callable smoke."""
    from dartlab.core.edgarClient import downloadCompanyfactsBulk

    assert callable(downloadCompanyfactsBulk)


def test_ensure_finance_parquet_callable() -> None:
    """ensureFinanceParquet() callable smoke."""
    from dartlab.core.edgarClient import ensureFinanceParquet

    assert callable(ensureFinanceParquet)


def test_extract_companyfacts_zip_callable() -> None:
    """extractCompanyfactsZip() callable smoke."""
    from dartlab.core.edgarClient import extractCompanyfactsZip

    assert callable(extractCompanyfactsZip)


def _makeZip(tmp_path, cik_json: dict):
    import json
    import zipfile

    z = tmp_path / "cf.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("CIK0000320193.json", json.dumps(cik_json))
    return z


def test_convert_detect_changed(tmp_path, monkeypatch) -> None:
    """detectChanged — fact 해시 매니페스트로 변경분만 changed 반환(daily 증분 발행)."""
    import polars as pl

    from dartlab.gather.edgar import bulk

    # companyFactsToRows mock — payload 무관 고정 df(write 성공). 해시는 payload 로 판정.
    monkeypatch.setattr(
        bulk,
        "companyFactsToRows",
        lambda payload: pl.DataFrame({"namespace": ["us-gaap"], "tag": ["X"], "val": [1.0]}),
    )
    outDir = tmp_path / "finance"

    # 1차: 매니페스트 없음 → changed + parquet + _factHash.json 생성
    r1 = bulk.convertBulkToParquets(
        zipPath=_makeZip(tmp_path, {"a": 1}), outDir=outDir, detectChanged=True, progress=False, force=True
    )
    assert "0000320193.parquet" in r1["changed"]
    assert (outDir / "0000320193.parquet").exists()
    assert (outDir / "_factHash.json").exists()

    # 2차: 동일 payload → 미변경 skip(changed 0)
    r2 = bulk.convertBulkToParquets(
        zipPath=_makeZip(tmp_path, {"a": 1}), outDir=outDir, detectChanged=True, progress=False, force=True
    )
    assert r2["changed"] == []
    assert r2["skipped"] >= 1

    # 3차: payload 변경 → 다시 changed
    r3 = bulk.convertBulkToParquets(
        zipPath=_makeZip(tmp_path, {"a": 2}), outDir=outDir, detectChanged=True, progress=False, force=True
    )
    assert "0000320193.parquet" in r3["changed"]


def test_convert_without_detect_changed_back_compat(tmp_path, monkeypatch) -> None:
    """detectChanged=False(기본) 면 매니페스트 미생성·changed 빈 리스트(기존 동작 무회귀)."""
    import polars as pl

    from dartlab.gather.edgar import bulk

    monkeypatch.setattr(
        bulk,
        "companyFactsToRows",
        lambda payload: pl.DataFrame({"namespace": ["us-gaap"], "tag": ["X"], "val": [1.0]}),
    )
    outDir = tmp_path / "finance"
    r = bulk.convertBulkToParquets(zipPath=_makeZip(tmp_path, {"a": 1}), outDir=outDir, progress=False, force=True)
    assert r["changed"] == []
    assert (outDir / "0000320193.parquet").exists()
    assert not (outDir / "_factHash.json").exists()


def test_ensure_finance_parquet_reconverts_when_local_exists(monkeypatch, tmp_path):
    """path 존재 시에도 stamp 가드 변환을 항상 시도한다 (zip 만 새로 받고 parquet 은 stale 이던 비정합 차단)."""
    from dartlab.gather.edgar import bulk as mod

    zipPath = tmp_path / "companyfacts.zip"
    zipPath.write_bytes(b"zip")
    target = tmp_path / "0000320193.parquet"
    target.write_bytes(b"parquet")

    calls: list[dict] = []
    monkeypatch.setattr(mod, "downloadCompanyfactsBulk", lambda *, force=False: zipPath)
    monkeypatch.setattr(
        mod,
        "convertBulkToParquets",
        lambda zipPath=None, **kwargs: calls.append({"zipPath": zipPath, **kwargs}),
    )

    mod.ensureFinanceParquet("AAPL", target)
    assert len(calls) == 1
    assert calls[0].get("force") is not True, "존재 경로는 stamp 가드 판정 (force 금지)"


def test_ensure_finance_parquet_missing_forces_full_convert(monkeypatch, tmp_path):
    """path 부재(최초)는 stamp 가드를 우회해 전체 변환을 강제한다."""
    from dartlab.gather.edgar import bulk as mod

    zipPath = tmp_path / "companyfacts.zip"
    zipPath.write_bytes(b"zip")
    target = tmp_path / "0000320193.parquet"

    calls: list[dict] = []

    def fakeConvert(zipPath=None, **kwargs):
        calls.append({"zipPath": zipPath, **kwargs})
        target.write_bytes(b"parquet")  # 변환이 대상 CIK parquet 을 생성

    monkeypatch.setattr(mod, "downloadCompanyfactsBulk", lambda *, force=False: zipPath)
    monkeypatch.setattr(mod, "convertBulkToParquets", fakeConvert)

    mod.ensureFinanceParquet("AAPL", target)
    assert calls and calls[0].get("force") is True
