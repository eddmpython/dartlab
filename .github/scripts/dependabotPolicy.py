"""Dependabot Python 자동 병합의 허용 범위와 CI 완료 상태를 판정한다."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

SAFE_UPDATE_TYPES = {
    "version-update:semver-patch",
    "version-update:semver-minor",
}
REQUIRED_WORKFLOWS = {"CI Fast", "CodeQL", "Policy Check"}


def evaluatePolicy(
    *,
    actor: str,
    author: str,
    ecosystem: str,
    updateType: str,
    baseRef: str,
    draft: bool,
    title: str,
    maintainerChanges: bool,
) -> dict[str, Any]:
    """신뢰된 Dependabot Python patch/minor PR만 허용한다."""
    checks = (
        (actor == "dependabot[bot]", "actorNotDependabot"),
        (author == "dependabot[bot]", "authorNotDependabot"),
        (ecosystem == "pip", "ecosystemNotPip"),
        (updateType in SAFE_UPDATE_TYPES, "unsafeUpdateType"),
        (baseRef == "master", "baseNotMaster"),
        (not draft, "draftPullRequest"),
        (not title.startswith("[CORELOOP-"), "coreloopRequiresReview"),
        (not maintainerChanges, "maintainerChangesPresent"),
    )
    for passed, reason in checks:
        if not passed:
            return {"allowed": False, "reason": reason}
    return {"allowed": True, "reason": "safePythonPatchOrMinor"}


def evaluateChecks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    """필수 workflow가 모두 보이고 전체 check가 green인지 판정한다."""
    seen = {str(item.get("workflow", "")) for item in checks}
    missing = sorted(REQUIRED_WORKFLOWS - seen)
    if missing:
        return {"allowed": False, "reason": "missingRequiredWorkflows", "missing": missing}
    blocked = [
        {
            "name": str(item.get("name", "")),
            "workflow": str(item.get("workflow", "")),
            "bucket": str(item.get("bucket", "")),
        }
        for item in checks
        if item.get("bucket") not in {"pass", "skipping"}
    ]
    if blocked:
        return {"allowed": False, "reason": "checksNotGreen", "blocked": blocked}
    return {"allowed": True, "reason": "allChecksGreen"}


def _bool(value: str) -> bool:
    return value.strip().lower() == "true"


def _writeOutput(result: dict[str, Any]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with Path(output).open("a", encoding="utf-8") as handle:
        handle.write(f"allowed={str(bool(result['allowed'])).lower()}\n")
        handle.write(f"reason={result['reason']}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    classify = sub.add_parser("classify")
    classify.add_argument("--actor", required=True)
    classify.add_argument("--author", required=True)
    classify.add_argument("--ecosystem", required=True)
    classify.add_argument("--update-type", required=True)
    classify.add_argument("--base-ref", required=True)
    classify.add_argument("--draft", required=True)
    classify.add_argument("--title", required=True)
    classify.add_argument("--maintainer-changes", required=True)
    check = sub.add_parser("checks")
    check.add_argument("--checks-file", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "classify":
        result = evaluatePolicy(
            actor=args.actor,
            author=args.author,
            ecosystem=args.ecosystem,
            updateType=args.update_type,
            baseRef=args.base_ref,
            draft=_bool(args.draft),
            title=args.title,
            maintainerChanges=_bool(args.maintainer_changes),
        )
    else:
        result = evaluateChecks(json.loads(args.checks_file.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    _writeOutput(result)
    return 0 if result["allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
