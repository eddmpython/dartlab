"""엔진이 계산한 공개 Lens Product JSON을 종목별로 발행한다.

실행 예시::

    uv run python -X utf8 landing/_scripts/buildLensProducts.py --code 005930
    uv run python -X utf8 landing/_scripts/buildLensProducts.py --all --shard-index 0 --shard-count 24
    uv run python -X utf8 landing/_scripts/buildLensProducts.py --merge-shards --shard-count 24
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "landing" / "static" / "lenses"
_UNIVERSE_AXES = ("debt", "valuation")


def _allCodes() -> list[str]:
    import dartlab

    codes: set[str] = set()
    for axis in _UNIVERSE_AXES:
        frame = dartlab.scan(axis)
        codeColumn = "stockCode" if frame is not None and "stockCode" in frame.columns else "종목코드"
        if frame is None or frame.is_empty() or codeColumn not in frame.columns:
            raise RuntimeError(f"scan {axis}에서 상장 종목코드를 읽을 수 없습니다.")
        codes.update(str(value).strip() for value in frame.get_column(codeColumn).to_list() if value is not None)
    return sorted(code for code in codes if code)


def shardCodes(codes: list[str], *, shardIndex: int, shardCount: int) -> list[str]:
    """정렬된 전 종목을 재현 가능한 modulo shard로 나눈다."""
    if shardCount < 1:
        raise ValueError("shardCount는 1 이상이어야 합니다.")
    if shardIndex < 0 or shardIndex >= shardCount:
        raise ValueError("shardIndex는 0 이상 shardCount 미만이어야 합니다.")
    stable = sorted(dict.fromkeys(codes))
    return [code for index, code in enumerate(stable) if index % shardCount == shardIndex]


def _codes(args: argparse.Namespace) -> list[str]:
    if args.code:
        codes = list(dict.fromkeys(str(code).strip() for code in args.code if str(code).strip()))
    elif args.all:
        codes = _allCodes()
    else:
        raise SystemExit("--code 또는 --all 중 하나가 필요합니다.")
    return shardCodes(codes, shardIndex=args.shardIndex, shardCount=args.shardCount)


def _writeManifest(output: Path, name: str, manifest: dict[str, Any]) -> Path:
    if Path(name).name != name or not name.endswith(".json"):
        raise ValueError("manifest 이름은 디렉터리 없는 .json 파일명이어야 합니다.")
    output.mkdir(parents=True, exist_ok=True)
    path = output / name
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path


def build(codes: list[str], output: Path, *, minProducts: int) -> tuple[list[dict], list[dict]]:
    import dartlab
    from dartlab.pipeline.lensArtifacts import writeLensArtifact, writeUnavailableLensArtifact

    succeeded: list[dict] = []
    failed: list[dict] = []
    for index, code in enumerate(codes, 1):
        print(f"[{index}/{len(codes)}] {code}", flush=True)
        company = None
        try:
            company = dartlab.Company(code)
            path = writeLensArtifact(company, output, minProducts=minProducts)
            payload = json.loads(path.read_text(encoding="utf-8"))
            count = len(payload.get("products") or {})
            succeeded.append({"target": payload["target"], "productCount": count, "path": path.name})
            print(f"  OK products={count} path={path.name}", flush=True)
        except Exception as exc:  # noqa: BLE001, 한 종목 실패가 전 종목 공개 바닥을 없애면 안 된다.
            error = f"{type(exc).__name__}: {str(exc)[:240]}"
            fallback = writeUnavailableLensArtifact(code, output, market="KR", reason=error)
            failed.append({"target": code, "error": error, "path": fallback.name})
            print(f"  BLOCKED {error}", flush=True)
        finally:
            if company is not None:
                del company
            gc.collect()
    return succeeded, failed


def _manifest(
    codes: list[str],
    succeeded: list[dict],
    failed: list[dict],
    *,
    shardIndex: int,
    shardCount: int,
) -> dict[str, Any]:
    requested = len(codes)
    published = len(succeeded)
    covered = published + len(failed)
    return {
        "schemaVersion": 1,
        "requested": requested,
        "covered": covered,
        "published": published,
        "coverageRate": round(covered / requested, 4) if requested else 1.0,
        "successRate": round(published / requested, 4) if requested else 1.0,
        "shardIndex": shardIndex,
        "shardCount": shardCount,
        "companies": succeeded,
        "failures": failed,
        "noComposite": True,
    }


def mergeManifests(output: Path, *, expectedShards: int) -> dict[str, Any]:
    """shard manifest와 회사 파일을 전 종목 단일 manifest로 검증·병합한다."""
    manifests = sorted(output.glob("_shard-*.json"))
    if len(manifests) != expectedShards:
        raise RuntimeError(f"shard manifest가 {len(manifests)}개이며 기대값 {expectedShards}개와 다릅니다.")

    rows = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    indices = {int(row["shardIndex"]) for row in rows}
    if indices != set(range(expectedShards)) or any(int(row["shardCount"]) != expectedShards for row in rows):
        raise RuntimeError("shard index 또는 shardCount가 완전하지 않습니다.")

    companies = [company for row in rows for company in row.get("companies", [])]
    failures = [failure for row in rows for failure in row.get("failures", [])]
    requested = sum(int(row["requested"]) for row in rows)
    covered = sum(int(row["covered"]) for row in rows)
    published = sum(int(row["published"]) for row in rows)
    targets = [str(row["target"]) for row in companies] + [str(row["target"]) for row in failures]
    if covered != requested or len(targets) != requested or len(set(targets)) != requested:
        raise RuntimeError("전 종목 artifact coverage 또는 target 유일성이 깨졌습니다.")

    companyFiles = [
        path for path in output.glob("*.json") if path.name != "index.json" and not path.name.startswith("_shard-")
    ]
    if len(companyFiles) != requested:
        raise RuntimeError(f"회사 artifact가 {len(companyFiles)}개이며 요청 종목 {requested}개와 다릅니다.")
    for path in companyFiles:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("noComposite") is not True or "results" in payload:
            raise RuntimeError(f"공개 계약을 위반한 artifact: {path.name}")

    merged = {
        "schemaVersion": 1,
        "requested": requested,
        "covered": covered,
        "published": published,
        "coverageRate": round(covered / requested, 4) if requested else 1.0,
        "successRate": round(published / requested, 4) if requested else 1.0,
        "shardCount": expectedShards,
        "companies": companies,
        "failures": failures,
        "noComposite": True,
    }
    _writeManifest(output, "index.json", merged)
    for path in manifests:
        path.unlink()
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument("--code", action="append", help="대상 종목코드 또는 ticker, 반복 가능")
    parser.add_argument("--all", action="store_true", help="scan SSOT의 전 상장 종목")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-products", type=int, default=3, dest="minProducts")
    parser.add_argument("--min-success-rate", type=float, default=0.7, dest="minSuccessRate")
    parser.add_argument("--shard-index", type=int, default=0, dest="shardIndex")
    parser.add_argument("--shard-count", type=int, default=1, dest="shardCount")
    parser.add_argument("--manifest-name", default="index.json", dest="manifestName")
    parser.add_argument("--merge-shards", action="store_true", dest="mergeShards")
    args = parser.parse_args()

    if args.mergeShards:
        merged = mergeManifests(args.output, expectedShards=args.shardCount)
        print(
            f"covered={merged['covered']}/{merged['requested']} published={merged['published']} "
            f"success={merged['successRate']:.1%}",
            flush=True,
        )
        return 0 if merged["coverageRate"] == 1.0 and merged["successRate"] >= args.minSuccessRate else 1

    codes = _codes(args)
    succeeded, failed = build(codes, args.output, minProducts=args.minProducts)
    manifest = _manifest(
        codes,
        succeeded,
        failed,
        shardIndex=args.shardIndex,
        shardCount=args.shardCount,
    )
    _writeManifest(args.output, args.manifestName, manifest)
    print(
        f"covered={manifest['covered']}/{manifest['requested']} published={manifest['published']} "
        f"success={manifest['successRate']:.1%}",
        flush=True,
    )
    return 0 if manifest["coverageRate"] == 1.0 and manifest["successRate"] >= args.minSuccessRate else 1


if __name__ == "__main__":
    sys.exit(main())
