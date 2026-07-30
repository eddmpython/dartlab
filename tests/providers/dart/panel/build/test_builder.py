"""panel builder mirror — 순수 헬퍼와 공개 빌드 API.

``providers/dart/panel/build/builder.py`` 의 1:1 mirror. 순수 _prevYear·panelXbrlRefPath 와
공개표면을 검증한다. 실 zip→16-col 빌드와 영수증 격리는 test_build_lossless.py 및
test_artifactWriter.py가 맡고, bounded 회사 fan-out은 test_batch.py가 맡는다.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_prev_year() -> None:
    """_prevYear: 연도 문자열 → 직전 연도 (변환 실패 시 원본)."""
    from dartlab.providers.dart.panel.build.builder import _prevYear

    assert _prevYear("2024") == "2023"
    assert _prevYear("abcd") == "abcd"


def test_panel_xbrl_ref_path() -> None:
    """panelXbrlRefPath: ref truth 단일 경로 — 패키지 동봉 build/refScan/panelXbrlRef.parquet (data/ 아님)."""
    from dartlab.providers.dart.panel.build.builder import panelXbrlRefPath

    p = panelXbrlRefPath()
    assert p.name == "panelXbrlRef.parquet"
    # 패키지 동봉(git 추적·wheel) — data/ 가 아니라 build/refScan/ 아래 (코드와 함께 버전·공유).
    assert p.as_posix().endswith("panel/build/refScan/panelXbrlRef.parquet")
    assert p.exists(), "패키지 동봉 ref parquet 부재"


def test_build_callables_public() -> None:
    """buildPanel/buildPanelFromStream/buildPanelBaseline 공개표면 존재 (단일 빌드 트랙)."""
    from dartlab.providers.dart.panel.build import buildPanel, buildPanelBaseline, buildPanelFromStream

    assert callable(buildPanel)
    assert callable(buildPanelFromStream)
    assert callable(buildPanelBaseline)
