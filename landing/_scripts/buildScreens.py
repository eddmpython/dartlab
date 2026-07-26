"""scan screens JSON을 UI contracts 정적 카탈로그로 코드 생성한다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src" / "dartlab" / "scan" / "screens"
OUTPUT = ROOT / "ui" / "packages" / "contracts" / "src" / "scanPresets.generated.ts"
HEADER = """// Generated from src/dartlab/scan/screens/*.json by landing/_scripts/buildScreens.py.
// Do not edit by hand. Python, watcher, runtime ports and public /scan consume these definitions.
import type { ScanScreenDefinition } from './scan';

export const SCAN_SCREEN_PRESETS = """


def render() -> str:
    definitions = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(SOURCE.glob("*.json"))]
    body = json.dumps(definitions, ensure_ascii=False, indent="\t")
    return f"{HEADER}{body} as const satisfies readonly ScanScreenDefinition[];\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            raise SystemExit("scanPresets.generated.ts drift: landing/_scripts/buildScreens.py 실행 필요")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
