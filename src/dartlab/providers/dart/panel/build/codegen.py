"""build/ 생성 모듈 공용 후처리 (SSOT).

`noteTaxonomy` 와 `spineBuilder` 는 각각 `.py` 모듈을 찍어내고 같은 방식으로 ruff
정본화를 걸었다. 본문이 같은 정의가 두 벌 있으면 한쪽만 고쳐지는 표류가 생기므로
여기 한 자리로 모은다. 생성물 후처리 헬퍼가 늘면 이 모듈에 붙인다.
"""

from __future__ import annotations

from pathlib import Path


def _ruffFormat(path: Path) -> None:
    """생성 모듈을 ruff format 정본화 (실패는 무시. ruff 부재 환경 안전).

    Args:
        path: 포맷할 .py 경로.

    Returns:
        None.

    Raises:
        없음. subprocess 실패는 흡수한다 (생성물은 이미 valid python).
    """
    import subprocess

    try:
        subprocess.run(
            ["uv", "run", "ruff", "format", str(path)],
            check=False,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        pass
