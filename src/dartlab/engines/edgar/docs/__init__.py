"""EDGAR 공시 문서 저장소 엔진.

현재 단계는 저장 규약, 로더 연동, sections horizontal view까지 포함한다.
개별 disclosure 파서는 experiments/055_edgarDocs, 057_edgarSectionMap 결과를 바탕으로 순차 흡수한다.
"""

from dartlab.engines.edgar.docs.fetch import downloadListedEdgarDocs, fetchEdgarDocs
from dartlab.engines.edgar.docs.sections import sections

__all__ = ["fetchEdgarDocs", "downloadListedEdgarDocs", "sections"]
