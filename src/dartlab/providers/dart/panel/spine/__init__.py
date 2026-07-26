"""panel 정부 서식 뼈대(spine) read 표면 — 행 순서·계층 lookup (순수 dict, lxml 0).

``spineData.py``(spineBuilder 생성물, git 추적)를 module-level dict 로 1회 변환. ``read.readWide``
가 wide 각 행의 ``rowIdentity`` 로 ``SPINE`` 을 조회해 정부 문서순서(chapterRank, spineOrder)로
정렬한다. 데이터 파일 read 0(코드 import), 누적 0(module-level 상수).

LLM Specifications:
    AntiPatterns:
        - parquet/외부 파일 read 금지 — spineData.py import (순수 코드, R2 read 표면).
        - 매 read dict 재구성 금지 — module-level 1회.
    OutputSchema:
        - ``SPINE: dict[str, tuple[int, str | None, int]]`` (identity → (spineOrder, parentKey, chapterRank)).
        - ``spineOrderOf(identity) -> int | None`` / ``chapterRankOf(identity) -> int | None``.
    Prerequisites:
        - spineData.py (spineBuilder 생성). 없으면 빈 SPINE.
    Freshness:
        - spineData.py 재생성 시 다음 import 반영.
    Dataflow:
        - spineData.SPINE_ROWS → SPINE dict.
    TargetMarkets:
        - KR (DART). EDGAR 후속.
"""

from __future__ import annotations

# 로직은 `lookup` 이 소유한다. 여기는 진입면만 모은다.
from dartlab.providers.dart.panel.spine.lookup import (
    SPINE,
    chapterRankOf,
    spineOrderOf,
)

__all__ = ["SPINE", "chapterRankOf", "spineOrderOf"]
