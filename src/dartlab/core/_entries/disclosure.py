"""DataEntry — disclosure 카테고리 진입점 (Cut 8 분할).

단일 진실의 원천은 list 자체. 로직은 ``core/registry.py``.
"""

from __future__ import annotations

from dartlab.core.dataEntry import DataEntry

# docs 농장 은퇴 — disclosure 서술형 공시(business/companyOverview/mdna/rawMaterial/sections)는
# panel(c.panel raw 공시 검색)이 단일 표면. 정형 docs entry 전부 제거(§영구소실).
_DISCLOSURE_ENTRIES: tuple[DataEntry, ...] = ()
