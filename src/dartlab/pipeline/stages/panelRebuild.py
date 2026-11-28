"""panelRebuild stage: DART panel 을 원문 tar 로 다시 만들고, 원문과 견주어 통과한 회사만 HF 에 올린다.

빌더 추출 규칙이 바뀌면(예: xmlRepair 가 글자 꺾쇠를 태그로 읽어 뒤 장이 묻히던 것) 과거 전 보고서에
전파해야 한다. ``dartZip`` 의 full-rebuild 는 검사 없이 통째로 덮어써서, 새 빌더의 회귀가 그대로
공개 panel 을 깎는다. 본 stage 는 회사마다 다음을 본 뒤에만 올린다.

1. 원문 zip 의 낱말이 panel 에 남았는지와 글 길이 비. 표 칸·줄바꿈으로 붙은 낱말은 빠진 것이 아니다.
2. 원문 zip 이 panel 에 다 들어갔는지.
3. 수리가 장 구조 태그(SECTION·BODY·LIBRARY·DOCUMENT)를 글자로 바꾸지 않았는지.
4. 옛 panel 의 장 이름(I~XII, 【】)이 빠지지 않았는지. 2단계 제목이 장으로 잘못 읽혔다가 빠진 것은 고친 것이다.

옛 panel 에만 있는 보고서(원문 tar 에 없는 보고서)는 ``PanelArtifactAssembler`` 로 그대로 붙이고,
붙인 뒤 줄 수와 글자 수가 새 파일·옛 파일과 같은지 본다. 올리기 직전 HF 파일이 그사이 바뀐 회사는
올리지 않는다(``hold:raced``). 커밋은 ``parent_commit`` 으로 걸고, 다른 커밋이 끼면 다시 견준다.

한 PC 는 메모리 가드(병렬 Company 2 이하)로 2 곳씩만 만들 수 있어 전 회사에 20 시간이 넘는다.
GitHub 러너 여러 대로 나눠 돌리도록 회사를 ``crc32(code) % n`` 샤드로 나눈다(tar 크기가 바뀌어도
배정이 흔들리지 않는다). 운영자 트리거 전용이다(``.github/workflows/panelRebuild.yml``).

env:
    PANEL_REBUILD_SHARD: ``"i/n"`` (기본 ``"0/1"``).
    PANEL_REBUILD_CODES: 쉼표·공백 구분 회사코드(비우면 원문 저장소의 전 회사).
    PANEL_REBUILD_CHUNK_MB: 한 묶음의 원문 tar 크기(기본 150). 빌드 시간이 크기에 비례한다.
    PANEL_REBUILD_DEADLINE_MIN: 이 분을 넘길 것 같으면 새 묶음을 시작하지 않는다(기본 290).
    PANEL_WORKERS: 빌드 작업자 1~2(기본 2, ``buildPanelAll`` 메모리 가드).

장부: ``data/panelRebuild/ledger-{i}.parquet`` (회사마다 한 줄. 상태와 검사 칸).
상태: ``ok`` 올림(검사만이면 통과), ``hold:*`` 보류(이유는 칸과 error), ``left`` 시간이 모자라 이번에 못 함.
"""

from __future__ import annotations

import hashlib
import html
import os
import random
import re
import shutil
import time
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dartlab.pipeline.types import PipelineMode, StageResult

_WORD = re.compile(r"[가-힣A-Za-z0-9]{2,}")
_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")
# 태그 없는 panel 글에도 없는 낱말이 보고서 하나에서 이보다 많으면 보류한다.
_MIN_LOST_WORDS = 30
# panel 글이 원문보다 이 배를 넘게 길면(같은 글이 겹쳐 들어감) 보류한다.
_MAX_LENGTH_RATIO = 1.5
_CHECK_WORKERS = 2
_COMMIT_ATTEMPTS = 20
_MDNA = "경영진단"
# 수리가 글자로 바꾼 장 구조 태그(있으면 보류)와 표 태그(세기만), 장(I~XII, 【】) 이름.
_STRUCT_TEXT = re.compile(r"&lt;/?(?:SECTION-\d|BODY|LIBRARY|DOCUMENT)(?=[\s/>])")
_TABLE_TEXT = re.compile(r"&lt;/?(?:TABLE|TBODY|THEAD|TR|TD|TH|TE|TU)(?=[\s/>])")
_CHAPTER_NAME = re.compile(r"^\s*(?:[IVX]+\.|【)")


def _parseShard(text: str) -> tuple[int, int]:
    """``"i/n"`` 을 (i, n) 으로 읽는다. 0 <= i < n 이 아니면 ValueError."""
    left, sep, right = (text or "0/1").strip().partition("/")
    if not sep:
        raise ValueError(f"PANEL_REBUILD_SHARD 는 i/n 꼴이어야 한다: {text!r}")
    index, count = int(left), int(right)
    if count < 1 or not 0 <= index < count:
        raise ValueError(f"PANEL_REBUILD_SHARD 범위 밖: {text!r}")
    return index, count


def _shardOf(code: str, shards: int) -> int:
    """회사코드의 샤드 번호. 같은 코드는 언제나 같은 샤드다."""
    return zlib.crc32(code.encode("utf-8")) % shards


def _chunks(codes: list[str], tarSize: dict[str, int], chunkBytes: float) -> list[list[str]]:
    """회사를 원문 tar 크기 합이 chunkBytes 를 넘지 않게 묶는다(한 회사가 넘으면 혼자 한 묶음)."""
    out: list[list[str]] = []
    current: list[str] = []
    size = 0
    for code in codes:
        one = tarSize.get(code, 0)
        if current and size + one > chunkBytes:
            out.append(current)
            current, size = [], 0
        current.append(code)
        size += one
    if current:
        out.append(current)
    return out


def _textWords(text: str) -> set[str]:
    """태그를 빼고 글자 참조를 풀어 두 글자 넘는 낱말 집합을 만든다."""
    return set(_WORD.findall(html.unescape(_TAG.sub(" ", text))))


def _flatLen(text: str) -> int:
    """태그와 공백을 뺀 글자 수."""
    return len(_SPACE.sub("", html.unescape(_TAG.sub("", text))))


def _repairedTags(raw: bytes, text: str) -> tuple[int, int]:
    """빌더와 같은 수리가 글자로 바꾼 장 구조 태그 수와 표 태그 수를 원문 글과 견주어 센다."""
    from dartlab.providers.dart.panel.build.refScan.zipScanWorker import _decodeXmlBytes

    fixed = _decodeXmlBytes(raw)
    struct = len(_STRUCT_TEXT.findall(fixed)) - len(_STRUCT_TEXT.findall(text))
    table = len(_TABLE_TEXT.findall(fixed)) - len(_TABLE_TEXT.findall(text))
    return struct, table


def _zipWords(path: Path) -> tuple[set[str], int, int, int]:
    """zip 안 모든 파일의 낱말 집합, 글자 수, 수리가 글자로 바꾼 장 구조 태그 수와 표 태그 수."""
    words: set[str] = set()
    length = struct = table = 0
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            raw = zf.read(info)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("cp949", errors="replace")
            words |= _textWords(text)
            length += _flatLen(text)
            if info.filename.lower().endswith(".xml"):
                a, b = _repairedTags(raw, text)
                struct += a
                table += b
    return words, length, struct, table


def _chapterSets(df: Any) -> dict[str, set[str]]:
    """접수번호마다 그 보고서에 나온 장 이름 집합."""
    out: dict[str, set[str]] = {}
    for rcept, chapter in df.select("rceptNo", "chapter").unique().drop_nulls().iter_rows():
        out.setdefault(rcept, set()).add(chapter)
    return out


def _fileSha(path: Path) -> str:
    """파일의 sha256 (HF LFS sha 와 같은 값)."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _mergeOld(newPath: Path, oldPath: Path, outPath: Path) -> None:
    """옛 panel 의 같은 보고서를 새 보고서로 바꾸고, 옛 panel 에만 있는 보고서는 남겨 outPath 에 쓴다."""
    import polars as pl

    from dartlab.providers.dart.panel.build.artifactWriter import PanelArtifactAssembler

    shutil.copyfile(oldPath, outPath)
    new = pl.read_parquet(newPath)
    with PanelArtifactAssembler(outPath) as assembler:
        for part in new.partition_by(["period", "rceptNo"], maintain_order=True):
            assembler.add(part, period=part["period"][0], receiptNumber=part["rceptNo"][0])
        assembler.commit(merge=True, overwrite=True)


def _mdnaReports(df: Any) -> int:
    """사업보고서(Q4) 가운데 경영진단 장이 있는 보고서 수."""
    import polars as pl

    q4 = df.filter(pl.col("period").str.ends_with("Q4") & pl.col("chapter").str.contains(_MDNA, literal=True))
    return q4["rceptNo"].n_unique()


def _baseRec(code: str, *, error: str = "", oldSha: str = "") -> dict[str, Any]:
    """장부 한 줄의 모든 칸을 기본값으로 만든다(보류한 회사도 칸이 같다)."""
    return {
        "code": code,
        "status": "",
        "error": error,
        "zips": 0,
        "zipMissing": 0,
        "worstCoverage": 1.0,
        "maxLengthRatio": 0.0,
        "measuredReports": 0,
        "maxRealLost": 0,
        "badReports": "",
        "structTextReports": 0,
        "tableTextReports": 0,
        "tagTextSample": "",
        "lostNamedChapterReports": 0,
        "oldExists": False,
        "oldRows": 0,
        "newRows": 0,
        "maxCell": 0,
        "oldReports": 0,
        "newReports": 0,
        "oldOnly": "",
        "oldOnlyRows": 0,
        "addedRcept": 0,
        "lostChapterReports": 0,
        "gainedChapterReports": 0,
        "newQ4": 0,
        "oldMdna": 0,
        "newMdna": 0,
        "outRows": 0,
        "oldSha": oldSha,
        "outSha": "",
        "uploaded": False,
        "commit": "",
    }


def _checkCompany(task: dict[str, Any]) -> dict[str, Any]:
    """회사 하나를 검사한다. 검사 중 예외는 그 회사만 hold:check 로 적는다(묶음을 멈추지 않는다)."""
    try:
        return _checkCompanyBody(task)
    except Exception as exc:  # noqa: BLE001 (회사 하나의 검사 실패는 그 회사만 보류)
        Path(task["outPath"]).unlink(missing_ok=True)
        shutil.rmtree(Path(task["oldDir"]) / task["code"], ignore_errors=True)
        rec = _baseRec(task["code"], error=task["error"], oldSha=task["oldSha"])
        rec["status"] = "hold:check"
        rec["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
        return rec


def _noteTagText(rec: dict[str, Any], stem: str, structText: int, tableText: int) -> None:
    """수리가 글자로 바꾼 장 구조 태그와 표 태그가 있는 보고서를 장부 칸에 센다."""
    if structText > 0:
        rec["structTextReports"] += 1
    if tableText > 0:
        rec["tableTextReports"] += 1
    if (structText > 0 or tableText > 0) and len(rec["tagTextSample"]) < 400:
        rec["tagTextSample"] += f"{stem}:{structText}/{tableText} "


def _compareZip(rec: dict[str, Any], zipPath: Path, texts: list[str], bad: list[str]) -> None:
    """원문 zip 하나를 그 보고서의 panel 글과 견주어 검사 칸을 채우고, 못 미치면 bad 에 더한다."""
    src, srcLength, structText, tableText = _zipWords(zipPath)
    _noteTagText(rec, zipPath.stem, structText, tableText)
    got: set[str] = set()
    gotLength = 0
    for t in texts:
        if t:
            got |= _textWords(t)
            gotLength += _flatLen(t)
    lostWords = src - got
    lost = len(lostWords)
    cov = 1.0 - lost / len(src) if src else 1.0
    ratio = gotLength / srcLength if srcLength else 0.0
    rec["worstCoverage"] = min(rec["worstCoverage"], round(cov, 5))
    rec["maxLengthRatio"] = max(rec["maxLengthRatio"], round(ratio, 4))
    if lost > _MIN_LOST_WORDS:
        # 표 칸이나 줄바꿈으로 나뉜 낱말을 panel 이 붙여 쓴 경우는 빠진 것이 아니다.
        # 태그와 공백을 뺀 panel 글 안에도 없는 낱말만 진짜 빠진 낱말로 센다.
        gotFlat = "".join(_SPACE.sub("", html.unescape(_TAG.sub("", t))) for t in texts if t)
        realLost = sum(1 for w in lostWords if w not in gotFlat)
        rec["measuredReports"] += 1
        rec["maxRealLost"] = max(rec["maxRealLost"], realLost)
        if realLost > _MIN_LOST_WORDS:
            bad.append(f"{zipPath.stem}:{cov:.3f}/{realLost}")
    if ratio > _MAX_LENGTH_RATIO:
        bad.append(f"{zipPath.stem}:x{ratio:.2f}")


def _downloadOld(task: dict[str, Any], oldLocal: Path) -> Path | None:
    """HF 의 옛 panel 을 sha 를 읽은 같은 revision 에서 받는다. HF 에 없던 회사는 None.

    받기 실패를 옛 panel 없음으로 넘기면 옛 panel 에만 있는 보고서가 빠진 채 올라가므로 잡지 않는다
    (``_checkCompany`` 가 hold:check 로 적는다).
    """
    if not task["oldSha"]:
        return None
    from huggingface_hub import hf_hub_download

    from dartlab.core.hfRetry import retryHfCall

    return Path(
        retryHfCall(
            hf_hub_download,
            task["repo"],
            f"dart/panel/{task['code']}.parquet",
            repo_type="dataset",
            revision=task["revision"],
            local_dir=str(oldLocal),
        )
    )


def _compareOld(
    rec: dict[str, Any], oldPath: Path, newSets: dict[str, set[str]], newAll: set[str]
) -> tuple[list[str], int]:
    """옛 panel 과 장·보고서 목록을 견주고, 옛 panel 에만 있는 보고서와 그 글자 수를 돌려준다."""
    import polars as pl

    rec["oldExists"] = True
    old = pl.read_parquet(oldPath, columns=["period", "rceptNo", "chapter"])
    oldSets = _chapterSets(old)
    rec["oldRows"], rec["oldReports"] = old.height, old["rceptNo"].n_unique()
    rec["oldMdna"] = _mdnaReports(old)
    oldAll = set(old["rceptNo"].unique().to_list())
    del old
    oldOnly = sorted(oldAll - newAll)
    rec["oldOnly"] = " ".join(oldOnly)[:500]
    rec["addedRcept"] = len(newAll - oldAll)
    rec["lostChapterReports"] = sum(1 for r, s in oldSets.items() if r in newSets and not s <= newSets[r])
    rec["gainedChapterReports"] = sum(1 for r, s in newSets.items() if r in oldSets and not s <= oldSets[r])
    rec["lostNamedChapterReports"] = sum(
        1 for r, s in oldSets.items() if r in newSets and any(_CHAPTER_NAME.match(c) for c in s - newSets[r])
    )
    if not oldOnly:
        return oldOnly, 0
    kept = (
        pl.scan_parquet(oldPath)
        .filter(pl.col("rceptNo").is_in(oldOnly))
        .select(pl.len().alias("rows"), pl.col("contentRaw").str.len_chars().sum().alias("length"))
        .collect()
    )
    rec["oldOnlyRows"] = int(kept["rows"][0])
    return oldOnly, int(kept["length"][0] or 0)


def _checkCompanyBody(task: dict[str, Any]) -> dict[str, Any]:
    """회사 하나를 원문 zip·옛 panel 과 견주고, 통과하면 올릴 파일을 만든다."""
    import polars as pl

    code = task["code"]
    rec = _baseRec(code, error=task["error"], oldSha=task["oldSha"])
    docsDir, newPath, outPath = Path(task["docsDir"]), Path(task["newPath"]), Path(task["outPath"])
    if not task["seedOk"]:
        rec["status"] = "hold:seed"
        return rec
    if not newPath.exists():
        rec["status"] = "hold:build"
        return rec
    new = pl.read_parquet(newPath, columns=["period", "rceptNo", "chapter", "contentRaw"])
    rec["newRows"] = new.height
    newLength = int(new["contentRaw"].str.len_chars().sum() or 0)
    rec["maxCell"] = int(new["contentRaw"].str.len_chars().max() or 0)
    rec["newQ4"] = new.filter(pl.col("period").str.ends_with("Q4"))["rceptNo"].n_unique()
    rec["newMdna"] = _mdnaReports(new)
    groups = {r: t for r, t in new.group_by("rceptNo").agg(pl.col("contentRaw")).iter_rows()}
    zips = sorted(docsDir.glob("*.zip"))
    rec["zips"] = len(zips)
    missing = [z.stem for z in zips if z.stem not in groups]
    bad: list[str] = []
    for z in zips:
        if z.stem in groups:
            _compareZip(rec, z, groups[z.stem], bad)
    rec["zipMissing"] = len(missing)
    rec["badReports"] = " ".join(bad + [f"{m}:없음" for m in missing])[:500]
    newSets = _chapterSets(new.select("rceptNo", "chapter"))
    rec["newReports"] = len(groups)
    newAll = set(new["rceptNo"].unique().to_list())
    del groups, new

    oldLocal = Path(task["oldDir"]) / code
    oldPath = _downloadOld(task, oldLocal)
    oldOnly, oldOnlyLength = _compareOld(rec, oldPath, newSets, newAll) if oldPath is not None else ([], 0)

    if missing or bad:
        rec["status"] = "hold:source"
    elif rec["structTextReports"] or rec["lostNamedChapterReports"]:
        rec["status"] = "hold:structure"
    else:
        _writeOut(rec, newPath, oldPath, outPath, oldOnly, newAll, newLength, oldOnlyLength)
    shutil.rmtree(oldLocal, ignore_errors=True)
    return rec


def _writeOut(
    rec: dict[str, Any],
    newPath: Path,
    oldPath: Path | None,
    outPath: Path,
    oldOnly: list[str],
    newAll: set[str],
    newLength: int,
    oldOnlyLength: int,
) -> None:
    """올릴 파일을 만들고 합친 결과가 새 파일·옛 파일과 맞는지 본다. 맞지 않으면 hold:merge 로 지운다."""
    import polars as pl

    outPath.parent.mkdir(parents=True, exist_ok=True)
    try:
        if oldOnly and oldPath is not None:
            _mergeOld(newPath, oldPath, outPath)
        else:
            shutil.copyfile(newPath, outPath)
        out = pl.read_parquet(outPath, columns=["rceptNo", "contentRaw"])
        rec["outRows"] = out.height
        fromOld = out.filter(pl.col("rceptNo").is_in(oldOnly))
        fromNew = out.filter(~pl.col("rceptNo").is_in(oldOnly))
        newGot = int(fromNew["contentRaw"].str.len_chars().sum() or 0)
        oldGot = int(fromOld["contentRaw"].str.len_chars().sum() or 0)
        problems = []
        if set(out["rceptNo"].unique().to_list()) != newAll | set(oldOnly):
            problems.append("합친 보고서 목록이 다름")
        # 새로 만든 보고서는 줄 수와 글자 수가 새 파일과 같고, 옛 파일에서 붙인 보고서는 옛 파일과 같아야 한다.
        if fromNew.height != rec["newRows"] or newGot != newLength:
            problems.append(f"새 보고서 줄 {fromNew.height}/{rec['newRows']}")
        if fromOld.height != rec["oldOnlyRows"] or oldGot != oldOnlyLength:
            problems.append(f"옛 보고서 줄 {fromOld.height}/{rec['oldOnlyRows']}")
        if problems:
            rec["status"] = "hold:merge"
            rec["error"] = (rec["error"] + " " + ", ".join(problems)).strip()[:500]
        else:
            rec["status"] = "ok"
            rec["outSha"] = _fileSha(outPath)
    except Exception as exc:  # noqa: BLE001 (합치기 실패는 장부에 적고 올리지 않는다)
        rec["status"] = "hold:merge"
        rec["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    if rec["status"] != "ok":
        outPath.unlink(missing_ok=True)


def _shaMap(api: Any, repo: str, codes: list[str], revision: str) -> dict[str, str]:
    """그 revision 에서 회사 panel 파일의 sha256. HF 에 없는 회사는 키가 없다."""
    from dartlab.core.hfRetry import retryHfCall

    paths = [f"dart/panel/{c}.parquet" for c in codes]
    out: dict[str, str] = {}
    for i in range(0, len(paths), 200):
        infos = retryHfCall(api.get_paths_info, repo, paths[i : i + 200], repo_type="dataset", revision=revision)
        for info in infos:
            lfs = getattr(info, "lfs", None)
            out[Path(info.path).stem] = lfs.sha256 if lfs else info.blob_id
    return out


def _headSha(api: Any, repo: str) -> str:
    """저장소의 지금 HEAD 커밋."""
    from dartlab.core.hfRetry import retryHfCall

    return retryHfCall(api.repo_info, repo, repo_type="dataset").sha


def _commitChunk(api: Any, repo: str, records: list[dict[str, Any]], uploadDir: Path, label: str) -> None:
    """통과한 회사 파일을 한 커밋으로 올린다.

    LFS 파일은 먼저 한 번 올려 두고(preupload), 커밋만 ``parent_commit`` 으로 건다. 다른 커밋이 끼면
    회사 파일을 다시 견주어, 그사이 바뀐 회사는 hold:raced 로 빼고 나머지를 다시 커밋한다.
    """
    from huggingface_hub import CommitOperationAdd
    from huggingface_hub.utils import HfHubHTTPError

    from dartlab.core.hfRetry import retryHfCall

    ops = {
        r["code"]: CommitOperationAdd(
            path_in_repo=f"dart/panel/{r['code']}.parquet", path_or_fileobj=str(uploadDir / f"{r['code']}.parquet")
        )
        for r in records
        if r["status"] == "ok" and not r["uploaded"]
    }
    if not ops:
        return
    retryHfCall(api.preupload_lfs_files, repo, additions=list(ops.values()), repo_type="dataset")
    for attempt in range(_COMMIT_ATTEMPTS):
        head = _headSha(api, repo)
        pending = [r for r in records if r["status"] == "ok" and not r["uploaded"]]
        current = _shaMap(api, repo, [r["code"] for r in pending], head)
        for r in pending:
            now = current.get(r["code"], "")
            if now == r["outSha"]:
                # 앞 시도가 서버에는 들어갔는데 답만 못 받은 경우다.
                r["uploaded"], r["commit"] = True, head
            elif now != r["oldSha"]:
                r["status"] = "hold:raced"
        send = [r for r in pending if r["status"] == "ok" and not r["uploaded"]]
        if not send:
            return
        try:
            info = retryHfCall(
                api.create_commit,
                repo_id=repo,
                repo_type="dataset",
                operations=[ops[r["code"]] for r in send],
                commit_message=f"sync panel: {len(send)} files (rebuild {label})",
                parent_commit=head,
            )
        except HfHubHTTPError as exc:
            moved = _headSha(api, repo)
            if moved == head:
                raise
            status = getattr(getattr(exc, "response", None), "status_code", None)
            print(f"[panelRebuild] 커밋 겹침 {attempt + 1}회({status}, {head[:8]} -> {moved[:8]})", flush=True)
            time.sleep(random.uniform(3, 15))
            continue
        for r in send:
            r["uploaded"], r["commit"] = True, info.oid
        return
    raise RuntimeError(f"다른 커밋과 {_COMMIT_ATTEMPTS}번 겹쳐 올리지 못함")


def _verifyUploaded(api: Any, repo: str, records: list[dict[str, Any]]) -> list[str]:
    """올린 회사의 HF 현재 파일이 올린 파일과 같은지 보고, 다른 회사는 hold:raced 로 돌린다."""
    sent = [r for r in records if r["uploaded"]]
    if not sent:
        return []
    current = _shaMap(api, repo, [r["code"] for r in sent], _headSha(api, repo))
    changed = [r["code"] for r in sent if current.get(r["code"], "") != r["outSha"]]
    for r in sent:
        if r["code"] in changed:
            r["status"], r["uploaded"] = "hold:raced", False
    return changed


def _writeLedger(records: list[dict[str, Any]], path: Path) -> None:
    """장부를 parquet 로 쓴다(회사마다 한 줄)."""
    import polars as pl

    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(records, infer_schema_length=None).write_parquet(path)


def _summaryLines(records: list[dict[str, Any]], label: str) -> list[str]:
    """GitHub step summary 에 쓸 요약 줄(상태별 수, 경영진단 장 전후, 보류 회사)."""
    counts: dict[str, int] = {}
    for r in records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    ok = [r for r in records if r["status"] == "ok"]
    lines = [
        f"## panel 재빌드 {label}",
        "",
        "상태: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
        f"경영진단 장이 있는 사업보고서: {sum(r['oldMdna'] for r in ok)} -> {sum(r['newMdna'] for r in ok)}",
        f"장 이름이 빠진 보고서 {sum(r['lostNamedChapterReports'] for r in records)}, "
        f"구조 태그가 글자가 된 보고서 {sum(r['structTextReports'] for r in records)}",
    ]
    held = [r for r in records if r["status"] not in ("ok", "left")]
    for r in held[:50]:
        reason = (r["error"] or r["badReports"] or r["tagTextSample"])[:160]
        lines.append(f"- {r['code']} {r['status']} {reason}")
    return lines


@dataclass
class _Run:
    """한 샤드 run 의 묶음들이 함께 쓰는 값과 장부."""

    api: Any
    repo: str
    label: str
    upload: bool
    token: str | None
    refPath: str
    workers: int
    newDir: Path
    oldDir: Path
    uploadDir: Path
    docsBase: Path
    ledgerPath: Path
    spawn: Any
    records: list[dict[str, Any]] = field(default_factory=list)


def _tarSizes(api: Any) -> dict[str, int]:
    """원문 저장소 docs/ 의 회사별 tar 크기(바이트)."""
    from dartlab.core.dataConfig import repoFor
    from dartlab.core.hfRetry import retryHfCall

    tree = retryHfCall(
        lambda: list(api.list_repo_tree(repoFor("dartOriginal"), repo_type="dataset", path_in_repo="docs"))
    )
    return {Path(f.path).stem: int(getattr(f, "size", 0) or 0) for f in tree if f.path.endswith(".tar")}


def _selectTargets(codes: list[str] | None, tarSize: dict[str, int], index: int, shards: int) -> list[str]:
    """인자나 ``PANEL_REBUILD_CODES`` 의 회사(둘 다 비면 원문 저장소의 전 회사) 가운데 이 샤드 몫."""
    wanted = codes if codes is not None else re.split(r"[\s,]+", os.environ.get("PANEL_REBUILD_CODES") or "")
    wanted = [c for c in wanted if c] or sorted(tarSize)
    return sorted(c for c in set(wanted) if _shardOf(c, shards) == index)


def _buildChunk(run: _Run, chunk: list[str]) -> tuple[set[str], dict[str, str], float]:
    """묶음의 원문을 받아 panel 을 만든다. 원문을 받은 회사, 회사별 빌드 오류, 받기에 걸린 초를 돌려준다."""
    from dartlab.pipeline.stages.dartZip import _seedChangedFromHf
    from dartlab.providers.dart.panel.build import buildPanelAll

    t0 = time.monotonic()
    for code in chunk:
        shutil.rmtree(run.docsBase / code, ignore_errors=True)
        (run.newDir / f"{code}.parquet").unlink(missing_ok=True)
    _seeded, safe = _seedChangedFromHf(chunk, token=run.token)
    fetchSeconds = time.monotonic() - t0
    build = sorted(c for c in safe if (run.docsBase / c).exists())
    errors: dict[str, str] = {}
    try:
        buildPanelAll(
            refPath=run.refPath, outBaseDir=str(run.newDir), codes=build, numWorkers=run.workers, verbose=False
        )
    except Exception as exc:  # noqa: BLE001 (한 회사 실패가 묶음을 멈추므로 남은 회사를 하나씩 다시 돈다)
        print(f"[panelRebuild] 묶음 빌드 중단, 하나씩 다시: {type(exc).__name__}: {str(exc)[:200]}", flush=True)
        for code in build:
            if (run.newDir / f"{code}.parquet").exists():
                continue
            try:
                buildPanelAll(
                    refPath=run.refPath, outBaseDir=str(run.newDir), codes=[code], numWorkers=1, verbose=False
                )
            except Exception as one:  # noqa: BLE001 (회사별 실패는 장부에 적는다)
                errors[code] = f"{type(one).__name__}: {str(one)[:300]}"
    return safe, errors, fetchSeconds


def _finalizeChunk(run: _Run, chunk: list[str], safe: set[str], errors: dict[str, str], name: str) -> float:
    """한 묶음의 검사, 업로드, 정리, 장부 쓰기(다음 묶음 빌드와 함께 돈다). 걸린 초를 돌려준다."""
    from concurrent.futures import ProcessPoolExecutor

    t0 = time.monotonic()
    revision = _headSha(run.api, run.repo)
    shaAt = _shaMap(run.api, run.repo, chunk, revision)
    tasks = [
        {
            "code": c,
            "seedOk": c in safe and (run.docsBase / c).exists(),
            "error": errors.get(c, ""),
            "docsDir": str(run.docsBase / c),
            "newPath": str(run.newDir / f"{c}.parquet"),
            "outPath": str(run.uploadDir / f"{c}.parquet"),
            "oldDir": str(run.oldDir),
            "repo": run.repo,
            "revision": revision,
            "oldSha": shaAt.get(c, ""),
        }
        for c in chunk
    ]
    with ProcessPoolExecutor(max_workers=_CHECK_WORKERS, mp_context=run.spawn) as pool:
        chunkRecs = list(pool.map(_checkCompany, tasks))
    if run.upload:
        _commitChunk(run.api, run.repo, chunkRecs, run.uploadDir, run.label)
    for r in chunkRecs:
        (run.uploadDir / f"{r['code']}.parquet").unlink(missing_ok=True)
        (run.newDir / f"{r['code']}.parquet").unlink(missing_ok=True)
        shutil.rmtree(run.docsBase / r["code"], ignore_errors=True)
    run.records.extend(chunkRecs)
    _writeLedger(run.records, run.ledgerPath)
    states: dict[str, int] = {}
    for r in chunkRecs:
        states[r["status"]] = states.get(r["status"], 0) + 1
    spent = time.monotonic() - t0
    print(f"[panelRebuild] 묶음 {name} 상태 {sorted(states.items())} 검사·올리기 {spent:.0f}s", flush=True)
    return spent


def _runChunks(
    run: _Run, chunks: list[list[str]], tarSize: dict[str, int], deadline: float, res: StageResult
) -> list[str]:
    """묶음을 차례로 만들고 앞 묶음의 검사·올리기는 다음 묶음 빌드와 함께 돌린다. 남긴 회사를 돌려준다."""
    from concurrent.futures import ThreadPoolExecutor

    builtBytes = builtSeconds = lastFinal = 0.0
    finalizer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="panel-finalize")
    pending = None
    left: list[str] = []
    try:
        for no, chunk in enumerate(chunks):
            size = sum(tarSize.get(c, 0) for c in chunk)
            # 지금까지 잰 MB당 빌드 시간으로 이 묶음이 마감을 넘길 것 같으면 남은 회사는 다음 run 몫이다.
            if builtBytes and (
                time.monotonic() + size * builtSeconds / builtBytes * 1.15 + max(lastFinal, 300.0) > deadline
            ):
                left = [c for rest in chunks[no:] for c in rest]
                print(f"[panelRebuild] 마감 전에 못 끝낼 것 같아 {len(left)}곳을 남김", flush=True)
                break
            name = f"{no + 1}/{len(chunks)} ({size / 1e6:.0f}MB)"
            t0 = time.monotonic()
            safe, errors, fetchSeconds = _buildChunk(run, chunk)
            buildSeconds = time.monotonic() - t0 - fetchSeconds
            builtBytes += size
            builtSeconds += buildSeconds
            print(f"[panelRebuild] 묶음 {name} 받기 {fetchSeconds:.0f}s 빌드 {buildSeconds:.0f}s", flush=True)
            if pending is not None:
                lastFinal = pending.result()
            pending = finalizer.submit(_finalizeChunk, run, chunk, safe, errors, name)
        if pending is not None:
            pending.result()
    except Exception as exc:  # noqa: BLE001 (묶음 밖 실패는 그때까지의 장부를 남기고 실패로 알린다)
        res.report.err = 1
        res.report.failures.append(f"panelRebuild {run.label}: {type(exc).__name__}: {str(exc)[:300]}")
        if pending is not None and not pending.done():
            try:
                pending.result()
            except Exception as late:  # noqa: BLE001 (앞 묶음의 실패도 같은 run 실패로 적는다)
                res.report.failures.append(
                    f"panelRebuild {run.label} 앞 묶음: {type(late).__name__}: {str(late)[:300]}"
                )
        done = {r["code"] for r in run.records}
        left = [c for rest in chunks for c in rest if c not in done]
    finally:
        finalizer.shutdown(wait=True)
    return left


def _finishRun(run: _Run, res: StageResult, left: list[str]) -> StageResult:
    """남긴 회사를 장부에 더하고, 올린 파일을 다시 확인하고, 요약과 결과를 채운다."""
    records = run.records
    records.extend({**_baseRec(c), "status": "left"} for c in left)
    if run.upload:
        changed = _verifyUploaded(run.api, run.repo, records)
        print(f"[panelRebuild] 확인: 올린 뒤 HF 파일이 바뀐 회사 {len(changed)} {changed[:20]}", flush=True)
    _writeLedger(records, run.ledgerPath)
    lines = _summaryLines(records, run.label)
    print("\n".join(lines), flush=True)
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if summaryPath:
        with open(summaryPath, "a", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
    res.changedFiles = [f"{r['code']}.parquet" for r in records if r["uploaded"]]
    res.uploaded = len(res.changedFiles)
    res.report.ok = sum(1 for r in records if r["status"] == "ok")
    res.report.skip = len(left)
    held = [f"{r['code']}:{r['status']}" for r in records if r["status"] not in ("ok", "left")]
    if held:
        res.report.failures.append(f"보류 {len(held)}곳: {' '.join(held[:30])}")
    return res


def runPanelRebuild(
    *,
    category: str = "panelRebuild",
    mode: PipelineMode = "full",
    codes: list[str] | None = None,
    upload: bool = True,
    token: str | None = None,
) -> StageResult:
    """샤드에 든 회사의 panel 을 원문 tar 로 다시 만들고, 원문과 견주어 통과한 회사만 HF 에 올린다.

    Args:
        category: 미사용("panelRebuild" 고정).
        mode: 미사용(전이력 재빌드 고정).
        codes: 대상 회사코드. None 이면 ``PANEL_REBUILD_CODES``, 그것도 비면 원문 저장소의 전 회사.
        upload: False 면 검사만 하고 올리지 않는다.
        token: HF 토큰(인자 > env > .env).

    Returns:
        StageResult. ``changedFiles`` 는 올린 panel 파일, ``report.ok`` 는 통과 회사 수,
        ``report.skip`` 은 시간이 모자라 남긴 회사 수, ``report.failures`` 는 보류 요약.

    Raises:
        ValueError: ``PANEL_REBUILD_SHARD`` 가 ``i/n`` 꼴이 아니거나 범위 밖일 때.

    Example:
        >>> runPanelRebuild(codes=["005930"], upload=False)  # doctest: +SKIP
        StageResult(category='panelRebuild', ...)
    """
    from multiprocessing import get_context

    from huggingface_hub import HfApi

    import dartlab.config as cfg
    from dartlab.core.dataConfig import repoFor
    from dartlab.pipeline.hfUpload import _resolveHfToken
    from dartlab.pipeline.stages.dartZip import _deadlineAt
    from dartlab.providers.dart.panel.build import panelXbrlRefPath

    index, count = _parseShard(os.environ.get("PANEL_REBUILD_SHARD", "0/1"))
    label = f"{index}/{count}"
    deadline = _deadlineAt("PANEL_REBUILD_DEADLINE_MIN", 290)
    chunkBytes = float(os.environ.get("PANEL_REBUILD_CHUNK_MB") or "150") * 1e6
    res = StageResult(category=category)
    tok = _resolveHfToken(token)
    api = HfApi(token=tok)

    tarSize = _tarSizes(api)
    targets = _selectTargets(codes, tarSize, index, count)
    chunks = _chunks(targets, tarSize, chunkBytes)
    total = sum(tarSize.get(c, 0) for c in targets)
    print(f"[panelRebuild] 샤드 {label}: 회사 {len(targets)} 원문 {total / 1e6:.0f}MB 묶음 {len(chunks)}", flush=True)

    base = Path(cfg.dataDir)
    run = _Run(
        api=api,
        repo=repoFor("panel"),
        label=label,
        upload=upload,
        token=tok,
        refPath=str(panelXbrlRefPath()),
        workers=max(1, min(2, int(os.environ.get("PANEL_WORKERS") or "2"))),
        newDir=base / "dart" / "panel",
        oldDir=base / "panelRebuild" / "old",
        uploadDir=base / "panelRebuild" / "upload",
        docsBase=base / "original" / "dart" / "docs",
        ledgerPath=base / "panelRebuild" / f"ledger-{index}.parquet",
        spawn=get_context("spawn"),  # polars 는 fork 된 자식에서 멈출 수 있다
    )
    for d in (run.newDir, run.oldDir, run.uploadDir):
        d.mkdir(parents=True, exist_ok=True)
    left = _runChunks(run, chunks, tarSize, deadline, res)
    return _finishRun(run, res, left)
