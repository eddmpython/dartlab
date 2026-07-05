"""사업보고서 완전 인벤토리 (처음부터 끝까지 모든 단위, L1.5 frame).

손으로 고르는 카탈로그가 아니라 **panel + report 에서 전수 자동 열거**한다. 한 회사 사업보고서의 모든
추출 단위(표준 노트 NT_Dxxxxx · 회사별 노트 NT_C_U/NT_S_U · 임베디드 정형 ACLASS[TOT_STK·EMPLOYEE·
VOT_STK·SUB_* 등] · 내러티브 섹션 · 재무 5표 · XII 상세표 · OpenDART 정형공시 apiType)를 안정 handle 과
함께 인벤토리로 만든다.

**정직 상한(전문에이전트 감사 반영)**: "cover-to-cover 100%" 가 아니라 **BUILD 로 포착한 모든 단위, unit
입도**. KR(DART) = panel(노트·정형표·내러티브) + report(정형공시). US(EDGAR) = edgar panel(재무 5표) +
docs sections(SEC 10-K/10-Q Item, `_itemUnits`). 양 시장 대칭 열거(동급). 상한 밖: 이미지 바이너리·cover
구조 메타·해소된 cross-ref·multi-axis cell 분해(공통), US exhibit(EX-*)·proxy 참조편입 Part III(별도 파일).

**2 층 설계**: (1) 인벤토리 = panel+report 전수 열거(본 모듈). (2) 의미 카탈로그(`core.extractionCatalog`)
= 고가치 단위에 DART<->EDGAR parity + 타입 추출기 부여(부분 enrich). 각 인벤토리 단위는 매칭 conceptId 로
태깅되어 두 층을 잇는다(enrich 여부 = cataloguedUnits/total).

**handle 규약**: 노트 = disclosureKey(NT_...) · 재무표 = is/bs/cf/cis/sce · 내러티브 = sectionLeaf.
회사별 코드(NT_C_U/NT_S_U)는 회사 내 handle 은 disclosureKey, 회사 간 안정 식별은 normalizedTitle.

**계층 (L1.5 frame)**: core(카탈로그·dataLoader)·providers(panel) 만 import. 진입은 root
`dartlab.dossier(code).inventory()`.
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from dartlab.core.extractionCatalog import DartSource, getExtractionConcepts

_PERIOD_COL = re.compile(r"^\d{4}Q[1-4]$")

_NATIVE_STATEMENTS = (
    ("is", "손익계산서"),
    ("bs", "재무상태표"),
    ("cf", "현금흐름표"),
    ("cis", "포괄손익계산서"),
    ("sce", "자본변동표"),
)
# 재무 5표 disclosureKey(scope-strip). native 5표 단위가 대표하므로 keyed-form 열거에서 제외.
_STATEMENT_KEYS = frozenset({"BS", "IS", "IS1", "IS2", "IS3", "CF", "CIS", "EF", "SCE"})
_INV_COLS = ("disclosureKey", "chapter", "sectionLeaf", "blockLeaf", "leafType", "period")
_NUM_PREFIX = re.compile(r"^\s*[0-9IVXLC]+[.)]\s*")


def _panelPath(code: str, marketNs: str):
    """market 별 panel parquet 경로."""
    from dartlab.core.dataLoader import _dataDir

    cat = "edgarPanel" if marketNs == "us" else "panel"
    return _dataDir(cat) / f"{code}.parquet"


def _normalizeTitle(title: str) -> str:
    """제목 정규화(번호 접두·공백 strip) = 회사 간 안정 식별 키."""
    return _NUM_PREFIX.sub("", (title or "").strip()).strip()


def _noteConceptIndex() -> dict[str, str]:
    """canonicalKey family(prefix) -> conceptId (인벤토리 단위 의미 태깅용)."""
    idx: dict[str, str] = {}
    for c in getExtractionConcepts(category="note"):
        if isinstance(c.dart, DartSource):
            idx[c.dart.key[:-1]] = c.conceptId
    return idx


def _narrativeConceptIndex() -> list[tuple[str, str]]:
    """[(sectionLeaf 키워드, conceptId)] (내러티브 단위 의미 태깅용)."""
    out: list[tuple[str, str]] = []
    for c in getExtractionConcepts(category="narrative"):
        if c.narrativeAnchor is not None:
            out.append((c.narrativeAnchor[1], c.conceptId))
    return out


def reportInventory(code: str, *, marketNs: str = "kr", board: Any = None) -> dict:
    """한 회사 사업보고서의 완전 인벤토리를 정규화된 wide board + report 에서 전수 자동 열거한다.

    전문에이전트 감사 반영: raw parquet 이 아니라 **reader 정규화 출력(Panel wide)** 에서 열거한다.
    Panel(code) 은 alignNotes -> anchorLatest -> absorbAttached -> anchorNarrativeToSpine 을 거친
    dedup·정규화 뷰라, 인벤토리 handle 이 get()/materialize() 가 검색하는 것과 정확히 일치한다
    (round-trip 정합·첨부 중복 제거·회사별 코드 표준 흡수). raw 열거의 phantom 단위 문제를 제거한다.

    Args:
        code: 종목코드/티커.
        marketNs: "kr"(DART panel) / "us"(EDGAR panel).
        board: 미리 로드한 Panel wide(materialize 가 1회 로드 재사용). None 이면 여기서 로드.

    Returns:
        {"code", "units": [unit...], "summary": {...}}. unit =
        {handle, kind(note/form/narrative/statement/report), title, normalizedTitle, chapter, scope,
        periods, rows, hasTable, hasText, disclosureKey, conceptId, companySpecific}.

    Raises:
        없음.

    Example:
        >>> import dartlab
        >>> inv = dartlab.dossier("005930").inventory()  # doctest: +SKIP
        >>> inv["summary"]["total"]                       # doctest: +SKIP

    Capabilities:
        - 손 카탈로그 없이 보고서 전 단위(표준·회사별 노트·정형표·내러티브·재무표·apiType) 열거.

    Guide:
        - "이 회사 사업보고서에 뭐가 다 있나" -> reportInventory(code)["units"].
        - 단위 실제 추출 -> dossier.get(unit["handle"]).

    AIContext:
        AI 가 보고서 전체를 탐색할 때 진입. 각 단위 handle 로 필요한 것만 lazy 추출.

    Requires:
        - core.extractionCatalog(의미 태깅), providers.dart.panel(정규화 열거 원천).
    """
    units: list[dict] = []
    empty = {"code": code, "units": units, "summary": {"total": 0, "byKind": {}}}
    if board is None:
        board = _loadBoard(code, marketNs)
    if board is None or getattr(board, "height", 0) == 0 or "disclosureKey" not in board.columns:
        return empty

    periodCols = [c for c in board.columns if _PERIOD_COL.match(c)]
    noteIdx = _noteConceptIndex()
    narrIdx = _narrativeConceptIndex()

    units += _keyedUnits(board, periodCols, noteIdx)  # NT_ 노트 + 임베디드 정형 ACLASS
    if marketNs == "us":
        units += _itemUnits(code)  # EDGAR docs Item(SEC 10-K/10-Q 섹션) = DART narrative+report 대응 surface
    else:
        units += _narrativeUnits(board, periodCols, narrIdx)  # DART 내러티브 섹션
    units += _statementUnits(board, marketNs)  # 재무 5표(native 분해)
    units += _reportUnits(code, marketNs)  # OpenDART 정형공시 apiType(KR only, US 는 _itemUnits 가 담당)

    byKind: dict[str, int] = {}
    for u in units:
        byKind[u["kind"]] = byKind.get(u["kind"], 0) + 1
    catalogued = sum(1 for u in units if u["conceptId"])
    return {
        "code": code,
        "units": units,
        "summary": {
            "total": len(units),
            "byKind": byKind,
            "cataloguedUnits": catalogued,
            "rawOnlyUnits": len(units) - catalogued,
        },
    }


def _loadBoard(code: str, marketNs: str):
    """Panel wide(정규화 뷰) 1회 로드. 부재/실패 시 None."""
    try:
        if marketNs == "us":
            from dartlab.providers.edgar.panel import Panel
        else:
            from dartlab.providers.dart.panel import Panel

        board = Panel(code, marketNs=marketNs)
    except (FileNotFoundError, OSError, ValueError, MemoryError):
        return None
    return board


def _keyedUnits(board: pl.DataFrame, periodCols: list[str], noteIdx: dict[str, str]) -> list[dict]:
    """keyed 행(disclosureKey non-null) 전수 열거 후 분류 (정규화 wide board).

    NT_ -> note(표준 NT_D + 회사별 NT_C_U/NT_S_U), 재무표 키 -> 제외(native 5표가 대표),
    그 외 -> form(임베디드 정형 ACLASS: TOT_STK·DIVIDEND·EMPLOYEE·VOT_STK·SUB_*·INS_* + XII SUB_CMPN 등).
    """
    keyed = board.filter(pl.col("disclosureKey").is_not_null() & (pl.col("disclosureKey") != ""))
    if keyed.is_empty():
        return []
    units: list[dict] = []
    for key, sub in keyed.group_by("disclosureKey"):
        dk = key[0] if isinstance(key, tuple) else key
        if dk in _STATEMENT_KEYS:
            continue  # native 5표 단위가 대표(중복 회피)
        isNote = dk.startswith("NT_")
        kind = "note" if isNote else "form"
        title = _dominantTitle(sub)
        leaf = set(sub.get_column("leafType").drop_nulls().to_list()) if "leafType" in sub.columns else set()
        scope = _first(sub, "scope") or (("separate" if dk.endswith("5") else "consolidated") if isNote else None)
        units.append(
            {
                "handle": dk,
                "kind": kind,
                "title": title,
                "normalizedTitle": _normalizeTitle(title),
                "chapter": _first(sub, "chapter"),
                "scope": scope,
                "periods": _periods(sub, periodCols),
                "rows": sub.height,
                "hasTable": "table" in leaf,
                "hasText": "text" in leaf,
                "disclosureKey": dk,
                "conceptId": noteIdx.get(dk[:-1]) if isNote else None,
                "companySpecific": dk.startswith("NT_C_U") or dk.startswith("NT_S_U"),
            }
        )
    units.sort(key=lambda u: (u["kind"], u["handle"]))
    return units


def _reportUnits(code: str, marketNs: str) -> list[dict]:
    """OpenDART 정형공시 apiType 단위 열거 (panel 밖 병렬 surface, report parquet).

    거버넌스·자본·부채·인력 정형표(dividend·employee·majorHolder·corporateBond 등)는 panel 이 아니라
    report parquet 에 산다. panel-only 열거가 놓치는 ~30 surface 를 여기서 채운다.
    """
    if marketNs != "kr":
        return []
    from dartlab.core.dataLoader import _dataDir

    path = _dataDir("report") / f"{code}.parquet"
    if not path.exists():
        return []
    try:
        if "apiType" not in pl.scan_parquet(path).collect_schema().names():
            return []
        at = pl.read_parquet(path, columns=["apiType"]).get_column("apiType")
    except (pl.exceptions.PolarsError, OSError):
        return []
    reportIdx = {c.dart.key: c.conceptId for c in getExtractionConcepts() if _isReport(c)}
    labelIdx = {c.dart.key: c.label for c in getExtractionConcepts() if _isReport(c)}
    from collections import Counter

    counts = Counter(x for x in at.drop_nulls().to_list() if x)
    units: list[dict] = []
    for apiType, n in counts.most_common():
        units.append(
            {
                "handle": apiType,
                "kind": "report",
                "title": labelIdx.get(apiType, apiType),
                "normalizedTitle": labelIdx.get(apiType, apiType),
                "chapter": None,
                "scope": None,
                "periods": [],
                "rows": n,
                "hasTable": True,
                "hasText": False,
                "disclosureKey": None,
                "conceptId": reportIdx.get(apiType),
                "companySpecific": False,
            }
        )
    units.sort(key=lambda u: u["handle"])
    return units


def _isReport(c) -> bool:
    """개념이 report surface 인지."""
    return isinstance(c.dart, DartSource) and c.dart.surface == "report"


def _itemUnits(code: str) -> list[dict]:
    """EDGAR docs Item 단위 열거 (SEC 10-K/10-Q/20-F 섹션, panel 밖 병렬 surface).

    DART report parquet 이 정형표 surface 이듯 EDGAR 는 docs sections 가 Item surface 다. topic(form::itemId)
    을 handle 로 열거하며 pipeline.sections 로 round-trip 추출된다. 열거는 topic 컬럼만 projection(본문 무접촉,
    OOM 안전). 얇고 회사별 편차 큰 edgar panel narrative 대신 정규화된 docs 열거가 US narrative parity 정본.
    """
    from dartlab.core.extractionCatalog import conceptForEdgarItem
    from dartlab.providers.edgar.docs.sections.topicUnits import topicUnits

    units: list[dict] = []
    for u in topicUnits(code):
        concept = conceptForEdgarItem(u["itemId"])
        units.append(
            {
                "handle": u["topic"],
                "kind": "item",
                "title": u["title"],
                "normalizedTitle": u["title"],
                "chapter": u["chapter"],
                "scope": None,
                "periods": [],
                "rows": None,
                "hasTable": u["hasTable"],
                "hasText": u["hasText"],
                "disclosureKey": None,
                "conceptId": concept.conceptId if concept else None,
                "companySpecific": False,
            }
        )
    units.sort(key=lambda x: x["handle"])
    return units


def _narrativeUnits(board: pl.DataFrame, periodCols: list[str], narrIdx: list[tuple[str, str]]) -> list[dict]:
    """내러티브 섹션 단위 열거 (disclosureKey null, chapter+sectionLeaf 그룹, 정규화 wide board).

    handle = sectionLeaf(panel sectionLeaf 매칭 라우팅). 정규화 wide board 라 라벨이 수렴되어 있어
    (chapter,sectionLeaf) 그룹이 distinct 단위. 드문 동일-라벨 다른-chapter 는 get() 이 합집합 반환(무손실).
    """
    nar = board.filter(pl.col("disclosureKey").is_null())
    if nar.is_empty() or "sectionLeaf" not in nar.columns:
        return []
    units: list[dict] = []
    for key, sub in nar.group_by(["chapter", "sectionLeaf"]):
        chapter = key[0] if isinstance(key, tuple) else None
        section = key[1] if isinstance(key, tuple) and len(key) > 1 else None
        if not section:
            continue
        leaf = set(sub.get_column("leafType").drop_nulls().to_list()) if "leafType" in sub.columns else set()
        conceptId = next((cid for kw, cid in narrIdx if kw in section), None)
        units.append(
            {
                "handle": section,
                "kind": "narrative",
                "title": section,
                "normalizedTitle": _normalizeTitle(section),
                "chapter": chapter,
                "scope": None,
                "periods": _periods(sub, periodCols),
                "rows": sub.height,
                "hasTable": "table" in leaf,
                "hasText": "text" in leaf,
                "disclosureKey": None,
                "conceptId": conceptId,
                "companySpecific": False,
            }
        )
    units.sort(key=lambda u: (u["chapter"] or "", u["handle"]))
    return units


_US_STATEMENT_LABELS: dict[str, str] = {
    "is": "Income Statement",
    "bs": "Balance Sheet",
    "cf": "Cash Flow",
    "cis": "Comprehensive Income",
    "sce": "Statement of Equity",
}


def _statementUnits(df: pl.DataFrame, marketNs: str = "kr") -> list[dict]:
    """재무 5표 단위 (panel 있으면 상존, native 분해 가능). US 는 영문 라벨."""
    if df.is_empty():
        return []
    concIdx = {c.dart.key: c.conceptId for c in getExtractionConcepts(category="financialStatement") if c.dart}
    isUs = marketNs == "us"
    units: list[dict] = []
    for key, label in _NATIVE_STATEMENTS:
        title = _US_STATEMENT_LABELS[key] if isUs else label
        units.append(
            {
                "handle": key,
                "kind": "statement",
                "title": title,
                "normalizedTitle": title,
                "chapter": "Financial Statements" if isUs else "III",
                "scope": "consolidated",
                "periods": [],
                "rows": None,
                "hasTable": True,
                "hasText": False,
                "disclosureKey": None,
                "conceptId": concIdx.get(key),
                "companySpecific": False,
            }
        )
    return units


def _dominantTitle(sub: pl.DataFrame) -> str:
    """그룹의 대표 제목: table blockLeaf 최빈 -> sectionLeaf."""
    if "blockLeaf" in sub.columns:
        bl = sub
        if "leafType" in sub.columns:
            bl = sub.filter(pl.col("leafType") == "table")
        vals = [x for x in bl.get_column("blockLeaf").drop_nulls().to_list() if x and 1 < len(x) <= 40]
        if vals:
            return max(set(vals), key=vals.count)
    return _first(sub, "sectionLeaf") or ""


def _periods(sub: pl.DataFrame, periodCols: list[str]) -> list[str]:
    """그룹이 커버하는 period 컬럼(어떤 행이든 non-null) 최신순."""
    covered = [pc for pc in periodCols if pc in sub.columns and sub.get_column(pc).drop_nulls().len() > 0]
    return sorted(covered, reverse=True)


def _first(sub: pl.DataFrame, col: str):
    """그룹의 첫 non-null 값."""
    if col not in sub.columns:
        return None
    vals = sub.get_column(col).drop_nulls().to_list()
    return vals[0] if vals else None
