"""설치 환경과 저장된 Python/npm lockfile의 보안 감사를 모두 실행한다."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def runCommand(args: list[str], repo: Path) -> tuple[int, str]:
    """검사 오류와 시간 초과를 성공으로 바꾸지 않는다."""
    try:
        result = subprocess.run(
            args, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return result.returncode, result.stdout + result.stderr


def runAudits(repo: Path, scratch: Path) -> list[tuple[str, int, str]]:
    """한 검사 실패 뒤에도 나머지 저장소의 감사를 수행한다."""
    results: list[tuple[str, int, str]] = []

    def check(label: str, args: list[str]) -> int:
        code, output = runCommand(args, repo)
        results.append((label, code, output))
        return code

    audit = [sys.executable, "-m", "pip_audit", "--strict", "--desc", "on"]
    check("installed-python", audit)
    requirements = scratch / "requirements.txt"
    exported = check(
        "lock-export",
        [
            "uv",
            "--quiet",
            "export",
            "--locked",
            "--all-groups",
            "--all-extras",
            "--no-emit-project",
            "--no-hashes",
            "--output-file",
            str(requirements),
        ],
    )
    if exported == 0:
        check("locked-python", [*audit, "--no-deps", "--disable-pip", "-r", str(requirements)])
    else:
        results.append(("locked-python", 1, "BLOCKED: uv.lock 내보내기 실패로 검사하지 못했습니다."))
    npm = shutil.which("npm") or "npm"
    check("npm-workspace", [npm, "audit", "--audit-level", "low"])
    check("npm-push-hub", [npm, "audit", "--prefix", "infra/workers/pushHub", "--audit-level", "low"])
    return results


def main() -> int:
    """CI는 audit-report.txt를 보존하고 로컬 임시 파일은 공유 실행 폴더에서 정리한다."""
    executionRoot = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local/share"))) / "dev-workspace"
    executionRoot.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dartlabSecurity-", dir=executionRoot) as output:
        results = runAudits(REPO_ROOT, Path(output))
        report = "\n".join(f"[{label}] exit={code}\n{text.strip()}\n" for label, code, text in results)
        print(report)
        reportDir = (
            REPO_ROOT
            if os.environ.get("GITHUB_ACTIONS") == "true"
            else Path(os.environ.get("DARTLAB_GATE_OUTPUT_DIR", output))
        )
        reportDir.mkdir(parents=True, exist_ok=True)
        (reportDir / "audit-report.txt").write_text(report, encoding="utf-8")
        return int(any(code != 0 for _, code, _ in results))


if __name__ == "__main__":
    raise SystemExit(main())
