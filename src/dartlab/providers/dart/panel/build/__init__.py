"""panel BUILD 공개표면. zip을 16-col parquet로 생산한다.

caller 는 ``from dartlab.providers.dart.panel.build import buildPanel`` 만 (deep leaf
import 금지, R6). lxml·zipfile 사용은 본 build 패키지에 격리 (reader 는 scan_parquet 만, R2).

공개:
    - ``buildPanel`` / ``buildPanelAll`` / ``buildPanelBaseline`` (builder, 로컬 zip 트랙 A).
    - ``buildPanelFromStream`` (online 1패스 — (rcept,bytes) 스트림 → parquet, 디스크 zip 0, 트랙 B).
    - ``buildSpine`` (한 회사 정부 문서순서 → spine/spineData.py 생성).
    - ``horizontalize`` (element→section 무손실 concat).
    - ``walkSections`` / ``detectSchemaEra`` (walker).
    - ``scanAllZips`` / ``scanRefBaseline`` / ``scanZipFiles`` (refScan, ref truth 생산).
"""

from __future__ import annotations

from .baseline import buildPanelBaseline
from .batch import buildPanelAll
from .builder import (
    PanelBuildError,
    buildPanel,
    buildPanelFromStream,
    panelXbrlRefPath,
)
from .horizontalize import horizontalize
from .refScan import scanAllZips, scanRefBaseline, scanZipFiles
from .spineBuilder import buildSpine
from .walker import detectSchemaEra, walkSections

__all__ = [
    "PanelBuildError",
    "buildPanel",
    "buildPanelAll",
    "buildPanelBaseline",
    "buildPanelFromStream",
    "buildSpine",
    "detectSchemaEra",
    "horizontalize",
    "panelXbrlRefPath",
    "scanAllZips",
    "scanRefBaseline",
    "scanZipFiles",
    "walkSections",
]
