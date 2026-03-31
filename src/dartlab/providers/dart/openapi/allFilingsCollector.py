"""전체 공시 원문 수집기 — 2단계 증분 수집.

Phase 1: 목록 수집 (collectMeta) — 일자별 API 1회, 매우 가볍다.
Phase 2: 원문 수집 (fillContent) — 건당 API 1회, 키 소비 큼.

목록을 먼저 전부 모은 뒤, 원문은 키 여유 있을 때 점진적으로 채운다.

사용법::

    from dartlab.providers.dart.openapi.allFilingsCollector import (
        collectMetaRange, fillContent, stats
    )

    # Phase 1: 목록만 빠르게 (5년치도 키 1개로 가능)
    collectMetaRange("20210401", "20260330")

    # Phase 2: 원문 채우기 (일자별, 키 여유 있을 때)
    fillContent("20260327")
    fillContentAll()  # 미수집 원문 전체
"""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import polars as pl
from bs4 import BeautifulSoup

from dartlab import config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.providers.dart.openapi.client import DartClient
from dartlab.providers.dart.openapi.disclosure import listFilings
from dartlab.providers.dart.openapi.zipCollector import (
    _collectOneZip,
    _tableToMarkdown,
    _RE_MULTI_NEWLINE,
)

# ── 상수 ──

_ALLFILINGS_DIR_KEY = "allFilings"
_META_SUFFIX = "_meta"  # 목록만: 20260327_meta.parquet
                        # 원문포함: 20260327.parquet

# ── 내부 유틸 ──


def _allFilingsDir() -> Path:
    """allFilings parquet 저장 디렉토리."""
    root = Path(_cfg.dataDir)
    d = root / DATA_RELEASES[_ALLFILINGS_DIR_KEY]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _htmlToPlainText(html: str) -> str:
    """HTML 전문 → plain text (section 구조 없는 공시 fallback)."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()

    for table in soup.find_all("table"):
        md = _tableToMarkdown(table)
        if md:
            table.replace_with(BeautifulSoup(f"\n\n{md}\n\n", "lxml"))
        else:
            table.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "li"]):
        p.insert_after("\n")

    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = _RE_MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def _collectOneDoc(client: DartClient, rceptNo: str) -> list[dict]:
    """단일 공시 원문 수집. section 구조가 있으면 섹션별, 없으면 전문 1개."""
    sections = _collectOneZip(client, rceptNo)
    if sections and len(sections) > 0:
        return sections

    try:
        raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    except (RuntimeError, OSError):
        return []

    if raw is None:
        return []

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        return []

    names = zf.namelist()
    if not names:
        return []

    largest = max(names, key=lambda n: zf.getinfo(n).file_size)
    content = zf.read(largest)

    htmlContent = None
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            htmlContent = content.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if htmlContent is None:
        htmlContent = content.decode("utf-8", errors="replace")

    text = _htmlToPlainText(htmlContent)
    if not text.strip():
        return []

    return [{"order": 0, "title": "(전문)", "content": text}]


# ═══════════════════════════════════════════
# Phase 1: 목록 수집 (가볍다 — 일자당 API ~15회)
# ═══════════════════════════════════════════


def collectMetaDay(
    date: str,
    *,
    client: DartClient | None = None,
    corpClasses: list[str] | None = None,
    showProgress: bool = True,
) -> pl.DataFrame | None:
    """하루치 공시 목록만 수집 → _meta.parquet 저장.

    이미 목록이 있거나 원문까지 완료된 날짜는 건너뛴다.
    """
    if client is None:
        client = DartClient()

    if corpClasses is None:
        corpClasses = ["Y", "K"]

    outDir = _allFilingsDir()
    metaPath = outDir / f"{date}{_META_SUFFIX}.parquet"
    fullPath = outDir / f"{date}.parquet"

    # 원문까지 완료됐거나 목록이 있으면 건너뜀
    if fullPath.exists():
        if showProgress:
            print(f"[{date}] 원문 수집 완료됨")
        return None
    if metaPath.exists():
        if showProgress:
            df = pl.read_parquet(metaPath)
            print(f"[{date}] 목록 있음 ({df.height}건)")
        return None

    meta = listFilings(client, start=date, end=date, fetchAll=True)
    if meta.height == 0:
        if showProgress:
            print(f"[{date}] 공시 없음 (휴일)")
        return None

    if corpClasses:
        meta = meta.filter(pl.col("corp_cls").is_in(corpClasses))

    if meta.height == 0:
        if showProgress:
            print(f"[{date}] 상장사 공시 없음")
        return None

    # 저장
    tmpPath = metaPath.with_suffix(".parquet.tmp")
    meta.write_parquet(tmpPath)
    tmpPath.rename(metaPath)

    if showProgress:
        print(f"[{date}] 목록 {meta.height}건 저장")

    return meta


def collectMetaRange(
    startDate: str,
    endDate: str,
    *,
    client: DartClient | None = None,
    corpClasses: list[str] | None = None,
    showProgress: bool = True,
) -> int:
    """날짜 범위 목록 일괄 수집. 최신→과거 순. 매우 가볍다.

    Returns
    -------
    int
        수집된 날짜 수.
    """
    from datetime import datetime, timedelta

    if client is None:
        client = DartClient()

    start = datetime.strptime(startDate, "%Y%m%d")
    end = datetime.strptime(endDate, "%Y%m%d")

    dates = []
    current = end
    while current >= start:
        dates.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)

    collected = 0
    for i, date in enumerate(dates):
        if showProgress and (i + 1) % 10 == 0:
            print(f"--- 목록 진행: {i + 1}/{len(dates)} ---")
        result = collectMetaDay(
            date, client=client, corpClasses=corpClasses, showProgress=showProgress,
        )
        if result is not None:
            collected += 1

    if showProgress:
        print(f"\n목록 수집 완료: {collected}일")

    return collected


# ═══════════════════════════════════════════
# Phase 2: 원문 채우기 (무겁다 — 건당 API 1회)
# ═══════════════════════════════════════════


def fillContent(
    date: str,
    *,
    client: DartClient | None = None,
    showProgress: bool = True,
) -> pl.DataFrame | None:
    """하루치 목록의 원문을 채운다. _meta.parquet → .parquet 승격.

    이미 원문이 있는 날짜는 건너뛴다.
    """
    if client is None:
        client = DartClient()

    outDir = _allFilingsDir()
    metaPath = outDir / f"{date}{_META_SUFFIX}.parquet"
    fullPath = outDir / f"{date}.parquet"

    # 원문 완료 → 건너뜀
    if fullPath.exists():
        if showProgress:
            print(f"[{date}] 원문 이미 완료")
        return None

    # 목록 없음
    if not metaPath.exists():
        if showProgress:
            print(f"[{date}] 목록 없음 (먼저 collectMetaDay 실행)")
        return None

    meta = pl.read_parquet(metaPath)
    total = meta.height

    if showProgress:
        print(f"[{date}] {total}건 원문 수집 시작")

    allRows: list[dict] = []
    success = empty = 0

    for idx, row in enumerate(meta.iter_rows(named=True)):
        rceptNo = row["rcept_no"]
        sections = _collectOneDoc(client, rceptNo)

        if sections:
            success += 1
            for s in sections:
                allRows.append({
                    "corp_code": row["corp_code"],
                    "corp_name": row["corp_name"],
                    "stock_code": row.get("stock_code", ""),
                    "corp_cls": row["corp_cls"],
                    "rcept_dt": row["rcept_dt"],
                    "rcept_no": rceptNo,
                    "report_nm": row["report_nm"],
                    "flr_nm": row.get("flr_nm", ""),
                    "section_order": s["order"],
                    "section_title": s["title"],
                    "section_content": s["content"],
                })
        else:
            empty += 1
            allRows.append({
                "corp_code": row["corp_code"],
                "corp_name": row["corp_name"],
                "stock_code": row.get("stock_code", ""),
                "corp_cls": row["corp_cls"],
                "rcept_dt": row["rcept_dt"],
                "rcept_no": rceptNo,
                "report_nm": row["report_nm"],
                "flr_nm": row.get("flr_nm", ""),
                "section_order": 0,
                "section_title": "",
                "section_content": None,
            })

        if showProgress and (idx + 1) % 100 == 0:
            print(f"  [{idx + 1}/{total}] 성공={success} 빈={empty}")

    if not allRows:
        return None

    df = pl.DataFrame(allRows).with_columns(
        pl.col("section_order").cast(pl.Int32),
    )

    # 원자적 저장 → .parquet (원문 완료)
    tmpPath = fullPath.with_suffix(".parquet.tmp")
    df.write_parquet(tmpPath)
    tmpPath.rename(fullPath)

    # _meta 제거 (승격 완료)
    if metaPath.exists():
        metaPath.unlink()

    if showProgress:
        print(f"[{date}] 완료: {success}건 성공, {empty}건 빈, "
              f"{df.height}행, {fullPath.stat().st_size / 1024 / 1024:.1f}MB")

    return df


def fillContentAll(
    *,
    client: DartClient | None = None,
    showProgress: bool = True,
) -> int:
    """목록만 있는 날짜 전체의 원문을 채운다. 최신순.

    Returns
    -------
    int
        원문 수집 완료한 날짜 수.
    """
    if client is None:
        client = DartClient()

    pending = pendingDates()
    if not pending:
        if showProgress:
            print("원문 미수집 날짜 없음")
        return 0

    if showProgress:
        print(f"원문 미수집 {len(pending)}일 처리 시작")

    filled = 0
    for i, date in enumerate(pending):
        if showProgress:
            print(f"\n=== [{i + 1}/{len(pending)}] ===")
        try:
            result = fillContent(date, client=client, showProgress=showProgress)
            if result is not None:
                filled += 1
        except Exception as e:
            if showProgress:
                print(f"[{date}] 에러: {e}")
            break  # API 한도 초과 등이면 중단

    if showProgress:
        print(f"\n원문 수집 완료: {filled}일")

    return filled


# ═══════════════════════════════════════════
# 조회/통계
# ═══════════════════════════════════════════


def collectedDates() -> list[str]:
    """원문 수집 완료된 날짜 목록 (최신순)."""
    outDir = _allFilingsDir()
    dates = sorted(
        [p.stem for p in outDir.glob("*.parquet")
         if len(p.stem) == 8 and p.stem.isdigit()],
        reverse=True,
    )
    return dates


def pendingDates() -> list[str]:
    """목록만 있고 원문 미수집인 날짜 목록 (최신순)."""
    outDir = _allFilingsDir()
    dates = sorted(
        [p.stem.replace(_META_SUFFIX, "")
         for p in outDir.glob(f"*{_META_SUFFIX}.parquet")],
        reverse=True,
    )
    return dates


def loadDay(date: str) -> pl.DataFrame | None:
    """수집된 하루치 데이터 로드."""
    path = _allFilingsDir() / f"{date}.parquet"
    if not path.exists():
        return None
    return pl.read_parquet(path)


def loadAll() -> pl.DataFrame:
    """원문 수집 완료된 전체 데이터 로드."""
    outDir = _allFilingsDir()
    files = sorted(f for f in outDir.glob("*.parquet")
                   if _META_SUFFIX not in f.stem)
    if not files:
        return pl.DataFrame()
    return pl.scan_parquet(files).collect()


def stats() -> dict:
    """수집 현황 통계."""
    completed = collectedDates()
    pending = pendingDates()

    outDir = _allFilingsDir()
    totalSize = 0
    totalRows = 0
    totalFilings = 0

    for d in completed:
        path = outDir / f"{d}.parquet"
        totalSize += path.stat().st_size
        df = pl.scan_parquet(path).select("rcept_no").collect()
        totalRows += df.height
        totalFilings += df["rcept_no"].n_unique()

    pendingFilings = 0
    for d in pending:
        path = outDir / f"{d}{_META_SUFFIX}.parquet"
        df = pl.scan_parquet(path).select("rcept_no").collect()
        pendingFilings += df["rcept_no"].n_unique()

    return {
        "completedDays": len(completed),
        "pendingDays": len(pending),
        "filings": totalFilings,
        "pendingFilings": pendingFilings,
        "rows": totalRows,
        "sizeMb": round(totalSize / 1024 / 1024, 1),
        "firstDate": completed[-1] if completed else None,
        "lastDate": completed[0] if completed else None,
    }
