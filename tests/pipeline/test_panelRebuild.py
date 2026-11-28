"""panelRebuild stage: 샤드 배정, 묶음 나누기, 회사 검사 판정, 커밋 겹침 처리, 워크플로 계약.

네트워크 없이 돈다. 회사 검사는 작은 원문 zip 과 panel parquet 으로, 커밋은 가짜 HF api 로 본다.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest
import yaml

from dartlab.pipeline.stages import panelRebuild as mod

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
RCEPT = "20250310000001"
WORDS = [f"낱말{i}가" for i in range(40)]


def test_shardOf_is_stable_and_partitions_codes() -> None:
    """같은 코드는 언제나 같은 샤드이고, 샤드를 모두 모으면 전 회사가 한 번씩 나온다."""
    assert mod._shardOf("005930", 16) == 8
    assert mod._shardOf("000660", 16) == 2
    codes = [f"{i:06d}" for i in range(500)]
    shards = [[c for c in codes if mod._shardOf(c, 16) == s] for s in range(16)]
    assert sorted(c for shard in shards for c in shard) == codes
    assert all(shards), "빈 샤드가 있으면 러너가 놀고 다른 샤드가 길어진다"


@pytest.mark.parametrize(("text", "expected"), [("0/1", (0, 1)), ("3/16", (3, 16)), ("", (0, 1))])
def test_parseShard_reads_index_and_count(text: str, expected: tuple[int, int]) -> None:
    """i/n 을 읽고, 비면 샤드 하나로 본다."""
    assert mod._parseShard(text) == expected


@pytest.mark.parametrize("text", ["16/16", "-1/4", "1/0", "3", "a/b"])
def test_parseShard_rejects_bad_value(text: str) -> None:
    """범위 밖이나 꼴이 틀린 값은 조용히 샤드 0 으로 돌지 않고 멈춘다."""
    with pytest.raises(ValueError):
        mod._parseShard(text)


def test_chunks_split_by_tar_size() -> None:
    """원문 tar 크기 합으로 묶고, 혼자 큰 회사는 혼자 한 묶음이다."""
    size = {"A": 60, "B": 60, "C": 200, "D": 10, "E": 10}
    assert mod._chunks(["A", "B", "C", "D", "E"], size, 100) == [["A"], ["B"], ["C"], ["D", "E"]]
    assert mod._chunks([], size, 100) == []


def test_registry_binds_panelRebuild() -> None:
    """CLI(python -m dartlab.pipeline panelRebuild)가 찾는 stage 로 등록돼 있다."""
    from dartlab.pipeline.registry import buildRegistry

    spec = buildRegistry()["panelRebuild"]
    assert spec.run is mod.runPanelRebuild
    assert spec.uploadCategories == ("panel",)


def _company(tmp_path: Path, panelText: str, *, extraZip: bool = False, seedOk: bool = True) -> dict:
    """원문 zip 하나(낱말 40개)와 새 panel 한 보고서를 만들고 검사 task 를 돌려준다."""
    docs = tmp_path / "docs" / "AAA"
    docs.mkdir(parents=True)
    xml = "<DOCUMENT><BODY><P>" + " ".join(WORDS) + "</P></BODY></DOCUMENT>"
    with zipfile.ZipFile(docs / f"{RCEPT}.zip", "w") as zf:
        zf.writestr(f"{RCEPT}.xml", xml.encode("utf-8"))
    if extraZip:
        with zipfile.ZipFile(docs / "20250515000002.zip", "w") as zf:
            zf.writestr("20250515000002.xml", xml.encode("utf-8"))
    pl.DataFrame(
        {
            "period": ["2024Q4"],
            "rceptNo": [RCEPT],
            "chapter": ["IV. 이사의 경영진단 및 분석의견"],
            "contentRaw": [panelText],
        }
    ).write_parquet(tmp_path / "new.parquet")
    return {
        "code": "AAA",
        "seedOk": seedOk,
        "error": "",
        "docsDir": str(docs),
        "newPath": str(tmp_path / "new.parquet"),
        "outPath": str(tmp_path / "upload" / "AAA.parquet"),
        "oldDir": str(tmp_path / "old"),
        "repo": "unused/repo",
        "revision": "unused",
        "oldSha": "",  # HF 에 옛 panel 이 없는 회사: 옛 판 받기를 하지 않는다
    }


def test_check_passes_when_panel_keeps_source_words(tmp_path: Path) -> None:
    """원문 낱말이 다 남으면 통과하고, 올릴 파일과 그 sha 를 만든다."""
    rec = mod._checkCompany(_company(tmp_path, " ".join(WORDS)))
    assert rec["status"] == "ok", rec
    assert rec["newMdna"] == 1 and rec["zips"] == 1 and rec["worstCoverage"] == 1.0
    out = tmp_path / "upload" / "AAA.parquet"
    assert out.exists() and rec["outSha"] == mod._fileSha(out)


def test_check_holds_when_words_are_lost(tmp_path: Path) -> None:
    """panel 글에서 원문 낱말 30 개 넘게 빠지면 올리지 않는다."""
    rec = mod._checkCompany(_company(tmp_path, " ".join(WORDS[:5])))
    assert rec["status"] == "hold:source"
    assert rec["maxRealLost"] == 35 and RCEPT in rec["badReports"]
    assert not (tmp_path / "upload" / "AAA.parquet").exists()


def test_check_holds_when_source_zip_is_missing_from_panel(tmp_path: Path) -> None:
    """원문 zip 하나가 panel 에 없으면 올리지 않는다."""
    rec = mod._checkCompany(_company(tmp_path, " ".join(WORDS), extraZip=True))
    assert rec["status"] == "hold:source" and rec["zipMissing"] == 1
    assert "20250515000002:없음" in rec["badReports"]


def test_check_holds_on_seed_or_build_failure(tmp_path: Path) -> None:
    """원문 받기에 실패했거나 빌드 파일이 없으면 검사하지 않고 보류한다."""
    assert mod._checkCompany(_company(tmp_path / "a", "x", seedOk=False))["status"] == "hold:seed"
    task = _company(tmp_path / "b", "x")
    Path(task["newPath"]).unlink()
    assert mod._checkCompany(task)["status"] == "hold:build"


class _FakeApi:
    """HEAD 와 회사 파일 sha 만 가진 HF api. 첫 커밋은 다른 커밋과 겹치게 할 수 있다."""

    def __init__(self, files: dict[str, str], *, conflictOnce: dict[str, str] | None = None) -> None:
        self.head = "h1"
        self.files = dict(files)
        self.conflictOnce = conflictOnce
        self.commits: list[tuple[str, list[str]]] = []
        self.preuploaded = 0

    def repo_info(self, repo: str, repo_type: str) -> SimpleNamespace:
        return SimpleNamespace(sha=self.head)

    def get_paths_info(self, repo: str, paths: list[str], repo_type: str, revision: str) -> list[SimpleNamespace]:
        out = []
        for path in paths:
            code = Path(path).stem
            if code in self.files:
                out.append(SimpleNamespace(path=path, lfs=SimpleNamespace(sha256=self.files[code]), blob_id=""))
        return out

    def preupload_lfs_files(self, repo: str, additions: list, repo_type: str) -> None:
        self.preuploaded += len(additions)

    def create_commit(self, *, repo_id: str, repo_type: str, operations: list, commit_message: str, parent_commit: str):
        from huggingface_hub.utils import HfHubHTTPError

        codes = [Path(op.path_in_repo).stem for op in operations]
        self.commits.append((parent_commit, codes))
        if self.conflictOnce is not None:
            # 그사이 다른 작업이 커밋해 HEAD 가 움직이고 그 작업이 바꾼 회사 파일도 있다.
            self.files.update(self.conflictOnce)
            self.conflictOnce = None
            self.head = "h2"
            raise HfHubHTTPError("412 Precondition Failed: A commit has happened since")
        for op in operations:
            self.files[Path(op.path_in_repo).stem] = mod._fileSha(Path(op.path_or_fileobj))
        self.head = "h3"
        return SimpleNamespace(oid="h3")


def _records(tmp_path: Path, codes: list[str]) -> list[dict]:
    """올릴 파일을 만들고 ok 상태 장부 줄을 돌려준다(옛 sha 는 old-{code})."""
    uploadDir = tmp_path / "upload"
    uploadDir.mkdir(parents=True, exist_ok=True)
    out = []
    for code in codes:
        path = uploadDir / f"{code}.parquet"
        path.write_bytes(f"new {code}".encode())
        out.append({**mod._baseRec(code, oldSha=f"old-{code}"), "status": "ok", "outSha": mod._fileSha(path)})
    return out


def test_commit_retries_on_conflict_and_skips_raced_company(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """다른 커밋과 겹치면 다시 견주고, 그사이 바뀐 회사는 빼고 나머지만 다시 커밋한다."""
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)
    records = _records(tmp_path, ["AAA", "BBB"])
    api = _FakeApi({"AAA": "old-AAA", "BBB": "old-BBB"}, conflictOnce={"BBB": "other-writer"})
    mod._commitChunk(api, "repo", records, tmp_path / "upload", "0/1")
    byCode = {r["code"]: r for r in records}
    assert api.preuploaded == 2, "LFS 는 한 번만 올린다"
    assert api.commits == [("h1", ["AAA", "BBB"]), ("h2", ["AAA"])]
    assert byCode["AAA"]["uploaded"] and byCode["AAA"]["commit"] == "h3"
    assert byCode["BBB"]["status"] == "hold:raced" and not byCode["BBB"]["uploaded"]
    assert api.files["BBB"] == "other-writer", "다른 작업이 올린 파일을 덮지 않는다"


def test_commit_marks_already_landed_file_without_new_commit(tmp_path: Path) -> None:
    """앞 시도가 서버에 들어갔는데 답만 못 받았으면 다시 커밋하지 않고 올린 것으로 적는다."""
    records = _records(tmp_path, ["AAA"])
    api = _FakeApi({"AAA": records[0]["outSha"]})
    mod._commitChunk(api, "repo", records, tmp_path / "upload", "0/1")
    assert api.commits == [] and records[0]["uploaded"] and records[0]["commit"] == "h1"


def test_verify_turns_changed_upload_into_raced(tmp_path: Path) -> None:
    """올린 뒤 HF 파일이 바뀐 회사는 다음 run 이 다시 하도록 hold:raced 로 돌린다."""
    records = _records(tmp_path, ["AAA", "BBB"])
    for r in records:
        r["uploaded"] = True
    api = _FakeApi({"AAA": records[0]["outSha"], "BBB": "changed-later"})
    assert mod._verifyUploaded(api, "repo", records) == ["BBB"]
    assert records[1]["status"] == "hold:raced" and not records[1]["uploaded"]
    assert records[0]["status"] == "ok" and records[0]["uploaded"]


def test_workflow_contract() -> None:
    """샤드는 공유 직렬 그룹 밖에서 서로 막지 않고 돌며, 장부는 실패해도 남는다."""
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "panelRebuild.yml").read_text(encoding="utf-8"))
    assert wf["concurrency"]["group"] == "panel-rebuild"
    rebuild = wf["jobs"]["rebuild"]
    assert "concurrency" not in rebuild, "샤드 job 에 그룹을 걸면 실행 1 + 대기 1 만 남고 나머지가 밀려난다"
    assert rebuild["strategy"]["fail-fast"] is False
    assert "needs.plan.outputs.shards" in rebuild["strategy"]["matrix"]["shard"]
    step = next(s for s in rebuild["steps"] if "PANEL_REBUILD_SHARD" in (s.get("env") or {}))
    deadline = int(step["env"]["PANEL_REBUILD_DEADLINE_MIN"])
    assert rebuild["timeout-minutes"] >= deadline + 30, "마감 뒤 마지막 묶음 검사·올리기와 확인이 끝날 여유"
    keep = next(s for s in rebuild["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact"))
    assert keep["if"] == "always()"
