"""DART panel-only source guard.

This audit blocks retired KR DART document runtime surfaces from reappearing.
EDGAR/EDINET keep their own source-native document packages; this guard is
deliberately scoped to DART KR runtime and its direct tests.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REMOVED_PATHS = (
    ROOT / ".github" / "workflows" / "sectionsAudit.yml",
    ROOT / "src" / "dartlab" / "providers" / "dart" / "sections.py",
    ROOT / "src" / "dartlab" / "scan" / "sectionsNew",
    ROOT / "tests" / "audit" / "sectionsCompleteness.py",
    ROOT / "tests" / "audit" / "sectionsParity.py",
    ROOT / "tests" / "audit" / "sectionsParityV5All.py",
    ROOT / "tests" / "audit" / "sectionsRawCompare.py",
)

SCAN_ROOTS = (
    ROOT / "src" / "dartlab" / "providers" / "dart",
    ROOT / "src" / "dartlab" / "server",
    ROOT / "src" / "dartlab" / "cli",
    ROOT / "src" / "dartlab" / "scan",
    ROOT / "src" / "dartlab" / "analysis",
    ROOT / "src" / "dartlab" / "credit",
    ROOT / "src" / "dartlab" / "industry",
    ROOT / "src" / "dartlab" / "quant",
    ROOT / "src" / "dartlab" / "core",
    ROOT / "src" / "dartlab" / "gather" / "dart",
    ROOT / "src" / "dartlab" / "pipeline",
    ROOT / "landing" / "src",
    ROOT / "tests" / "audit",
    ROOT / "tests" / "cli",
    ROOT / "tests" / "search",
    ROOT / "tests" / "server",
    ROOT / "tests" / "viz",
    ROOT / "tests" / "providers" / "dart" / "search",
)

ALLOW_DOCS_CATEGORY = {
    ROOT / "src" / "dartlab" / "core" / "dataLoader.py",
    ROOT / "src" / "dartlab" / "providers" / "dart" / "checks.py",
}


def _token(*parts: str) -> str:
    return "".join(parts)


BANNED_FIXED = (
    _token("dartlab.providers.dart", ".sections"),
    "rawDocs",
    _token("c", ".sections"),
    _token("company", ".sections"),
    _token("Company", ".sections"),
    _token("self.c", ".sections"),
    "_hasDocs",
    "loadDocsForStock",
    _token("loadLiveCompany", "Docs"),
    _token("dartlab.providers.dart.build", ".sections"),
    "dart/build/sections.py",
    _token("sections", "=True"),
    _token("sections", ": bool"),
    "collectOneZip",
    "ZIP 다운로드 + 섹션",
    "구조화된 섹션",
    # 전체(bulk) 다운로드만 차단 — 사이트에서 전 회사 데이터를 통째로 긁어가는 표면 방지.
    # 뷰어 개별 다운로드(보던 회사 1곳의 panel CSV·재무 Excel, 이미 로드된 데이터 변환,
    # panel-SSOT 기반)와 HF 데이터셋 링크는 허용(2026-06-08 운영자 결정). 옛 0e986832d 가
    # docs/sections 정리하며 개별 export(dataExport/panelToCsv/financeToExcel/downloadPanel
    # Csv/downloadFinanceExcel)·HF 링크(DATASET_URL/전체 데이터셋)까지 쓸어담은 과잉 차단을 해제.
    _token("download", "All"),
    "includeDocs",
    "docsBatchSize",
    '_dataDir("docs")',
    "_dataDir('docs')",
    'DATA_RELEASES["docs"]["dir"]',
    "DATA_RELEASES['docs']['dir']",
    '_getDataRoot() / "dart" / "docs"',
)

DOCS_CATEGORY_RE = re.compile(
    r"category\s*=\s*['\"]docs['\"]|loadData\([^)\n]*['\"]docs['\"]",
    re.MULTILINE,
)


def _iterFiles() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path == Path(__file__).resolve():
                continue
            if path.suffix not in {".py", ".yml", ".yaml", ".sh", ".ts", ".svelte"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if "/providers/edgar/" in rel or "/providers/edinet/" in rel:
                continue
            if "/skills/" in rel:
                continue
            files.append(path)
    return files


def _containsBannedFixed(text: str, pattern: str) -> bool:
    """고정 금지어를 식별자 경계까지 포함해 정확히 찾는다."""
    if pattern == "downloadAll":
        return re.search(r"\bdownloadAll\b", text) is not None
    return pattern in text


def collectViolations() -> list[str]:
    """Collect DART KR docs/sections residue violations."""

    violations: list[str] = []
    for path in REMOVED_PATHS:
        if path.exists():
            violations.append(f"removed path still exists: {path.relative_to(ROOT).as_posix()}")

    for path in _iterFiles():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for pattern in BANNED_FIXED:
            if _containsBannedFixed(text, pattern):
                violations.append(f"{rel}: banned pattern {pattern!r}")
        if path not in ALLOW_DOCS_CATEGORY and DOCS_CATEGORY_RE.search(text):
            violations.append(f"{rel}: category='docs' load path is retired; use panel")

    return violations


def testDartPanelOnlyGuard() -> None:
    """pytest entrypoint."""

    violations = collectViolations()
    assert not violations, "\n".join(violations)


def main() -> int:
    """CLI entrypoint for Guard runner."""

    violations = collectViolations()
    if violations:
        print("DART panel-only guard violations:")
        for item in violations:
            print(f"- {item}")
        return 1
    print("DART panel-only guard OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
