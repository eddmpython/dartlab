"""Svelte 프로덕션 빌드 전처리와 도구 버전 계약."""

import json
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
    for package_path in (
        Path("landing/package.json"),
        Path("ui/apps/local/package.json"),
    ):
        package = json.loads(package_path.read_text(encoding="utf-8"))
        dependencies = package["devDependencies"]

        assert dependencies["vite"] == "7.3.6"
        assert dependencies["@sveltejs/vite-plugin-svelte"] == "6.2.4"

    root_package = json.loads(Path("package.json").read_text(encoding="utf-8"))
    assert root_package["overrides"]["vite"] == "7.3.6"
    assert root_package["overrides"]["@sveltejs/vite-plugin-svelte"] == "6.2.4"
    assert root_package["devDependencies"]["vite"] == "7.3.6"
    assert root_package["devDependencies"]["@sveltejs/vite-plugin-svelte"] == "6.2.4"
