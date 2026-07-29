"""mappingPromote CLI — dryrun/apply/rollback 단위 테스트.

prod JSON 단독 권한 진입점. atomic write, 충돌 reject, _metadata 갱신,
AccountMapper.release 동작을 검증.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "src" / "dartlab" / "reference" / "mapping" / "mappingPromote.py"


@pytest.fixture
def promoteMod():
    spec = importlib.util.spec_from_file_location("mappingPromote", _SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mappingPromote"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def stagingFile(tmp_path: Path) -> Path:
    schema = {
        "firstSeenAt": pl.String,
        "lastSeenAt": pl.String,
        "accountId": pl.String,
        "accountNm": pl.String,
        "occurrenceCount": pl.Int64,
        "stockCodes": pl.List(pl.String),
        "sjDivs": pl.List(pl.String),
        "corporateDispersion": pl.Int64,
        "suggestedSnakeId": pl.String,
        "confidence": pl.Float64,
        "signalBreakdown": pl.String,
        "autoEligible": pl.Boolean,
        "status": pl.String,
        "operatorNote": pl.String,
        "decidedAt": pl.String,
    }
    rows = [
        {
            "firstSeenAt": "2026-05-15T00:00:00+00:00",
            "lastSeenAt": "2026-05-15T00:00:00+00:00",
            "accountId": "",
            "accountNm": "기타의금융자산",
            "occurrenceCount": 14,
            "stockCodes": ["005930", "000660", "035720"],
            "sjDivs": ["BS"],
            "corporateDispersion": 3,
            "suggestedSnakeId": "other_financial_assets",
            "confidence": 0.86,
            "signalBreakdown": "{}",
            "autoEligible": True,
            "status": "confirmed",
            "operatorNote": None,
            "decidedAt": "2026-05-15T00:00:00+00:00",
        },
        # human_review — 미적용
        {
            "firstSeenAt": "2026-05-15T00:00:00+00:00",
            "lastSeenAt": "2026-05-15T00:00:00+00:00",
            "accountId": "",
            "accountNm": "지배지업소유주지분",
            "occurrenceCount": 6,
            "stockCodes": ["005930", "000660", "035720"],
            "sjDivs": ["BS"],
            "corporateDispersion": 3,
            "suggestedSnakeId": None,
            "confidence": 0.0,
            "signalBreakdown": "{}",
            "autoEligible": False,
            "status": "human_review",
            "operatorNote": None,
            "decidedAt": None,
        },
    ]
    target = tmp_path / "staging.parquet"
    pl.DataFrame(rows, schema=schema).write_parquet(target)
    return target


@pytest.fixture
def jsonFile(tmp_path: Path) -> Path:
    payload = {
        "_metadata": {
            "description": "test fixture",
            "lastUpdate": "2026-03-09",
            "addedCount": 0,
        },
        "standardAccounts": {
            "total_assets": {"korName": "자산총계"},
            "total_stockholders_equity": {"korName": "자본총계"},
            "other_financial_assets": {"korName": "기타금융자산"},
            "different_value": {"korName": "다른가치"},
            "different_snake_id": {"korName": "다른snake"},
        },
        "mappings": {
            "자산총계": "total_assets",
        },
    }
    target = tmp_path / "accountMappings.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def test_dryrun_does_not_modify_json(promoteMod, stagingFile: Path, jsonFile: Path, capsys) -> None:
    before = jsonFile.read_text(encoding="utf-8")
    rc = promoteMod.main(["--staging", str(stagingFile), "--json", str(jsonFile), "dryrun"])
    assert rc == 0
    after = jsonFile.read_text(encoding="utf-8")
    assert before == after

    captured = capsys.readouterr()
    assert "기타의금융자산" in captured.out
    assert "추가 예정 1 매핑" in captured.out


def test_apply_adds_mapping_and_updates_metadata(promoteMod, stagingFile: Path, jsonFile: Path) -> None:
    rc = promoteMod.main(["--staging", str(stagingFile), "--json", str(jsonFile), "apply"])
    assert rc == 0

    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    assert data["mappings"]["기타의금융자산"] == "other_financial_assets"
    # 기존 매핑 보존
    assert data["mappings"]["자산총계"] == "total_assets"
    # 신호 거부된 typo 는 미적용
    assert "지배지업소유주지분" not in data["mappings"]

    meta = data["_metadata"]
    assert meta["addedCount"] == 1
    # lastUpdate 갱신 — fixture 의 2026-03-09 와 달라짐
    assert meta["lastUpdate"] != "2026-03-09"


def test_apply_idempotent_when_already_synced(promoteMod, stagingFile: Path, jsonFile: Path) -> None:
    # 1 차 apply
    promoteMod.main(["--staging", str(stagingFile), "--json", str(jsonFile), "apply"])
    # 2 차 apply — 추가할 매핑 없음
    rc = promoteMod.main(["--staging", str(stagingFile), "--json", str(jsonFile), "apply"])
    assert rc == 0

    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    # addedCount 는 1 유지
    assert data["_metadata"]["addedCount"] == 1


def test_apply_rejects_conflict_without_force(promoteMod, stagingFile: Path, jsonFile: Path) -> None:
    # 충돌 시나리오: 기존에 "기타의금융자산" → 다른 snakeId 등록
    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    data["mappings"]["기타의금융자산"] = "different_snake_id"
    jsonFile.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    before = jsonFile.read_text(encoding="utf-8")
    rc = promoteMod.main(["--staging", str(stagingFile), "--json", str(jsonFile), "apply"])
    assert rc == 1
    after = jsonFile.read_text(encoding="utf-8")
    assert before == after  # zero modification


def test_apply_with_force_skips_conflict_but_adds_other(promoteMod, tmp_path: Path, jsonFile: Path) -> None:
    """force 시에도 충돌 매핑은 overwrite 하지 않고, 새 매핑만 추가."""
    # 새 staging — 충돌 1 + 신규 1
    schema = {
        "firstSeenAt": pl.String,
        "lastSeenAt": pl.String,
        "accountId": pl.String,
        "accountNm": pl.String,
        "occurrenceCount": pl.Int64,
        "stockCodes": pl.List(pl.String),
        "sjDivs": pl.List(pl.String),
        "corporateDispersion": pl.Int64,
        "suggestedSnakeId": pl.String,
        "confidence": pl.Float64,
        "signalBreakdown": pl.String,
        "autoEligible": pl.Boolean,
        "status": pl.String,
        "operatorNote": pl.String,
        "decidedAt": pl.String,
    }
    rows = [
        {
            "firstSeenAt": "2026-05-15T00:00:00+00:00",
            "lastSeenAt": "2026-05-15T00:00:00+00:00",
            "accountId": "",
            "accountNm": "자산총계",  # 기존과 충돌
            "occurrenceCount": 5,
            "stockCodes": ["005930", "000660", "035720"],
            "sjDivs": ["BS"],
            "corporateDispersion": 3,
            "suggestedSnakeId": "different_value",
            "confidence": 0.9,
            "signalBreakdown": "{}",
            "autoEligible": True,
            "status": "confirmed",
            "operatorNote": None,
            "decidedAt": "2026-05-15T00:00:00+00:00",
        },
        {
            "firstSeenAt": "2026-05-15T00:00:00+00:00",
            "lastSeenAt": "2026-05-15T00:00:00+00:00",
            "accountId": "",
            "accountNm": "기타의금융자산",
            "occurrenceCount": 14,
            "stockCodes": ["005930", "000660", "035720"],
            "sjDivs": ["BS"],
            "corporateDispersion": 3,
            "suggestedSnakeId": "other_financial_assets",
            "confidence": 0.86,
            "signalBreakdown": "{}",
            "autoEligible": True,
            "status": "confirmed",
            "operatorNote": None,
            "decidedAt": "2026-05-15T00:00:00+00:00",
        },
    ]
    staging = tmp_path / "staging.parquet"
    pl.DataFrame(rows, schema=schema).write_parquet(staging)

    rc = promoteMod.main(["--staging", str(staging), "--json", str(jsonFile), "apply", "--force"])
    assert rc == 0

    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    # 기존 매핑은 보존 — overwrite 금지
    assert data["mappings"]["자산총계"] == "total_assets"
    # 신규 매핑은 추가
    assert data["mappings"]["기타의금융자산"] == "other_financial_assets"


def test_apply_rejects_ghost_snake_id(promoteMod, tmp_path: Path, jsonFile: Path) -> None:
    """standardAccounts 부재 snakeId 는 apply 차단 (환각 매핑 가드)."""
    schema = {
        "firstSeenAt": pl.String,
        "lastSeenAt": pl.String,
        "accountId": pl.String,
        "accountNm": pl.String,
        "occurrenceCount": pl.Int64,
        "stockCodes": pl.List(pl.String),
        "sjDivs": pl.List(pl.String),
        "corporateDispersion": pl.Int64,
        "suggestedSnakeId": pl.String,
        "confidence": pl.Float64,
        "signalBreakdown": pl.String,
        "autoEligible": pl.Boolean,
        "status": pl.String,
        "operatorNote": pl.String,
        "decidedAt": pl.String,
    }
    rows = [
        {
            "firstSeenAt": "2026-05-16T00:00:00+00:00",
            "lastSeenAt": "2026-05-16T00:00:00+00:00",
            "accountId": "",
            "accountNm": "환각계정",
            "occurrenceCount": 10,
            "stockCodes": ["005930", "000660", "035720"],
            "sjDivs": ["BS"],
            "corporateDispersion": 3,
            "suggestedSnakeId": "non_existent_snake_id",  # standardAccounts 부재
            "confidence": 0.99,
            "signalBreakdown": "{}",
            "autoEligible": True,
            "status": "confirmed",
            "operatorNote": None,
            "decidedAt": "2026-05-16T00:00:00+00:00",
        }
    ]
    staging = tmp_path / "ghost_staging.parquet"
    pl.DataFrame(rows, schema=schema).write_parquet(staging)

    before = jsonFile.read_text(encoding="utf-8")
    rc = promoteMod.main(["--staging", str(staging), "--json", str(jsonFile), "apply"])
    assert rc == 1
    after = jsonFile.read_text(encoding="utf-8")
    assert before == after  # zero modification


def test_apply_to_layer_routes_target(promoteMod, stagingFile: Path, jsonFile: Path) -> None:
    """--layer nameSynonym → layers.nameSynonym 에 추가, 기본 mappings 미오염."""
    rc = promoteMod.main(["--staging", str(stagingFile), "--json", str(jsonFile), "--layer", "nameSynonym", "apply"])
    assert rc == 0
    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    assert data["layers"]["nameSynonym"]["기타의금융자산"] == "other_financial_assets"
    assert "기타의금융자산" not in data.get("mappings", {})


def test_non_snake_layer_skips_ghost_check(promoteMod, tmp_path: Path, jsonFile: Path) -> None:
    """idSynonym(value=영문 id, snakeId 아님)은 standardAccounts ghost check 미적용.

    같은 후보가 mappings 였다면 ghost 로 reject 되지만, idSynonym 은 value 가
    snakeId 가 아니므로 SA 부재여도 적용된다.
    """
    schema = {
        "firstSeenAt": pl.String,
        "lastSeenAt": pl.String,
        "accountId": pl.String,
        "accountNm": pl.String,
        "occurrenceCount": pl.Int64,
        "stockCodes": pl.List(pl.String),
        "sjDivs": pl.List(pl.String),
        "corporateDispersion": pl.Int64,
        "suggestedSnakeId": pl.String,
        "confidence": pl.Float64,
        "signalBreakdown": pl.String,
        "autoEligible": pl.Boolean,
        "status": pl.String,
        "operatorNote": pl.String,
        "decidedAt": pl.String,
    }
    rows = [
        {
            "firstSeenAt": "2026-06-05T00:00:00+00:00",
            "lastSeenAt": "2026-06-05T00:00:00+00:00",
            "accountId": "",
            "accountNm": "SalesRevenue",
            "occurrenceCount": 10,
            "stockCodes": ["005930", "000660", "035720"],
            "sjDivs": ["IS"],
            "corporateDispersion": 3,
            "suggestedSnakeId": "Revenue",  # 영문 id, standardAccounts 부재 — idSynonym 에선 OK
            "confidence": 0.9,
            "signalBreakdown": "{}",
            "autoEligible": True,
            "status": "confirmed",
            "operatorNote": None,
            "decidedAt": "2026-06-05T00:00:00+00:00",
        }
    ]
    staging = tmp_path / "idsyn_staging.parquet"
    pl.DataFrame(rows, schema=schema).write_parquet(staging)

    rc = promoteMod.main(["--staging", str(staging), "--json", str(jsonFile), "--layer", "idSynonym", "apply"])
    assert rc == 0
    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    assert data["layers"]["idSynonym"]["SalesRevenue"] == "Revenue"


def test_apply_to_edgar_learned_tags(promoteMod, stagingFile: Path, jsonFile: Path) -> None:
    """--layer edgarLearnedTags → edgar.learnedTags (DART/EDGAR 단일 write 게이트)."""
    rc = promoteMod.main(
        ["--staging", str(stagingFile), "--json", str(jsonFile), "--layer", "edgarLearnedTags", "apply"]
    )
    assert rc == 0
    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    assert data["edgar"]["learnedTags"]["기타의금융자산"] == "other_financial_assets"
    assert "기타의금융자산" not in data.get("mappings", {})  # DART 미오염


def test_set_repairs_existing_alias_with_compare_and_set(promoteMod, jsonFile: Path) -> None:
    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    data.setdefault("layers", {})["snakeAlias"] = {"old_equity": "owners_of_parent_equity"}
    jsonFile.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    rc = promoteMod.main(
        [
            "--json",
            str(jsonFile),
            "--layer",
            "snakeAlias",
            "set",
            "--key",
            "old_equity",
            "--expected",
            "owners_of_parent_equity",
            "--value",
            "total_stockholders_equity",
        ]
    )

    result = json.loads(jsonFile.read_text(encoding="utf-8"))
    assert rc == 0
    assert result["layers"]["snakeAlias"]["old_equity"] == "total_stockholders_equity"


def test_delete_removes_only_expected_alias(promoteMod, jsonFile: Path) -> None:
    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    data.setdefault("layers", {})["snakeAlias"] = {"total_stockholders_equity": "total_equity"}
    jsonFile.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    rc = promoteMod.main(
        [
            "--json",
            str(jsonFile),
            "--layer",
            "snakeAlias",
            "delete",
            "--key",
            "total_stockholders_equity",
            "--expected",
            "total_equity",
        ]
    )

    result = json.loads(jsonFile.read_text(encoding="utf-8"))
    assert rc == 0
    assert "total_stockholders_equity" not in result["layers"]["snakeAlias"]


def test_set_rejects_stale_expected_value(promoteMod, jsonFile: Path) -> None:
    data = json.loads(jsonFile.read_text(encoding="utf-8"))
    data.setdefault("layers", {})["snakeAlias"] = {"old_equity": "owners_of_parent_equity"}
    jsonFile.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    rc = promoteMod.main(
        [
            "--json",
            str(jsonFile),
            "--layer",
            "snakeAlias",
            "set",
            "--key",
            "old_equity",
            "--expected",
            "stale_value",
            "--value",
            "total_stockholders_equity",
        ]
    )

    assert rc == 1


def test_rollback_restores_previous_file(promoteMod, monkeypatch, tmp_path: Path) -> None:
    """git show 호출을 mock 하고 복원 동작 검증."""
    target = tmp_path / "accountMappings.json"
    target.write_text(
        json.dumps({"mappings": {"current": "x"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    class _FakeResult:
        stdout = json.dumps({"mappings": {"restored": "y"}}, ensure_ascii=False)

    def _fakeRun(*args, **kwargs):
        return _FakeResult()

    monkeypatch.setattr(promoteMod.subprocess, "run", _fakeRun)
    rc = promoteMod.main(["--json", str(target), "rollback", "--to", "deadbeef"])
    assert rc == 0
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == {"mappings": {"restored": "y"}}
