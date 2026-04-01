"""파이프라인 건강 모니터 — 워크플로우 실행 상태 확인 + GitHub Issue 알림.

gh CLI로 각 워크플로우의 최근 실행을 조회하고,
실패 시 pipeline-failure 라벨로 Issue를 생성한다.
전부 성공이면 열린 Issue를 자동으로 닫는다.

환경변수:
  GH_TOKEN: GitHub 토큰 (Actions에서 자동 제공)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

MONITORED_WORKFLOWS = [
    "Data Sync",
    "Daily Data Sync",
    "EDGAR Data Sync",
    "Update KindList",
    "Data Prebuild",
]

FAILURE_LABEL = "pipeline-failure"


def _gh(args: list[str], *, check: bool = True) -> str:
    """gh CLI 실행 후 stdout 반환."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        env={**os.environ},
    )
    if check and result.returncode != 0:
        print(f"[monitor] gh 실행 실패: {' '.join(args)}")
        print(f"  stderr: {result.stderr}")
    return result.stdout.strip()


def _getLatestRun(workflowName: str) -> dict | None:
    """워크플로우의 최근 실행 1건 조회."""
    raw = _gh(
        ["run", "list", "--workflow", workflowName, "--limit", "1", "--json",
         "conclusion,status,createdAt,updatedAt,url,headBranch,displayTitle"],
        check=False,
    )
    if not raw:
        return None
    try:
        runs = json.loads(raw)
        return runs[0] if runs else None
    except (json.JSONDecodeError, IndexError):
        return None


def _ensureLabel() -> None:
    """pipeline-failure 라벨이 없으면 생성."""
    existing = _gh(["label", "list", "--search", FAILURE_LABEL, "--json", "name"], check=False)
    if FAILURE_LABEL not in existing:
        _gh(["label", "create", FAILURE_LABEL, "--color", "d73a4a",
             "--description", "데이터 파이프라인 자동 실패 알림"])


def _findOpenIssue() -> int | None:
    """pipeline-failure 라벨의 열린 Issue 번호."""
    raw = _gh(["issue", "list", "--label", FAILURE_LABEL, "--state", "open",
               "--json", "number", "--limit", "1"], check=False)
    if not raw:
        return None
    try:
        issues = json.loads(raw)
        return issues[0]["number"] if issues else None
    except (json.JSONDecodeError, IndexError):
        return None


def main():
    print(f"[monitor] {len(MONITORED_WORKFLOWS)}개 워크플로우 상태 확인")

    statuses: list[dict] = []
    failures: list[dict] = []

    for name in MONITORED_WORKFLOWS:
        run = _getLatestRun(name)
        if run is None:
            entry = {"name": name, "status": "no_runs", "conclusion": "-", "url": "-", "updated": "-"}
        else:
            conclusion = run.get("conclusion") or run.get("status", "unknown")
            entry = {
                "name": name,
                "status": run.get("status", "unknown"),
                "conclusion": conclusion,
                "url": run.get("url", "-"),
                "updated": run.get("updatedAt", "-"),
            }
            if conclusion not in ("success", "skipped", ""):
                failures.append(entry)

        statuses.append(entry)
        icon = "pass" if entry["conclusion"] == "success" else ("running" if entry["conclusion"] == "" else "FAIL")
        print(f"  [{icon}] {name}: {entry['conclusion']}")

    # GitHub Issue 관리
    _ensureLabel()
    openIssue = _findOpenIssue()

    if failures:
        body = _buildIssueBody(statuses, failures)
        if openIssue:
            _gh(["issue", "comment", str(openIssue), "--body", body])
            print(f"[monitor] 기존 Issue #{openIssue}에 코멘트 추가")
        else:
            failNames = ", ".join(f["name"] for f in failures)
            title = f"Pipeline failure: {failNames}"
            if len(title) > 100:
                title = f"Pipeline failure: {len(failures)}개 워크플로우"
            out = _gh(["issue", "create", "--title", title, "--body", body,
                        "--label", FAILURE_LABEL])
            print(f"[monitor] Issue 생성: {out}")
    elif openIssue:
        _gh(["issue", "close", str(openIssue), "--comment",
             "모든 파이프라인 워크플로우가 정상 통과했습니다. 자동 닫기."])
        print(f"[monitor] Issue #{openIssue} 자동 닫기 (전부 성공)")
    else:
        print("[monitor] 전부 성공, 열린 Issue 없음")

    # GitHub Actions summary
    _writeSummary(statuses, failures)


def _buildIssueBody(statuses: list[dict], failures: list[dict]) -> str:
    """Issue 본문 생성."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## Pipeline Monitor Report ({now})\n",
        "| 워크플로우 | 상태 | 링크 |",
        "|-----------|------|------|",
    ]
    for s in statuses:
        icon = "white_check_mark" if s["conclusion"] == "success" else "x"
        lines.append(f"| {s['name']} | :{icon}: {s['conclusion']} | [보기]({s['url']}) |")

    lines.append("\n### 실패 상세")
    for f in failures:
        lines.append(f"- **{f['name']}**: `{f['conclusion']}` — [로그 보기]({f['url']})")

    lines.append(f"\n> 자동 생성 by Pipeline Monitor ({now})")
    return "\n".join(lines)


def _writeSummary(statuses: list[dict], failures: list[dict]) -> None:
    """GitHub Actions step summary."""
    summaryPath = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summaryPath:
        return

    with open(summaryPath, "a", encoding="utf-8") as f:
        f.write("## Pipeline Health\n\n")
        f.write("| 워크플로우 | 상태 | 마지막 실행 |\n")
        f.write("|-----------|------|------------|\n")
        for s in statuses:
            icon = ":white_check_mark:" if s["conclusion"] == "success" else ":x:"
            f.write(f"| {s['name']} | {icon} {s['conclusion']} | {s['updated']} |\n")

        if failures:
            f.write(f"\n**{len(failures)}개 워크플로우 실패** → Issue 생성/업데이트됨\n")
        else:
            f.write("\n**전체 정상**\n")


if __name__ == "__main__":
    main()
