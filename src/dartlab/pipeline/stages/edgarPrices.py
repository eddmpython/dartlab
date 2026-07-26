"""EDGAR prices stage — 회사별 일별 OHLCV bake + 스냅샷 파생 (터미널 주가 그래프 + 게이트).

한 스테이지가 둘을 생산한다(덕지덕지 차단 — gather 호출 1회/티커):
  ① 그래프: ``edgar/prices/company/{ticker}.parquet`` (회사별 일별 OHLCV 전체이력). 브라우저 터미널
     PriceChart 가 ``rt.price`` US 브랜치(``edgarPriceSource``)로 직독 — KR ``krx``/``gov`` 회사 주가와 동일 reader.
  ② 게이트: ``landing/map/prices-snapshot-us.json`` (현재가·수익률·52주·변동성 요약). ``buildCompany`` 의
     prices 게이트(``raw.prices.data[ticker]``)를 채워 US 종목이 검색→열림 되게 한다(KR prices-snapshot 동형).

별도빌드 금지 — 수집은 gather 에 위임(``gather.price(ticker, market="US")``). 본 모듈은 오케스트레이션
(유니버스 루프·parquet 쓰기·스냅샷 파생·HF 발행)만 한다. 온라인(Yahoo)이라 daily companyfacts(``edgar``
스테이지)와 카덴스가 달라 별 스테이지로 둔다(KR ``buildGovPriceData`` 가 별 워크플로인 것과 동형).
"""

from __future__ import annotations

import json
import math
import time

from dartlab.pipeline.types import PipelineMode, StageResult

# date=Utf8 'YYYYMMDD' (Candle.t 규약). edgarPriceSource.parseEdgarPriceRows 가 대시 제거로 흡수하지만
# 정본을 8자리 문자열로 굳혀 브라우저(hyparquet) read 가 결정적이게 한다.
_START_DEFAULT = "2015-01-01"  # Yahoo 일봉 ~10년 — 그래프 전체이력(US 는 좌측 백필 없음, seed 가 곧 범위)

# 스냅샷 수익률 거래일 오프셋 (KR buildPricesSnapshot 동일 규약 — 1M/3M/1Y).
_RET_OFFSETS = {"return1m": 21, "return3m": 63, "return1y": 252}
_SNAPSHOT_REPO = "eddmpython/dartlab-data"
_SNAPSHOT_PATH_IN_REPO = "landing/map/prices-snapshot-us.json"

# 행수 가드 — Yahoo 는 throttle(429) 시 에러 없이 default 범위(~110행 ≈ 6개월)만 반환하는 조용한
# 부분응답을 낸다(실측: UNH·AAPL 2887행 대신 110행). 이보다 적으면 degraded 의심 → 검증 재시도.
_DEGRADED_ROW_FLOOR = 250  # 다년 start 인데 이 미만이면 부분응답 의심(252거래일=1년)
_DEGRADED_RETRY_SLEEP = 20.0  # degraded 재시도 전 throttle 해소 대기(초)


def _universeTickers() -> list[str]:
    """주가 bake 대상 유니버스 ticker(대문자) — edgarPanel 우선순위(상장 universe)와 동일 scope.

    Returns:
        list[str] — 중복 제거 ticker 목록. 부재 시 빈 목록(상위가 skip).
    """
    try:
        from dartlab.pipeline.stages.edgarPanel import _priorityTickers

        seen: dict[str, None] = {}
        for t in _priorityTickers():
            tk = str(t).strip().upper()
            if tk and tk not in seen:
                seen[tk] = None
        return list(seen)
    # 유니버스 산출 실패는 skip 하고 빌드는 격리
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] edgarPrices universe 산출 실패: {type(exc).__name__}: {exc}", flush=True)
        return []


def _retPct(closes: list, bars: int) -> float | None:
    """종가열의 bars 거래일 전 대비 수익률(%) — KR buildPricesSnapshot._retPct 동형."""
    if len(closes) <= bars:
        return None
    last, prev = closes[-1], closes[-1 - bars]
    if last is None or prev is None or prev == 0:
        return None
    return round((last / prev - 1) * 100, 2)


def _volatility1y(closes: list) -> float | None:
    """일별 로그수익률 표본표준편차 × √252 × 100 (최근 252수익률, 최소 60개) — KR 동형."""
    window = [c for c in closes[-253:] if c is not None and c > 0]
    rets = [math.log(window[i] / window[i - 1]) for i in range(1, len(window)) if window[i - 1] > 0]
    if len(rets) < 60:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return round(math.sqrt(var) * math.sqrt(252) * 100, 2)


def _snapshotRow(closes: list, highs: list, lows: list, vols: list, lastDate: str) -> dict:
    """OHLCV 열에서 터미널 게이트 스냅샷 행 파생 — KR PriceRow schema 동형.

    Args:
        closes: 종가 오름차순.
        highs/lows: 고가/저가 오름차순.
        vols: 거래량 오름차순.
        lastDate: 최신 거래일 'YYYYMMDD'.

    Returns:
        dict — currentPrice·return*·volatility1y·week52*·volumeAvg30d·marketCap(null)·priceUpdated.
            marketCap 은 shares(EDGAR dei) 결합이 별 작업이라 현재 null(게이트는 행 존재만 요구).
    """
    hi252 = [v for v in highs[-252:] if v is not None]
    lo252 = [v for v in lows[-252:] if v is not None]
    vol30 = [v for v in vols[-30:] if v is not None]
    return {
        "currentPrice": closes[-1],
        "marketCap": None,  # TODO: shares(EDGAR dei EntityCommonStockSharesOutstanding) × currentPrice 후속 보강
        "return1m": _retPct(closes, _RET_OFFSETS["return1m"]),
        "return3m": _retPct(closes, _RET_OFFSETS["return3m"]),
        "return1y": _retPct(closes, _RET_OFFSETS["return1y"]),
        "volatility1y": _volatility1y(closes),
        "week52High": max(hi252) if hi252 else None,
        "week52Low": min(lo252) if lo252 else None,
        "volumeAvg30d": int(sum(vol30) / len(vol30)) if vol30 else None,
        "foreignPct": None,
        "beta": None,
        "priceUpdated": lastDate,
    }


def buildSnapshotFromCompanyDir(companyDir) -> dict:
    """company/{ticker}.parquet 디렉터리 전체에서 deep 스냅샷 행을 빌드한다(실수익률·52주·변동성).

    백필 publish 잡이 회사 parquet(전체이력)로 게이트 스냅샷을 정확히 채울 때 쓴다. daily(recent ~7일)는
    currentPrice 만 패치하므로 returns/52w/volatility 의 정본은 본 함수(deep base)다. 둘을 분리해 daily 가
    deep 수익률을 덮지 않게 한다(스냅샷 returns 전부 null 회귀 차단).

    Args:
        companyDir: edgar/prices/company 디렉터리(Path 또는 str) — {ticker}.parquet 들.

    Returns:
        dict — {ticker: snapshotRow}. parquet 부재/손상/빈 ticker 는 제외.

    Example:
        >>> buildSnapshotFromCompanyDir("data/edgar/prices/company")  # doctest: +SKIP
        {'AAPL': {'currentPrice': 283.78, 'return1y': 12.4, ...}, ...}
    """
    from pathlib import Path

    import polars as pl

    d = Path(companyDir)
    snap: dict = {}
    for fp in sorted(d.glob("*.parquet")):
        ticker = fp.stem.upper()
        try:
            df = pl.read_parquet(fp).sort("date")
            if df.height == 0:
                continue
            snap[ticker] = _snapshotRow(
                df["close"].to_list(), df["high"].to_list(), df["low"].to_list(), df["volume"].to_list(), df["date"][-1]
            )
        except Exception:  # noqa: BLE001 — 개별 parquet 손상 격리(나머지 진행)
            continue
    return snap


def _bakeOne(ticker: str, start: str, outDir) -> dict | None:
    """단일 ticker 의 US OHLCV 를 gather 위임으로 받아 parquet 으로 굽고 스냅샷 행을 파생한다.

    Args:
        ticker: US 티커(대문자).
        start: 시작일 'YYYY-MM-DD'.
        outDir: parquet 출력 디렉터리(Path).

    Returns:
        dict | None — 스냅샷 행(게이트용). 무데이터/실패 None.
    """
    import time as _time

    import polars as pl

    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    df = g.price(ticker, market="US", start=start)
    if df is None or not hasattr(df, "height") or df.height == 0:
        return None
    # 행수 가드 — 적은 행은 throttle 부분응답(~110행) 의심. 더 긴 sleep 후 검증 재시도: 재시도가 더 주면
    # 첫 응답이 degraded(큰 쪽 채택), 같으면 진짜 짧은 이력(최근 IPO 등 — 그대로). 손상 백필 차단.
    if df.height < _DEGRADED_ROW_FLOOR:
        _time.sleep(_DEGRADED_RETRY_SLEEP)
        df2 = g.price(ticker, market="US", start=start)
        if df2 is not None and hasattr(df2, "height") and df2.height > df.height:
            df = df2
    # gather 출력 = [date(Date), open, high, low, close, volume]. date → Utf8 'YYYYMMDD'.
    dateExpr = (
        pl.col("date").dt.strftime("%Y%m%d")
        if df.schema.get("date") == pl.Date
        else pl.col("date").cast(pl.Utf8).str.replace_all("-", "")
    )
    out = df.with_columns(dateExpr.alias("date")).select(["date", "open", "high", "low", "close", "volume"])
    out = (
        out.filter(pl.col("date").str.contains(r"^\d{8}$") & pl.col("close").is_not_null())
        .sort("date")
        .unique(subset=["date"], keep="last")
    )
    if out.height == 0:
        return None
    out.write_parquet(outDir / f"{ticker}.parquet", compression="zstd", statistics=True)
    return _snapshotRow(
        out["close"].to_list(), out["high"].to_list(), out["low"].to_list(), out["volume"].to_list(), out["date"][-1]
    )


def _writeSnapshot(snap: dict, *, upload: bool, token, patchFields: tuple[str, ...] | None = None) -> str:
    """스냅샷 dict 를 기존 prices-snapshot-us.json 과 병합해 쓰고(증분 안전) 선택적 HF 발행.

    Args:
        snap: {ticker: row} 신규/갱신분.
        upload: True 면 HF(landing/map/prices-snapshot-us.json) 직접 발행(KR snapshot 패턴 동형).
        token: HF 토큰(None=env).
        patchFields: 지정 시 *기존* ticker 행은 이 키들만 덮어쓴다(나머지 deep 필드 보존). 신규 ticker 는
            전체 행 생성. daily(recent)가 deep 수익률을 덮지 않게 하는 분리 장치. None=행 전체 교체.

    Returns:
        str — 쓴 로컬 경로.
    """
    from datetime import datetime, timezone
    from pathlib import Path

    # repo 루트 = stages→pipeline→dartlab→src→repo (parents[4]). landing 정적 자산은 repo 상대(데이터 dir 무관).
    repoRoot = Path(__file__).resolve().parents[4]
    outLocal = repoRoot / "landing" / "static" / "map" / "prices-snapshot-us.json"
    merged: dict = {}
    if outLocal.exists():
        try:
            prev = json.loads(outLocal.read_text(encoding="utf-8"))
            merged = dict(prev.get("data") or {})
        except Exception:  # noqa: BLE001 — 손상/부재 → 신규분만
            merged = {}
    elif upload:
        # 로컬 부재(CI fresh 청크 런) → 기존 HF 스냅샷 다운로드해 누적. 청크 백필이 서로 덮지 않게.
        try:
            from huggingface_hub import hf_hub_download

            from dartlab.core.hfRetry import retryHfCall
            from dartlab.pipeline.hfUpload import _resolveHfToken

            cached = retryHfCall(
                hf_hub_download,
                repo_id=_SNAPSHOT_REPO,
                repo_type="dataset",
                filename=_SNAPSHOT_PATH_IN_REPO,
                token=_resolveHfToken(token),
            )
            merged = dict(json.loads(Path(cached).read_text(encoding="utf-8")).get("data") or {})
        except Exception:  # noqa: BLE001 — 첫 발행 등 미존재 → 신규분만
            merged = {}
    if patchFields:
        for tk, row in snap.items():
            if tk in merged and isinstance(merged[tk], dict):
                for k in patchFields:
                    if k in row:
                        merged[tk][k] = row[k]
            else:
                merged[tk] = row
    else:
        merged.update(snap)
    payload = {
        "schemaVersion": 1,
        "builtAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "currency": "USD",
        "count": len(merged),
        "data": merged,
    }
    outLocal.parent.mkdir(parents=True, exist_ok=True)
    outLocal.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[pipeline] edgarPrices snapshot: {len(merged)}종목 → {outLocal}", flush=True)
    if upload:
        from huggingface_hub import HfApi

        from dartlab.core.hfRetry import retryHfCall
        from dartlab.pipeline.hfUpload import _resolveHfToken

        retryHfCall(
            HfApi(token=_resolveHfToken(token)).upload_file,
            path_or_fileobj=str(outLocal),
            path_in_repo=_SNAPSHOT_PATH_IN_REPO,
            repo_id=_SNAPSHOT_REPO,
            repo_type="dataset",
            commit_message=f"갱신: prices-snapshot-us ({len(merged)}종목)",
        )
        print(f"[pipeline] edgarPrices snapshot HF 발행 → {_SNAPSHOT_PATH_IN_REPO}", flush=True)
    return str(outLocal)


def runEdgarPrices(
    *,
    category: str = "edgarPriceCompany",
    mode: PipelineMode = "recent",
    tickers: list[str] | None = None,
    start: str = _START_DEFAULT,
    limit: int | None = None,
    offset: int = 0,
    pauseSeconds: float = 0.0,
    writeSnapshotFlag: bool = True,
    upload: bool = True,
    token=None,
) -> StageResult:
    """유니버스 회사별 US OHLCV → 그래프 parquet + 게이트 스냅샷 bake + HF 발행.

    offset/limit = 청크(matrix 백필 분산 IP — runner 마다 distinct IP 라 Yahoo throttle 회피).
    writeSnapshotFlag=False = company parquet 만(matrix 청크 병렬 시 스냅샷 race 방지 — 스냅샷은 daily 가 빌드).

    수집은 gather(Yahoo, 429 백오프·fallback 체인 내장)에 위임한다. tickers 미지정이면 상장 universe
    전체(edgarPanel scope), 지정 시 그 목록만(스모크·증분). 개별 실패는 격리(나머지 진행). 스냅샷은
    기존 파일과 병합 발행(증분 안전).

    Args:
        category: 그래프 parquet HF 카테고리(``edgarPriceCompany``).
        mode: 미사용(인터페이스 호환).
        tickers: bake 대상 ticker 목록(대문자 무관). None=유니버스 전체.
        start: OHLCV 시작일 'YYYY-MM-DD'.
        limit: 처리 ticker 수 상한(스모크·부분 실행). None=전체.
        pauseSeconds: ticker 간 대기(추가 페이싱 — gather 자체 백오프 위. 0=없음).
        upload: True 면 parquet 증분 + 스냅샷 HF 발행.
        token: HF 토큰(None=env).

    Returns:
        StageResult — ok=성공 ticker 수, err=실패 수.

    Raises:
        없음 — 개별 실패 격리.

    Example:
        >>> runEdgarPrices(tickers=["AAPL"], upload=False)  # doctest: +SKIP
        StageResult(category='edgarPriceCompany', ...)
    """
    from pathlib import Path

    import dartlab.config as cfg

    res = StageResult(category=category)
    uni = [str(t).strip().upper() for t in (tickers if tickers is not None else _universeTickers()) if str(t).strip()]
    if offset:
        uni = uni[offset:]
    if limit is not None:
        uni = uni[:limit]
    if not uni:
        print("[pipeline] edgarPrices: 대상 ticker 0 → skip", flush=True)
        res.report.skip += 1
        return res

    outDir = Path(cfg.dataDir) / "edgar" / "prices" / "company"
    outDir.mkdir(parents=True, exist_ok=True)
    changed: list[str] = []
    snap: dict = {}
    for i, ticker in enumerate(uni):
        try:
            row = _bakeOne(ticker, start, outDir)
            if row is not None:
                changed.append(f"{ticker}.parquet")
                snap[ticker] = row
                res.report.ok += 1
            else:
                res.report.skip += 1
        except Exception as exc:  # noqa: BLE001 — 개별 ticker 실패 격리
            res.report.err += 1
            res.report.failures.append(f"{ticker}: {type(exc).__name__}: {exc}")
            print(f"[pipeline] edgarPrices bake 실패({ticker}): {exc}", flush=True)
        if pauseSeconds and i + 1 < len(uni):
            time.sleep(pauseSeconds)

    print(f"[pipeline] edgarPrices: {res.report.ok}개 bake (대상 {len(uni)})", flush=True)
    if changed:
        from dartlab.pipeline.changed import writeChanged

        writeChanged(category, changed)
        if upload:
            from dartlab.pipeline.hfUpload import uploadCategoryToHf

            n = uploadCategoryToHf(category, changedFiles=changed, token=token)
            print(f"[pipeline] edgarPrices parquet HF 발행: {n}개", flush=True)
    if snap and writeSnapshotFlag:
        try:
            _writeSnapshot(snap, upload=upload, token=token)
        except Exception as exc:  # noqa: BLE001 — 스냅샷 발행 실패 격리(parquet 발행은 성공 유지)
            res.report.failures.append(f"snapshot: {type(exc).__name__}: {exc}")
            print(f"[pipeline] edgarPrices snapshot 실패(격리): {exc}", flush=True)
    return res


# ── 일증분 (Polygon by-day) — gov daily 대칭 ──────────────────────────────────────────────
# 백필(runEdgarPrices, Yahoo per-ticker)이 회사별 전체이력 base 를 깐 뒤, 매일 Polygon grouped-daily
# 1콜로 그날 전종목 OHLC 를 받아 edgar/prices/recent.parquet(최근 tail 1파일)에 누적한다. 런타임이
# company(base) + recent(tail)를 머지(KR govPriceSource 와 동형). 6437 per-ticker 매일 회피.
_POLYGON_PACE_SECONDS = 13.0  # 무료 5콜/분 → 12s/콜 + 여유
_RECENT_KEEP_DAYS = 45  # recent tail 보관 달력일 (backfill 주기 사이 가교)
# daily(recent ~7일)가 스냅샷에서 덮어도 되는 필드 — 최신가만. returns/52w/volatility 는 윈도가 짧아
# 신뢰 불가 → deep 백필(buildSnapshotFromCompanyDir)이 정본이라 기존 값 보존.
_DAILY_PATCH_FIELDS = ("currentPrice", "priceUpdated")


def _resolvePolygonKey(key: str | None = None) -> str:
    """Polygon(Massive) 키 해석 — 인자 > POLYGON_API_KEY env > repo .env. 도메인은 env 미참조라 여기서 주입."""
    if key:
        return key
    import os

    env = os.environ.get("POLYGON_API_KEY", "").strip()
    if env:
        return env
    from pathlib import Path

    envPath = Path(__file__).resolve().parents[4] / ".env"
    if envPath.exists():
        import re

        m = re.search(r"^POLYGON_API_KEY=(.*)$", envPath.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).strip().strip('"').strip("'").strip()
    return ""


def runEdgarPricesDaily(
    *,
    dates: list[str] | None = None,
    lookbackDays: int = 7,
    listedOnly: bool = True,
    upload: bool = True,
    token=None,
    polygonKey: str | None = None,
) -> StageResult:
    """Polygon grouped-daily 위임 → edgar/prices/recent.parquet 누적 + 스냅샷 현재가 패치 (gov daily 대칭).

    수집은 gather(``domains.polygon.fetchGroupedDaily``)에 위임 — 별도빌드 금지. 본 스테이지는 날짜 루프·
    recent tail 누적·스냅샷 패치·HF 발행만. by-day 1콜/날짜라 per-ticker 6437 회피.

    Args:
        dates: 'YYYYMMDD' 목록(명시). None=최근 lookbackDays 평일.
        lookbackDays: dates 미지정 시 최근 평일 수(휴장일은 빈 응답 → skip).
        listedOnly: True 면 edgar/tickers 의 상장 ticker 만 recent 에 보관(OTC junk 제외).
        upload: True 면 recent.parquet + 스냅샷 HF 발행.
        token: HF 토큰(None=env).
        polygonKey: Polygon 키(None=env/.env).

    Returns:
        StageResult — ok=수집 성공 날짜 수, err=실패.

    Raises:
        SystemExit: POLYGON_API_KEY 부재.

    Example:
        >>> runEdgarPricesDaily(lookbackDays=3, upload=False)  # doctest: +SKIP
    """
    from datetime import date as _date
    from datetime import timedelta
    from pathlib import Path

    import httpx
    import polars as pl

    import dartlab.config as cfg
    from dartlab.gather.domains.polygon import fetchGroupedDaily

    res = StageResult(category="edgarPriceRecent")
    key = _resolvePolygonKey(polygonKey)
    if not key:
        raise SystemExit("[edgarPricesDaily] POLYGON_API_KEY 없음 — .env/secret 등록 필요")

    if dates is None:
        out: list[str] = []
        d = _date.today()
        while len(out) < lookbackDays:
            d -= timedelta(days=1)
            if d.weekday() < 5:  # 평일만(휴장일은 빈 응답 skip)
                out.append(d.strftime("%Y%m%d"))
        dates = sorted(out)

    frames: list[pl.DataFrame] = []
    cli = httpx.Client(timeout=30.0, headers={"User-Agent": "Mozilla/5.0"})
    try:
        for i, ds in enumerate(dates):
            try:
                df = fetchGroupedDaily(ds, apiKey=key, client=cli)
                if df.height:
                    frames.append(df)
                    res.report.ok += 1
                else:
                    res.report.skip += 1
                print(f"[edgarPricesDaily] {ds}: {df.height}행", flush=True)
            except Exception as exc:  # noqa: BLE001 — 개별 날짜 실패 격리
                res.report.err += 1
                res.report.failures.append(f"{ds}: {type(exc).__name__}: {exc}")
                print(f"[edgarPricesDaily] {ds} 실패: {exc}", flush=True)
            if i + 1 < len(dates):
                time.sleep(_POLYGON_PACE_SECONDS)
    finally:
        cli.close()

    if not frames:
        print("[edgarPricesDaily] 신규 0 → skip", flush=True)
        return res

    fresh = pl.concat(frames, how="vertical_relaxed")
    if listedOnly:
        try:
            tickers = pl.read_parquet(Path(cfg.dataDir) / "edgar" / "tickers.parquet", columns=["ticker"])
            listed = {str(t).strip().upper() for t in tickers["ticker"].to_list() if t}
            if listed:
                fresh = fresh.filter(pl.col("ticker").is_in(list(listed)))
        except Exception:  # noqa: BLE001 — tickers 부재 → 필터 없이 전체
            pass

    outDir = Path(cfg.dataDir) / "edgar" / "prices"
    outDir.mkdir(parents=True, exist_ok=True)
    recentPath = outDir / "recent.parquet"
    if recentPath.exists():
        try:
            fresh = pl.concat([pl.read_parquet(recentPath), fresh], how="vertical_relaxed")
        except Exception:  # noqa: BLE001 — 손상 recent 무시(신규로 대체)
            pass
    cutoff = (_date.today() - timedelta(days=_RECENT_KEEP_DAYS)).strftime("%Y%m%d")
    fresh = (
        fresh.unique(subset=["ticker", "date"], keep="last").filter(pl.col("date") >= cutoff).sort(["ticker", "date"])
    )
    fresh.write_parquet(recentPath, compression="zstd", statistics=True)
    print(f"[edgarPricesDaily] recent.parquet: {fresh.height}행 ({fresh['ticker'].n_unique()}종목)", flush=True)

    # 스냅샷 패치 — daily(recent ~7일)는 currentPrice·priceUpdated 만 갱신한다(_DAILY_PATCH_FIELDS). returns/
    # 52w/volatility 는 윈도가 짧아 신뢰 불가 → deep 백필(buildSnapshotFromCompanyDir·publish)이 정본이라 기존
    # 값을 덮지 않는다(스냅샷 returns 전부 null 회귀 차단). 신규 ticker(아직 deep 미존재)는 게이트 엔트리만 생성.
    snap: dict = {}
    for tk, grp in fresh.sort("date").group_by("ticker"):
        ticker = str(tk[0] if isinstance(tk, tuple) else tk)
        g2 = grp.sort("date")
        snap[ticker] = _snapshotRow(
            g2["close"].to_list(), g2["high"].to_list(), g2["low"].to_list(), g2["volume"].to_list(), g2["date"][-1]
        )

    if upload:
        from huggingface_hub import HfApi

        from dartlab.core.hfRetry import retryHfCall
        from dartlab.pipeline.hfUpload import _resolveHfToken

        retryHfCall(
            HfApi(token=_resolveHfToken(token)).upload_file,
            path_or_fileobj=str(recentPath),
            path_in_repo="edgar/prices/recent.parquet",
            repo_id=_SNAPSHOT_REPO,
            repo_type="dataset",
            commit_message=f"갱신: edgar/prices/recent ({fresh.height}행)",
        )
        print("[edgarPricesDaily] recent.parquet HF 발행", flush=True)
    try:
        _writeSnapshot(snap, upload=upload, token=token, patchFields=_DAILY_PATCH_FIELDS)
    except Exception as exc:  # noqa: BLE001 — 스냅샷 발행 실패 격리(recent 발행은 성공 유지)
        res.report.failures.append(f"snapshot: {type(exc).__name__}: {exc}")
    return res
