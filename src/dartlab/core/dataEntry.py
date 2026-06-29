"""DataEntry / ColumnMeta — dartlab 데이터 레지스트리 최소 단위 (L0 dataclass).

원래 core/registry.py 의 일부였으나 registry ↔ _entries 양방향 import 로
circular 발생. dataclass 만 별도 모듈로 분리 → _entries 가 본 모듈만 import,
registry 가 본 모듈 + _entries 둘 다 import (단방향).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ColumnMeta:
    """DataFrame 컬럼 메타데이터 (LLM 컨텍스트용)."""

    name: str
    description: str
    unit: str = ""


@dataclass(frozen=True)
class DataEntry:
    """데이터 소스 메타데이터 — registry의 최소 단위.

    category별 역할:
    - finance: 시계열 재무제표 (annual.IS, timeseries.BS 등)
    - report: 공시 파싱 모듈 (dividend, employee 등)
    - notes: K-IFRS 주석 (notes.receivables 등)
    - disclosure: 서술형 공시 (business, mdna 등)
    - raw: 원본 parquet (rawFinance, rawReport)
    - analysis: L2 분석 엔진 (ratios, insight, sector, rank)
    """

    name: str
    label: str
    category: str
    dataType: str
    description: str

    modulePath: str | None = None
    funcName: str | None = None
    extractor: Any = None

    apiType: str | None = None

    notesDispatch: tuple[str, str] | None = None

    aliases: tuple[str, ...] = ()

    requires: str | None = None
    unit: str = "백만원"
    columns: tuple[ColumnMeta, ...] = ()
    analysisHints: tuple[str, ...] = ()
    relatedModules: tuple[str, ...] = ()
    maxRows: int = 30

    aiExposed: bool = True
    aiCategory: str = "data"
    aiHint: str = ""
    aiQuestionTypes: tuple[str, ...] = ()
    aiKeywords: tuple[str, ...] = ()
