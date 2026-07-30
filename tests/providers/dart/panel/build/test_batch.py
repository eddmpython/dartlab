"""panel batch mirror — bounded 회사 thread fan-out 공개표면 (데이터 0).

``providers/dart/panel/build/batch.py`` 의 1:1 mirror. buildPanelAll/_main 공개표면 존재와
_buildOne 의 source failure 전파를 순수 경로에서 검증한다. 실 전종목
빌드와 공시별 child process 검증은 운영자/CI sync 및 documentProcess mirror가 담당한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_batch_callables_public() -> None:
    """buildPanelAll/_main 공개표면 존재 (build __init__ re-export 포함)."""
    from dartlab.providers.dart.panel.build import buildPanelAll
    from dartlab.providers.dart.panel.build.batch import _main
    from dartlab.providers.dart.panel.build.batch import buildPanelAll as ba

    assert callable(buildPanelAll)
    assert buildPanelAll is ba
    assert callable(_main)


def test_build_one_propagates_missing_reference() -> None:
    """_buildOne은 없는 ref를 성공 모양의 0행 결과로 바꾸지 않는다."""
    from dartlab.providers.dart.panel.build.batch import _buildOne

    with pytest.raises(FileNotFoundError):
        _buildOne(("000000nonexistent", "data/__no_such_ref__.parquet", "data/__no_out__"))


def test_batch_rejects_more_than_two_concurrent_companies(tmp_path: Path) -> None:
    """회사 병렬도는 자식 변환 process를 합쳐 최대 2개로 제한한다."""
    from dartlab.providers.dart.panel.build.batch import buildPanelAll

    with pytest.raises(ValueError, match="1 또는 2"):
        buildPanelAll(
            refPath="data/__no_such_ref__.parquet",
            outBaseDir=tmp_path,
            codes=[],
            numWorkers=3,
            verbose=False,
        )
