"""Notes Scanner — 종목별 notes 구조 패턴 스캔.

2,700종목의 panel parquet에서 notes 항목의 구조 패턴을 추출하여
notesStructure.json을 갱신한다.

사용법::

    from dartlab.providers.mappers.scanner import scanNotes, scanAll

    # 단일 종목 스캔
    result = scanNotes("005930")

    # 전체 종목 스캔 → notesStructure.json 갱신
    stats = scanAll(limit=100)  # 테스트용 100종목
    stats = scanAll()           # 전체 (~2,700종목, 수십 분)
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from dartlab.providers.mappers.common import normalizeName

log = logging.getLogger(__name__)

_STRUCTURE_PATH = Path(__file__).resolve().parent / "mapperData" / "notesStructure.json"

# 비금액 패턴 — pipeline.py의 _NON_AMOUNT_PATTERNS + 추가 발견 패턴
_RATE_PATTERNS = re.compile(
    r"(연이자율|이자율|할인율|수익률|배당률|증가율|성장률|비율|%)",
    re.IGNORECASE,
)

_TEXT_PATTERNS = re.compile(
    r"(기술$|설명$|기술:$|에\s*대한\s*(기술|설명)|내용$|사유$|비고$)",
    re.IGNORECASE,
)

# 외화 관련 항목명 패턴
_FOREIGN_NAME_PATTERNS = re.compile(
    r"(외화|USD|JPY|EUR|GBP|CNY|HKD|달러|엔화|위안)",
    re.IGNORECASE,
)

# alias 합계/소계 변형 접미 — "재고자산" ↔ "재고자산계" ↔ "재고자산합계" 만 alias 후보.
_TOTAL_SUFFIXES = ("계", "합계", "총계", "소계")


def _classifyType(name: str, values: list[str]) -> str:
    """항목명 + 값에서 유형 자동 분류."""
    if _RATE_PATTERNS.search(name):
        return "rate"
    if _TEXT_PATTERNS.search(name):
        return "text"
    # 값에서 % 문자가 지배적이면 rate
    pct_count = sum(1 for v in values if "%" in str(v))
    if pct_count > len(values) * 0.5 and values:
        return "rate"
    return "amount"


def _hasForeignInName(name: str) -> bool:
    """항목명에 외화 관련 키워드가 있는지."""
    return bool(_FOREIGN_NAME_PATTERNS.search(name))


# 노트 제목 행 정규화 — "8. 재고자산 (연결)" → "재고자산" (번호·scope 접미 strip, 태그 제거).
_NOTE_NUM_RE = re.compile(r"^\s*\d+[.)]\s*")
_NOTE_SCOPE_RE = re.compile(r"\s*\((?:연결|별도)\)\s*$")
_PERIOD_COL_RE = re.compile(r"^\d{4}Q[1-4]$")


def _noteTitleFromContent(content: str | None) -> str:
    """노트 leaf content 의 제목(번호·scope·태그 strip). 비제목(표·산문)이면 "".

    Args:
        content: panel 노트 행 content (raw XML 또는 plain).

    Returns:
        정규화 제목 (예 "재고자산", "영업부문") 또는 "" (제목 아님).

    Example:
        >>> _noteTitleFromContent("<P>8. 재고자산 (연결)</P>")
        '재고자산'
        >>> _noteTitleFromContent("<TABLE>취득원가 ...</TABLE>")
        ''
    """
    if not content:
        return ""
    s = re.sub(r"<[^>]+>", " ", str(content))
    s = re.sub(r"\s+", " ", s).strip()
    if not s or len(s) > 40 or any(ch.isdigit() for ch in s[-8:]):
        return ""  # 제목 행은 짧고 끝이 숫자가 아님 (표·산문 배제)
    s = _NOTE_SCOPE_RE.sub("", _NOTE_NUM_RE.sub("", s)).strip()
    return s[:24] if 1 < len(s) <= 30 else ""


def scanNotes(stockCode: str) -> dict[str, dict[str, Any]]:
    """단일 종목의 notes 구조 패턴 추출 — panel SSOT(NT_ 행 contentRaw) 직독.

    Panel(code) 을 1회 read 해 NT_ 표 행을 ``cellsFromContent`` 로 분해, 라인아이템(label)을
    수집·분류한다. category = 노트 제목(content 제목행 discover), canonicalKey = NT_ 코드,
    noteShape = axisPath 멤버 유무로 composition/lineitem. 최근 연간(Q4) 5기간 + 연결만.

    Args:
        stockCode: 종목코드 (KR 6자리).

    Returns:
        {항목명: {"type", "category", "canonicalKey", "noteShape", "foreignCurrency",
        "count", "years": set[str]}}. import/데이터 실패 시 빈 dict.

    Example:
        >>> scanNotes("005930")  # doctest: +SKIP
        {'재고자산': {'type': 'amount', 'category': '재고자산', 'canonicalKey': 'NT_D826380', ...}}

    Raises:
        없음 — import/데이터 로드 실패(파일·메모리)는 빈 dict 로 흡수한다.
    """
    try:
        import polars as pl

        from dartlab.providers.dart.panel import Panel
        from dartlab.providers.dart.panel.build.cell import cellsFromContent
    except ImportError:
        return {}

    try:
        p = Panel(stockCode)
    except (FileNotFoundError, OSError, ValueError, MemoryError):
        return {}
    if p is None or getattr(p, "height", 0) == 0:
        return {}

    nt = p.filter(pl.col("disclosureKey").fill_null("").str.starts_with("NT_"))
    if nt.is_empty():
        return {}

    periodCols = [c for c in nt.columns if _PERIOD_COL_RE.match(c)]
    annual = (
        sorted((c for c in periodCols if c.endswith("Q4")), reverse=True)[:5] or sorted(periodCols, reverse=True)[:5]
    )
    if not annual:
        return {}

    # 노트가족(disclosureKey)별 제목 — content 제목행 discover (sectionLeaf 는 일반명뿐).
    titles: dict[str, str] = {}
    for r in nt.iter_rows(named=True):
        dk = r.get("disclosureKey")
        if not dk or dk in titles:
            continue
        for c in annual:
            t = _noteTitleFromContent(r.get(c))
            if t:
                titles[dk] = t
                break

    items: dict[str, dict[str, Any]] = {}
    for r in nt.filter(pl.col("leafType") == "table").iter_rows(named=True):
        if (r.get("scope") or "consolidated") != "consolidated":
            continue
        dk = r.get("disclosureKey") or ""
        category = titles.get(dk, dk)
        rcept = r.get("rceptNo") or ""
        for c in annual:
            content = r.get(c)
            if not content:
                continue
            year = c[:4]
            try:
                cells = list(
                    cellsFromContent(content, statement=dk, scope="consolidated", period=c, code=stockCode, rcept=rcept)
                )
            except (ValueError, TypeError, KeyError):
                continue
            if not cells:
                continue
            hasAxis = any((cell.get("axisPath") or "") not in ("", "ConsolidatedMember") for cell in cells)
            shape = "composition" if hasAxis else "lineitem"
            for cell in cells:
                name = normalizeName(str(cell.get("label") or ""))
                if not name:
                    continue
                entry = items.get(name)
                if entry is None:
                    entry = items[name] = {
                        "type": _classifyType(name, [str(cell.get("valueRaw") or "")]),
                        "category": category,
                        "canonicalKey": dk,
                        "noteShape": shape,
                        "foreignCurrency": _hasForeignInName(name),
                        "count": 0,
                        "years": set(),
                    }
                entry["count"] += 1
                entry["years"].add(year)
    return items


def discoverAliases(
    stockCodes: list[str],
    *,
    minSupport: int = 3,
) -> dict[str, str]:
    """다종목 스캔으로 alias 후보 자동 탐지.

    같은 category에서 상호배타적으로 출현하는 항목 쌍을 alias로 제안.
    예: "재고자산" (2025-2024)과 "제품및상품" (2023-2021) → 같은 것.

    Args:
        stockCodes: 스캔 대상 종목 리스트
        minSupport: 최소 지지 종목 수 (이 이상에서 발견돼야 alias 등록)

    Returns:
        {variant: canonical} — alias 후보

    Example:
        >>> discoverAliases(["005930", "000660"], minSupport=2)  # doctest: +SKIP
        {'재고자산계': '재고자산'}

    Raises:
        없음 — 종목별 스캔 실패(MemoryError/OSError)는 건너뛴다.
    """

    # category별 항목 출현 패턴 수집
    # {category: {item: {years: set, companies: int}}}
    catItems: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"years": set(), "companies": 0}))

    for code in stockCodes:
        try:
            items = scanNotes(code)
        except (MemoryError, OSError):
            continue

        for name, info in items.items():
            cat = info.get("category", "")
            if not cat:
                continue
            entry = catItems[cat][name]
            entry["years"] |= info.get("years", set())
            entry["companies"] += 1

    # 상호배타적 쌍 탐지 — 같은 종류의 "합계/총계" 행끼리만
    # 예: "재고자산" vs "제품및상품" vs "재고자산계" (합계 행 역할)
    aliases: dict[str, str] = {}

    # alias 탐지 대상 category — 이름 4글자 이상 (법인세, 리스 등 짧은 건 과잉매칭)
    _ALIAS_CATEGORIES = {"재고자산", "차입금", "충당부채", "매출채권", "투자부동산", "무형자산"}

    for cat, items in catItems.items():
        catName = cat.replace(" ", "")
        if catName not in _ALIAS_CATEGORIES:
            continue

        # category 이름을 포함하는 짧은 항목만 (합계/총계 역할)
        candidates = [
            (name, data)
            for name, data in items.items()
            if data["companies"] >= minSupport and catName in name and len(name) <= 20
        ]

        for i, (name1, data1) in enumerate(candidates):
            for name2, data2 in candidates[i + 1 :]:
                years1 = data1["years"]
                years2 = data2["years"]

                # 상호배타적: 연도 겹침 없음
                if years1 & years2:
                    continue

                # 합치면 최소 3년 커버
                if len(years1 | years2) < 3:
                    continue

                # 이름 길이/관계 조건
                shorter = min(name1, name2, key=len)
                longer = max(name1, name2, key=len)
                if len(shorter) <= 3:
                    continue

                # 핵심 규칙: suffix 변형만 alias ("재고자산" ↔ "재고자산계" ↔ "재고자산합계").
                isVariant = False
                for sfx in _TOTAL_SUFFIXES:
                    base1 = name1.removesuffix(sfx) if name1.endswith(sfx) else None
                    base2 = name2.removesuffix(sfx) if name2.endswith(sfx) else None
                    # 한쪽이 suffix 제거하면 다른쪽과 같아짐
                    if base1 and base1 == name2:
                        isVariant = True
                        break
                    if base2 and base2 == name1:
                        isVariant = True
                        break
                    # 둘 다 suffix가 있고 base가 같으면
                    if base1 and base2 and base1 == base2:
                        isVariant = True
                        break
                if not isVariant:
                    continue

                # 더 많은 종목에서 출현한 쪽이 canonical
                if data1["companies"] >= data2["companies"]:
                    canonical, variant = name1, name2
                else:
                    canonical, variant = name2, name1

                aliases[variant] = canonical
                log.info("alias 발견: %s → %s (category=%s)", variant, canonical, cat)

    return aliases


def scanAll(
    limit: int | None = None,
    output: Path | None = None,
) -> dict[str, Any]:
    """전체 종목 notes 구조 스캔 → notesStructure.json 갱신.

    Args:
        limit: 스캔 종목 수 제한 (None=전체)
        output: 결과 저장 경로 (None=기본 경로)

    Returns:
        {"scanned": int, "newItems": int, "updatedItems": int, "totalItems": int}

    Example:
        >>> scanAll(limit=100)  # doctest: +SKIP
        {'scanned': 100, 'newItems': 12, 'updatedItems': 88, ...}

    Raises:
        없음 — 데이터 디렉터리 부재 시 scanned=0 stats 로 반환.
    """
    outPath = output or _STRUCTURE_PATH

    # 기존 구조 로드
    existing: dict[str, Any] = {"_metadata": {}, "items": {}}
    if outPath.exists():
        existing = json.loads(outPath.read_text(encoding="utf-8"))

    existingItems = existing.get("items", {})

    # 종목 목록 가져오기
    try:
        from dartlab.core.dataLoader import _dataDir

        dataDir = _dataDir("panel")
    except (ImportError, KeyError):
        log.warning("데이터 디렉토리 없음 — 스캔 불가")
        return {"scanned": 0, "newItems": 0, "updatedItems": 0, "totalItems": len(existingItems)}

    if not dataDir.exists():
        log.warning("panel 디렉토리 없음: %s", dataDir)
        return {"scanned": 0, "newItems": 0, "updatedItems": 0, "totalItems": len(existingItems)}

    stockCodes = sorted(p.stem for p in dataDir.glob("*.parquet") if len(p.stem) == 6 and p.stem.isdigit())
    if limit:
        stockCodes = stockCodes[:limit]

    log.info("notes 구조 스캔 시작: %d종목", len(stockCodes))

    # 종목별 항목 출현 카운트
    globalCounts: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"type": "amount", "category": "", "foreignCurrency": False, "companyCount": 0}
    )

    scanned = 0
    for i, code in enumerate(stockCodes):
        try:
            items = scanNotes(code)
        except (MemoryError, OSError):
            log.warning("스캔 실패 (메모리): %s", code)
            continue

        for name, info in items.items():
            entry = globalCounts[name]
            entry["companyCount"] += 1
            # 유형은 다수결
            if info["type"] != "amount":
                entry["type"] = info["type"]
            if info["foreignCurrency"]:
                entry["foreignCurrency"] = True
            if info["category"] and not entry["category"]:
                entry["category"] = info["category"]

        scanned += 1
        if (i + 1) % 100 == 0:
            log.info("  스캔 진행: %d/%d", i + 1, len(stockCodes))

        # 메모리 안전: 500종목마다 gc
        if (i + 1) % 500 == 0:
            import gc

            gc.collect()

    # 기존 + 신규 병합
    newCount = 0
    updatedCount = 0
    for name, info in globalCounts.items():
        freq = info["companyCount"] / scanned if scanned > 0 else 0.0
        entry = {
            "type": info["type"],
            "category": info["category"],
            "foreignCurrency": info["foreignCurrency"],
            "frequency": round(freq, 4),
            "skip": info["type"] in ("rate", "text"),
        }
        if name in existingItems:
            # 기존 항목 — frequency만 갱신, type은 기존 유지 (수동 보정 보존)
            existingItems[name]["frequency"] = entry["frequency"]
            if existingItems[name].get("category") == "":
                existingItems[name]["category"] = entry["category"]
            updatedCount += 1
        else:
            existingItems[name] = entry
            newCount += 1

    # alias 자동 탐지 + 흡수
    existingAliases = existing.get("aliases", {})
    if scanned >= 10:  # 최소 10종목 이상 스캔했을 때만
        discovered = discoverAliases(stockCodes[: min(100, len(stockCodes))], minSupport=3)
        newAliasCount = 0
        for variant, canonical in discovered.items():
            if variant not in existingAliases:
                existingAliases[variant] = canonical
                newAliasCount += 1
        if newAliasCount:
            log.info("alias %d건 자동 흡수", newAliasCount)
    else:
        newAliasCount = 0

    # 저장
    result = {
        "_metadata": {
            "version": "1.1.0",
            "lastScan": datetime.now().strftime("%Y-%m-%d"),
            "companiesScanned": scanned,
            "description": "notes 항목 구조 매퍼 — Scanner 자동 생성",
        },
        "keywords": existing.get("keywords", {}),
        "items": dict(sorted(existingItems.items())),
        "aliases": existingAliases,
    }
    outPath.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    stats = {
        "scanned": scanned,
        "newItems": newCount,
        "updatedItems": updatedCount,
        "newAliases": newAliasCount,
        "totalItems": len(existingItems),
        "totalAliases": len(existingAliases),
    }
    log.info("스캔 완료: %s", stats)
    return stats
