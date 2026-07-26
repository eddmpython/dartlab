"""edgarPanel stage (Job 3) — EDGAR panel **per-filing 증분** + deploy.

원본=SSOT 전략([[project_original_ssot_strategy]]): EDGAR = panel only(fetch→build→raw 폐기).
EDGAR full-submission ``.txt`` 는 로컬 원본으로 저장하지 않는다. daily-index/submissions 로 발견한
``txt_url`` 을 메모리로 fetch 한 뒤 바로 panel parser 에 넘기고, 산출물은
``data/edgar/panel/{ticker}.parquet`` 단일 artifact 다.

  ① SEC daily-index(``master.idx``)로 최근 N일 재무 공시 발견(윈도 일수만큼의 요청).
  ② cik→상장 universe ticker 매핑 → 영향 ticker 만 추림.
  ③ 영향 ticker 의 기존 ``edgar/panel`` 을 HF 에서 selective seed.
  ④ seed 성공(기존 종목) → 신규 accession text 만 받아 ``appendFilingTextsToPanel``(중복 dedup).
     404(신규 종목) → 전체 history text fetch + ``buildEdgarPanel(overwrite=True)``.
  ⑤ 변경 ticker 만 deploy.

``EDGAR_FULL_REBUILD=1`` 이면 전 universe archive+재빌드 부트스트랩(무겁다 — 디스크 floor 가드 +
dispatch 전용). lookback 은 ``SYNC_LOOKBACK_DAYS``/``EDGAR_LOOKBACK`` env(기본 7).

알려진 한계: 정정 보고서(``10-K/A`` 등 amended form)는 현재 discovery/parse 에서 제외 —
원본 form 만 반영(staleness, 손상 X). 정정 supersede 는 dedup 키를 accession→period 로 바꾸는
후속 작업 필요(regular form 은 period 가 고유라 안전하나 별도 검증 동반). → TODO.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import date, timedelta
from pathlib import Path

from dartlab.pipeline.types import PipelineMode, StageResult

_REGULAR_FORMS = ("10-K", "10-Q", "20-F", "40-F")

# full-rebuild resumable ledger — panel dir 의 *부모*(edgar/)에 둔다. panel dir 동거 시
# tree 열거(seed._remoteTreeFiles)·prebuild stem 추출이 가짜 code 로 오염(전문에이전트 치명결함).
_REBUILD_LEDGER_REMOTE = "edgar/_rebuildState.json"
# 한 배치 빌드 후 1회 HF upload + ledger push. 작을수록 timeout 손실면↓, commit(412)횟수↑ (전문에이전트 권장 100).
_REBUILD_BATCH = int(os.environ.get("EDGAR_REBUILD_BATCH") or "100")
# 루프 시간 가드(분) — job timeout 보다 충분히 작게(upload·ledger·412 backoff 여유). 기본 320 (350분 timeout 기준).
_REBUILD_DEADLINE_MIN = int(os.environ.get("EDGAR_REBUILD_DEADLINE_MIN") or "320")


def _recentDates(days: int) -> list[str]:
    """오늘 포함 최근 ``days`` 일의 YYYYMMDD 리스트(최신→과거)."""
    today = date.today()
    return [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]


def _universeTickerByCik() -> dict[str, list[str]]:
    """상장 universe 의 ``{cik(10-pad): [ticker, ...]}`` 맵 — daily-index cik 를 ticker 로 해소.

    한 CIK 가 여러 ticker(주식 클래스 GOOG/GOOGL, BRK.A/BRK.B 등)를 가지므로 **list** 로
    모은다 — 단일 맵이면 한 클래스만 갱신되고 나머지는 영구 stale.

    Returns:
        dict[str, list[str]] — cik→ticker list. universe 부재/컬럼 부재 시 빈 dict(honest skip).
    """
    try:
        from dartlab.core.dataLoader import loadEdgarListedUniverse

        # 일간 증분은 universe 를 *강제 갱신* — TTL(24h) 안의 stale universe 면 지난 24h 신규 상장
        # (IPO)의 CIK 가 빠져 daily-index 의 그 공시가 조용히 누락되고 0 changed 로 녹색 보고된다.
        # forceUpdate fetch 실패 시엔 universe.updateListedUniverse 가 stale 캐시를 서빙(무중단).
        uni = loadEdgarListedUniverse(forceUpdate=True)
    # universe 부재면 상위가 0 changed 로 보고한다.
    except Exception as exc:  # noqa: BLE001
        # 이 자리의 침묵은 신규 상장 공시 누락을 녹색 보고로 바꿔 놓기 때문에 반드시 남긴다.
        print(f"[pipeline] edgarPanel universe 로드 실패: {type(exc).__name__}: {exc}", flush=True)
        return {}
    if "cik" not in uni.columns or "ticker" not in uni.columns:
        return {}
    out: dict[str, list[str]] = {}
    for c, t in zip(uni["cik"].to_list(), uni["ticker"].to_list()):
        if t and c is not None:
            out.setdefault(str(c).strip().zfill(10), []).append(str(t).strip())
    return out


def _seedTickerPanel(ticker: str, *, token: str | None) -> bool | None:
    """영향 ticker 의 기존 panel 을 HF 에서 받아 로컬 배치 — append 전제.

    Returns:
        bool | None — True=기존 panel seed(증분 append 대상), False=404 신규 종목(full build),
        None=일시 실패(이번 run skip).
    """
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError

    import dartlab.config as cfg
    from dartlab.core.dataConfig import HF_REPO
    from dartlab.core.hfRetry import retryHfCall
    from dartlab.pipeline.hfUpload import _resolveHfToken

    root = str(Path(cfg.dataDir))
    tok = _resolveHfToken(token)
    try:
        retryHfCall(
            hf_hub_download,
            repo_id=HF_REPO,
            repo_type="dataset",
            filename=f"edgar/panel/{ticker.upper()}.parquet",
            token=tok,
            local_dir=root,
        )
    except (EntryNotFoundError, RepositoryNotFoundError):
        return False  # 신규 종목 — HF 미존재(404)
    except Exception as exc:  # noqa: BLE001 — 일시 실패 → skip(다음 run)
        # 근본 원인 관측화 — 호출부는 None 만 받아 exc 를 잃으므로 여기서 1줄 남긴다(간헐 패턴 추적).
        print(f"[pipeline] edgarPanel seed {ticker} panel 일시실패: {type(exc).__name__}: {exc}", flush=True)
        return None
    return True


def _flattenFetched(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    """``fetchFilingTexts`` grouped result → record list."""
    return [rec for records in grouped.values() for rec in records]


def _runIncremental(res: StageResult, *, lookback: int, upload: bool, token: str | None) -> StageResult:
    """per-filing 증분: daily-index 발견 → 영향 ticker append/build → 변경분 deploy."""
    from dartlab.gather.original.edgar.collect import (
        fetchFilingTexts,
        listRecentFilings,
    )
    from dartlab.gather.original.edgar.submissions import listAllFilings
    from dartlab.providers.edgar.panel.build import (
        appendFilingTextsToPanel,
        buildEdgarPanel,
        existingAccessions,
    )

    dates = _recentDates(lookback)

    # 0. builder cik 해소용 tickers.parquet 보장(클린 러너엔 부재 — 없으면 신규 종목 full-build 가
    #    cik 미해소로 0행). loadTickers 가 SEC company_tickers.json(UA 설정)로 자체 생성.
    try:
        from dartlab.gather.edgar.identity import loadTickers

        loadTickers(refresh=False)
    except Exception as exc:  # noqa: BLE001 — 실패해도 진행(해소 안 되는 신규 종목만 skip)
        res.report.failures.append(f"edgar tickers seed: {type(exc).__name__}: {exc}")

    # 1. 최근 공시 발견 (daily-index, 재무 폼만)
    try:
        rows = listRecentFilings(dates, forms=_REGULAR_FORMS)
    except Exception as exc:  # noqa: BLE001 — 발견 실패 격리
        res.report.err = 1
        res.report.failures.append(f"edgar listRecent: {type(exc).__name__}: {exc}")
        print(f"[pipeline] edgarPanel listRecent 실패(격리): {exc}", flush=True)
        return res

    # 2. cik → 상장 universe ticker(주식클래스 다중) 매핑 → CIK 그룹
    tickerByCik = _universeTickerByCik()
    if not tickerByCik:
        # universe 는 loadEdgarListedUniverse 가 SEC 에서 자체 fetch — 비면 SEC 차단/장애 등
        # *진짜 실패*다. 조용한 ok(녹색) 가 아니라 err=1 로 CI 를 red 로(silent no-op 방지).
        res.report.err = 1
        res.report.failures.append("edgar universe 부재(listedUniverse SEC fetch 실패) — 증분 불가")
        print("[pipeline] edgarPanel: universe 부재 → 실패(err)", flush=True)
        return res
    byCik: dict[str, list] = {}
    for r in rows:
        if r["cik"] in tickerByCik:
            byCik.setdefault(r["cik"], []).append(r)
    if not byCik:
        res.report.ok = 1
        print(f"[pipeline] edgarPanel: 최근 {lookback}일 universe 신규 재무공시 0", flush=True)
        return res

    sinceYear = int(os.environ.get("EDGAR_SINCE_YEAR") or "2015")
    changed: list[str] = []
    for cik, crows in byCik.items():
        cikComplete = True  # 이 CIK 의 모든 ticker 가 완전 처리됐는가 — report 용
        for ticker in tickerByCik[cik]:  # 한 CIK 의 모든 ticker(공유 클래스 전부 갱신)
            try:
                seeded = _seedTickerPanel(ticker, token=token)
                if seeded is None:
                    res.report.failures.append(f"edgar seed {ticker}: 일시 실패 skip(다음 run 재시도)")
                    cikComplete = False
                    continue
                if seeded:  # 기존 종목 — 신규 accession 만 append
                    existing = existingAccessions(ticker)
                    newRows = [r for r in crows if r["accession_no"] not in existing]
                    if not newRows:
                        continue
                    records = _flattenFetched(fetchFilingTexts(newRows))
                    if len(records) < len(newRows):
                        res.report.failures.append(
                            f"edgar existing {ticker}: fetch {len(records)}/{len(newRows)} → skip(다음 run 재시도)"
                        )
                        cikComplete = False
                        continue
                    stat = appendFilingTextsToPanel(ticker, records, verbose=False)
                    if stat["appended"]:
                        changed.append(ticker)
                else:  # 신규 종목 — 전체 history text fetch + 빌드
                    history = listAllFilings(ticker, forms=list(_REGULAR_FORMS), sinceYear=sinceYear)
                    records = _flattenFetched(fetchFilingTexts(history))
                    if len(records) < len(history):
                        res.report.failures.append(
                            f"edgar new {ticker}: fetch {len(records)}/{len(history)} → 불완전, skip(다음 run 재시도)"
                        )
                        cikComplete = False
                        continue
                    stat = buildEdgarPanel(ticker, records, overwrite=True, verbose=False)
                    if stat.get("rows"):
                        changed.append(ticker)
            except Exception as exc:  # noqa: BLE001 — ticker 단위 격리(1건 실패가 run 중단 X)
                res.report.failures.append(f"edgar ticker {ticker}: {type(exc).__name__}: {exc}")
                cikComplete = False
                continue
        if not cikComplete:
            continue

    res.rows = len(changed)
    res.changedFiles = [f"{t.upper()}.parquet" for t in changed]
    res.report.ok = 1
    print(f"[pipeline] edgarPanel 증분: 영향 CIK {len(byCik)} 중 {len(changed)} ticker 변경", flush=True)

    # 3. deploy(변경분만)
    if upload and changed:
        from dartlab.pipeline.hfUpload import uploadCategoryToHf

        cf = [f"{t.upper()}.parquet" for t in changed]
        for cat in ("edgarPanel",):
            try:
                uploadCategoryToHf(cat, changedFiles=cf, token=token)
            except Exception as exc:  # noqa: BLE001 — deploy 격리
                res.report.fail = 1
                res.report.failures.append(f"deploy {cat}: {type(exc).__name__}: {exc}")
                print(f"[pipeline] edgarPanel deploy {cat} 실패(격리): {exc}", flush=True)
    return res


def _priorityTickers() -> list[str]:
    """재빌드 처리 순서 — sp500 먼저, 그 다음 tier="all"(Nasdaq+NYSE+CBOE, OTC 제외). dedup·upper.

    universe 에 시총/거래량 컬럼이 없어(SEC 원본 부재) sp500 교차 + exchange tier 가 '가치 큰 종목
    우선'의 최선 근사. OTC 는 대부분 재무공시 부재라 제외(tier="all" 이 이미 OTC 제외). 신규 상장
    반영 위해 호출 전 universe 캐시를 force 갱신한다(_runFullRebuild 가 수행).

    Returns:
        list[str] — 우선순위 정렬된 대문자 ticker (중복 제거).
    """
    from dartlab.core.dataLoader import _loadSp500Tickers, loadEdgarTargetUniverse

    out: list[str] = []
    seen: set[str] = set()

    def _add(tickers: list) -> None:
        for t in tickers:
            u = str(t).strip().upper() if t else ""
            if u and u not in seen:
                seen.add(u)
                out.append(u)

    _add(_loadSp500Tickers() or [])
    try:
        _add(loadEdgarTargetUniverse(tier="all")["ticker"].to_list())
    except (OSError, KeyError, ValueError) as exc:
        print(f"[pipeline] edgarPanel priority universe 일부 실패(sp500 만): {exc}", flush=True)
    return out


def _loadRebuildLedger(token: str | None) -> set[str]:
    """HF rebuild 진행 ledger(완료 ticker 집합) 로드. 부재/파손 시 빈 set(처음부터 — 재빌드 idempotent)."""
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError

    from dartlab.core.dataConfig import HF_REPO
    from dartlab.core.hfRetry import retryHfCall

    try:
        p = retryHfCall(
            hf_hub_download,
            repo_id=HF_REPO,
            repo_type="dataset",
            filename=_REBUILD_LEDGER_REMOTE,
            token=token,
        )
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        return {str(t).upper() for t in data} if isinstance(data, list) else set()
    except (EntryNotFoundError, RepositoryNotFoundError):
        return set()
    except Exception as exc:  # noqa: BLE001 — 파손/일시 실패 → 빈 set(중복 빌드는 idempotent)
        print(f"[pipeline] edgarPanel ledger 로드 실패 → 처음부터: {type(exc).__name__}: {exc}", flush=True)
        return set()


def _saveRebuildLedger(done: set[str], token: str | None) -> None:
    """완료 ticker 집합을 HF ledger(`edgar/_rebuildState.json`)로 push — 다음 run 재개 기준."""
    from huggingface_hub import HfApi

    from dartlab.core.dataConfig import HF_REPO
    from dartlab.core.hfRetry import retryHfCall
    from dartlab.pipeline.hfUpload import _resolveHfToken

    payload = json.dumps(sorted(done), ensure_ascii=False).encode("utf-8")
    retryHfCall(
        HfApi().upload_file,
        path_or_fileobj=payload,
        path_in_repo=_REBUILD_LEDGER_REMOTE,
        repo_id=HF_REPO,
        repo_type="dataset",
        token=_resolveHfToken(token),
        commit_message=f"edgar rebuild ledger: {len(done)} done",
    )


def _publishTickers(token: str | None) -> None:
    """ticker↔CIK 맵(tickers.parquet)을 HF ``edgar/tickers/`` 로 publish (S0.2).

    finance=cik·panel=ticker 이중키라 퍼블릭 브라우저가 ticker→cik 를 해소하려면 이 맵이
    HF(DATA_RELEASES ``edgarTickers``)에 있어야 한다. 엔진은 로컬 flat 직독, 브라우저는
    HF range-fetch. 최신 SEC company_tickers.json 반영 후 업로드(idempotent overwrite).

    Args:
        token: HF 토큰(None=env/.env 해소).

    Raises:
        없음 — 호출부가 격리(실패는 failures 기록).
    """
    from huggingface_hub import HfApi

    import dartlab.config as cfg
    from dartlab.core.dataConfig import HF_REPO
    from dartlab.core.hfRetry import retryHfCall
    from dartlab.pipeline.hfUpload import _resolveHfToken

    try:
        from dartlab.gather.edgar.identity import loadTickers

        loadTickers(refresh=True)  # 최신 company_tickers.json 반영
    except Exception:  # noqa: BLE001 — 신선화 실패해도 기존 캐시 업로드
        pass

    src = Path(cfg.dataDir) / "edgar" / "tickers.parquet"
    if not src.exists():
        return
    try:
        _enrichTickerGaps(src)  # company_tickers.json 누락 sp500(BK·CTRA·HOLX) browse-edgar 보강
    except Exception:  # noqa: BLE001 — 보강 실패해도 기본 맵 업로드
        pass
    retryHfCall(
        HfApi().upload_file,
        path_or_fileobj=str(src),
        path_in_repo="edgar/tickers/tickers.parquet",
        repo_id=HF_REPO,
        repo_type="dataset",
        token=_resolveHfToken(token),
        commit_message="edgar tickers map publish (S0.2)",
    )


def _enrichTickerGaps(src: "Path") -> None:
    """universe 에 있으나 company_tickers.json 에 없는 ticker 를 browse-edgar CIK 로 보강.

    SEC ``company_tickers.json`` 은 일부 활성 sp500(Coterra CTRA·Hologic HOLX·BNY Mellon BK)을
    누락한다 → 발행 맵(tickers.parquet)도 그 종목을 빠뜨려 브라우저가 finance(cik-keyed)를 못
    해소한다. universe gap 을 browse-edgar 정본 인덱스로 채워 발행 맵을 universe-완전하게 한다.
    gap 은 소수(실측 3종)라 bounded. 해소 실패분은 조용히 skip(원문 맵 유지).

    Args:
        src: ``data/edgar/tickers.parquet`` 경로(in-place 보강).

    Raises:
        없음 — 호출부가 격리.
    """
    import polars as pl

    from dartlab.gather.original.edgar.submissions import _browseEdgarCik

    df = pl.read_parquet(str(src))
    if "ticker" not in df.columns or "cik" not in df.columns:
        return
    have = set(df["ticker"].cast(pl.Utf8).str.to_uppercase().to_list())
    gap = [t for t in _priorityTickers() if t not in have]
    # df 스키마 무관(3-col company_tickers.json or 6-col universe) — 모든 컬럼 null 초기화 후
    # ticker/cik/title 만 채운다(브라우저는 ticker↔cik 만 소비, 나머지는 null 허용).
    rows: list[dict] = []
    for t in gap:
        cik = _browseEdgarCik(t)
        if not cik:
            continue
        row: dict = {c: None for c in df.columns}
        row["ticker"] = t
        row["cik"] = cik
        if "title" in row:
            row["title"] = t
        rows.append(row)
    if not rows:
        return
    extra = pl.DataFrame(rows, schema={c: df.schema[c] for c in df.columns})
    pl.concat([df, extra], how="vertical").write_parquet(str(src))


def _flushRebuildBatch(
    uploaded: list[str], processed: list[str], done: set[str], *, upload: bool, token: str | None
) -> None:
    """배치 마감 — rows>0 ticker 만 HF upload(+로컬 삭제로 디스크 확보) → processed 전부 ledger 기록·push.

    upload 성공분만 로컬 panel 을 unlink(다음 ticker 빌드는 SEC 에서 새로 받으므로 무손실). ledger 는
    processed 전부 기록(재무공시 0행도 '처리완료'로 — 매 run 재fetch 방지). 배치 후 짧은 sleep 으로
    commit rate(412 빈도) 완화.
    """
    from dartlab.pipeline.hfUpload import uploadCategoryToHf
    from dartlab.providers.edgar.panel.build.builder import panelPath

    if upload and uploaded:
        uploadCategoryToHf("edgarPanel", changedFiles=[f"{t}.parquet" for t in uploaded], token=token)
        for t in uploaded:
            panelPath(t).unlink(missing_ok=True)  # 업로드 성공분 로컬 삭제(러너 디스크 floor)
    done.update(processed)
    if upload:
        _saveRebuildLedger(done, token)
        time.sleep(8)  # commit rate 완화(412 conflict 빈도 ↓)


def _runFullRebuild(res: StageResult, *, upload: bool, token: str | None) -> StageResult:
    """전 universe 재빌드 부트스트랩 — resumable(ledger) + 배치 upload + 시간가드(dispatch 전용).

    universe(Nasdaq+NYSE+CBOE) × SEC fetch(5 req/s)는 단일 job(≤360분)으로 물리적 불가 → HF ledger
    (`edgar/_rebuildState.json`)로 완료 ticker 를 건너뛰며 여러 run 에 걸쳐 누적한다. 빌드한 배치마다
    즉시 HF upload(`changedFiles`) + ledger push 라 timeout(취소) 손실이 '진행 중 1배치'로 bounded
    (옛 all-at-end = 3시간 전부 손실 회귀 차단). 처리 순서 sp500→exchange tier(가치 우선).
    """
    import dartlab.config as cfg

    floor = float(os.environ.get("EDGAR_DISK_FLOOR_GB") or "5")
    probe = Path(cfg.dataDir)
    while not probe.exists() and probe != probe.parent:  # 미존재/상대경로 대비 — 존재하는 상위로
        probe = probe.parent
    freeGb = shutil.disk_usage(str(probe)).free / 1e9
    if freeGb < floor:
        res.report.err = 1
        res.report.failures.append(f"edgar full-rebuild: 디스크 {freeGb:.1f}GB < floor {floor}GB — 중단")
        print(f"[pipeline] edgarPanel full-rebuild 중단: 디스크 {freeGb:.1f}GB", flush=True)
        return res

    try:
        from dartlab.core.dataLoader import loadEdgarListedUniverse
        from dartlab.gather.original.edgar.collect import fetchFilingTexts
        from dartlab.gather.original.edgar.submissions import listAllFilings
        from dartlab.providers.edgar.panel.build import buildEdgarPanel

        loadEdgarListedUniverse(forceUpdate=True)  # 신규 상장 반영 — 이후 _priorityTickers 가 캐시 read
        if upload:  # S0.2 — ticker↔CIK 맵 publish(브라우저 식별자 해소). run 당 1회.
            try:
                _publishTickers(token)
            except Exception as exc:  # noqa: BLE001 — publish 실패해도 rebuild 진행
                res.report.failures.append(f"edgar tickers publish: {type(exc).__name__}: {exc}")
        tickers = _priorityTickers()
        done = _loadRebuildLedger(token) if upload else set()
        pending = [t for t in tickers if t not in done]
        sinceYear = int(os.environ.get("EDGAR_SINCE_YEAR") or "2015")
        deadline = time.monotonic() + _REBUILD_DEADLINE_MIN * 60
        print(
            f"[pipeline] edgarPanel full-rebuild: universe {len(tickers)} / 완료 {len(done)} / "
            f"잔여 {len(pending)} (배치 {_REBUILD_BATCH}, 시간가드 {_REBUILD_DEADLINE_MIN}분)",
            flush=True,
        )

        totalRows = 0
        uploaded: list[str] = []
        processed: list[str] = []
        timedOut = False
        for ticker in pending:
            if time.monotonic() > deadline:
                timedOut = True
                break
            try:
                history = listAllFilings(ticker, forms=list(_REGULAR_FORMS), sinceYear=sinceYear)
                records = _flattenFetched(fetchFilingTexts(history))
                if len(records) < len(history):  # 불완전 fetch — ledger 기록 안 함(다음 run 재시도)
                    res.report.failures.append(f"edgar full {ticker}: fetch {len(records)}/{len(history)} → skip")
                    continue
                stat = buildEdgarPanel(ticker, records, overwrite=True, verbose=False)
                totalRows += int(stat.get("rows", 0))
                processed.append(ticker)  # 재무공시 0행도 '처리완료'(매 run 재fetch 방지)
                if stat.get("rows"):
                    uploaded.append(ticker)
            except Exception as exc:  # noqa: BLE001 — ticker 단위 격리(ledger 기록 안 함 → 재시도)
                res.report.failures.append(f"edgar full {ticker}: {type(exc).__name__}: {exc}")
                continue
            if len(processed) >= _REBUILD_BATCH:
                _flushRebuildBatch(uploaded, processed, done, upload=upload, token=token)
                uploaded, processed = [], []
        if processed:  # 잔여 배치
            _flushRebuildBatch(uploaded, processed, done, upload=upload, token=token)

        res.rows = totalRows
        res.report.ok = 1
        remaining = len([t for t in tickers if t not in done])
        print(
            f"[pipeline] edgarPanel full-rebuild {'중단(시간가드)' if timedOut else '완료'}: "
            f"누적 {len(done)}/{len(tickers)} (잔여 {remaining}, 이번 run +{totalRows:,} rows)",
            flush=True,
        )
        if remaining:
            res.report.failures.append(f"edgar full-rebuild 잔여 {remaining} — 다음 run/dispatch 재개")
    except Exception as exc:  # noqa: BLE001 — 전역 격리
        res.report.err = 1
        res.report.failures.append(f"edgar full-rebuild: {type(exc).__name__}: {exc}")
        print(f"[pipeline] edgarPanel full-rebuild 실패(격리): {exc}", flush=True)
    return res


def runEdgarPanel(
    *,
    category: str = "edgarPanel",
    mode: PipelineMode = "incremental",
    codes: list[str] | None = None,
    upload: bool = True,
    token: str | None = None,
) -> StageResult:
    """EDGAR panel per-filing 증분(기본) 또는 전 universe 부트스트랩(``EDGAR_FULL_REBUILD=1``).

    Args:
        category: 미사용("edgarPanel" 고정).
        mode: ``"full"``/``"backfill"`` 이면 전 universe 부트스트랩(``EDGAR_FULL_REBUILD=1`` 동치).
            그 외(기본 incremental)는 per-filing 증분.
        codes: 미사용(daily-index 발견 기반).
        upload: HF deploy(edgarPanel) 여부.
        token: HF 토큰.

    Returns:
        StageResult (rows=변경 ticker 수[증분]/총행수[full], changedFiles=변경 parquet).

    Raises:
        없음 (발견/seed/build/deploy 예외는 StageResult 로 격리).

    Example:
        >>> runEdgarPanel(upload=False)  # doctest: +SKIP
        StageResult(category='edgarPanel', ...)
    """
    res = StageResult(category="edgarPanel")
    fullRebuild = os.environ.get("EDGAR_FULL_REBUILD") == "1" or mode in ("full", "backfill")
    if fullRebuild:
        return _runFullRebuild(res, upload=upload, token=token)
    lookback = int(os.environ.get("SYNC_LOOKBACK_DAYS") or os.environ.get("EDGAR_LOOKBACK") or "7")
    return _runIncremental(res, lookback=lookback, upload=upload, token=token)
