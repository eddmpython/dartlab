"""dartlab 전역 설정.

사용법::

    import dartlab
    dartlab.verbose = False   # 진행 표시 끄기
    dartlab.dataDir = "/my/data"  # 데이터 저장 경로 변경

환경변수::

    DARTLAB_DATA_DIR=/my/data    # 데이터 저장 경로
"""

import os
from pathlib import Path

verbose: bool = True

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

dataDir: str = os.environ.get("DARTLAB_DATA_DIR", str(_DEFAULT_DATA_DIR))
