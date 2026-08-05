"""UI 빌드 경로 해석 — web.py와 cli/commands/ai.py가 공유한다.

UI = ui/apps/local (SvelteKit 챗·터미널 셸). 번들 UI = 공유 surface(@dartlab/ui-surfaces)
소비 SvelteKit 앱이라 랜딩(공표)과 로컬(pip·dev)이 같은 터미널을 쓴다.

옛 React ui/web(financial/quant bento 대시보드)은 import 0·미배선으로 회수됨 (debt-honesty P2-2)
— DARTLAB_UI_LEGACY 가역 escape 도 함께 제거.

resolveUiBuildDir 우선순위:
1. DARTLAB_UI_DIR 환경변수 (dartlab-desktop 등 외부 소비자가 명시)
2. 패키지 내부: site-packages/dartlab/ui/build/ (pip install — wheel 번들)
3. 개발 환경: project_root/ui/apps/local/build/ (SvelteKit adapter-static)
"""

from __future__ import annotations

import os
from pathlib import Path

# dartlab 패키지 루트: site-packages/dartlab/ 또는 src/dartlab/
_PKG_ROOT = Path(__file__).resolve().parent.parent


def _repoRoot() -> Path:
    """editable/dev 체크아웃의 repo 루트 (src/dartlab/server/_ui_path.py → repo)."""
    return _PKG_ROOT.parent.parent


def resolveUiBuildDir() -> Path:
    """UI 빌드 결과물(index.html, _app/) 디렉토리를 반환한다.

    dev 체크아웃에서는 로컬 앱 빌드가 패키지 번들을 이긴다. 실측 장애(2026-08-04):
    `src/dartlab/ui/build/` 는 gitignore 대상 릴리즈 산출물인데 한 번 생기면 그대로
    남아, `npm run build` 로 갱신한 dev 빌드를 조용히 가렸다. 화면은 이틀 전 코드인데
    빌드는 성공해서 UI 수정이 반영되지 않는 원인을 찾기 어려웠다. dev 에서는 소스가
    정본이므로 로컬 빌드를 먼저 본다.
    """
    # 1. 환경변수 (dartlab-desktop 등 외부 소비자가 명시)
    if env := os.environ.get("DARTLAB_UI_DIR"):
        return Path(env)

    # 2. dev 체크아웃: SvelteKit 로컬 앱 빌드. 소스가 곁에 있으면 dev 로 판정한다.
    dev_build = _repoRoot() / "ui" / "apps" / "local" / "build"
    if dev_build.is_dir() and (_repoRoot() / "ui" / "apps" / "local" / "package.json").is_file():
        return dev_build

    # 3. 패키지 내부 (pip install): site-packages/dartlab/ui/build/
    pip_build = _PKG_ROOT / "ui" / "build"
    if pip_build.is_dir():
        return pip_build

    return dev_build


def resolveUiSourceDir() -> Path:
    """UI 소스 디렉토리를 반환한다 (dev 모드 npm 명령용)."""
    if env := os.environ.get("DARTLAB_UI_DIR"):
        return Path(env)
    return _repoRoot() / "ui" / "apps" / "local"
