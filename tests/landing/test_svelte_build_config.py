"""Svelte 프로덕션 빌드 전처리와 도구 버전 계약."""

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def testSvelteConfigPreprocessesTypeScriptBeforeViteBuild() -> None:
    config = Path("landing/svelte.config.js").read_text(encoding="utf-8")

    assert "import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';" in config
    assert config.index("vitePreprocess(),") < config.index("mdsvex({")


def testViteSkipsRawSvelteFilesInDynamicImportAnalysis() -> None:
    config = Path("landing/vite.config.ts").read_text(encoding="utf-8")

    assert "dynamicImportVarsOptions" in config
    assert "exclude: [/\\.svelte(?:\\?|$)/]" in config


def testSvelteWorkspacesUseVerifiedViteToolchain() -> None:
    """vite 7 과 vite-plugin-svelte 6 을 정확한 판 하나로 모든 작업 공간에 맞춘다.

    vite override 는 숫자 대신 루트 devDependencies 를 따라간다(`$vite`). 숫자로 고정하면
    Dependabot 이 devDependencies 만 올려 `npm install` 이 EOVERRIDE 로 실패한다.

    vite-plugin-svelte override 는 숫자로 둔다. `$@sveltejs/vite-plugin-svelte` 참조는
    vite-plugin-svelte-inspector 의 peer 해석에서 npm 이 풀지 못해, lock 없이 트리를 새로 짜는
    설치(`npm install --no-save --package-lock=false`, pyproc gate-a·gate-b)가
    "Unable to resolve reference" 로 실패했다(2026-11-27 master 실측, 흉내 시험 재현).
    """
    root_package = json.loads(Path("package.json").read_text(encoding="utf-8"))
    overrides = root_package["overrides"]
    pinned = root_package["devDependencies"]
    assert overrides["vite"] == "$vite"
    assert overrides["@sveltejs/vite-plugin-svelte"] == pinned["@sveltejs/vite-plugin-svelte"]

    assert re.fullmatch(r"7\.\d+\.\d+", pinned["vite"])
    assert re.fullmatch(r"6\.\d+\.\d+", pinned["@sveltejs/vite-plugin-svelte"])

    sources = []
    for package_path in (
        Path("landing/package.json"),
        Path("ui/apps/local/package.json"),
    ):
        sources.append(json.loads(package_path.read_text(encoding="utf-8"))["devDependencies"])

    for dependencies in sources:
        assert dependencies["vite"] == pinned["vite"]
        assert dependencies["@sveltejs/vite-plugin-svelte"] == pinned["@sveltejs/vite-plugin-svelte"]
