"""공시 panel 표 → export 격자 추상화 — DIP (정공법 B, F1.7).

`viz/export` 는 공시 표를 .xlsx 로 내보낼 때 panel wide(`readWide`) 로드 + 행 선택 +
DART XML 정규화(`normalizeDartXml`) + 병합 격자 전개(`cellGrid`) + 셀 값 정합(`coerceCell`)
이 필요하다. 그런데 viz 가 providers 를 직접 import 하면 layer 위반(`from dartlab.providers`
금지 — `test_export_module_does_not_depend_on_root_company_internals`).

PanelTableAccessor Protocol 을 core 에 두고 `providers/dart/parse/panelExportGrid` 가
register(auto-discovery). viz 는 core import 만 — provider 직접 의존 0. 결과는 평면
``PanelExportSheet`` (위치·병합·정합값·단위) 라 viz 는 openpyxl 쓰기만 한다.

FinanceDocAccessor/htmlRenderer/gatherProvider 와 동일 패턴 (register + auto-discovery).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap


@dataclass
class PanelExportCell:
    """병합 보존 격자의 앵커 셀 1개 — 위치·정합값·병합 span·스타일 힌트.

    병합셀은 앵커(top-left) 1개로만 표현하고 ``rowspan``/``colspan`` 으로 범위를 전한다
    (극단 rowspan 도 셀 1개). 소비처(viz)가 앵커에 값 쓰고 span>1 이면 merge.
    """

    row: int  # 0-base (표 격자 기준 — viz 가 단위/노트 머리행 offset 가산)
    col: int  # 0-base
    value: int | float | str | None  # coerceCell 결과 (None = 결손 = honest-gap 빈셀)
    isHeader: bool = False
    align: str = ""  # "right"/"center"/"left"/""
    rowspan: int = 1
    colspan: int = 1


@dataclass
class PanelExportSheet:
    """공시 표 1개의 export 격자 — 앵커 셀 + 단위/노트. provider 가 만들고 viz 가 쓴다."""

    cells: list[PanelExportCell] = field(default_factory=list)
    unit: str = ""  # detectUnit 결과 (값 환산 0 — 라벨만)
    note: str = ""  # 예: "수평화 미지원(원본 구조) — as-filed 2024Q1"


@runtime_checkable
class PanelTableAccessor(Protocol):
    """공시 panel 표 → export 격자 추상화 — viz/export 가 사용."""

    def panelTableGrid(
        self,
        stockCode: str,
        *,
        marketNs: str = "kr",
        chapter: str = "",
        sectionLeaf: str = "",
        blockLeaf: str = "",
        leafType: str = "table",
        disclosureKey: str | None = None,
        scope: str | None = None,
        leafSeq: int | None = None,
        periodMode: str = "asFiled",
        period: str | None = None,
    ) -> PanelExportSheet | None:
        """식별 필드로 panel wide 행 1개를 골라 export 격자(앵커 셀+병합+단위)로.

        제공된(non-None) 식별 필드만으로 매칭, 다중이면 leafSeq 디스앰비그. periodMode=
        "asFiled"=단일 기간 원본 격자, "horizontalized"=일반 공시 표는 as-filed 폴백+노트.
        실패(panel/행/기간 부재)는 None — 소비처 graceful skip.
        """
        ...


_ACCESSOR: PanelTableAccessor | None = None


def _discover() -> None:
    """root composition이 등록한 PanelTableAccessor bootstrap을 실행한다."""
    bootstrap(__name__)


def registerPanelTableAccessor(accessor: PanelTableAccessor) -> None:
    """PanelTableAccessor 등록 — providers 가 import 시점에 호출."""
    global _ACCESSOR
    _ACCESSOR = accessor


def getPanelTableAccessor() -> PanelTableAccessor | None:
    """현재 등록된 PanelTableAccessor 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _ACCESSOR
