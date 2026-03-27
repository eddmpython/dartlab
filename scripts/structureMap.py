"""dartlab 전체 구조 맵 자동 생성.

사용법:
    python scripts/structureMap.py              # 콘솔 출력
    python scripts/structureMap.py --save       # STRUCTURE_MAP.md 저장

출력:
    1. 레이어별 모듈 트리 (파일 수, 함수/클래스 수)
    2. 모듈 간 import 의존성 요약
    3. 공개 API 목록 (registry 기반)
    4. 복잡도 핫스팟 (radon E/F)
    5. 의존성 건강 요약
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src" / "dartlab"

# ── 레이어 분류 ─────────────────────────────────────────────────

_LAYERS = {
    "L0 core": ["core"],
    "L1 providers": ["providers"],
    "L1 gather": ["gather"],
    "L1 market": ["market"],
    "L2 analysis": ["analysis"],
    "L3 ai": ["ai"],
    "Server": ["server"],
    "CLI": ["cli"],
    "Export": ["export"],
    "MCP": ["mcp"],
    "Display": ["display"],
    "Tools": ["tools"],
    "Channel": ["channel"],
    "Review": ["review"],
}


def _classifyModule(relPath: str) -> str:
    """상대 경로 → 레이어 분류."""
    parts = relPath.replace("\\", "/").split("/")
    if len(parts) >= 1:
        for layer, prefixes in _LAYERS.items():
            if parts[0] in prefixes:
                return layer
    return "Root"


# ── AST 스캔 ────────────────────────────────────────────────────

def _scanFile(filepath: Path) -> dict:
    """파일 하나를 AST 파싱하여 함수/클래스/import 정보 추출."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return {"functions": 0, "classes": 0, "imports": [], "lines": 0}

    functions = 0
    classes = 0
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return {
        "functions": functions,
        "classes": classes,
        "imports": [i for i in imports if i != "dartlab"],
        "lines": len(source.splitlines()),
    }


# ── 전체 스캔 ───────────────────────────────────────────────────

def _scanAll() -> dict:
    """전체 소스 스캔."""
    pyFiles = sorted(_SRC.rglob("*.py"))
    layers = defaultdict(lambda: {"files": 0, "functions": 0, "classes": 0, "lines": 0, "modules": []})
    allImports = defaultdict(set)  # module -> set of external imports
    totalFiles = 0
    totalFunctions = 0
    totalClasses = 0
    totalLines = 0

    for f in pyFiles:
        relPath = str(f.relative_to(_SRC))
        if "_reference" in relPath or "__pycache__" in relPath:
            continue

        layer = _classifyModule(relPath)
        info = _scanFile(f)

        layers[layer]["files"] += 1
        layers[layer]["functions"] += info["functions"]
        layers[layer]["classes"] += info["classes"]
        layers[layer]["lines"] += info["lines"]

        totalFiles += 1
        totalFunctions += info["functions"]
        totalClasses += info["classes"]
        totalLines += info["lines"]

        for imp in info["imports"]:
            allImports[layer].add(imp)

    return {
        "layers": dict(layers),
        "imports": {k: sorted(v) for k, v in allImports.items()},
        "totals": {
            "files": totalFiles,
            "functions": totalFunctions,
            "classes": totalClasses,
            "lines": totalLines,
        },
    }


# ── radon 핫스팟 ────────────────────────────────────────────────

def _getHotspots() -> list[dict]:
    """radon E/F 등급 함수 목록."""
    result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", str(_SRC), "-j", "-nc"],
        capture_output=True, text=True, cwd=str(_ROOT),
    )
    if not result.stdout.strip():
        return []

    hotspots = []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    srcPrefix = str(_SRC).replace("\\", "/") + "/"
    for filepath, blocks in data.items():
        shortPath = filepath.replace("\\", "/").replace(srcPrefix, "")
        for block in blocks:
            if block.get("rank", "A") in ("E", "F"):
                hotspots.append({
                    "file": shortPath,
                    "name": block["name"],
                    "line": block.get("lineno", 0),
                    "complexity": block.get("complexity", 0),
                    "rank": block["rank"],
                })

    hotspots.sort(key=lambda x: -x["complexity"])
    return hotspots


# ── registry 공개 API ───────────────────────────────────────────

def _getRegistryCount() -> int:
    """registry DataEntry 수."""
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             "from dartlab.core.registry import getEntries; print(len(getEntries()))"],
            capture_output=True, text=True, cwd=str(_ROOT),
        )
        return int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    except (ValueError, FileNotFoundError):
        return 0


# ── 출력 ────────────────────────────────────────────────────────

def _buildReport(scan: dict, hotspots: list[dict], registryCount: int) -> str:
    lines = []
    lines.append("# dartlab 구조 맵 (자동 생성)\n")

    # 요약
    t = scan["totals"]
    lines.append(f"**총계**: {t['files']}개 파일, {t['functions']}개 함수, "
                 f"{t['classes']}개 클래스, {t['lines']:,}줄")
    lines.append(f"**Registry**: {registryCount}개 DataEntry")
    lines.append(f"**복잡도 핫스팟**: E/F 등급 {len(hotspots)}개\n")

    # 레이어별
    lines.append("## 레이어별 현황\n")
    lines.append("| 레이어 | 파일 | 함수 | 클래스 | 줄 |")
    lines.append("|--------|------|------|--------|------|")

    layerOrder = ["L0 core", "L1 providers", "L1 gather", "L1 market",
                  "L2 analysis", "L3 ai", "Server", "CLI", "Export",
                  "MCP", "Display", "Tools", "Channel", "Review", "Root"]
    for layer in layerOrder:
        if layer in scan["layers"]:
            d = scan["layers"][layer]
            lines.append(f"| {layer} | {d['files']} | {d['functions']} | {d['classes']} | {d['lines']:,} |")

    # 외부 import 요약
    lines.append("\n## 레이어별 외부 import\n")
    for layer in layerOrder:
        if layer in scan["imports"]:
            externalImports = [i for i in scan["imports"][layer]
                              if i not in ("__future__", "typing", "collections",
                                          "dataclasses", "abc", "enum", "pathlib",
                                          "json", "re", "math", "os", "sys",
                                          "logging", "functools", "itertools",
                                          "datetime", "copy", "textwrap",
                                          "time", "hashlib", "string")]
            if externalImports:
                lines.append(f"- **{layer}**: {', '.join(sorted(externalImports)[:15])}")

    # 핫스팟 Top 20
    if hotspots:
        lines.append("\n## 복잡도 핫스팟 (E/F 등급, Top 20)\n")
        lines.append("| 파일 | 함수 | 복잡도 | 등급 |")
        lines.append("|------|------|--------|------|")
        for h in hotspots[:20]:
            shortFile = h["file"].replace("src/dartlab/", "")
            lines.append(f"| {shortFile}:{h['line']} | {h['name']} | {h['complexity']} | {h['rank']} |")

        if len(hotspots) > 20:
            lines.append(f"\n... 외 {len(hotspots) - 20}개")

    lines.append("\n---\n*`python scripts/structureMap.py`로 자동 생성*\n")
    return "\n".join(lines)


def main() -> None:
    args = sys.argv[1:]
    save = "--save" in args

    print("dartlab 소스 스캔 중...")
    scan = _scanAll()

    print("복잡도 분석 중...")
    hotspots = _getHotspots()

    print("registry 카운트...")
    registryCount = _getRegistryCount()

    report = _buildReport(scan, hotspots, registryCount)

    if save:
        outPath = _ROOT / "STRUCTURE_MAP.md"
        outPath.write_text(report, encoding="utf-8")
        print(f"저장: {outPath}")
    else:
        print(report)


if __name__ == "__main__":
    main()
