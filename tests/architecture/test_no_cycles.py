"""F3 강행 — 양방향 cycle 회귀 방지.

cycleScan 의 --strict-toplevel 모드 (lazy import 면제, 진짜 런타임 cycle 만)
가 exit 0 이어야 한다.

진짜 런타임 cycle 가 다시 들어오면 dartlab import 자체가 실패할 수 있고,
ai-policy 분석도 비결정적이 된다. 이 가드는 그것을 차단.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent


@pytest.mark.unit
def test_no_toplevel_cycles() -> None:
    """top-level (런타임 실행) import 양방향 cycle = 0."""
    script = REPO / "tests" / "audit" / "cycleScan.py"
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(script), "--strict-toplevel"],
        capture_output=True,
        text=True,
        # 자식은 -X utf8 로 한글을 UTF-8 로 쓴다. 여기서 인코딩을 안 적으면 로케일
        # (한국어 Windows 는 cp949) 로 디코드하다 읽기 스레드가 죽고 출력이 비어,
        # 실패 메시지에 원인이 한 줄도 안 남는다.
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO),
    )
    assert result.returncode == 0, (
        f"cycleScan --strict-toplevel exit {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
