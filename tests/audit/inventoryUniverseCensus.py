"""인벤토리 완전성 census: 전 종목 unit 전수 열거 vs 카탈로그 head (2-tier 완전성).

`extractionCoverageCensus.py`(개념 표본 커버리지)의 형제. 이쪽은 **전 우주(2930 KR panel + 전 US docs)를
전수 훑어** 실재하는 모든 추출 unit(note/form/narrative/table/statement · US Item)을 빈도로 집계하고, 어느
것이 카탈로그 head 인지 대조한다. 손 표본 아니라 전 종목 실측이라 카탈로그 생존편향을 원천 차단한다.

**2-tier 완전성 정의(전문에이전트 도메인 감사)**:
- Tier A(mechanical): 우주의 모든 unit 이 inventory 로 열거·round-trip 추출 가능(mechanicalTotal).
- Tier B(curated head): 고빈도 표준 unit 만 카탈로그 first-class. headCoverage = 카탈로그된 head.
"완전 = (Tier A 열거 100%, Tier B head 커버) + 잔여 tail 명시" 이지 손 카탈로그 100% 아님.

**OOM 안전(CLAUDE.md Polars Rust 힙 가드)**: reportInventory/Panel 을 우주에 돌리지 않는다(회사당 200~500MB).
파일당 식별 문자열 컬럼만 columnar projection + drop + 주기 gc. baseline(`_baselines/inventoryUniverse.json`)은
부채 원장 = 신규 gap/감소만 회귀.

실행::

    uv run python -X utf8 tests/audit/inventoryUniverseCensus.py            # 원장 출력
    uv run python -X utf8 tests/audit/inventoryUniverseCensus.py --write    # baseline 갱신
    uv run python -X utf8 tests/audit/inventoryUniverseCensus.py --limit 300 # 표본(빠른 확인)
"""

from __future__ import annotations

import argparse
import gc
import json
import re
from collections import Counter
from pathlib import Path

import polars as pl

from dartlab.core.extractionCatalog import DartSource, edgarItemCoverage, getExtractionConcepts

_BASELINE = Path(__file__).resolve().parent / "_baselines" / "inventoryUniverse.json"
_NUM_PREFIX = re.compile(r"^\s*[0-9IVXLC]+[.)]\s*")
_STATEMENT_KEYS = frozenset({"BS", "IS", "IS1", "IS2", "IS3", "CF", "CIS", "EF", "SCE"})


def _normTitle(title: str) -> str:
    """제목 번호 접두 제거 = 회사 간 안정 키."""
    return _NUM_PREFIX.sub("", (title or "").strip()).strip()


def _dirs() -> tuple[Path, Path, Path]:
    """dart panel/report + edgar docs 디렉터리 해소 (edgarPanel 형제로 docs 위치)."""
    from dartlab.core.dataLoader import _dataDir

    panDir = _dataDir("panel")
    repDir = _dataDir("report")
    docsDir = _dataDir("edgarPanel").parent / "docs"  # data/edgar/panel -> data/edgar/docs
    return panDir, repDir, docsDir


def surveyKr(panDir: Path, repDir: Path, limit: int | None) -> dict:
    """KR panel+report 전수를 훑어 note/form/narrative/table/api unit 을 회사 빈도로 집계한다.

    Args:
        panDir: dart panel 디렉터리.
        repDir: dart report 디렉터리.
        limit: 표본 상한(None=전수).

    Returns:
        {n, notes, forms, narr, tables, apis} (각 Counter: unitKey -> 보유 회사수).

    Raises:
        없음.

    Example:
        >>> surveyKr(Path("data/dart/panel"), Path("data/dart/report"), 10)  # doctest: +SKIP
    """
    notes: Counter = Counter()
    forms: Counter = Counter()
    narr: Counter = Counter()
    tables: Counter = Counter()
    apis: Counter = Counter()
    files = sorted(panDir.glob("*.parquet"))
    if limit is not None:
        files = files[:limit]
    for i, pp in enumerate(files):
        code = pp.stem
        try:
            df = pl.read_parquet(pp, columns=["disclosureKey", "sectionLeaf", "blockLeaf", "leafType"])
        except (pl.exceptions.PolarsError, OSError):
            continue
        dk = df.filter(pl.col("disclosureKey").is_not_null() & (pl.col("disclosureKey") != ""))
        seenN, seenF = set(), set()
        for k in dk.get_column("disclosureKey").unique().to_list():
            if k in _STATEMENT_KEYS:
                continue
            if k.startswith("NT_"):
                seenN.add(k[:-1] if k[-1].isdigit() else k)
            else:
                seenF.add(re.sub(r"\d+$", "", k))
        notes.update(seenN)
        forms.update(seenF)
        na = df.filter(pl.col("disclosureKey").is_null())
        narr.update({_normTitle(x) for x in na.get_column("sectionLeaf").drop_nulls().to_list() if x} - {""})
        tb = df.filter(pl.col("leafType") == "table")
        tables.update(
            {_normTitle(x) for x in tb.get_column("blockLeaf").drop_nulls().to_list() if x and 1 < len(x) <= 40} - {""}
        )
        rp = repDir / f"{code}.parquet"
        if rp.exists():
            try:
                if "apiType" in pl.scan_parquet(rp).collect_schema().names():
                    at = pl.read_parquet(rp, columns=["apiType"]).get_column("apiType")
                    apis.update({x for x in at.drop_nulls().to_list() if x})
            except (pl.exceptions.PolarsError, OSError):
                pass
        del df
        if (i + 1) % 50 == 0:
            gc.collect()
    return {"n": len(files), "notes": notes, "forms": forms, "narr": narr, "tables": tables, "apis": apis}


def surveyUs(docsDir: Path, limit: int | None) -> dict:
    """US docs 전수를 훑어 SEC Item topicId 를 filer 빈도로 집계한다 (network-free, mapSectionTitle).

    Args:
        docsDir: edgar docs 디렉터리.
        limit: 표본 상한(None=전수).

    Returns:
        {n, items} (items Counter: topicId -> 보유 filer 수).

    Raises:
        없음.

    Example:
        >>> surveyUs(Path("data/edgar/docs"), 10)  # doctest: +SKIP
    """
    from dartlab.providers.edgar.docs.sections.mapper import mapSectionTitle

    items: Counter = Counter()
    files = sorted(docsDir.glob("*.parquet")) if docsDir.exists() else []
    if limit is not None:
        files = files[:limit]
    for i, pp in enumerate(files):
        try:
            df = pl.read_parquet(pp, columns=["form_type", "section_title"])
        except (pl.exceptions.PolarsError, OSError):
            continue
        seen = set()
        for row in df.drop_nulls().unique().iter_rows(named=True):
            form = str(row["form_type"] or "")
            title = str(row["section_title"] or "")
            if not form or not title:
                continue
            topic = mapSectionTitle(form, title)
            seen.add(topic.split("::", 1)[1] if "::" in topic else topic)
        items.update(seen)
        del df
        if (i + 1) % 50 == 0:
            gc.collect()
    return {"n": len(files), "items": items}


def _catalogNoteFamilies() -> set[str]:
    """카탈로그 note canonicalKey family 집합 (커버리지 대조용)."""
    return {c.dart.key[:-1] for c in getExtractionConcepts(category="note") if isinstance(c.dart, DartSource)}


def _catalogApiKeys() -> set[str]:
    """카탈로그 report apiType 집합."""
    return {
        c.dart.key for c in getExtractionConcepts() if isinstance(c.dart, DartSource) and c.dart.surface == "report"
    }


def run(limit: int | None = None) -> dict:
    """전 종목 unit 전수 census 실행 후 2-tier 완전성 원장을 산출한다.

    Args:
        limit: 시장별 표본 상한(None=전수. 빠른 확인용 표본).

    Returns:
        {kr, us, rollup} 완전성 원장 dict.

    Raises:
        없음.

    Example:
        >>> run(limit=50)  # doctest: +SKIP
    """
    panDir, repDir, docsDir = _dirs()
    if not panDir.exists():
        return {"error": f"panel dir 부재: {panDir}"}
    kr = surveyKr(panDir, repDir, limit)
    us = surveyUs(docsDir, limit)

    catNote = _catalogNoteFamilies()
    catApi = _catalogApiKeys()
    noteUncat = sorted(((k, n) for k, n in kr["notes"].items() if k not in catNote), key=lambda x: -x[1])
    apiUncat = sorted(((k, n) for k, n in kr["apis"].items() if k not in catApi), key=lambda x: -x[1])
    itemCov = edgarItemCoverage(dict(us["items"]))

    krRollup = {
        "companies": kr["n"],
        "noteFamiliesPresent": len(kr["notes"]),
        "noteFamiliesCatalogued": len(kr["notes"]) - len(noteUncat),
        "formsPresent": len(kr["forms"]),
        "narrativeTitlesPresent": len(kr["narr"]),
        "tableTitlesPresent": len(kr["tables"]),
        "apiTypesPresent": len(kr["apis"]),
        "apiTypesCatalogued": len(kr["apis"]) - len(apiUncat),
        # Tier A: 열거된 distinct unit 총합(모두 inventory round-trip 대상).
        "mechanicalDistinctUnits": len(kr["notes"]) + len(kr["forms"]) + len(kr["narr"]) + len(kr["tables"]),
    }
    usRollup = {
        "filers": us["n"],
        "itemTopicsPresent": itemCov["present"],
        "itemTopicsCatalogued": itemCov["catalogued"],
    }
    return {
        "limit": limit,
        "kr": krRollup,
        "us": usRollup,
        "krNoteUncataloguedTop": noteUncat[:30],
        "krApiUncatalogued": apiUncat,
        "usItemUncataloguedTop": itemCov["uncatalogued"][:30],
        "krNarrativeTop": kr["narr"].most_common(40),
        "krFormsTop": kr["forms"].most_common(40),
        "usItemsTop": us["items"].most_common(50),
    }


def writeBaseline(result: dict) -> Path:
    """census 원장을 baseline 부채원장으로 저장한다 (신규 gap/감소만 회귀).

    Args:
        result: run() 산출 dict.

    Returns:
        저장 경로.

    Raises:
        없음.

    Example:
        >>> writeBaseline(run(limit=50))  # doctest: +SKIP
    """
    _BASELINE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": "인벤토리 완전성 부채 원장(2-tier). 전 종목 unit 전수 vs 카탈로그 head. --write 로 갱신.",
        "kr": result.get("kr", {}),
        "us": result.get("us", {}),
        "krNoteUncataloguedTop": result.get("krNoteUncataloguedTop", []),
        "krApiUncatalogued": result.get("krApiUncatalogued", []),
        "usItemUncataloguedTop": result.get("usItemUncataloguedTop", []),
    }
    _BASELINE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return _BASELINE


def main() -> None:
    """CLI 진입점: census 실행 후 2-tier 완전성 원장 출력 (--write 면 baseline 갱신)."""
    ap = argparse.ArgumentParser(description="인벤토리 완전성 census (전 종목 unit 전수)")
    ap.add_argument("--write", action="store_true", help="baseline 원장 갱신")
    ap.add_argument("--limit", type=int, default=None, help="시장별 표본 상한(빠른 확인)")
    args = ap.parse_args()

    result = run(limit=args.limit)
    if result.get("error"):
        print("census 불가:", result["error"])
        return
    kr, us = result["kr"], result["us"]
    print("=== KR 완전성 (전 종목", kr["companies"], "사) ===")
    print(f"  note family: 카탈로그 {kr['noteFamiliesCatalogued']} / 실재 {kr['noteFamiliesPresent']}")
    print(
        f"  narrative 제목: {kr['narrativeTitlesPresent']} · form: {kr['formsPresent']} · table: {kr['tableTitlesPresent']}"
    )
    print(f"  apiType: 카탈로그 {kr['apiTypesCatalogued']} / 실재 {kr['apiTypesPresent']}")
    print(f"  Tier A mechanical distinct units(모두 열거·round-trip): {kr['mechanicalDistinctUnits']}")
    print("=== US 완전성 (filer", us["filers"], ") ===")
    print(f"  SEC Item topic: 카탈로그 {us['itemTopicsCatalogued']} / 실재 {us['itemTopicsPresent']}")
    top = result["krNoteUncataloguedTop"][:8]
    if top:
        print("  KR 미카탈로그 note 상위:", ", ".join(f"{k}({n})" for k, n in top))
    if result["usItemUncataloguedTop"]:
        print("  US 미카탈로그 item 상위:", ", ".join(f"{k}({n})" for k, n in result["usItemUncataloguedTop"][:8]))
    if args.write:
        print("baseline 갱신:", writeBaseline(result))


if __name__ == "__main__":
    main()
