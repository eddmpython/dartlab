"""screens/*.json에서 UI 계약 카탈로그로 이어지는 코드젠 드리프트 가드."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_scan_screens_typescript_catalog_is_current():
    root = Path(__file__).parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "landing" / "_scripts" / "buildScreens.py"), "--check"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
