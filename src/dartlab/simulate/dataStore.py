"""simulate 저장소 접근 primitive SSOT. 데이터 루트 해석과 테이블 파케이 샤드 읽기.

simulate 의 파일 기반 저장소는 넷이다. 기대 원장 · 판독 원장 · 국내 표 · 미국 표. 넷이
데이터 루트를 고르는 같은 네 줄을, 원장 둘은 파케이 샤드를 모으는 같은 네 줄을 각자 갖고
있었다. 한쪽만 고치면 같은 실행 안에서 원장과 표가 서로 다른 디렉터리를 본다.

경로 규약: 명시 baseDir > ``DARTLAB_DATA_DIR`` 환경변수 > 상대경로 ``data``. 마지막이
절대경로가 아닌 이유는 이 값이 프로세스 cwd 기준의 개발용 기본값이라서다. 배포 경로는
환경변수로 준다. ``dartlab.config.dataDir`` 은 이름만 같은 다른 값이다. 그쪽은 홈 아래
설치 기본 경로로 떨어지므로 여기서 참조하면 기존 원장 위치가 바뀐다.

원장 디렉터리(``ledgerDir``)는 여기 없다. 원장마다 하위 폴더 이름이 달라(expectations /
readings) 그 상수를 소유한 모듈에 남는다. 공통인 루트 해석만 이쪽으로 내려온다.
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl


def dataDir(baseDir: Path | None = None) -> Path:
    """데이터 루트: 명시 baseDir > DARTLAB_DATA_DIR env > ./data."""
    if baseDir is not None:
        return baseDir
    root = os.environ.get("DARTLAB_DATA_DIR")
    return Path(root) if root else Path("data")


def _readAll(base: Path, table: str) -> pl.DataFrame | None:
    """``{table}_*.parquet`` 샤드를 이름순으로 모아 세로로 잇는다. 없으면 None."""
    files = sorted(base.glob(f"{table}_*.parquet"))
    if not files:
        return None
    return pl.concat([pl.read_parquet(f) for f in files], how="vertical")
