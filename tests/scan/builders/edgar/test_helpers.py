"""EDGAR scan helpers — edgarCikToTicker 가 다중티커 CIK 에서 대표(보통주·첫) 티커를 채택하는지.

합성 universe → 네트워크/OOM 무관.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_cik_to_ticker_first_wins_for_multiticker():
    """다중티커 CIK 는 첫 티커(보통주) 채택 — 마지막(우선주·구조화상품) 아님."""
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    univ = pl.DataFrame(
        {
            "cik": ["19617", "19617", "19617", "320193"],
            "ticker": ["JPM", "JPM-PC", "VYLD", "AAPL"],  # SEC 순서: 보통주 우선
        }
    )
    m = edgarCikToTicker(univ)
    assert m["0000019617"] == "JPM"  # 첫 티커(VYLD/우선주 아님)
    assert m["0000320193"] == "AAPL"


def test_cik_to_ticker_zero_pads_cik():
    """CIK를 10자리 ASCII identity로 정규화한다."""
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    univ = pl.DataFrame({"cik": ["78003"], "ticker": ["pfe"]})
    m = edgarCikToTicker(univ)
    assert m == {"0000078003": "PFE"}


@pytest.mark.parametrize(
    ("cik", "ticker"),
    [
        ("１２３４", "FULLWIDTH"),
        ("1234", None),
        ("1234", "1234"),
    ],
)
def test_cik_to_ticker_rejects_invalid_identity(cik: str, ticker: str | None):
    """유니코드 숫자 CIK와 비어 있거나 숫자인 ticker를 정상 identity로 삼지 않는다."""
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    with pytest.raises(ValueError, match="유효하지 않습니다"):
        edgarCikToTicker(pl.DataFrame({"cik": [cik], "ticker": [ticker]}))


def test_cik_to_ticker_filters_nonlisted_and_otc_rows():
    """listed exchange membership 밖의 행은 prebuild identity에서 제외한다."""
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    univ = pl.DataFrame(
        {
            "cik": ["1", "2", "3"],
            "ticker": ["AAA", "OTC", "OLD"],
            "is_exchange_listed": [True, False, False],
            "is_otc": [False, True, False],
        }
    )
    assert edgarCikToTicker(univ) == {"0000000001": "AAA"}


def test_cik_to_ticker_rejects_ticker_owned_by_multiple_ciks():
    """같은 ticker를 서로 다른 CIK가 소유하면 입력 순서로 하나를 고르지 않는다."""
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    univ = pl.DataFrame({"cik": ["1", "2"], "ticker": ["DUP", "DUP"]})
    with pytest.raises(ValueError, match="여러 CIK"):
        edgarCikToTicker(univ)


def test_atomic_parquet_write_preserves_previous_file_on_replace_failure(tmp_path: Path, monkeypatch):
    """원자 교체가 실패하면 기존 artifact와 write 오류를 모두 보존하고 임시 파일을 정리한다."""
    from dartlab.scan.builders.edgar import helpers

    output = tmp_path / "finance.parquet"
    old = pl.DataFrame({"value": [1]})
    new = pl.DataFrame({"value": [2]})
    old.write_parquet(output)

    def failReplace(_source, _target):
        raise OSError("replace blocked")

    monkeypatch.setattr(helpers.os, "replace", failReplace)
    with pytest.raises(OSError, match="replace blocked"):
        helpers._writeParquetAtomic(new, output)

    assert pl.read_parquet(output).equals(old)
    assert list(tmp_path.glob(".*.tmp.parquet")) == []


def test_validate_prebuild_enforces_exact_cohort_and_identity(tmp_path: Path, monkeypatch):
    """8개 artifact가 exact schema·listed identity·고유 key를 만족할 때만 cohort를 승인한다."""
    from dartlab.scan.builders.edgar import builder
    from dartlab.scan.builders.edgar.report.auditorBuild import AUDITOR_COLS
    from dartlab.scan.builders.edgar.report.build import (
        CAPITAL_CHANGES_COLS,
        DEBT_MATURITY_COLS,
        EXEC_COMP_COLS,
        SHAREHOLDER_RETURN_COLS,
    )
    from dartlab.scan.builders.edgar.report.employeeBuild import EMPLOYEE_COLS
    from dartlab.scan.builders.edgar.valuationBuild import VALUATION_SCHEMA

    monkeypatch.setattr(builder, "edgarCikToTicker", lambda: {"0000000001": "ONE"})
    financeRow = dict.fromkeys(builder.FINANCE_SCHEMA)
    financeRow.update({"stockCode": "ONE", "cik": "0000000001", "corpName": "One", "fy": 2025})
    frames = {
        "finance.parquet": pl.DataFrame([financeRow], schema=builder.FINANCE_SCHEMA, strict=False),
        "valuation.parquet": pl.DataFrame(
            [
                {
                    "stockCode": "ONE",
                    "marketCap": 1.0,
                    "per": 1.0,
                    "pbr": 1.0,
                    "current": 1.0,
                    "dividendYield": None,
                    "snapshotAt": "2026-01-01T00:00:00+00:00",
                }
            ],
            schema=VALUATION_SCHEMA,
        ),
    }
    reportContracts = {
        "shareholderReturn": SHAREHOLDER_RETURN_COLS,
        "debtMaturity": DEBT_MATURITY_COLS,
        "execComp": EXEC_COMP_COLS,
        "capitalChanges": CAPITAL_CHANGES_COLS,
        "employee": EMPLOYEE_COLS,
        "auditor": AUDITOR_COLS,
    }
    for name, schema in reportContracts.items():
        row = dict.fromkeys(schema)
        row.update({"stockCode": "ONE", "year": "2025"})
        frames[f"report/{name}.parquet"] = pl.DataFrame([row], schema=schema, strict=False)
    for relative, frame in frames.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.write_parquet(path)

    counts = builder.validateEdgarPrebuild(scanDir=tmp_path)
    assert counts["finance.parquet"] == 1
    assert len(counts) == 8
    manifestPath = builder._writeEdgarPrebuildManifest(tmp_path, counts)
    manifest = json.loads(manifestPath.read_text(encoding="utf-8"))
    assert manifest["kind"] == "dartlab.edgar.scan.prebuild"
    assert [item["path"] for item in manifest["artifacts"]] == list(counts)
    for artifact in manifest["artifacts"]:
        source = tmp_path / artifact["path"]
        assert artifact["bytes"] == source.stat().st_size
        assert artifact["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    previousManifest = manifestPath.read_bytes()

    def rejectManifestReplace(_source, _target):
        """manifest 원자 교체 실패를 재현한다."""

        raise OSError("manifest replace blocked")

    monkeypatch.setattr(builder.os, "replace", rejectManifestReplace)
    with pytest.raises(OSError, match="manifest replace blocked"):
        builder._writeEdgarPrebuildManifest(tmp_path, counts)
    assert manifestPath.read_bytes() == previousManifest
    assert list(tmp_path.glob(".prebuild-manifest-*.tmp.json")) == []

    invalid = frames["valuation.parquet"].with_columns(pl.lit("0000000001").alias("stockCode"))
    invalid.write_parquet(tmp_path / "valuation.parquet")
    with pytest.raises(ValueError, match="listed identity 위반"):
        builder.validateEdgarPrebuild(scanDir=tmp_path)


def test_finance_builder_reads_only_listed_cik_and_writes_exact_schema(tmp_path: Path, monkeypatch):
    """unlisted CIK는 읽기 전에 제외하고 canonical ticker finance만 exact schema로 발행한다."""
    import dartlab.config as cfg
    from dartlab.scan.builders.edgar import builder

    financeDir = tmp_path / "edgar" / "finance"
    financeDir.mkdir(parents=True)
    pl.DataFrame(
        {
            "form": ["10-K"],
            "fy": [2025],
            "end": [date(2025, 12, 31)],
            "start": [date(2025, 1, 1)],
            "frame": ["CY2025"],
            "entityName": ["One Inc."],
            "unit": ["USD"],
            "tag": ["Revenue"],
            "val": [100.0],
            "filed": [date(2026, 2, 1)],
        }
    ).write_parquet(financeDir / "1.parquet")
    (financeDir / "2.parquet").write_bytes(b"unlisted file must not be read")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(builder, "edgarCikToTicker", lambda: {"0000000001": "ONE"})
    monkeypatch.setattr(builder, "_buildCikToSicMap", lambda: {})
    monkeypatch.setattr(builder, "_buildReverseTagMap", lambda _accounts: {"sales": ["Revenue"]})

    output = builder.buildEdgarFinance(sinceYear=2021)
    frame = pl.read_parquet(output)
    assert frame.schema == pl.Schema(builder.FINANCE_SCHEMA)
    assert frame.select(["stockCode", "cik", "fy", "sales"]).to_dicts() == [
        {"stockCode": "ONE", "cik": "0000000001", "fy": 2025, "sales": 100.0}
    ]


def test_finance_builder_fails_loud_on_corrupt_listed_source(tmp_path: Path, monkeypatch):
    """listed CIK 원천 손상은 빈/부분 finance로 바뀌지 않는다."""
    import dartlab.config as cfg
    from dartlab.scan.builders.edgar import builder

    financeDir = tmp_path / "edgar" / "finance"
    financeDir.mkdir(parents=True)
    corrupt = financeDir / "1.parquet"
    corrupt.write_bytes(b"corrupt")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(builder, "edgarCikToTicker", lambda: {"0000000001": "ONE"})
    monkeypatch.setattr(builder, "_buildCikToSicMap", lambda: {})
    monkeypatch.setattr(builder, "_buildReverseTagMap", lambda _accounts: {})

    with pytest.raises(RuntimeError, match="cik=0000000001"):
        builder.buildEdgarFinance()


@pytest.mark.parametrize("annualForm", ["10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"])
def test_finance_builder_accepts_sec_annual_forms(annualForm: str, tmp_path: Path, monkeypatch):
    """미국·해외 발행사의 SEC annual form과 정정본을 같은 finance 계약으로 처리한다."""
    import dartlab.config as cfg
    from dartlab.scan.builders.edgar import builder

    financeDir = tmp_path / "edgar" / "finance"
    financeDir.mkdir(parents=True)
    pl.DataFrame(
        {
            "form": [annualForm],
            "fy": [2025],
            "end": [date(2025, 12, 31)],
            "start": [date(2025, 1, 1)],
            "frame": ["CY2025"],
            "entityName": ["Foreign Issuer"],
            "unit": ["USD"],
            "tag": ["Revenue"],
            "val": [100.0],
            "filed": [date(2026, 2, 1)],
        }
    ).write_parquet(financeDir / "1.parquet")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(builder, "edgarCikToTicker", lambda: {"0000000001": "ONE"})
    monkeypatch.setattr(builder, "_buildCikToSicMap", lambda: {})
    monkeypatch.setattr(builder, "_buildReverseTagMap", lambda _accounts: {"sales": ["Revenue"]})

    frame = pl.read_parquet(builder.buildEdgarFinance())
    assert frame["sales"].to_list() == [100.0]
