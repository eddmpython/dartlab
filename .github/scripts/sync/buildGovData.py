"""공공데이터포털(공공누리/KOGL, 비상업+출처표시 재배포 가능) 주가·지수 HF 캐시 빌드.

HF = 캐시. 미리 전부 수집(bulk)하지 않는다. 두 갈래:

1. **date/ (전종목·전지수 일별)** — 엔진(scan/quant/benchmark)이 전시장 횡단을 쓰므로
   매일 어제 1콜로 `date/{year}` 1파일만 upsert (운영자 cron).
       gov/prices/date/{year}.parquet     전종목 횡단(KRX raw schema)
       gov/indices/date/{year}.parquet    전지수 횡단(KRX 지수 schema)

2. **company/{code}·index/{key} (엔티티별)** — 프론트가 종목/지수 하나를 **온디맨드**로
   호출할 때만 채운다. HF 캐시 hit 면 그대로, 미스면 라이브 호출→그리고→HF 저장
   (draw-first-save-later). 미리 수집 안 함.
       gov/prices/company/{code}.parquet  종목 1개 호출 캐시 (--stock, gov 라이브)
       gov/indices/index/{key}.parquet    지수 1개 호출 캐시 (--index, date/ 추출)

모드:
    --daily         어제 전종목 1콜 → date/{year} upsert + recent.parquet 갱신 (cron).
    --daily-index   어제 전지수 1콜 → date/{year} upsert (cron).
    --stock CODE    종목 하나 → company/{code} (프론트 온디맨드 캐시 채움).
    --index "M|NM"  지수 하나(시장군|지수명) → index/{key} (프론트 온디맨드 캐시 채움).
    --derive-companies  date/ 전 연도(기수집분)를 회사별 company/{code} 전종목 파생 (주간).
                    gov API 호출 0 — 수집이 아닌 레이아웃 파생(미캐시 종목 차트 수 초 → 1 GET).

키: DATA_GO_KR_KEY(디코딩) + HF_TOKEN. 환경변수 우선, 없으면 repo 루트 .env 직독.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import polars as pl

_REPO = "eddmpython/dartlab-data"
_HF_BASE = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main"
_NOW_YEAR = date.today().year


def _env(name: str) -> str:
    """환경변수 우선, 없으면 repo 루트 .env 직독."""
    val = os.environ.get(name, "").strip()
    if val:
        return val
    envPath = Path(__file__).resolve().parents[3] / ".env"
    if envPath.exists():
        m = dict(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", envPath.read_text(encoding="utf-8"), re.M))
        return m.get(name, "").strip().strip('"').strip("'")
    return ""


def _hfRead(pathInRepo: str) -> pl.DataFrame | None:
    """HF parquet 읽기 (없으면 None) — cold-cache 시 기존 이력 seed(축소 사고 방지)."""
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError

    from dartlab.core.hfRetry import retryHfCall

    try:
        localPath = retryHfCall(
            hf_hub_download,
            repo_id=_REPO,
            filename=pathInRepo,
            repo_type="dataset",
            token=_env("HF_TOKEN") or None,
        )
    except EntryNotFoundError:
        return None
    return pl.read_parquet(localPath)


def _deployFolder(localRoot: Path, pathInRepo: str, hfToken: str, msg: str) -> int:
    """로컬 폴더(서브디렉토리 포함)를 HF 에 폴더 단위 1커밋 업로드. 반환: parquet 수."""
    files = list(localRoot.rglob("*.parquet"))
    if not files:
        print(f"[gov/deploy] 업로드 대상 0건: {localRoot}")
        return 0
    from huggingface_hub import HfApi, create_repo

    from dartlab.core.hfRetry import retryHfCall

    retryHfCall(create_repo, _REPO, token=hfToken, repo_type="dataset", exist_ok=True)
    api = HfApi(token=hfToken)
    retryHfCall(
        api.upload_folder,
        folder_path=str(localRoot),
        path_in_repo=pathInRepo,
        repo_id=_REPO,
        repo_type="dataset",
        commit_message=msg,
    )
    print(f"[gov/deploy] {len(files)} files → {pathInRepo}")
    return len(files)


def _uploadFile(df: pl.DataFrame, pathInRepo: str, hfToken: str, msg: str) -> None:
    """단일 parquet → HF 업로드 (온디맨드 캐시 채움용)."""
    from huggingface_hub import HfApi

    from dartlab.core.hfRetry import retryHfCall

    buf = io.BytesIO()
    df.write_parquet(buf, compression="zstd")
    buf.seek(0)
    api = HfApi(token=hfToken)

    def upload() -> None:
        buf.seek(0)
        api.upload_file(
            path_or_fileobj=buf,
            path_in_repo=pathInRepo,
            repo_id=_REPO,
            repo_type="dataset",
            commit_message=msg,
        )

    retryHfCall(upload)


# ─────────────────────────── 주가 (prices) ───────────────────────────


def _appendYearlyRaw(df: pl.DataFrame, dateDir: Path) -> dict[int, int]:
    """KRX-raw 전종목 df 를 연도별 date/{year}.parquet 에 upsert (BAS_DD+ISU_CD dedup).

    로컬 cold-cache 시 HF 기존 연도 파일을 seed 후 merge — 1일치로 전년 축소 방지.
    """
    if df.is_empty():
        return {}
    dateDir.mkdir(parents=True, exist_ok=True)
    out: dict[int, int] = {}
    df2 = df.with_columns(pl.col("BAS_DD").str.slice(0, 4).alias("_year"))
    for partKey, grp in df2.partition_by("_year", as_dict=True).items():
        year = int(partKey[0]) if isinstance(partKey, tuple) else int(partKey)
        grp = grp.drop("_year")
        path = dateDir / f"{year}.parquet"
        existing = pl.read_parquet(path) if path.exists() else _hfRead(f"gov/prices/date/{year}.parquet")
        if existing is not None and not existing.is_empty():
            grp = pl.concat([existing, grp], how="diagonal_relaxed").unique(subset=["BAS_DD", "ISU_CD"], keep="last")
        grp = grp.sort(["BAS_DD", "ISU_CD"])
        grp.write_parquet(path, compression="zstd")
        out[year] = grp.height
        print(f"[gov/price] {year}: {grp.height}행 → {path}")
    return out


def _lookbackBizDays(endYmd: str, n: int) -> list[str]:
    """endYmd(YYYYMMDD) 부터 과거로 평일 n 개 (YYYYMMDD, 최신 우선). n<=1 은 endYmd 1개 그대로.

    n>1 = catch-up: 직전 run 이 놓친 영업일(cron skip·발행 지연)을 다음 run 이 재수집한다.
    주말만 건너뛴다 — 휴장일은 포함되지만 fetch 시 빈 응답이라 무해(idempotent upsert).
    """
    if n <= 1:
        return [endYmd]
    end = date(int(endYmd[:4]), int(endYmd[4:6]), int(endYmd[6:8]))
    out: list[str] = []
    cur = end
    while len(out) < n:
        if cur.weekday() < 5:
            out.append(cur.strftime("%Y%m%d"))
        cur -= timedelta(days=1)
    return out


def _collectedPriceDates(days: list[str], dateDir: Path) -> set[str]:
    """로컬 또는 HF 연도 샤드에서 이미 완결된 거래일을 찾고 로컬 캐시를 복원한다."""
    collected: set[str] = set()
    try:
        minRows = max(1, int(os.environ.get("DARTLAB_GOV_MIN_COMPLETE_ROWS", "1000")))
    except ValueError:
        minRows = 1000
    for year in sorted({day[:4] for day in days}):
        path = dateDir / f"{year}.parquet"
        frame = pl.read_parquet(path) if path.exists() else _hfRead(f"gov/prices/date/{year}.parquet")
        if frame is None or frame.is_empty() or "BAS_DD" not in frame.columns:
            continue
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            frame.write_parquet(path, compression="zstd")
            print(f"[gov/daily] {year}: HF date 샤드로 로컬 캐시 복원 ({frame.height}행)")
        complete = (
            frame.select(pl.col("BAS_DD").cast(pl.Utf8))
            .drop_nulls()
            .group_by("BAS_DD")
            .len()
            .filter(pl.col("len") >= minRows)
        )
        collected.update(str(value) for value in complete["BAS_DD"].to_list())
    return collected


def daily(*, apiKey: str, hfToken: str, basDt: str | None = None, lookbackDays: int = 1) -> int:
    """어제(또는 basDt) 기준 최근 lookbackDays 영업일 전종목 수집 → date/{year} upsert + recent → HF. 반환: 행수.

    lookbackDays>1 = catch-up: 직전 run 누락(cron skip·미확정)을 다음 run 이 재수집(idempotent upsert).
    gov 는 전일치를 T+1 오후 발행 → 오전 run 은 직전 영업일 재확인, 저녁 run 이 어제치 확보.
    회사별 company/{code} 전량 갱신은 주간 `--derive-companies` 담당 — 일일 신선도는 recent.parquet.
    """
    from dartlab.gather.gov.govApi import fetchGovBydd, normalizeGovToKrxRaw

    end = (basDt or (date.today() - timedelta(days=1)).strftime("%Y%m%d")).replace("-", "")
    days = _lookbackBizDays(end, lookbackDays)
    dateDir = Path("data/gov/prices/date")
    collected = _collectedPriceDates(days, dateDir)
    pendingDays = [day for day in days if day not in collected]
    if not pendingDays:
        print(f"[gov/daily] {days[-1]}~{days[0]}: 이미 수집 완료, API 호출과 HF 재발행 생략")
        return 0

    frames = []
    for day in pendingDays:
        raw = normalizeGovToKrxRaw(fetchGovBydd(day, apiKey=apiKey))
        if raw.is_empty():
            print(f"[gov/daily] {day}: 데이터 없음(휴장/미확정)")
        else:
            frames.append(raw)
            print(f"[gov/daily] {day}: {raw.height}행")
    if not frames:
        return 0
    counts = _appendYearlyRaw(pl.concat(frames, how="diagonal_relaxed"), dateDir)
    _deployFolder(dateDir, "gov/prices/date", hfToken, f"갱신: 주가 일별 {days[-1]}~{days[0]}")
    buildRecent(hfToken=hfToken)
    total = sum(counts.values())
    print(f"[gov/daily] {days[-1]}~{days[0]}: date {len(counts)}개 연도, {total}행")
    return total


# KRX raw(date 샤드) → 회사 표준 schema 매핑 (normalizeGovFrame 산출과 동일 컬럼명·Float64).
_KRXRAW_TO_STD = {
    "BAS_DD": "date",
    "ISU_NM": "name",
    "MKT_NM": "market",
    "TDD_OPNPRC": "open",
    "TDD_HGPRC": "high",
    "TDD_LWPRC": "low",
    "TDD_CLSPRC": "close",
    "CMPPREVDD_PRC": "priceChange",
    "FLUC_RT": "fluctuationRate",
    "ACC_TRDVOL": "volume",
    "ACC_TRDVAL": "tradedValue",
    "MKTCAP": "marketCap",
    "LIST_SHRS": "listedShares",
}


def _stdFromKrxRaw(df: pl.DataFrame) -> pl.DataFrame:
    """date 샤드 KRX raw → 회사 표준 schema (stockCode 6자리, 수치 Float64).

    ISU_CD 는 gov 시대 'A'+코드 / KRX 이관분 코드 단독 혼재 — 선행 'A' 제거 후 6자리만 채택.
    """
    cols = [c for c in _KRXRAW_TO_STD if c in df.columns]
    out = df.select(["ISU_CD", *cols]).rename({c: _KRXRAW_TO_STD[c] for c in cols})
    out = out.with_columns(pl.col("ISU_CD").cast(pl.Utf8).str.replace(r"^A", "").alias("stockCode")).drop("ISU_CD")
    out = out.filter(pl.col("stockCode").str.contains(r"^\d{6}$"))
    floatCols = [v for k, v in _KRXRAW_TO_STD.items() if v not in ("date", "name", "market") and v in out.columns]
    return out.with_columns([pl.col(c).cast(pl.Float64, strict=False) for c in floatCols])


def deriveCompanies(*, hfToken: str, sinceYear: int = 2010) -> int:
    """date/ 전 연도(기수집분)를 회사별 company/{code}.parquet 전종목으로 파생 → 폴더 1커밋.

    gov API 호출 0 — HF 에 이미 있는 date 샤드의 레이아웃 파생이다(수집 아님). 미캐시 종목의
    차트 콜드 경로(전종목 날짜정렬 스캔 수 초)를 회사 파일 1 GET 으로 바꾼다. 주간 cron 이
    재실행해 회사 파일 신선도를 회복하고, 일일 gap 은 recent.parquet 이 메운다. 반환: 종목 수.
    """
    frames = []
    for y in range(sinceYear, _NOW_YEAR + 1):
        local = Path(f"data/gov/prices/date/{y}.parquet")
        df = pl.read_parquet(local) if local.exists() else _hfRead(f"gov/prices/date/{y}.parquet")
        if df is None or df.is_empty():
            continue
        frames.append(_stdFromKrxRaw(df))
        print(f"[gov/derive] {y}: {frames[-1].height}행")
    if not frames:
        print("[gov/derive] date 샤드 없음")
        return 0
    allDf = pl.concat(frames, how="diagonal_relaxed").unique(subset=["stockCode", "date"], keep="last")
    outDir = Path("data/gov/prices/company")
    outDir.mkdir(parents=True, exist_ok=True)
    n = 0
    for partKey, grp in allDf.partition_by("stockCode", as_dict=True).items():
        code = partKey[0] if isinstance(partKey, tuple) else partKey
        grp.sort("date").write_parquet(outDir / f"{code}.parquet", compression="zstd")
        n += 1
    _deployFolder(outDir, "gov/prices/company", hfToken, f"갱신: 회사별 주가 전종목 파생 ({n}종목)")
    print(f"[gov/derive] {n}종목 ({allDf.height}행)")
    return n


def buildRecent(*, hfToken: str, tradingDays: int = 30) -> int:
    """현재 연도 date 샤드에서 최근 N거래일 전종목 슬림 추출 → recent.parquet 1파일.

    프론트 신선 tail — 회사 파일(주간 파생)과 병합해 일일 갱신 없이도 최신 캔들 보장.
    연초처럼 거래일이 N 미만이면 있는 만큼만(직전 연도 보충은 회사 파일이 커버). 반환: 행수.
    """
    local = Path(f"data/gov/prices/date/{_NOW_YEAR}.parquet")
    df = pl.read_parquet(local) if local.exists() else _hfRead(f"gov/prices/date/{_NOW_YEAR}.parquet")
    if df is None or df.is_empty():
        print("[gov/recent] 현재 연도 date 샤드 없음 — 건너뜀")
        return 0
    days = sorted(df["BAS_DD"].unique().to_list())[-tradingDays:]
    # fluctuationRate(기준가 대비 등락률) = 수정주가 체이닝 입력 / tradedValue = 거래대금 툴팁·TVAL 페인
    slim = (
        _stdFromKrxRaw(df.filter(pl.col("BAS_DD").is_in(days)))
        .select(["stockCode", "date", "open", "high", "low", "close", "volume", "fluctuationRate", "tradedValue"])
        .sort(["stockCode", "date"])
    )
    _uploadFile(slim, "gov/prices/recent.parquet", hfToken, f"갱신: 최근 {len(days)}거래일 전종목")
    print(f"[gov/recent] {len(days)}거래일 {slim.height}행")
    return slim.height


def produceStock(code: str, *, apiKey: str, hfToken: str, merge: bool = True) -> int:
    """종목 하나 gov 전체이력 → company/{code} merge → HF 단일 업로드(프론트 온디맨드). 반환: 행수."""
    from dartlab.gather.gov.govApi import fetchGovStock, normalizeGovFrame

    fresh = normalizeGovFrame(fetchGovStock(code, apiKey=apiKey))
    if fresh.is_empty():
        print(f"[gov/stock] {code}: gov 데이터 없음")
        return 0
    existing = _hfRead(f"gov/prices/company/{code}.parquet") if merge else None
    if existing is not None and not existing.is_empty():
        cols = [c for c in fresh.columns if c in existing.columns]
        fresh = pl.concat([existing.select(cols), fresh.select(cols)], how="diagonal_relaxed").unique(
            subset=["date"], keep="last"
        )
    out = fresh.sort("date")
    _uploadFile(out, f"gov/prices/company/{code}.parquet", hfToken, f"갱신: 회사별 주가 {code} ({out.height}행)")
    print(f"[gov/stock] {code}: {out.height}행 ({out['date'].min()}~{out['date'].max()})")
    return out.height


# ─────────────────────────── 지수 (indices) ───────────────────────────

_RESERVED = '/\\:*?"<>|'


def indexKey(market: str, idxNm: str) -> str:
    """(market, idxNm) → 파일시스템 안전 키. '/' 등 9개 예약문자+공백만 '_' 치환(한글 유지)."""
    s = unicodedata.normalize("NFC", str(idxNm)).strip()
    for ch in _RESERVED:
        s = s.replace(ch, "_")
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return f"{market}-{s}"


def _appendYearlyIndex(df: pl.DataFrame, dateDir: Path) -> dict[int, int]:
    """KRX-지수 df 를 연도별 date/{year}.parquet 에 upsert (BAS_DD+MARKET_GROUP+IDX_CLSS+IDX_NM dedup)."""
    if df.is_empty():
        return {}
    dateDir.mkdir(parents=True, exist_ok=True)
    keys = ["BAS_DD", "MARKET_GROUP", "IDX_CLSS", "IDX_NM"]
    out: dict[int, int] = {}
    df2 = df.with_columns(pl.col("BAS_DD").str.slice(0, 4).alias("_year"))
    for partKey, grp in df2.partition_by("_year", as_dict=True).items():
        year = int(partKey[0]) if isinstance(partKey, tuple) else int(partKey)
        grp = grp.drop("_year")
        path = dateDir / f"{year}.parquet"
        existing = pl.read_parquet(path) if path.exists() else _hfRead(f"gov/indices/date/{year}.parquet")
        if existing is not None and not existing.is_empty():
            grp = pl.concat([existing, grp], how="diagonal_relaxed").unique(subset=keys, keep="last")
        grp = grp.sort(keys)
        grp.write_parquet(path, compression="zstd")
        out[year] = grp.height
        print(f"[gov/index] {year}: {grp.height}행 → {path}")
    return out


def dailyIndex(*, apiKey: str, hfToken: str, basDt: str | None = None, lookbackDays: int = 1) -> int:
    """어제(또는 basDt) 기준 최근 lookbackDays 영업일 전지수 수집 → date/{year} upsert → HF (cron). 반환: 행수.

    lookbackDays>1 = catch-up (주가 daily 와 동일 규약 — cron skip·미확정 재수집, idempotent).
    지수별 index/{key} 는 여기서 안 받는다 — 프론트가 지수 하나를 `--index` 온디맨드로 채운다.
    """
    from dartlab.gather.gov.govApi import fetchGovIndex, normalizeGovIndexFrame

    end = (basDt or (date.today() - timedelta(days=1)).strftime("%Y%m%d")).replace("-", "")
    days = _lookbackBizDays(end, lookbackDays)
    frames = []
    for day in days:
        norm = normalizeGovIndexFrame(fetchGovIndex(day, apiKey=apiKey))
        if norm.is_empty():
            print(f"[gov/daily-index] {day}: 데이터 없음(휴장/미확정)")
        else:
            frames.append(norm)
            print(f"[gov/daily-index] {day}: {norm.height}행")
    if not frames:
        return 0
    dateDir = Path("data/gov/indices/date")
    counts = _appendYearlyIndex(pl.concat(frames, how="diagonal_relaxed"), dateDir)
    _deployFolder(dateDir, "gov/indices/date", hfToken, f"갱신: 지수 일별 {days[-1]}~{days[0]}")
    total = sum(counts.values())
    print(f"[gov/daily-index] {days[-1]}~{days[0]}: date {len(counts)}개 연도, {total}행")
    return total


def produceIndex(market: str, idxNm: str, *, hfToken: str) -> int:
    """지수 하나 → date/ 전체에서 추출 → index/{key} 단일 업로드(프론트 온디맨드). 반환: 행수.

    지수는 종목별 likeSrtnCd 같은 단일-엔티티 API 가 없어, 전지수를 담은 date/ 에서 뽑는다.
    """
    frames = []
    for y in range(2010, _NOW_YEAR + 1):
        df = _hfRead(f"gov/indices/date/{y}.parquet")
        if df is not None and not df.is_empty():
            frames.append(df.filter((pl.col("MARKET_GROUP") == market) & (pl.col("IDX_NM") == idxNm)))
    if not frames:
        print(f"[gov/index1] {market}|{idxNm}: date 없음")
        return 0
    out = pl.concat(frames, how="diagonal_relaxed").unique(subset=["BAS_DD"], keep="last").sort("BAS_DD")
    if out.is_empty():
        print(f"[gov/index1] {market}|{idxNm}: 매칭 행 없음")
        return 0
    key = indexKey(market, idxNm)
    _uploadFile(out, f"gov/indices/index/{key}.parquet", hfToken, f"갱신: 지수별 {key} ({out.height}행)")
    print(f"[gov/index1] {key}: {out.height}행")
    return out.height


# 프론트 IndexPort 큐레이트 화이트리스트 — contracts KR_INDEX_PRESETS 와 1:1 (이름 정확 일치 필수, gov 실측 확인).
CURATED_INDICES = [
    ("KOSPI", "코스피"),
    ("KOSPI", "코스피 200"),
    ("KOSDAQ", "코스닥"),
    ("KOSDAQ", "코스닥 150"),
    ("KRX", "KRX 300"),
]


def seedCuratedIndices(*, hfToken: str) -> int:
    """큐레이트 5 지수 index/{key} 전이력 일괄 추출(date/ → index/). 프론트 IndexPort 전이력 활성용.

    주간/수동 권장 — 매일 date/ fresh tail(govIndexSource 폴백 병합)이 seed 이후 갭을 메우므로 daily 불요
    (지수당 17 연도 HF read 라 daily×5 는 과도). 반환: 총 행수.
    """
    total = 0
    for market, idxNm in CURATED_INDICES:
        total += produceIndex(market, idxNm, hfToken=hfToken)
    print(f"[gov/seed-curated] {len(CURATED_INDICES)}개 지수, {total}행")
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description="공공데이터포털 주가·지수 HF 캐시 빌드 (date daily + 엔티티 온디맨드)")
    ap.add_argument("--daily", action="store_true", help="어제 전종목 1콜 → date/{year} (cron)")
    ap.add_argument(
        "--daily-index", dest="dailyIndex", action="store_true", help="어제 전지수 1콜 → date/{year} (cron)"
    )
    ap.add_argument("--stock", help="종목 하나 → company/{code} 온디맨드 캐시")
    ap.add_argument("--index", dest="indexSpec", help='지수 하나 "시장군|지수명" → index/{key} 온디맨드 캐시')
    ap.add_argument(
        "--seed-curated",
        dest="seedCurated",
        action="store_true",
        help="큐레이트 5 지수(코스피·코스피200·코스닥·코스닥150·KRX300) index/{key} 전이력 일괄 추출 (프론트 전이력 활성·주간/수동)",
    )
    ap.add_argument("--basDt", help="--daily/--daily-index 기준일자 YYYYMMDD (기본 어제)")
    ap.add_argument(
        "--lookback",
        type=int,
        default=1,
        help="--daily/--daily-index 최근 N 영업일 catch-up 수집 (기본 1=어제만, cron 은 4 권장)",
    )
    ap.add_argument(
        "--derive-companies",
        dest="deriveCompanies",
        action="store_true",
        help="date/ 전 연도 → 회사별 전종목 파생 (API 호출 0)",
    )
    args = ap.parse_args()

    hfToken = _env("HF_TOKEN")
    if not hfToken:
        print("HF_TOKEN 필수")
        return 1

    if args.deriveCompanies:
        deriveCompanies(hfToken=hfToken)
        buildRecent(hfToken=hfToken)
        return 0
    if args.indexSpec:
        if "|" not in args.indexSpec:
            print('--index 형식: "시장군|지수명" (예: "KOSPI|코스피 200")')
            return 1
        market, idxNm = args.indexSpec.split("|", 1)
        produceIndex(market.strip(), idxNm.strip(), hfToken=hfToken)
        return 0

    apiKey = _env("DATA_GO_KR_KEY")
    if (args.stock or args.daily or args.dailyIndex) and not apiKey:
        print("DATA_GO_KR_KEY 필수")
        return 1
    if args.stock:
        produceStock(args.stock.strip(), apiKey=apiKey, hfToken=hfToken)
        return 0
    if args.daily:
        daily(apiKey=apiKey, hfToken=hfToken, basDt=args.basDt, lookbackDays=args.lookback)
        return 0
    if args.dailyIndex:
        dailyIndex(apiKey=apiKey, hfToken=hfToken, basDt=args.basDt, lookbackDays=args.lookback)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
