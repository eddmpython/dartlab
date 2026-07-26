"""wheel 검증 스크립트 — 번들 리소스 + 런타임 체인 통합 검사.

ci.yml 의 wheel-smoke 잡과 publish.yml 의 build 잡이 동일한 검증 로직을 쓰도록
한 곳에 모음. 과거 두 워크플로우가 서로 다른 코드로 wheel 을 검증해서 "CI 는
통과했는데 publish wheel 은 깨진" 사고(2026-04-19) 가 발생한 구조적 원인 제거.

사용법::

    python .github/scripts/verifyWheel.py dist/dartlab-0.9.17-py3-none-any.whl
    python .github/scripts/verifyWheel.py dist/dartlab-0.9.17-py3-none-any.whl --skip-install

옵션::

    --skip-install    격리 venv 설치 단계 생략 (네트워크 제약 환경용).

종료 코드::

    0 성공 / 1 번들 리소스 누락 / 2 런타임 검증 실패 / 3 입력 오류
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

# 필수 번들 리소스 — 2026-04-19 사고 class 직접 방어.
# `tests/audit/test_wheelPackaging.py::test_parserMappings_inWheel` 와 동기화.
_REQUIRED_BUNDLE_FILES = [
    # parserMappings
    "dartlab/providers/mappers/mapperData/parserMappings/panelTopics.json",
    "dartlab/providers/mappers/mapperData/parserMappings/affiliate.json",
    "dartlab/providers/mappers/mapperData/parserMappings/costByNature.json",
    "dartlab/providers/mappers/mapperData/parserMappings/sectorPriors.json",
    # reference data
    "dartlab/reference/data/accountMappings.json",
    "dartlab/reference/data/labelSupplements.json",
    "dartlab/providers/mappers/mapperData/notesStructure.json",
    "dartlab/reference/data/dalio48Cases.json",
    "dartlab/reference/data/dalioDetailCases.json",
    "dartlab/reference/data/damodaranDefaults.json",
    "dartlab/reference/data/rrCrises800y.json",
    # DART sections runtime (docs 농장 은퇴 — sectionMappings 는 sectionTopic 옆 provider 루트로 이전)
    "dartlab/providers/dart/sectionMappings.json",
    # EDGAR sections
    "dartlab/providers/edgar/docs/sections/mapperData/sectionMappings.json",
    # EDINET sections
    "dartlab/providers/edinet/docs/sections/mapperData/sectionMappings.json",
]

# 데스크탑 런처가 기동에 요구하는 번들 UI. wheel 에 이게 없으면 런처는
# "UI 빌드 파일(index.html) 없음" 으로 죽는다 (0.10.9 사고). UI 빌드 step 이 선행하는
# publish 경로에서만 --require-ui 로 켠다 (ci-fast wheel-smoke 는 UI 를 굽지 않는다).
_REQUIRED_UI_FILES = [
    "dartlab/ui/build/index.html",
]


def checkBundle(whl: Path, *, requireUi: bool = False) -> int:
    """wheel zip 목록에 필수 리소스가 모두 있는지 확인."""
    with zipfile.ZipFile(whl) as z:
        names = set(z.namelist())
    required = list(_REQUIRED_BUNDLE_FILES)
    if requireUi:
        required += _REQUIRED_UI_FILES
    missing = [f for f in required if f not in names]
    if missing:
        print("FAIL - wheel 에 필수 리소스 누락 (2026-04-19 사고 class):")
        for m in missing:
            print(f"  - {m}")
        if requireUi and any(m in _REQUIRED_UI_FILES for m in missing):
            print(
                "\n  진단: `python -m build` 는 sdist 를 먼저 굽고 *그 sdist 로* wheel 을 만든다.\n"
                "  src/dartlab/ui/build/ 는 .gitignore 대상이라 sdist 타깃에 artifacts 가 없으면\n"
                "  sdist 단계에서 통째로 탈락하고 wheel 에서도 사라진다.\n"
                "  확인: pyproject.toml [tool.hatch.build.targets.sdist] 의 artifacts."
            )
        return 1
    uiCount = len([n for n in names if n.startswith("dartlab/ui/")])
    print(f"OK - 번들 리소스 {len(required)}개 모두 포함, wheel 총 {len(names)} 파일 (UI {uiCount} 파일)")
    return 0


def checkRuntime(whl: Path) -> int:
    """격리 venv 에 wheel 설치 후 panel topic 매핑 로더 호출."""
    with tempfile.TemporaryDirectory(prefix="wheel-verify-") as tmp:
        venvDir = Path(tmp) / "venv"
        venv.create(venvDir, with_pip=True)
        py = venvDir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")

        install = subprocess.run(
            [str(py), "-m", "pip", "install", "--quiet", str(whl)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if install.returncode != 0:
            print("FAIL — 격리 venv 에 wheel 설치 실패:")
            print((install.stderr or install.stdout or "")[-800:])
            return 2

        check = subprocess.run(
            [
                str(py),
                "-X",
                "utf8",
                "-c",
                (
                    "from dartlab.providers.mappers.parserMapper import loadSections;"
                    " s = loadSections();"
                    " assert s.get('chapterByMajor'), 'chapterByMajor empty';"
                    " print('OK chapterByMajor:', len(s['chapterByMajor']))"
                ),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if check.returncode != 0:
            print("FAIL — 설치된 wheel 에서 loadSections 런타임 체인 실패:")
            print("STDOUT:", check.stdout)
            print("STDERR:", check.stderr)
            return 2
        print(check.stdout.strip())

        smoke = subprocess.run(
            [
                str(py),
                "-X",
                "utf8",
                str(Path(__file__).resolve().parents[2] / "tests" / "audit" / "productSmoke.py"),
                "--suite",
                "quick",
                "--data-mode",
                "fixtures",
                "--import-mode",
                "installed",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if smoke.returncode != 0:
            print("FAIL — 설치된 wheel 에서 사용자 API quick smoke 실패:")
            print("STDOUT:", smoke.stdout[-4000:])
            print("STDERR:", smoke.stderr[-4000:])
            return 2
        print(smoke.stdout.strip())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="dartlab wheel 검증")
    parser.add_argument("wheel", type=Path, help="검증할 .whl 파일")
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="격리 venv 설치 단계 생략 (번들 검증만 수행)",
    )
    parser.add_argument(
        "--require-ui",
        action="store_true",
        help="dartlab/ui/build/index.html 번들 필수화 (UI 빌드 step 이 선행하는 publish 경로 전용)",
    )
    args = parser.parse_args()

    whl: Path = args.wheel
    if not whl.exists():
        print(f"FAIL — wheel 파일 없음: {whl}", file=sys.stderr)
        return 3
    if not whl.suffix == ".whl":
        print(f"FAIL — .whl 확장자 아님: {whl}", file=sys.stderr)
        return 3

    print(f"[verify-wheel] {whl}")
    rc = checkBundle(whl, requireUi=args.require_ui)
    if rc != 0:
        return rc

    if args.skip_install:
        print("[verify-wheel] --skip-install 지정 → 런타임 검증 생략")
        return 0

    return checkRuntime(whl)


if __name__ == "__main__":
    sys.exit(main())
