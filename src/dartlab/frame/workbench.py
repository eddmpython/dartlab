"""데이터 공동 작업대 (Dossier): 카탈로그 구동 단일사 조립 view (L1.5 frame).

한 회사의 재무·노트·거버넌스·자본·부채·부문·정성을 카탈로그(`core.extractionCatalog`) 구동으로 한 자리에
정리·조립하는 read-only 워크벤치다. 손으로 c.panel·report·narrative 를 조합하던 것을 개념 카탈로그 하나로
통일한다. 무bake: 런타임이 SSOT(panel/report/finance)에서 직독한다.

**계층 (L1.5 frame)**: core(카탈로그·dataLoader)·providers(panel)·frame(narrative) 만 import. 진입점은
root `dartlab.dossier(code)` 다 (Company(L1)가 frame(L1.5)을 import 하면 상향 위반이라 facade 는 root).

**정리 vs 추출**: `available()` 은 경량 신호맵(어떤 개념이 이 회사에 실재하나, 조직도). `extract()` 은
개념 1건 실제 추출(요청 시). `category()`/`assemble()` 은 카테고리 조립.

**예측 위임**: 워크벤치는 재료를 정리해 내주고, 예측은 L2(analysis·quant·macro)가 그 위에서 한다. Dossier
는 예측을 소유하지 않고 위임 힌트만 제공(`forecastHint`). 4계층 단방향 보존.
"""

from __future__ import annotations

import polars as pl

from dartlab.core.extractionCatalog import (
    CATEGORIES,
    DartSource,
    ExtractionConcept,
    getConcept,
    getExtractionConcepts,
)


def _panelKeys(code: str) -> set[str]:
    """panel disclosureKey 집합(노트 NT_ 신호) 1회 읽기."""
    from dartlab.core.dataLoader import _dataDir

    path = _dataDir("panel") / f"{code}.parquet"
    if not path.exists():
        return set()
    try:
        dk = pl.read_parquet(path, columns=["disclosureKey"]).get_column("disclosureKey")
        return {x for x in dk.drop_nulls().to_list() if x}
    except (pl.exceptions.PolarsError, OSError):
        return set()


def _panelSections(code: str) -> set[str]:
    """panel narrative sectionLeaf 집합(정성 신호) 1회 읽기."""
    from dartlab.core.dataLoader import _dataDir

    path = _dataDir("panel") / f"{code}.parquet"
    if not path.exists():
        return set()
    try:
        df = pl.read_parquet(path, columns=["disclosureKey", "sectionLeaf"])
        nar = df.filter(pl.col("disclosureKey").is_null())
        return {x for x in nar.get_column("sectionLeaf").drop_nulls().to_list() if x}
    except (pl.exceptions.PolarsError, OSError):
        return set()


def _reportApiTypes(code: str) -> set[str]:
    """report apiType 집합(정형공시 신호) 1회 읽기."""
    from dartlab.core.dataLoader import _dataDir

    path = _dataDir("report") / f"{code}.parquet"
    if not path.exists():
        return set()
    try:
        at = pl.read_parquet(path, columns=["apiType"]).get_column("apiType")
        return {x for x in at.drop_nulls().to_list() if x}
    except (pl.exceptions.PolarsError, OSError):
        return set()


def _conceptPresent(concept: ExtractionConcept, notes: set[str], apiTypes: set[str], sections: set[str]) -> bool:
    """개념의 DART 신호가 이 회사에 있나(경량 판정, 조직맵용)."""
    d = concept.dart
    if not isinstance(d, DartSource):
        return False
    if d.surface == "note":
        prefix = d.key[:-1]
        return any(k.startswith(prefix) for k in notes)
    if d.surface == "report":
        return d.key in apiTypes
    if d.surface == "statement":
        return bool(notes or sections)  # panel 있으면 재무 5표 상존
    if d.surface == "narrative" and concept.narrativeAnchor is not None:
        kw = concept.narrativeAnchor[1]
        return any(kw in s for s in sections)
    if d.surface == "segmentTable":
        return any("매출" in s and "수주" in s for s in sections)
    return False


def _loadBoard(code: str, marketNs: str):
    """dart/edgar Panel 스위치 SSOT (inventory._loadBoard 재사용, 단일 진실의 원천)."""
    from dartlab.frame.inventory import _loadBoard as _inventoryLoadBoard

    return _inventoryLoadBoard(code, marketNs)


def _sliceSections(sectionsDf, topic: str):
    """로드된 edgar docs sections df 에서 topic(form::itemId) 슬라이스. 비면 None."""
    if sectionsDf is None or "topic" not in getattr(sectionsDf, "columns", []):
        return None
    df = sectionsDf.filter(pl.col("topic") == topic)
    return df if not df.is_empty() else None


class Dossier:
    """한 회사의 카탈로그 구동 데이터 워크벤치(조립 view).

    available/extract/category 로 정리·조립. 예측은 L2 위임(forecastHint).
    """

    def __init__(self, code: str, *, marketNs: str = "kr"):
        self.code = code
        self.marketNs = marketNs

    def available(self) -> dict:
        """이 회사에서 실재(추출가능)한 개념을 카테고리별로 정리한 조직맵을 반환한다.

        경량 신호(panel NT_ 키 + report apiType + narrative sectionLeaf)만 읽어 무거운 추출 없이
        "무엇을 뽑을 수 있나" 를 조직한다. 데이터 공동 작업대의 핵심 정리 표면.

        Returns:
            {category: [{conceptId, label, present, parity}]} (present=신호 있음).

        Raises:
            없음. 데이터 부재 시 present 전부 False.

        Example:
            >>> import dartlab
            >>> dartlab.dossier("005930").available()["note"][0]["conceptId"]  # doctest: +SKIP
            'note.inventory'
        """
        notes = _panelKeys(self.code)
        apiTypes = _reportApiTypes(self.code)
        sections = _panelSections(self.code)
        out: dict[str, list[dict]] = {c: [] for c in CATEGORIES}
        for concept in getExtractionConcepts():
            present = _conceptPresent(concept, notes, apiTypes, sections)
            out.setdefault(concept.category, []).append(
                {
                    "conceptId": concept.conceptId,
                    "label": concept.label,
                    "present": present,
                    "parity": concept.parity(),
                }
            )
        return out

    def inventory(self) -> dict:
        """사업보고서 완전 인벤토리(모든 단위 100% 자동 열거)를 반환한다.

        손 카탈로그가 아니라 panel 전수 열거. 표준 노트 + 회사별 노트(NT_C_U/NT_S_U) + 내러티브 섹션
        + 재무 5표를 안정 handle 과 함께. 각 단위는 conceptId 로 의미 태깅(카탈로그 enrich 여부).

        Returns:
            {code, units[...], summary{total, byKind, cataloguedUnits, rawOnlyUnits}}.

        Raises:
            없음.

        Example:
            >>> import dartlab
            >>> dartlab.dossier("005930").inventory()["summary"]["total"]  # doctest: +SKIP
        """
        from dartlab.frame.inventory import reportInventory

        return reportInventory(self.code, marketNs=self.marketNs)

    def get(self, handle: str) -> pl.DataFrame | None:
        """인벤토리 handle(어떤 단위든)로 실제 추출한다.

        handle 은 노트 disclosureKey(NT_...) · 재무표 키(is/bs/cf/cis/sce) · 내러티브 sectionLeaf.
        panel __call__ 이 canonicalKey exact + native + sectionLeaf substring 을 모두 처리하므로 단일 경로.

        Args:
            handle: inventory 단위의 handle.

        Returns:
            pl.DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> import dartlab
            >>> dartlab.dossier("005930").get("NT_C_U800100")  # doctest: +SKIP  회사별 노트
        """
        # report apiType handle 은 report parquet 직독(panel 밖 병렬 surface).
        reportKeys = {
            c.dart.key for c in getExtractionConcepts() if isinstance(c.dart, DartSource) and c.dart.surface == "report"
        }
        if handle in reportKeys:
            return self._extractReport(handle)
        # US item handle(form::itemId)은 edgar docs sections 직독(panel 밖 병렬 surface, DART report 대응).
        if self.marketNs == "us" and "::" in handle:
            return _sliceSections(self._loadSectionsDf(), handle)
        board = _loadBoard(self.code, self.marketNs)  # dart/edgar Panel 스위치 SSOT
        if board is None or getattr(board, "height", 0) == 0:
            return None
        return board(handle)

    def materialize(self, *, kinds: tuple[str, ...] | None = None) -> dict[str, pl.DataFrame | None]:
        """인벤토리 전 단위를 Panel 1회 로드로 배치 추출한다 (OOM-safe round-trip).

        get() 는 호출마다 Panel 을 새로 잡아 다수 단위 루프 시 Panel N회 로드(무겁다). materialize 는
        Panel 을 1회 잡고 in-memory board 를 재사용해 모든 handle 을 추출한다. report apiType 는
        report parquet 1회 로드로 apiType 필터.

        Args:
            kinds: 추출할 kind 필터(예 ("note","form")). None 이면 전부.

        Returns:
            {handle: DataFrame|None}.

        Raises:
            없음.

        Example:
            >>> import dartlab
            >>> mats = dartlab.dossier("005930").materialize(kinds=("note",))  # doctest: +SKIP
        """
        from dartlab.frame.inventory import reportInventory

        board = _loadBoard(self.code, self.marketNs)  # 정규화 wide board 1회 로드(인벤토리·추출 공유)
        inv = reportInventory(self.code, marketNs=self.marketNs, board=board)
        reportDf = None
        sectionsDf = None
        loadedSections = False
        out: dict[str, pl.DataFrame | None] = {}
        for u in inv.get("units", []):
            if kinds is not None and u["kind"] not in kinds:
                continue
            handle = u["handle"]
            if u["kind"] == "report":
                if reportDf is None:
                    reportDf = self._loadReportDf()
                out[handle] = self._sliceReport(reportDf, handle)
                continue
            if u["kind"] == "item":
                if not loadedSections:  # sections 1회 로드 후 topic slice (OOM 안전 round-trip)
                    sectionsDf = self._loadSectionsDf()
                    loadedSections = True
                out[handle] = _sliceSections(sectionsDf, handle)
                continue
            out[handle] = board(handle) if board is not None and getattr(board, "height", 0) > 0 else None
        return out

    def _loadReportDf(self) -> pl.DataFrame | None:
        """report parquet 1회 로드."""
        from dartlab.core.dataLoader import _dataDir

        path = _dataDir("report") / f"{self.code}.parquet"
        if not path.exists():
            return None
        try:
            return pl.read_parquet(path)
        except (pl.exceptions.PolarsError, OSError):
            return None

    def _loadSectionsDf(self) -> pl.DataFrame | None:
        """edgar docs sections wide 1회 로드 (US item handle 추출용, topic x period)."""
        from dartlab.providers.edgar.docs.sections.pipeline import sections

        try:
            return sections(self.code)
        except (pl.exceptions.PolarsError, OSError, ValueError):
            return None

    def _sliceReport(self, reportDf: pl.DataFrame | None, apiType: str) -> pl.DataFrame | None:
        """로드된 report df 에서 apiType 슬라이스."""
        if reportDf is None or "apiType" not in reportDf.columns:
            return None
        df = reportDf.filter(pl.col("apiType") == apiType)
        return df if not df.is_empty() else None

    def extract(self, conceptId: str) -> pl.DataFrame | None:
        """개념 1건을 카탈로그 표면 라우팅으로 실제 추출한다.

        note 는 panel canonicalKey, statement 는 panel native, narrative 는 frame.narrative,
        report 는 report parquet(apiType 필터). segment(횡단) 은 None(scan 경로).

        Args:
            conceptId: 카탈로그 conceptId.

        Returns:
            pl.DataFrame 또는 None(미대상/데이터 부재).

        Raises:
            없음.

        Example:
            >>> import dartlab
            >>> dartlab.dossier("005930").extract("note.tax")  # doctest: +SKIP
        """
        concept = getConcept(conceptId)
        if concept is None or not isinstance(concept.dart, DartSource):
            return None
        surface = concept.dart.surface
        if surface == "narrative":
            from dartlab.frame.narrative import extractNarrative

            return extractNarrative(self.code, conceptId, marketNs=self.marketNs)
        if surface in ("note", "statement"):
            board = _loadBoard(self.code, self.marketNs)  # dart/edgar Panel 스위치 SSOT
            if board is None or getattr(board, "height", 0) == 0:
                return None
            return board(concept.dart.key)
        if surface == "report":
            return self._extractReport(concept.dart.key)
        return None  # segmentTable(횡단) 은 scan 경로

    def _extractReport(self, apiType: str) -> pl.DataFrame | None:
        """report parquet 에서 apiType 행을 직독(정형공시 raw). 단건은 로드+슬라이스 위임."""
        return self._sliceReport(self._loadReportDf(), apiType)

    def category(self, category: str) -> dict[str, pl.DataFrame | None]:
        """한 카테고리의 전 개념을 조립해 {conceptId: DataFrame|None} 로 반환한다.

        Args:
            category: 9 대분류 중 하나.

        Returns:
            {conceptId: 추출결과}.

        Raises:
            없음.

        Example:
            >>> import dartlab
            >>> list(dartlab.dossier("005930").category("financialStatement"))  # doctest: +SKIP
        """
        return {c.conceptId: self.extract(c.conceptId) for c in getExtractionConcepts(category=category)}

    def forecastHint(self) -> dict:
        """예측 위임 힌트를 반환한다(워크벤치는 예측 소유 X, L2 위임).

        4계층 단방향: 워크벤치는 재료 정리, 예측은 analysis/quant/macro(L2)가 그 위에서.

        Returns:
            {engine, call, note} 위임 안내.

        Raises:
            없음.

        Example:
            >>> import dartlab
            >>> dartlab.dossier("005930").forecastHint()["engine"]
            'analysis'
        """
        return {
            "engine": "analysis",
            "call": f'dartlab.Company("{self.code}").analysis("financial", "전망")',
            "note": "워크벤치는 재료 정리 전담. 예측/시나리오는 L2(analysis·quant·macro) 위임.",
        }

    def __repr__(self) -> str:
        return f"Dossier({self.code!r}, marketNs={self.marketNs!r})"


def dossier(code: str, *, marketNs: str = "kr") -> Dossier:
    """한 회사의 데이터 워크벤치(Dossier)를 연다.

    Args:
        code: 종목코드/티커.
        marketNs: 시장 ("kr" 기본).

    Returns:
        Dossier (available/extract/category/forecastHint).

    Raises:
        없음.

    Example:
        >>> import dartlab
        >>> d = dartlab.dossier("005930")  # doctest: +SKIP
        >>> d.available()["note"]           # doctest: +SKIP  조직맵
        >>> d.extract("note.tax")           # doctest: +SKIP  단일 추출
    """
    return Dossier(code, marketNs=marketNs)
