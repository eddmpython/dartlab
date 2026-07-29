"""mappingLedgerCompact CLI의 strict NDJSON 소비와 평가 parquet 단위 테스트."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "src" / "dartlab" / "reference" / "mapping" / "mappingLedgerCompact.py"


@pytest.fixture
def compactMod():
    """src/dartlab/reference/mapping/mappingLedgerCompact.py 를 모듈로 동적 로드."""
    spec = importlib.util.spec_from_file_location("mappingLedgerCompact", _SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mappingLedgerCompact"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def fakeMappingsFile(tmp_path: Path) -> Path:
    payload = {
        "_metadata": {},
        "standardAccounts": {
            "other_financial_assets": {"korName": "기타금융자산"},
            "controlling_equity": {"korName": "지배기업소유주지분"},
            "total_assets": {"korName": "자산총계"},
        },
        "mappings": {
            "자산총계": "total_assets",
        },
    }
    target = tmp_path / "accountMappings.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return target


def _writeNdjson(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _validRow(**overrides) -> dict:
    row = {
        "observedAt": "2026-05-15T00:00:00+00:00",
        "stockCode": "005930",
        "accountId": "-표준계정코드 미사용-",
        "accountNm": "기타의금융자산",
        "sjDiv": "BS",
        "occurrenceCount": 1,
    }
    row.update(overrides)
    return row


def test_compact_groups_and_evaluates(compactMod, tmp_path: Path, fakeMappingsFile: Path) -> None:
    raw = tmp_path / "raw.ndjson"
    out = tmp_path / "out.parquet"

    rows = [
        # 기타의금융자산 — 5 회사, autoEligible 예상
        {
            "observedAt": "2026-05-15T00:00:00+00:00",
            "stockCode": code,
            "accountId": "-표준계정코드 미사용-",
            "accountNm": "기타의금융자산",
            "sjDiv": "BS",
            "occurrenceCount": 3,
        }
        for code in ["005930", "000660", "035720", "035420", "051910"]
    ]
    # 지배지업소유주지분 — typo, autoEligible False
    rows.extend(
        [
            {
                "observedAt": "2026-05-15T00:00:00+00:00",
                "stockCode": code,
                "accountId": "-표준계정코드 미사용-",
                "accountNm": "지배지업소유주지분",
                "sjDiv": "BS",
                "occurrenceCount": 2,
            }
            for code in ["005930", "000660", "035720"]
        ]
    )

    _writeNdjson(raw, rows)
    n = compactMod.compact(raw, out, fakeMappingsFile)
    assert n == 2
    assert out.exists()

    df = pl.read_parquet(out)
    assert set(df.columns) == {
        "firstSeenAt",
        "lastSeenAt",
        "accountId",
        "accountNm",
        "occurrenceCount",
        "stockCodes",
        "sjDivs",
        "corporateDispersion",
        "suggestedSnakeId",
        "confidence",
        "signalBreakdown",
        "autoEligible",
        "status",
        "operatorNote",
        "decidedAt",
    }

    autoRow = df.filter(pl.col("accountNm") == "기타의금융자산").row(0, named=True)
    assert autoRow["autoEligible"] is True
    assert autoRow["status"] == "auto_proposed"
    assert autoRow["suggestedSnakeId"] == "other_financial_assets"
    assert autoRow["occurrenceCount"] == 15
    assert autoRow["corporateDispersion"] == 5

    typoRow = df.filter(pl.col("accountNm") == "지배지업소유주지분").row(0, named=True)
    assert typoRow["autoEligible"] is False
    assert typoRow["status"] == "human_review"
    breakdown = json.loads(typoRow["signalBreakdown"])
    assert breakdown["s5Typo"] is True
    assert breakdown["s5Fix"] == "지배기업소유주지분"


def test_compact_handles_empty_ledger(compactMod, tmp_path: Path, fakeMappingsFile: Path) -> None:
    raw = tmp_path / "empty.ndjson"
    raw.write_text("", encoding="utf-8")
    out = tmp_path / "empty.parquet"

    n = compactMod.compact(raw, out, fakeMappingsFile)
    assert n == 0
    assert out.exists()
    df = pl.read_parquet(out)
    assert df.height == 0


def test_compact_creates_output_directory(compactMod, tmp_path: Path, fakeMappingsFile: Path) -> None:
    raw = tmp_path / "raw.ndjson"
    raw.write_text("", encoding="utf-8")
    out = tmp_path / "nested" / "sub" / "out.parquet"

    compactMod.compact(raw, out, fakeMappingsFile)
    assert out.exists()


def test_compact_raises_when_mappings_missing(compactMod, tmp_path: Path) -> None:
    raw = tmp_path / "raw.ndjson"
    raw.write_text("", encoding="utf-8")
    out = tmp_path / "out.parquet"
    missing = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        compactMod.compact(raw, out, missing)


def test_groupRows_accepts_one_pass_iterator(compactMod) -> None:
    rows = (_validRow(stockCode=code) for code in ["005930", "000660"])

    grouped = compactMod._groupRows(rows)

    assert grouped[("-표준계정코드 미사용-", "기타의금융자산")]["occurrenceCount"] == 2


def test_compact_raises_when_raw_ledger_missing(
    compactMod,
    tmp_path: Path,
    fakeMappingsFile: Path,
) -> None:
    missing = tmp_path / "missing.ndjson"

    with pytest.raises(FileNotFoundError, match="mapping ledger 부재"):
        compactMod.compact(missing, tmp_path / "out.parquet", fakeMappingsFile)


def test_compact_reports_malformed_json_line(
    compactMod,
    tmp_path: Path,
    fakeMappingsFile: Path,
) -> None:
    raw = tmp_path / "malformed.ndjson"
    raw.write_text(json.dumps(_validRow(), ensure_ascii=False) + "\n{broken\n", encoding="utf-8")
    out = tmp_path / "out.parquet"

    with pytest.raises(ValueError, match=r"malformed\.ndjson:2: invalid JSON"):
        compactMod.compact(raw, out, fakeMappingsFile)

    assert not out.exists()


@pytest.mark.parametrize(
    "payload,message",
    [
        ("42\n", "ledger row must be a JSON object"),
        (
            json.dumps(_validRow(occurrenceCount=0), ensure_ascii=False) + "\n",
            "occurrenceCount must be greater than zero",
        ),
        (
            json.dumps(_validRow(observedAt="not-a-date"), ensure_ascii=False) + "\n",
            "observedAt must be ISO8601",
        ),
    ],
)
def test_compact_rejects_invalid_row_schema(
    compactMod,
    tmp_path: Path,
    fakeMappingsFile: Path,
    payload: str,
    message: str,
) -> None:
    raw = tmp_path / "invalid.ndjson"
    raw.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        compactMod.compact(raw, tmp_path / "out.parquet", fakeMappingsFile)


def test_compact_rejects_invalid_mappings_schema(compactMod, tmp_path: Path) -> None:
    mappingsPath = tmp_path / "invalid-mappings.json"
    mappingsPath.write_text(
        json.dumps({"standardAccounts": [], "mappings": {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    raw = tmp_path / "raw.ndjson"
    raw.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="standardAccounts must be an object"):
        compactMod.compact(raw, tmp_path / "out.parquet", mappingsPath)
