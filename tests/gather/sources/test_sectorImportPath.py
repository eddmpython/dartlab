"""업종 축의 backend import 경로 가드.

``sources/sector.py`` 만 ``from .domains.krx`` 로 점을 하나 썼다. domains 는 gather 바로
아래(``..domains``) 라 그 경로는 없는 모듈이고, ModuleNotFoundError 가 같은 줄의
``except ImportError`` 에 잡혀 warning 한 줄만 남기고 None 이 됐다. 업종 축이 어느
회사에서도 비었고, 업종코드로 피어를 찾는 축까지 함께 죽었다.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.unit

from dartlab.gather.infra.http import runAsync
from dartlab.gather.sources.sector import fetch
from dartlab.gather.types import SectorInfo, SourceUnavailableError


def _info() -> SectorInfo:
    return SectorInfo(
        sectorCode="278",
        sectorName="반도체 제조업",
        industryCode="278",
        industryName="",
        market="코스피",
        source="krx",
    )


class TestSectorFetch:
    def test_reaches_krx_backend(self):
        """backend 에 실제로 닿는다. 경로가 틀리면 여기서 None 이 나온다."""
        info = _info()
        with patch("dartlab.gather.domains.krx.fetchSectorInfo", new=AsyncMock(return_value=info)) as backend:
            out = runAsync(fetch("000660", market="KR", client=object()))
        assert out is info
        backend.assert_awaited_once()

    def test_non_kr_market_is_none(self):
        assert runAsync(fetch("AAPL", market="US", client=object())) is None

    def test_source_failure_is_none(self):
        """공급원 장애는 None. 이것만 흡수하고 import 오류는 흡수하지 않는다."""
        boom = AsyncMock(side_effect=SourceUnavailableError("krx down"))
        with patch("dartlab.gather.domains.krx.fetchSectorInfo", new=boom):
            assert runAsync(fetch("000660", market="KR", client=object())) is None


def test_sources_do_not_use_single_dot_domains():
    """``sources`` 안에서 domains 를 형제 패키지로 적으면 없는 경로가 된다."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[3] / "src" / "dartlab" / "gather" / "sources"
    offenders = [path.name for path in root.rglob("*.py") if "from .domains" in path.read_text(encoding="utf-8")]
    assert not offenders, f"sources 안에서 한 점 domains import: {offenders}"
