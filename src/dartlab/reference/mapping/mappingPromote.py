"""prod JSON patch CLI — `accountMappings.json` SSOT layer 단독 권한 갱신.

`--layer` 로 편집 대상 선택 (default `mappings`) — DART/EDGAR 단일 write 진입점:
    mappings · layers.idSynonym · layers.nameSynonym · layers.snakeAlias ·
    layers.labelEn · layers.korSynonym · edgar.learnedTags
value 가 DART snakeId 인 layer (mappings/snakeAlias/korSynonym) 만 standardAccounts
hard check (ghost 차단) 적용. edgarLearnedTags 는 EDGAR canonical snakeId 라 미적용.

`src/dartlab/reference/mapping/mappingReview.py` 가 status=confirmed 로 결정한 staging 행만
취합하여 atomic write 로 추가. 본 CLI 는 `accountMappings.json` 을 직접
변경하는 유일한 진입점.

서브커맨드:
    dryrun    confirmed 행 → 추가 예정 diff 미리보기 (파일 미수정)
    apply     atomic write + _metadata 갱신 + AccountMapper.release() + lru_cache 무효화
    set       expected 값 확인 후 기존 항목 교정
    delete    expected 값 확인 후 기존 항목 제거
    rollback  --to=<gitsha>  이전 commit 의 accountMappings.json 복원

규약:
    - apply는 추가만 허용한다. 기존 계약 교정은 expected가 필수인 set/delete만 허용한다.
    - 기존 한글명 충돌 시 자세히 stdout 노출, 미적용.
    - `_metadata.lastUpdate` / `_metadata.addedCount` / `_metadata.promoteCommit` 갱신.
    - apply 후 동일 프로세스의 AccountMapper 싱글턴 캐시 무효화.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import polars as pl

_DEFAULT_STAGING = Path("data") / "mapping_candidates.parquet"
_DEFAULT_JSON = Path("src/dartlab/reference/data/accountMappings.json")

# 편집 가능한 SSOT layer — (JSON dotted 경로, value 가 DART snakeId 인가 = ghost check 대상)
# edgarLearnedTags 는 value 가 EDGAR canonical snakeId (일부는 net_income_cf 등 DART
# standardAccounts 부재) 라 SA hard check 미적용 — 과다 reject 회피.
_LAYER_TARGETS: dict[str, tuple[str, bool]] = {
    "mappings": ("mappings", True),
    "idSynonym": ("layers.idSynonym", False),
    "nameSynonym": ("layers.nameSynonym", False),
    "snakeAlias": ("layers.snakeAlias", True),
    "labelEn": ("layers.labelEn", False),
    "korSynonym": ("layers.korSynonym", True),
    "edgarLearnedTags": ("edgar.learnedTags", False),
}


def _targetNode(data: dict, layer: str) -> tuple[dict, str]:
    """layer 의 부모 node + 마지막 키 (중간 node 없으면 생성).

    Args:
        data: accountMappings.json 파싱 dict.
        layer: ``_LAYER_TARGETS`` 키.

    Returns:
        ``(node, key)`` — ``node[key]`` 가 편집 대상 dict.

    Example:
        >>> _targetNode({"layers": {"idSynonym": {}}}, "idSynonym")[1]
        'idSynonym'
    """
    path, _ = _LAYER_TARGETS[layer]
    parts = path.split(".")
    node = data
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    return node, parts[-1]


def _ghostCheckAccounts(data: dict, layer: str) -> dict[str, dict] | None:
    """value 가 snakeId 인 layer 만 standardAccounts hard check 적용 (그 외 None).

    Args:
        data: accountMappings.json 파싱 dict.
        layer: ``_LAYER_TARGETS`` 키.

    Returns:
        standardAccounts dict (snakeId-value layer) 또는 None (id/name/label layer).

    Example:
        >>> _ghostCheckAccounts({"standardAccounts": {}}, "idSynonym") is None
        True
    """
    _, valueIsSnakeId = _LAYER_TARGETS[layer]
    return data.get("standardAccounts", {}) if valueIsSnakeId else None


def _loadJson(path: Path) -> dict:
    """Args:
        path: JSON 경로.

    Returns:
        파싱된 dict.

    Example:
        >>> _loadJson(_DEFAULT_JSON)  # doctest: +SKIP

    Raises:
        FileNotFoundError: 경로 부재.
    """
    if not path.exists():
        raise FileNotFoundError(f"accountMappings.json 부재: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _readConfirmed(stagingPath: Path) -> dict[str, str]:
    """staging parquet 에서 status=confirmed 의 (accountNm, suggestedSnakeId) 추출.

    Args:
        stagingPath: staging parquet 경로.

    Returns:
        ``{accountNm: snakeId}`` dict.

    Example:
        >>> _readConfirmed(Path("data/x.parquet"))  # doctest: +SKIP

    Raises:
        FileNotFoundError: 경로 부재.
    """
    if not stagingPath.exists():
        raise FileNotFoundError(f"staging parquet 부재: {stagingPath}")
    df = pl.read_parquet(stagingPath)
    df = df.filter(pl.col("status") == "confirmed")
    df = df.filter(pl.col("suggestedSnakeId").is_not_null())
    out: dict[str, str] = {}
    for row in df.iter_rows(named=True):
        nm = row["accountNm"]
        snake = row["suggestedSnakeId"]
        if nm and snake:
            out[nm] = snake
    return out


def _computeDiff(
    existing: dict[str, str],
    confirmed: dict[str, str],
    standardAccounts: dict[str, dict] | None = None,
) -> tuple[dict[str, str], dict[str, tuple[str, str]], dict[str, str]]:
    """추가 후보·충돌·standardAccounts 부재 분리.

    Args:
        existing: 현 ``accountMappings.json::mappings``.
        confirmed: staging confirmed dict.
        standardAccounts: standardAccounts 메타. None 이면 hard check 생략.

    Returns:
        (additions, conflicts, ghostSnakes) — ghostSnakes 는 ``confirmed`` 의
        snakeId 가 ``standardAccounts`` 에 부재한 환각 매핑.

    Example:
        >>> additions, conflicts, ghosts = _computeDiff({}, {"a": "x"}, {})
        >>> ghosts
        {'a': 'x'}

    Raises:
        없음.
    """
    additions: dict[str, str] = {}
    conflicts: dict[str, tuple[str, str]] = {}
    ghostSnakes: dict[str, str] = {}
    for nm, snake in confirmed.items():
        if standardAccounts is not None and snake not in standardAccounts:
            ghostSnakes[nm] = snake
            continue
        if nm in existing:
            if existing[nm] != snake:
                conflicts[nm] = (existing[nm], snake)
            continue
        additions[nm] = snake
    return additions, conflicts, ghostSnakes


def _writeJsonAtomic(path: Path, data: dict, *, compact: bool = True) -> None:
    """atomic write — tempfile + replace.

    원본이 single-line 컴팩트 JSON (DART accountMappings.json) 인 경우
    diff 폭증 회피 위해 동일 형식 유지. ``compact=False`` 시 indent=2.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if compact:
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)


def _resetMapperCache() -> None:
    """account SSOT 전 캐시 무효화 — owner ``release()`` 직결.

    loadAccounts/loadSupplements lru + normalize/edgar/labels/aliases 파생캐시 +
    in-place 모듈 dict(ID_SYNONYMS/SNAKEID_ALIASES 등) 전부 1 함수로 리셋.
    """
    try:
        from dartlab.core.accounts import release

        release()
    except ImportError:  # pragma: no cover - import 실패 시 동일 프로세스 캐시 미해제
        pass


def _touchMetadata(data: dict) -> None:
    """SSOT 수정 시 공통 provenance metadata를 갱신한다."""

    meta = data.setdefault("_metadata", {})
    meta["lastUpdate"] = date.today().isoformat()
    meta["promoteCommit"] = _gitHead() or meta.get("promoteCommit", "")


def _checkedExistingValue(existing: dict[str, str], key: str, expected: str) -> bool:
    """동시 수정과 잘못된 repair 대상을 막는 compare-and-set 검사."""

    current = existing.get(key)
    if current != expected:
        print(f"[mappingPromote] {key!r} 현재값 불일치: expected={expected!r}, actual={current!r}")
        return False
    return True


def cmdSet(args: argparse.Namespace) -> int:
    """기존 layer 값을 expected 비교 뒤 명시적으로 교정한다."""

    data = _loadJson(args.json)
    node, key = _targetNode(data, args.layer)
    existing = node.get(key, {})
    if not _checkedExistingValue(existing, args.key, args.expected):
        return 1
    standardAccounts = _ghostCheckAccounts(data, args.layer)
    if standardAccounts is not None and args.value not in standardAccounts:
        print(f"[mappingPromote set] standardAccounts 부재 snakeId: {args.value!r}")
        return 1
    existing[args.key] = args.value
    _touchMetadata(data)
    _writeJsonAtomic(args.json, data)
    _resetMapperCache()
    print(f"[mappingPromote set] layer={args.layer} {args.key!r}: {args.expected!r} -> {args.value!r}")
    return 0


def cmdDelete(args: argparse.Namespace) -> int:
    """기존 layer 값을 expected 비교 뒤 명시적으로 제거한다."""

    data = _loadJson(args.json)
    node, key = _targetNode(data, args.layer)
    existing = node.get(key, {})
    if not _checkedExistingValue(existing, args.key, args.expected):
        return 1
    del existing[args.key]
    _touchMetadata(data)
    _writeJsonAtomic(args.json, data)
    _resetMapperCache()
    print(f"[mappingPromote delete] layer={args.layer} {args.key!r} 제거")
    return 0


def cmdDryrun(args: argparse.Namespace) -> int:
    """dryrun 서브커맨드 — diff 만 출력, 파일 미수정.

    Args:
        args: argparse Namespace (staging, json).

    Returns:
        exit code 0 (충돌 있어도 0 — dryrun 은 보고만).

    Example:
        >>> cmdDryrun(args)  # doctest: +SKIP
        0

    Raises:
        FileNotFoundError: staging / json 경로 부재.
    """
    confirmed = _readConfirmed(args.staging)
    data = _loadJson(args.json)
    node, key = _targetNode(data, args.layer)
    existing = node.get(key, {})
    standardAccounts = _ghostCheckAccounts(data, args.layer)
    additions, conflicts, ghostSnakes = _computeDiff(existing, confirmed, standardAccounts)

    print(f"[mappingPromote dryrun] layer={args.layer} 추가 예정 {len(additions)} 매핑:")
    for nm, snake in sorted(additions.items()):
        print(f"  + {nm!r} → {snake}")
    if conflicts:
        print(f"\n  ⚠ 충돌 {len(conflicts)} 매핑 (apply 시 reject):")
        for nm, (old, new) in sorted(conflicts.items()):
            print(f"    ! {nm!r}: 기존={old} vs 신규={new}")
    if ghostSnakes:
        print(f"\n  ⚠ standardAccounts 부재 snakeId {len(ghostSnakes)} 매핑 (apply 시 reject):")
        for nm, snake in sorted(ghostSnakes.items()):
            print(f"    ? {nm!r} → {snake} (snakeId 환각)")
    return 0


def cmdApply(args: argparse.Namespace) -> int:
    """apply 서브커맨드 — accountMappings.json patch.

    Args:
        args: argparse Namespace (staging, json, force).

    Returns:
        exit code 0 (성공) / 1 (충돌 발견, force 아님).

    Example:
        >>> cmdApply(args)  # doctest: +SKIP
        0

    Raises:
        FileNotFoundError: staging / json 경로 부재.
    """
    confirmed = _readConfirmed(args.staging)
    data = _loadJson(args.json)
    node, key = _targetNode(data, args.layer)
    existing = node.get(key, {})
    standardAccounts = _ghostCheckAccounts(data, args.layer)
    additions, conflicts, ghostSnakes = _computeDiff(existing, confirmed, standardAccounts)

    if ghostSnakes and not args.force:
        print(f"[mappingPromote apply] standardAccounts 부재 snakeId {len(ghostSnakes)} 매핑 — 적용 중단.")
        for nm, snake in sorted(ghostSnakes.items()):
            print(f"  ? {nm!r} → {snake} (snakeId 환각)")
        print("  → 운영자가 정확한 snakeId 로 mappingReview confirm 재실행.")
        return 1
    if conflicts and not args.force:
        print(f"[mappingPromote apply] 충돌 {len(conflicts)} 매핑 — 적용 중단.")
        for nm, (old, new) in sorted(conflicts.items()):
            print(f"  ! {nm!r}: 기존={old} vs 신규={new}")
        print("  → 운영자가 mappingReview.py 로 alias/reject 결정 후 재시도.")
        return 1
    if not additions:
        print("[mappingPromote apply] 추가할 매핑 없음 (이미 동기화 상태).")
        return 0

    # patch
    merged = dict(existing)
    merged.update(additions)
    node[key] = merged
    meta = data.setdefault("_metadata", {})
    _touchMetadata(data)
    meta["addedCount"] = int(meta.get("addedCount", 0)) + len(additions)

    _writeJsonAtomic(args.json, data)
    _resetMapperCache()

    print(f"[mappingPromote apply] layer={args.layer} {len(additions)} 매핑 추가, _metadata 갱신.")
    print(f"  lastUpdate: {meta['lastUpdate']}")
    print(f"  addedCount(누적): {meta['addedCount']}")
    return 0


def cmdRollback(args: argparse.Namespace) -> int:
    """rollback 서브커맨드 — 이전 git commit 의 accountMappings.json 복원.

    Args:
        args: argparse Namespace (to, json).

    Returns:
        exit code 0.

    Example:
        >>> cmdRollback(args)  # doctest: +SKIP
        0

    Raises:
        subprocess.CalledProcessError: git show 실패.
    """
    result = subprocess.run(
        ["git", "show", f"{args.to}:{args.json.as_posix()}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    args.json.write_text(result.stdout, encoding="utf-8")
    _resetMapperCache()
    print(f"[mappingPromote rollback] {args.json} ← {args.to}")
    return 0


def _gitHead() -> str | None:
    """현재 HEAD sha (rollback 추적용). git 없으면 None."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _buildParser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    p.add_argument("--staging", type=Path, default=_DEFAULT_STAGING)
    p.add_argument("--json", type=Path, default=_DEFAULT_JSON)
    p.add_argument(
        "--layer",
        choices=list(_LAYER_TARGETS),
        default="mappings",
        help="편집 대상 SSOT layer (default mappings). "
        "idSynonym/nameSynonym/snakeAlias/labelEn/korSynonym/edgarLearnedTags.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pd_ = sub.add_parser("dryrun")
    pd_.set_defaults(func=cmdDryrun)

    pa = sub.add_parser("apply")
    pa.add_argument(
        "--force",
        action="store_true",
        help="충돌이 있어도 새 매핑 추가 (overwrite 는 여전히 금지).",
    )
    pa.set_defaults(func=cmdApply)

    pr = sub.add_parser("rollback")
    pr.add_argument("--to", required=True)
    pr.set_defaults(func=cmdRollback)

    ps = sub.add_parser("set")
    ps.add_argument("--key", required=True)
    ps.add_argument("--expected", required=True)
    ps.add_argument("--value", required=True)
    ps.set_defaults(func=cmdSet)

    pdel = sub.add_parser("delete")
    pdel.add_argument("--key", required=True)
    pdel.add_argument("--expected", required=True)
    pdel.set_defaults(func=cmdDelete)

    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: argparse 인자 리스트. None 이면 ``sys.argv[1:]``.

    Returns:
        프로세스 exit code.

    Example:
        >>> main(["dryrun"])  # doctest: +SKIP
        0

    Raises:
        SystemExit: argparse 실패 시.
    """
    args = _buildParser().parse_args(list(sys.argv[1:] if argv is None else argv))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
