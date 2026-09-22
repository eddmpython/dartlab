"""python -m dartlab.pipeline <stage> [--mode M] [--no-upload] [--all] [--list].

로컬 CLI(`dartlab sync`)와 CI 워크플로가 호출하는 동일 SSOT 진입점.
"""

from __future__ import annotations

import argparse
import os
import sys

from dartlab.pipeline.orchestrator import describeStages, runPipeline, runStage
from dartlab.pipeline.types import StageResult


def _writeStepOutput(result: StageResult) -> None:
    """단일 stage 의 ``skipped`` 를 GitHub Actions step output 으로 남긴다.

    워크플로는 ``steps.<id>.outputs.skipped == 'true'`` 로 "할 일 없음" 을 알고 뒤 단계를 건너뛴다
    (예: allFilings 백필이 floor 에 닿은 날의 버킷 빌드). Actions 밖에서는 아무것도 하지 않는다.
    """
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(f"skipped={'true' if result.skipped else 'false'}\n")


def _printSummary(results: dict[str, StageResult]) -> bool:
    """결과 요약 출력 + 실패 여부 반환."""
    failed = False
    for cat, r in results.items():
        rp = r.report
        print(
            f"[pipeline] {cat}: ok={rp.ok} skip={rp.skip} err={rp.err} fail={rp.fail} "
            f"changed={len(r.changedFiles)} skipped={r.skipped}",
            flush=True,
        )
        for f in rp.failures[:5]:
            print(f"    - {f}", flush=True)
        failed = failed or bool(rp.err or rp.fail)
    return failed


def main(argv: list[str] | None = None) -> int:
    """파이프라인 CLI 진입점.

    Args:
        argv: 인자 목록(None=sys.argv).

    Returns:
        종료코드(0 성공, 1 실패).

    Raises:
        없음.

    Example:
        >>> main(["--list"])  # doctest: +SKIP
        0
    """
    p = argparse.ArgumentParser(prog="dartlab.pipeline")
    p.add_argument("stage", nargs="?", help="stage category (생략+--all=recent set)")
    p.add_argument("--mode", default="recent")
    p.add_argument("--no-upload", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--list", action="store_true", dest="listStages")
    args = p.parse_args(argv)

    if args.listStages:
        for d in describeStages():
            print(f"  {d['category']:12} {d['label']}")
        return 0

    upload = not args.no_upload
    if args.all or not args.stage:
        results = runPipeline(mode=args.mode, upload=upload)
    else:
        results = {args.stage: runStage(args.stage, mode=args.mode, upload=upload)}
        _writeStepOutput(results[args.stage])
    return 1 if _printSummary(results) else 0


if __name__ == "__main__":
    sys.exit(main())
