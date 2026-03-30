"""전체 공시 원문 수집기 — 일자 단위 증분 수집.

날짜 단위로 전 종목 공시를 수집한다. 하루씩 점진적으로 확장.
이미 수집된 날짜는 건너뛰고, 신규 날짜만 수집.

사용법::

    from dartlab.providers.dart.openapi.allFilingsCollector import collectDay, collectRange

    collectDay("20260327")                    # 하루
    collectRange("20260324", "20260327")       # 범위 (일자별 증분)
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


# ── 일자 단위 수집 ──


def collectDay(
    date: str,
    *,
    client: DartClient | None = None,
    corpClasses: list[str] | None = None,
    showProgress: bool = True,
) -> pl.DataFrame | None:
    """하루치 전체 공시 수집 → 일자별 parquet 저장.

    이미 수집된 날짜면 건너뛴다 (incremental).

    Parameters
    ----------
    date : YYYYMMDD 형식.
    client : DartClient. None이면 자동 생성.
    corpClasses : 법인구분 필터 (기본 ["Y", "K"] = 유가+코스닥).
    showProgress : 진행 표시.

    Returns
    -------
    pl.DataFrame | None
        수집된 데이터. 이미 수집됐거나 공시 없으면 None.
    """
    if client is None:
        client = DartClient()

    if corpClasses is None:
        corpClasses = ["Y", "K"]

    outDir = _allFilingsDir()
    parquetPath = outDir / f"{date}.parquet"

    # 이미 수집된 날짜 → 건너뜀
    if parquetPath.exists():
        if showProgress:
            existing = pl.read_parquet(parquetPath)
            print(f"[{date}] 이미 수집됨 ({existing['rcept_no'].n_unique()}건)")
        return None

    # 목록 수집
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

    total = meta.height
    if showProgress:
        print(f"[{date}] {total}건 수집 시작")

    # 원문 수집
    allRows: list[dict] = []
    success = fail = empty = 0

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

    # 원자적 저장
    tmpPath = parquetPath.with_suffix(".parquet.tmp")
    df.write_parquet(tmpPath)
    tmpPath.rename(parquetPath)

    if showProgress:
        print(f"[{date}] 완료: {success}건 성공, {empty}건 빈, {df.height}행, "
              f"{parquetPath.stat().st_size / 1024 / 1024:.1f}MB")

    return df


def collectRange(
    startDate: str,
    endDate: str,
    *,
    client: DartClient | None = None,
    corpClasses: list[str] | None = None,
    showProgress: bool = True,
) -> list[str]:
    """날짜 범위 증분 수집. 이미 수집된 날짜는 건너뛴다.

    Parameters
    ----------
    startDate, endDate : YYYYMMDD. 최신→과거 순으로 수집.
    client : DartClient.
    showProgress : 진행 표시.

    Returns
    -------
    list[str]
        수집 완료된 날짜 목록.
    """
    from datetime import datetime, timedelta

    if client is None:
        client = DartClient()

    start = datetime.strptime(startDate, "%Y%m%d")
    end = datetime.strptime(endDate, "%Y%m%d")

    # 최신 → 과거 순서
    dates = []
    current = end
    while current >= start:
        dates.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)

    collected: list[str] = []
    for i, date in enumerate(dates):
        if showProgress:
            print(f"\n=== [{i + 1}/{len(dates)}] ===")
        result = collectDay(
            date,
            client=client,
            corpClasses=corpClasses,
            showProgress=showProgress,
        )
        if result is not None:
            collected.append(date)

    if showProgress:
        print(f"\n총 {len(collected)}일 수집 완료")

    return collected


def collectedDates() -> list[str]:
    """수집 완료된 날짜 목록 (최신순)."""
    outDir = _allFilingsDir()
    dates = sorted(
        [p.stem for p in outDir.glob("*.parquet") if len(p.stem) == 8 and p.stem.isdigit()],
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
    """수집된 전체 데이터 로드 (모든 일자 병합)."""
    outDir = _allFilingsDir()
    files = sorted(outDir.glob("*.parquet"))
    if not files:
        return pl.DataFrame()
    return pl.scan_parquet(files).collect()


def stats() -> dict:
    """수집 현황 통계."""
    dates = collectedDates()
    if not dates:
        return {"days": 0, "filings": 0, "rows": 0, "sizeMb": 0}

    outDir = _allFilingsDir()
    totalSize = sum((outDir / f"{d}.parquet").stat().st_size for d in dates)

    # 첫/마지막 파일만 읽어서 건수 추정
    totalRows = 0
    totalFilings = 0
    for d in dates:
        df = pl.scan_parquet(outDir / f"{d}.parquet").select("rcept_no").collect()
        totalRows += df.height
        totalFilings += df["rcept_no"].n_unique()

    return {
        "days": len(dates),
        "firstDate": dates[-1],
        "lastDate": dates[0],
        "filings": totalFilings,
        "rows": totalRows,
        "sizeMb": round(totalSize / 1024 / 1024, 1),
    }
