"""커밋, push, 배포에서 같은 패치 버전 전이 계약을 검사한다.

운영 계약: operation.contributionWorkflow의 릴리즈 규칙.
승인 없이 major/minor를 변경할 수 있는 CLI 옵션이나 환경변수는 없다.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
import urllib.request

VERSION_PATTERN = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
PYPI_URL = "https://pypi.org/pypi/dartlab/json"


def parseVersion(value: str) -> tuple[int, int, int]:
    """정식 세 자리 버전만 허용한다."""
    match = VERSION_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"정식 X.Y.Z 버전이 필요합니다: {value!r}")
    return tuple(int(part) for part in match.groups())


def checkTransition(published: str, candidate: str, *, publishing: bool = False) -> None:
    """발행된 버전 유지 또는 다음 patch 한 단계만 허용한다."""
    previous = parseVersion(published)
    current = parseVersion(candidate)
    if current[:2] != previous[:2]:
        raise ValueError(
            f"major/minor 변경 차단: {published} -> {candidate}. "
            "운영자의 정확한 목표 버전 지시가 필요합니다. 일반 릴리즈 지시는 권한이 아닙니다."
        )
    expected = (*previous[:2], previous[2] + 1)
    if current == previous and not publishing:
        return
    if current != expected:
        nextVersion = ".".join(map(str, expected))
        raise ValueError(
            f"patch는 발행 완료 버전에서 한 단계만 올립니다: {published} -> {nextVersion}, 요청={candidate}"
        )


def gitText(*args: str) -> str:
    """Git 실패를 빈 값으로 바꾸지 않는다."""
    result = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git {args[0]} 실패")
    return result.stdout


def publishedVersion() -> str:
    """PyPI에서 실제 발행된 정식 최신 버전을 확인하며 조회 실패 시 차단한다."""
    request = urllib.request.Request(PYPI_URL, headers={"User-Agent": "dartlab-release-policy"})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    version = payload["info"]["version"]
    parseVersion(version)
    return version


def versionAt(ref: str) -> str:
    """작업 트리 대신 검사할 Git 객체 또는 index의 패키지와 lock 버전을 읽는다."""
    prefix = f"{ref}:" if ref else ":"
    project = tomllib.loads(gitText("show", f"{prefix}pyproject.toml"))
    lock = tomllib.loads(gitText("show", f"{prefix}uv.lock"))
    version = project["project"]["version"]
    locked = [package["version"] for package in lock["package"] if package["name"] == "dartlab"]
    if locked != [version]:
        raise ValueError(f"pyproject/uv.lock 버전 불일치: {version}, {locked}")
    parseVersion(version)
    return version


def checkPush(published: str, lines: list[str]) -> None:
    """pre-push stdin의 실제 ref와 SHA를 검사한다. HEAD로 대체하지 않는다."""
    for line in lines:
        localRef, localSha, remoteRef, remoteSha = line.split()
        if set(localSha) == {"0"}:
            if remoteRef.startswith("refs/tags/v"):
                raise ValueError(f"공개 릴리즈 태그 삭제 차단: {remoteRef}")
            continue
        version = versionAt(localSha)
        isRelease = remoteRef.startswith("refs/tags/v")
        if isRelease:
            tagVersion = remoteRef.removeprefix("refs/tags/v")
            if tagVersion != version:
                raise ValueError(f"태그/패키지 버전 불일치: {tagVersion}, {version}")
            if set(remoteSha) != {"0"} and remoteSha != localSha:
                raise ValueError(f"공개 릴리즈 태그 이동 차단: {remoteRef}")
        checkTransition(published, version, publishing=isRelease)
        if not isRelease and set(remoteSha) != {"0"}:
            commits = gitText("rev-list", f"{remoteSha}..{localSha}", "--", "pyproject.toml").splitlines()
            for commit in commits:
                checkTransition(published, versionAt(commit))
        print(f"[release-policy] {localRef} -> {remoteRef}: {version} OK")


def main() -> int:
    """같은 검사를 staged, push, CI 배포 진입점에 제공한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--pre-push", action="store_true")
    mode.add_argument("--ref")
    mode.add_argument("--tag")
    args = parser.parse_args()
    try:
        published = publishedVersion()
        if args.pre_push:
            checkPush(published, [line.strip() for line in sys.stdin if line.strip()])
        else:
            ref = "" if args.staged else (args.ref or f"refs/tags/{args.tag}")
            version = versionAt(ref)
            if args.tag and args.tag != f"v{version}":
                raise ValueError(f"태그/패키지 버전 불일치: {args.tag}, {version}")
            checkTransition(published, version, publishing=bool(args.tag))
            print(f"[release-policy] PyPI={published}, candidate={version} OK")
    except (ValueError, KeyError, OSError) as exc:
        print(f"[release-policy] BLOCKED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
