"""corpProfile v2 publisher와 resume migration 계약."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def test_normalizeJurirNo_accepts_only_ascii_legal_id() -> None:
    from dartlab.scan.builders.kr.corpProfile import normalizeJurirNo

    assert normalizeJurirNo("123456-1234567") == "1234561234567"
    assert normalizeJurirNo("１２３４５６-１２３４５６７") is None
    assert normalizeJurirNo("법인 123456-1234567") is None


def _loadScript():
    path = ROOT / ".github" / "scripts" / "meta" / "buildCorpProfile.py"
    spec = importlib.util.spec_from_file_location("buildCorpProfileTest", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fetchOne_preserves_normalized_legal_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _loadScript()
    monkeypatch.setattr(
        module,
        "companyInfo",
        lambda _client, _corpCode: {
            "jurir_no": "123456-1234567",
            "bizr_no": "123-45-67890",
            "acc_mt": "12",
            "induty_code": "12345",
            "est_dt": "20000101",
            "corp_cls": "K",
        },
    )

    result = module._fetchOne(
        object(),
        {"corp_code": "A", "stock_code": "100001", "corp_name": "알파"},
        retry=0,
    )

    assert result is not None
    assert result["jurir_no"] == "1234561234567"
    assert result["profileSchemaVersion"] == module.CORP_PROFILE_SCHEMA_VERSION


def test_atomic_writer_migrates_legacy_rows_to_canonical_v1(tmp_path: Path) -> None:
    module = _loadScript()
    output = tmp_path / "corpProfile.parquet"

    module._atomicWriteParquet(
        {
            "A": {
                "corp_code": "A",
                "stockCode": "100001",
                "corp_name": "알파",
                "acc_mt": "12",
            },
            "B": {
                "corp_code": "B",
                "stockCode": "100002",
                "corp_name": "베타",
                "jurir_no": "",
                "profileSchemaVersion": module.CORP_PROFILE_SCHEMA_VERSION,
            },
        },
        output,
    )

    result = pl.read_parquet(output)
    assert result.schema == module.CORP_PROFILE_SCHEMA
    assert result["corp_code"].to_list() == ["A", "B"]
    assert result["profileSchemaVersion"].to_list() == [1, module.CORP_PROFILE_SCHEMA_VERSION]
    assert list(tmp_path.glob("*.tmp.parquet")) == []


def test_resume_retries_only_v1_rows_and_preserves_failed_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _loadScript()
    output = tmp_path / "corpProfile.parquet"
    module._atomicWriteParquet(
        {
            "A": {
                "corp_code": "A",
                "stockCode": "OLD",
                "corp_name": "옛알파",
                "profileSchemaVersion": 1,
            },
            "B": {
                "corp_code": "B",
                "stockCode": "OLD",
                "corp_name": "옛베타",
                "jurir_no": "",
                "profileSchemaVersion": module.CORP_PROFILE_SCHEMA_VERSION,
            },
        },
        output,
    )
    master = pl.DataFrame(
        {
            "corp_code": ["A", "B"],
            "stock_code": ["100001", "100002"],
            "corp_name": ["알파", "베타"],
        }
    )
    monkeypatch.setattr(module, "_resolveApiKeys", lambda: ["key"])
    monkeypatch.setattr(module, "DartClient", lambda **_kwargs: object())
    monkeypatch.setattr(module, "loadCorpCodes", lambda _client: master)

    calls: list[str] = []

    def failFetch(_client, row):
        calls.append(row["corp_code"])
        return None

    monkeypatch.setattr(module, "_fetchOne", failFetch)
    module.buildCorpProfile(workers=1, output=output)
    failed = pl.read_parquet(output)

    assert calls == ["A"]
    assert failed.filter(pl.col("corp_code") == "A")["profileSchemaVersion"].item() == 1
    assert failed.filter(pl.col("corp_code") == "B")["stockCode"].item() == "100002"

    calls.clear()

    def succeedFetch(_client, row):
        calls.append(row["corp_code"])
        return {
            "corp_code": row["corp_code"],
            "stockCode": row["stock_code"],
            "corp_name": row["corp_name"],
            "jurir_no": "1234561234567",
            "bizr_no": "",
            "acc_mt": "12",
            "induty_code": "",
            "est_dt": "",
            "corp_cls": "K",
            "profileSchemaVersion": module.CORP_PROFILE_SCHEMA_VERSION,
        }

    monkeypatch.setattr(module, "_fetchOne", succeedFetch)
    module.buildCorpProfile(workers=1, output=output)
    completed = pl.read_parquet(output)

    assert calls == ["A"]
    assert completed["profileSchemaVersion"].to_list() == [2, 2]
