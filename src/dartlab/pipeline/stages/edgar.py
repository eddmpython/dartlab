"""EDGAR stage — daily 벌크(companyfacts.zip) + 분기 데이터셋(sub/pre/tag) 동형.

edgarSync 의 daily core 2 스텝(inline python)을 충실 재현 — companyfacts bulk
download+convert + 최신 4 분기 discover/download/convert. force 플래그는 env
EDGAR_FORCE_COMPANYFACTS/EDGAR_FORCE_QUARTERLY. (docs/panel/scan 은 조건부·별 캐시라
별 스텝 유지.) build 만(로컬 parquet) — HF deploy 는 별 스텝.
"""

from __future__ import annotations

import os
from pathlib import Path

from dartlab.pipeline.types import PipelineMode, StageResult

# HF dataset 은 디렉터리 하나에 파일 10,000 개까지만 받는다. 넘기는 커밋은 300 개 원자 배치 전체가 400 이다.
_HF_DIR_FILE_LIMIT = 10_000
# 누락분 회복(재발행) 때 한 run 이 떠안는 발행·financeStmt bake 상한 (bake 실측 약 1.5 초/회사).
# 넘는 분량은 원장에 남아 다음 run 이 이어 받는다.
_MAX_FINANCE_PUBLISH_PER_RUN = 1_500
# companyfacts 변경분 중 HF 발행을 마치지 못한 파일 원장. zip·변환 스탬프와 같은 bulk cache 경로라
# 같은 run 의 재시도와 다음 날 run 으로 이월된다.
_FINANCE_PENDING_NAME = "financeHfPending.txt"


def _fourQuarters(year: int, quarter: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for i in range(4):
        q, y = quarter - i, year
        while q <= 0:
            q += 4
            y -= 1
        out.append((y, q))
    return out


def _cikToTicker() -> dict[str, str]:
    """universe ticker↔CIK 맵 — CIK(zero-pad 10) → ticker(대문자). 부재 시 빈 dict.

    Returns:
        dict[str, str] — {cik10: ticker}. 한 CIK 다중 ticker 면 첫 행(보통주 우선).
    """
    try:
        from pathlib import Path

        import polars as pl

        import dartlab.config as cfg

        tk = pl.read_parquet(Path(cfg.dataDir) / "edgar" / "tickers.parquet")
        out: dict[str, str] = {}
        for row in tk.iter_rows(named=True):
            cik = str(row.get("cik", "")).strip().zfill(10)
            ticker = str(row.get("ticker", "")).strip().upper()
            if cik and ticker and cik not in out:
                out[cik] = ticker
        return out
    # 맵 부재면 stmt 발행만 skip 하고 raw 빌드는 진행
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] edgar cik→ticker 맵 산출 실패: {type(exc).__name__}: {exc}", flush=True)
        return {}


def _bakeTerminalFinanceStmt(changedFin: list[str], *, upload: bool, token) -> int:
    """changed-universe CIK 의 companyfacts → 터미널 financeStmt(DART 동형) bake + HF 증분 발행.

    raw companyfacts(edgar/finance)는 백엔드 파사드용. 본 스텝은 파사드 ``Company.panel`` 표준화를
    빌드타임에 ``edgar/financeStmt/{ticker}.parquet`` 으로 구워 브라우저 터미널이 KR=dart/finance 와
    동일 reader 로 직독하게 한다(16 카드 동일 배선).

    Args:
        changedFin: 변경된 "{cik}.parquet" 목록(universe 필터 후).
        upload: True 면 변경분만 ``edgar/financeStmt`` 로 HF 증분 발행.
        token: HF 토큰(None=env).

    Returns:
        int — bake 성공한 회사 수.
    """
    if not changedFin:
        return 0
    from pathlib import Path

    import dartlab.config as cfg
    from dartlab.company import Company
    from dartlab.providers.edgar.finance.terminalStmt import bakeTerminalFinance

    cik2tk = _cikToTicker()
    if not cik2tk:
        print("[pipeline] edgar financeStmt: ticker 맵 부재 → bake skip", flush=True)
        return 0
    outDir = Path(cfg.dataDir) / "edgar" / "financeStmt"
    outDir.mkdir(parents=True, exist_ok=True)
    changedStmt: list[str] = []
    nOk = 0
    for fn in changedFin:
        cik = fn.removesuffix(".parquet").strip().zfill(10)
        ticker = cik2tk.get(cik)
        if not ticker:
            continue
        try:
            # facade Company 를 pipeline 에서 만들어 주입(provider 는 상향 facade import 불가).
            df = bakeTerminalFinance(ticker, company=Company(ticker))
        except Exception as exc:  # noqa: BLE001 — 개별 회사 실패 격리(나머지 진행)
            print(f"[pipeline] edgar financeStmt bake 실패({ticker}): {exc}", flush=True)
            continue
        if df is None or df.height == 0:
            continue
        df.write_parquet(outDir / f"{ticker}.parquet", compression="zstd", statistics=True)
        changedStmt.append(f"{ticker}.parquet")
        nOk += 1
    if changedStmt:
        from dartlab.pipeline.changed import writeChanged

        writeChanged("edgarFinanceStmt", changedStmt)
        if upload:
            from dartlab.pipeline.hfUpload import uploadCategoryToHf

            n = uploadCategoryToHf("edgarFinanceStmt", changedFiles=changedStmt, token=token)
            print(f"[pipeline] edgar financeStmt HF 발행: {n}개 (universe 변경분)", flush=True)
    return nOk


def _universeCiks() -> set[str]:
    """edgar/finance HF 발행 대상 universe CIK(10-pad) 집합.

    HF 는 디렉터리당 10,000 파일 한도가 있어 전 SEC filer(~17k)를 flat 으로 못 올린다. panel 과
    동일하게 *상장 universe*(sp500 + Nasdaq/NYSE/CBOE)로 scope — 터미널 표시 종목 전부 커버하며
    한도 밑(~6k). 비-universe filer 는 로컬엔 변환돼 있고(백엔드 직독) HF 미러만 제외.

    Returns:
        set[str]: universe CIK(zero-pad 10). tickers/universe 부재 시 빈 set(상위가 발행 중단).
    """
    try:
        import polars as pl

        from dartlab.gather.edgar.identity import loadTickers
        from dartlab.pipeline.stages.edgarPanel import _priorityTickers

        universe = {str(t).strip().upper() for t in _priorityTickers() if str(t).strip()}
        if not universe:
            raise RuntimeError("상장 ticker universe가 비어 있음")

        tickerFrame = loadTickers(refresh=False)
        required = {"ticker", "cik"}
        if not required.issubset(tickerFrame.columns):
            missing = sorted(required - set(tickerFrame.columns))
            raise RuntimeError(f"ticker map 필수 컬럼 누락: {missing}")

        hit = tickerFrame.filter(pl.col("ticker").cast(pl.Utf8).str.to_uppercase().is_in(list(universe)))
        ciks = {str(c).strip().zfill(10) for c in hit["cik"].to_list() if str(c).strip()}
        if not ciks:
            raise RuntimeError("상장 universe와 ticker map의 CIK 교집합이 비어 있음")
        return ciks
    # universe 산출 실패면 빈 집합을 반환하고 호출자가 공개 발행을 fail-closed 처리한다.
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] edgar universe CIK 산출 실패: {type(exc).__name__}: {exc}", flush=True)
        return set()


def _readFinancePending(path: Path) -> set[str]:
    """HF 발행을 마치지 못한 finance 파일("{cik}.parquet") 원장을 읽는다. 없으면 빈 set."""
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _writeFinancePending(path: Path, files: set[str]) -> None:
    """원장을 원자적으로 쓴다. 남은 파일이 없으면 원장을 지운다."""
    if not files:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text("\n".join(sorted(files)) + "\n", encoding="utf-8")
    tmp.replace(path)


def _splitByHfCapacity(files: list[str], remote: set[str]) -> tuple[list[str], list[str]]:
    """HF 디렉터리 한도 안에서 (발행 가능, 보류할 신규) 로 나눈다. 입력 순서를 유지한다.

    이미 HF 에 있는 파일의 갱신은 파일 수를 늘리지 않으므로 항상 발행한다. 신규 파일은 남은 자리만큼만.
    """
    room = max(_HF_DIR_FILE_LIMIT - len(remote), 0)
    publishable: list[str] = []
    blocked: list[str] = []
    for name in files:
        if name in remote:
            publishable.append(name)
        elif room > 0:
            publishable.append(name)
            room -= 1
        else:
            blocked.append(name)
    return publishable, blocked


def _publishFinance(candidates: list[str], pendingPath: Path, *, token, res: StageResult) -> list[str]:
    """universe 변경분을 ``edgar/finance`` 로 발행하고 이번 run 에 실제로 올린 파일 목록을 돌려준다.

    후보 전체를 먼저 원장에 적고 업로드가 끝난 파일만 지운다. 변환 단계가 해시 매니페스트와 스탬프를
    업로드 전에 "처리됨" 으로 남기므로, 원장이 없으면 업로드 실패분이 재시도(같은 run attempt 2) 와
    다음 날 run 에서 사라진다(2026-07-11 이후 누락 원인). HF 디렉터리 한도를 넘길 신규 파일은 보류해
    원장에 남기고 fail 로 드러내며, 기존 파일 갱신은 계속 발행한다.
    """
    from dartlab.pipeline.hfUpload import uploadCategoryToHf
    from dartlab.pipeline.seed import listRemoteFiles

    _writeFinancePending(pendingPath, set(candidates))
    remote = {rel.rsplit("/", 1)[-1] for rel in listRemoteFiles("edgar", token=token)}
    publishable, blocked = _splitByHfCapacity(candidates, remote)
    batch = publishable[:_MAX_FINANCE_PUBLISH_PER_RUN]
    if len(publishable) > len(batch):
        print(
            f"[pipeline] edgar finance: 이번 run 발행 {len(batch)}건, {len(publishable) - len(batch)}건은 다음 run 으로 이월",
            flush=True,
        )
    if blocked:
        res.report.fail += 1
        res.report.failures.append(
            f"edgar/finance HF 디렉터리 {len(remote)}/{_HF_DIR_FILE_LIMIT} 파일로 신규 CIK {len(blocked)}건 발행 보류"
            f" (universe 밖 잔존 파일 정리 필요): {blocked[:5]}"
        )
    if not batch:
        return []
    n = uploadCategoryToHf("edgar", changedFiles=batch, token=token)
    _writeFinancePending(pendingPath, set(candidates) - set(batch))
    print(f"[pipeline] edgar finance HF 발행: {n}개 (universe 변경분)", flush=True)
    return batch


def runEdgar(
    *, category: str = "edgar", mode: PipelineMode = "recent", codes=None, upload: bool = True, token=None
) -> StageResult:
    """EDGAR daily 벌크 + 분기 데이터셋 — providers.edgar.bulk(gather 위임) 동형 호출.

    Args:
        category: 카테고리 라벨.
        mode: 미사용.
        codes: 미사용.
        upload: True 면 companyfacts 변경분(detectChanged)만 ``edgar/finance`` 로 HF 증분
            발행. 분기 벌크(meta)는 별 스텝/deploy 가 담당.
        token: HF 토큰(uploadCategoryToHf 위임, None=env).

    Returns:
        StageResult (bulk/quarterly 부분 실패는 격리 기록).

    Raises:
        없음.

    Example:
        >>> runEdgar()  # doctest: +SKIP
        StageResult(category='edgar', ...)
    """
    from dartlab.providers.edgar.bulk import (
        convertBulkToParquets,
        convertQuarterlyToParquets,
        discoverLatestQuarter,
        downloadCompanyfactsBulk,
        downloadQuarterlyDataset,
        listLocalQuarters,
    )

    res = StageResult(category="edgar")

    # 1. daily 벌크: companyfacts.zip → {cik}.parquet (변경분만 증분 + HF 발행)
    #    브라우저 터미널은 HF 직독이라 edgar/finance 도 미러 필요 — detectChanged 로 그날 공시한
    #    회사만 올린다(16,600 전체 재업로드 회피). deploy.py 의 옛 "finance HF 미러링 없음" 정책은
    #    백엔드(사용자 PC 자동 다운로드) 전용 가정 — 퍼블릭 패리티엔 본 스텝이 finance 를 발행.
    try:
        forceCf = os.environ.get("EDGAR_FORCE_COMPANYFACTS") == "true"
        zipPath = downloadCompanyfactsBulk(force=forceCf, progress=False)
        print(f"[pipeline] edgar companyfacts zip: {zipPath}", flush=True)
        stat = convertBulkToParquets(zipPath=zipPath, progress=False, detectChanged=True)
        print(f"[pipeline] edgar convert: {stat}", flush=True)
        changedFin = stat.get("changed") or []
        pendingPath = Path(zipPath).parent / _FINANCE_PENDING_NAME
        pending = _readFinancePending(pendingPath) if upload else set()
        # 누락분 일괄 회복 스위치 (workflow_dispatch republishFinance). 로컬 universe 파일 전체를 후보로
        # 올리고, 상한을 넘는 분량은 원장으로 다음 run 에 이월한다.
        republish = upload and os.environ.get("EDGAR_REPUBLISH_FINANCE") == "true"
        if changedFin or pending or republish:
            # HF 디렉터리당 10k 파일 한도 + panel 과 동일 scope 일관 → universe(상장 universe)만 발행.
            # 비-universe(무명·상폐) filer 는 로컬엔 있으나(백엔드 _loadFacts 직독) HF 미러 제외.
            uniCiks = _universeCiks()
            if not uniCiks:
                raise RuntimeError("EDGAR 상장 universe를 확인할 수 없어 edgar/finance 공개 발행을 중단함")
            import dartlab.config as cfg
            from dartlab.core.dataConfig import DATA_RELEASES

            financeDir = Path(cfg.dataDir) / DATA_RELEASES["edgar"]["dir"]

            def _isPublishable(name: str) -> bool:
                return name.removesuffix(".parquet") in uniCiks and (financeDir / name).exists()

            carried = sorted(name for name in pending if _isPublishable(name))
            extra = sorted(p.name for p in financeDir.glob("*.parquet") if _isPublishable(p.name)) if republish else []
            # 그날 변경분을 먼저 두어 상한에 걸려도 최신 공시가 먼저 나간다.
            changedFin = list(dict.fromkeys([*(f for f in changedFin if _isPublishable(f)), *carried, *extra]))
            from dartlab.pipeline.changed import writeChanged

            writeChanged("edgar", changedFin)
            if upload and changedFin:
                changedFin = _publishFinance(changedFin, pendingPath, token=token, res=res)
            # 터미널 financeStmt bake — 변경분 companyfacts → 파사드 표준화 → DART 동형 발행.
            # raw(위)는 백엔드 파사드용·financeStmt(여기)는 브라우저 터미널 직독용(동일 배선).
            # 업로드 모드에서는 이번 run 에 실제 발행한 회사만 bake 해 raw 와 financeStmt 가 어긋나지 않게 한다.
            try:
                _bakeTerminalFinanceStmt(changedFin, upload=upload, token=token)
            except Exception as exc:  # noqa: BLE001 — financeStmt bake 실패 격리(raw 발행은 성공 유지)
                res.report.failures.append(f"financeStmt: {type(exc).__name__}: {exc}")
                print(f"[pipeline] edgar financeStmt 실패(격리): {exc}", flush=True)
        res.report.ok += 1
    except Exception as exc:  # noqa: BLE001 — bulk 실패 격리(quarterly 진행)
        res.report.err += 1
        res.report.failures.append(f"companyfacts: {type(exc).__name__}: {exc}")
        print(f"[pipeline] edgar companyfacts 실패(격리): {exc}", flush=True)

    # 2. 분기 벌크: 최신 4 분기 discover/download/convert
    try:
        forceQ = os.environ.get("EDGAR_FORCE_QUARTERLY") == "true"
        latest = discoverLatestQuarter()
        if latest is None:
            print("[pipeline] edgar 분기 감지 실패 — skip", flush=True)
            res.report.skip += 1
        else:
            have = set(listLocalQuarters(kind="sub"))
            for y, q in _fourQuarters(*latest):
                if not forceQ and (y, q) in have:
                    continue
                zp = downloadQuarterlyDataset(y, q, force=forceQ)
                if zp is None:
                    print(f"[pipeline] edgar {y}Q{q} 다운로드 실패", flush=True)
                    continue
                print(
                    f"[pipeline] edgar {y}Q{q}: {list(convertQuarterlyToParquets(y, q, zipPath=zp).keys())}", flush=True
                )
            res.report.ok += 1
    except Exception as exc:  # noqa: BLE001 — quarterly 실패 격리
        res.report.err += 1
        res.report.failures.append(f"quarterly: {type(exc).__name__}: {exc}")
        print(f"[pipeline] edgar quarterly 실패(격리): {exc}", flush=True)

    return res
