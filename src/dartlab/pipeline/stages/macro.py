"""Macro stage — FRED/ECOS/관세청 거시 + cycle + regime (in-library 흡수).

옛 ``.github/scripts/sync/buildMacro{Data,Cycle,Regime}.py`` 의 오케스트레이션을 stage
함수로 흡수 — ``runScript`` 서브프로세스 위임 제거(edgar/allFilings 패턴). 빌드 본체는
여전히 L1 ``dartlab.gather.{fred,ecos,customs}`` + L2 ``dartlab.macro.{cycles,forecast,
rates,crisis}`` 공개함수 위임이며(별도빌드 0), 본 모듈은 *위치만* 흡수한 얇은
오케스트레이터(루프 + 직렬화 + HF push)다.

``runMacro`` 의 의존게이트: data(rc1) 성공 시에만 cycle·regime 빌드. cycle·regime 은
서로 독립(둘 다 FRED bulk 캐시 공유) — cycle 실패가 regime 빌드를 막지 않는다. source 는
env ``MACRO_SOURCE``(기본 all). HF push 는 stage 내부 + ``token`` 인자(``upload=False`` skip).
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dartlab.pipeline.hfUpload import _resolveHfToken, uploadCategoryToHf
from dartlab.pipeline.types import PipelineMode, StageResult

_REPO_ID = "eddmpython/dartlab-data"


# ──────────────────────────────────────────────────────────────────────────
# data (FRED/ECOS/Customs) — buildMacroData.py 인라인
# ──────────────────────────────────────────────────────────────────────────


def _utcNow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _requireEnv(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} 환경변수 필수 (운영자 macro 벌크 빌드).")
    return value


def _readExisting(outDir: Path):
    import polars as pl

    obsPath = outDir / "observations.parquet"
    manifestPath = outDir / "manifest.parquet"
    obs = pl.read_parquet(obsPath) if obsPath.exists() else pl.DataFrame()
    manifest = pl.read_parquet(manifestPath) if manifestPath.exists() else pl.DataFrame()
    return obs, manifest


def _fallbackSeries(existingObs, seriesId: str):
    import polars as pl

    if existingObs.is_empty() or "seriesId" not in existingObs.columns:
        return pl.DataFrame(schema={"seriesId": pl.Utf8, "date": pl.Date, "value": pl.Float64})
    return existingObs.filter(pl.col("seriesId") == seriesId)


def _stats(df) -> dict[str, object]:
    if df.is_empty():
        return {"rowCount": 0, "startDate": None, "latestDate": None}
    dates = df.get_column("date").drop_nulls()
    if len(dates) == 0:
        return {"rowCount": df.height, "startDate": None, "latestDate": None}
    return {"rowCount": df.height, "startDate": str(dates.min()), "latestDate": str(dates.max())}


def _gradeStatus(status: str, error: str, rowCount: int, source: str, seriesId: str) -> tuple[str, str]:
    """받아온 행이 0 이면 성공으로 적지 않는다.

    세 수집 단계 모두 `status = "ok"` 를 먼저 두고 예외가 날 때만 바꿨다. 그래서 호출이
    멀쩡히 끝나고 0 행을 돌려주면 그대로 성공으로 기록됐다. 실측으로 ECOS 쉰세 지표 중
    열여덟 개가 status ok 에 rowCount 0 이다. 국고채 3·5·10 년, 회사채, 코어 CPI, PPI,
    고용, 소매판매, 실질 GDP 가 그 안에 있다. 소비자는 manifest 를 믿고 지표가 있는 줄
    알았고, 거시 베타 축은 그 GDP 공백 하나 때문에 전종목 빈 표를 냈다.

    Returns:
        (status, error). 빈 수집이면 status 는 "empty" 이고 error 에 사유가 적힌다.
    """
    if status != "ok" or rowCount:
        return status, error
    reason = "수집은 성공했으나 관측 0 행"
    print(f"[{source}] {seriesId}: empty ({reason})", flush=True)
    return "empty", reason


def _write(outDir: Path, observations: list, manifestRows: list[dict]) -> None:
    import polars as pl

    outDir.mkdir(parents=True, exist_ok=True)
    if observations:
        obs = pl.concat(observations, how="diagonal_relaxed")
    else:
        obs = pl.DataFrame(schema={"seriesId": pl.Utf8, "date": pl.Date, "value": pl.Float64})
    obs = obs.with_columns(pl.col("date").cast(pl.Date), pl.col("value").cast(pl.Float64)).sort(["seriesId", "date"])
    manifest = pl.DataFrame(manifestRows)
    obs.write_parquet(outDir / "observations.parquet", compression="zstd")
    manifest.write_parquet(outDir / "manifest.parquet", compression="zstd")
    print(f"[macro] wrote {outDir} observations={obs.height} series={manifest.height}", flush=True)


def _buildFred(outDir: Path) -> None:
    import polars as pl

    from dartlab.gather.fred import Fred
    from dartlab.gather.fred.catalog import getAllEntries

    key = _requireEnv("FRED_API_KEY")
    fred = Fred(apiKey=key)
    existingObs, _ = _readExisting(outDir)
    updatedAt = _utcNow()
    observations: list = []
    manifestRows: list[dict] = []

    for entry in getAllEntries():
        status = "ok"
        err = ""
        try:
            df = fred.series(entry.id)
            df = df.with_columns(pl.lit(entry.id).alias("seriesId")).select("seriesId", "date", "value")
        except Exception as exc:  # noqa: BLE001 — 시리즈 단위 실패는 fallback(stale)·전체 중단 0
            fallback = _fallbackSeries(existingObs, entry.id)
            df = fallback
            status = "stale" if not fallback.is_empty() else "error"
            err = f"{type(exc).__name__}: {exc}"
            print(f"[fred] {entry.id}: {status} ({err})", flush=True)
        observations.append(df)
        st = _stats(df)
        status, err = _gradeStatus(status, err, int(st["rowCount"] or 0), "fred", entry.id)
        manifestRows.append(
            {
                "source": "fred",
                "seriesId": entry.id,
                "label": entry.label,
                "group": entry.group,
                "frequency": entry.frequency,
                "unit": entry.unit,
                "description": entry.description,
                "rowCount": st["rowCount"],
                "startDate": st["startDate"],
                "latestDate": st["latestDate"],
                "providerUpdatedAt": None,
                "updatedAtUtc": updatedAt,
                "status": status,
                "error": err,
            }
        )
    fred.close()
    _write(outDir, observations, manifestRows)


def _buildEcos(outDir: Path) -> None:
    import polars as pl

    from dartlab.gather.ecos import Ecos
    from dartlab.gather.ecos.catalog import getAllIds, getEntry

    key = _requireEnv("ECOS_API_KEY")
    ecos = Ecos(apiKey=key)
    existingObs, _ = _readExisting(outDir)
    updatedAt = _utcNow()
    observations: list = []
    manifestRows: list[dict] = []

    for seriesId in getAllIds():
        entry = getEntry(seriesId)
        if entry is None:
            continue
        status = "ok"
        err = ""
        try:
            df = ecos.series(seriesId)
            df = df.with_columns(pl.lit(seriesId).alias("seriesId")).select("seriesId", "date", "value")
        except Exception as exc:  # noqa: BLE001 — 시리즈 단위 실패는 fallback(stale)·전체 중단 0
            fallback = _fallbackSeries(existingObs, seriesId)
            df = fallback
            status = "stale" if not fallback.is_empty() else "error"
            err = f"{type(exc).__name__}: {exc}"
            print(f"[ecos] {seriesId}: {status} ({err})", flush=True)
        observations.append(df)
        st = _stats(df)
        status, err = _gradeStatus(status, err, int(st["rowCount"] or 0), "ecos", entry.id)
        manifestRows.append(
            {
                "source": "ecos",
                "seriesId": entry.id,
                "label": entry.label,
                "group": entry.group,
                "frequency": entry.frequency,
                "unit": entry.unit,
                "description": entry.description,
                "rowCount": st["rowCount"],
                "startDate": st["startDate"],
                "latestDate": st["latestDate"],
                "providerUpdatedAt": None,
                "updatedAtUtc": updatedAt,
                "status": status,
                "error": err,
            }
        )
    ecos.close()
    _write(outDir, observations, manifestRows)


def _buildCustoms(outDir: Path) -> None:
    import polars as pl

    from dartlab.gather.customs import Customs, getAllEntries

    customs = Customs()  # DATA_GO_KR_KEY 자동 해석 (credentials 레지스트리)
    existingObs, _ = _readExisting(outDir)
    updatedAt = _utcNow()
    observations: list = []
    manifestRows: list[dict] = []

    for entry in getAllEntries():
        status = "ok"
        err = ""
        try:
            df = customs.series(entry.id)  # 월별 수출액(expDlr) 전체 이력
            df = df.with_columns(pl.lit(entry.id).alias("seriesId")).select("seriesId", "date", "value")
        except Exception as exc:  # noqa: BLE001 — 시리즈 단위 실패는 fallback(stale)·전체 중단 0
            fallback = _fallbackSeries(existingObs, entry.id)
            df = fallback
            status = "stale" if not fallback.is_empty() else "error"
            err = f"{type(exc).__name__}: {exc}"
            print(f"[customs] {entry.id}: {status} ({err})", flush=True)
        observations.append(df)
        st = _stats(df)
        status, err = _gradeStatus(status, err, int(st["rowCount"] or 0), "customs", entry.id)
        manifestRows.append(
            {
                "source": "customs",
                "seriesId": entry.id,
                "label": entry.label,
                "group": entry.group,
                "frequency": entry.frequency,
                "unit": entry.unit,
                "description": entry.description,
                "rowCount": st["rowCount"],
                "startDate": st["startDate"],
                "latestDate": st["latestDate"],
                "providerUpdatedAt": None,
                "updatedAtUtc": updatedAt,
                "status": status,
                "error": err,
            }
        )
    customs.close()
    _write(outDir, observations, manifestRows)


def runMacroData(*, source: str = "all", upload: bool = True, token: str | None = None) -> StageResult:
    """FRED/ECOS/관세청 카탈로그 전체 → macro 벌크 parquet 빌드 + HF push.

    ``buildMacroData.py`` 흡수 — ``_buildFred``/``_buildEcos``/``_buildCustoms`` 인라인 후
    ``uploadCategoryToHf('macroFred'|'macroEcos'|'macroCustoms')`` 로 deploy(스크립트
    ``upload_folder(path_in_repo='macro/{subdir}')`` 와 byte 경로 동등 — ``DATA_RELEASES``
    dir 가 ``macro/fred`` 등). source/upload 축은 입구에서 해석한다.

    Args:
        source: 'fred'|'ecos'|'customs'|'all'.
        upload: HF 업로드 여부(False 면 push skip — 로컬 안전).
        token: HF 토큰(인자>env>.env). None+upload 시 ``_resolveHfToken`` 해석.

    Returns:
        StageResult (report.ok=빌드 성공, report.err=빌드 실패, report.fail=push 실패).

    Raises:
        없음 (빌드/업로드 예외는 StageResult 로 격리).

    Example:
        >>> runMacroData(source="fred", upload=False)  # doctest: +SKIP
        StageResult(category='macroData', ...)
    """
    res = StageResult(category="macroData")
    outRoot = Path(os.environ.get("DARTLAB_DATA_DIR", "data")) / "macro"
    try:
        if source in ("fred", "all"):
            _buildFred(outRoot / "fred")
        if source in ("ecos", "all"):
            _buildEcos(outRoot / "ecos")
        if source in ("customs", "all"):
            _buildCustoms(outRoot / "customs")
        res.report.ok = 1
    except Exception as exc:  # noqa: BLE001 — 빌드 실패 격리(다음 sync 자연 회복)
        res.report.err = 1
        res.report.failures.append(f"macroData {source}: {type(exc).__name__}: {exc}")
        print(f"[pipeline] macroData 빌드 실패(격리): {exc}", flush=True)
        return res

    if upload:
        cats = []
        if source in ("fred", "all"):
            cats.append("macroFred")
        if source in ("ecos", "all"):
            cats.append("macroEcos")
        if source in ("customs", "all"):
            cats.append("macroCustoms")
        try:
            for cat in cats:
                uploadCategoryToHf(cat, token=token, fullUpload=True)
        except Exception as exc:  # noqa: BLE001 — 업로드 실패 격리
            res.report.fail = 1
            res.report.failures.append(f"macroData push: {type(exc).__name__}: {exc}")
            print(f"[pipeline] macroData push 실패(격리): {exc}", flush=True)
    return res


# ──────────────────────────────────────────────────────────────────────────
# cycle — buildMacroCycle.py 인라인
# ──────────────────────────────────────────────────────────────────────────


def _analyzeMarketCycle(market: str) -> dict:
    """analyzeCycle 호출 wrapper — 시계열 제거 + computedAt 포함."""
    from dartlab.macro.cycles.cycle import analyzeCycle

    result = analyzeCycle(market=market)
    result.pop("timeseries", None)
    result.setdefault("market", market)
    result["computedAt"] = datetime.now(timezone.utc).isoformat()
    return result


def _buildCycle(outDir: Path) -> dict[str, Path]:
    """KR + US cycle 분석 JSON 빌드."""
    outDir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for market in ("KR", "US"):
        t0 = time.time()
        print(f"[macroCycle] {market} analyzing …", flush=True)
        try:
            result = _analyzeMarketCycle(market)
        except Exception as e:  # noqa: BLE001 — 시장 단위 실패 격리(다른 시장 진행)
            print(f"[macroCycle] {market} 실패: {type(e).__name__}: {e}", flush=True)
            continue
        path = outDir / f"{market.lower()}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=0), encoding="utf-8")
        kb = path.stat().st_size / 1024
        print(
            f"[macroCycle] {market}: phase={result.get('phase')} "
            f"confidence={result.get('confidence')} → {path} ({kb:.1f}KB, {time.time() - t0:.0f}s)",
            flush=True,
        )
        written[market.lower()] = path

    return written


def _deployJson(written: dict[str, Path], *, subdir: str, token: str | None) -> None:
    """HF dataset ``macro/{subdir}/`` 에 KR/US JSON publish (retryHfCall 래핑)."""
    from huggingface_hub import HfApi

    from dartlab.core.hfRetry import retryHfCall

    api = HfApi(token=_resolveHfToken(token))
    for market, path in written.items():
        commit = retryHfCall(
            api.upload_file,
            path_or_fileobj=str(path),
            path_in_repo=f"macro/{subdir}/{market}.json",
            repo_id=_REPO_ID,
            repo_type="dataset",
            commit_message=f"build: macro {subdir} {market}.json",
        )
        print(f"[hf] macro/{subdir}/{market}.json: {getattr(commit, 'commit_url', None)}", flush=True)


def runMacroCycle(*, upload: bool = True, token: str | None = None) -> StageResult:
    """KR/US 경기 국면(cycle) 분석 JSON 빌드 + HF push.

    ``buildMacroCycle.py`` 흡수 — ``analyzeCycle(market)`` for KR/US →
    ``data/macro/cycle/{kr,us}.json`` write → HF ``macro/cycle/{kr,us}.json`` push.
    결과 0건이면 ``report.err``(스크립트 rc=1 동형).

    Args:
        upload: HF 업로드 여부(False 면 push skip).
        token: HF 토큰(인자>env>.env).

    Returns:
        StageResult (report.ok=≥1 시장 산출, report.err=0건, report.fail=push 실패).

    Raises:
        없음 (빌드/업로드 예외는 StageResult 로 격리).

    Example:
        >>> runMacroCycle(upload=False)  # doctest: +SKIP
        StageResult(category='macroCycle', ...)
    """
    res = StageResult(category="macroCycle")
    outDir = Path(os.environ.get("DARTLAB_DATA_DIR", "data")) / "macro" / "cycle"
    written = _buildCycle(outDir)
    if not written:
        res.report.err = 1
        res.report.failures.append("macroCycle: 결과 0 건")
        print("[macroCycle] 결과 0 건 — report.err", flush=True)
        return res
    res.report.ok = 1
    res.rows = len(written)
    if upload:
        try:
            _deployJson(written, subdir="cycle", token=token)
        except Exception as exc:  # noqa: BLE001 — 업로드 실패 격리
            res.report.fail = 1
            res.report.failures.append(f"macroCycle push: {type(exc).__name__}: {exc}")
            print(f"[pipeline] macroCycle push 실패(격리): {exc}", flush=True)
    return res


# ──────────────────────────────────────────────────────────────────────────
# regime — buildMacroRegime.py 인라인
# ──────────────────────────────────────────────────────────────────────────

# 모델별 vintage(staleAfterDays) — 시리즈 cadence 반영(단일 asOf 뭉치기 금지).
_STALE_PROBIT = 7  # T10Y3M 일간
_STALE_SAHM = 45  # UNRATE 월간
_STALE_LEI = 75  # CB-LEI 월간
_STALE_QUARTER = 120  # Hamilton/GaR/regimeBand 분기 GDP(revision 잦음)

# Nelson-Siegel interpretation enum → 한국어 라벨(prose 파싱 0·SSOT 매핑).
_CURVE_LABEL = {"steep_normal": "가파른정상", "normal": "정상", "flat": "평탄", "inverted": "역전"}

# Hamilton regime 분리도 임계 — Cohen's d 중간효과(두 regime 평균차 ≥ 큰쪽 σ의 절반).
_SEPARATION_MIN = 0.5
# LEI 사용가능 구성요소 개수 게이트(전체 10 중 ~6 이상).
_LEI_COMPONENT_RATIO_MIN = 0.6


def _miss(axis: str, e: Exception) -> dict:
    return {"id": axis, "status": "error", "reason": f"{type(e).__name__}: {e}"}


def _lastObsDate(g, seriesId: str) -> str | None:
    """시리즈 최종 관측일(YYYY-MM-DD). gather macro df 의 date 컬럼 max."""
    try:
        df = g.macro(seriesId)
        if df is None or len(df) == 0:
            return None
        dates = df.get_column("date").to_list()
        return str(max(dates))[:10] if dates else None
    # asOf 보조 정보라 실패해도 None 으로 진행
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] macro 최종 관측일 산출 실패: {type(exc).__name__}: {exc}", flush=True)
        return None


def _round5pct(p: float | None) -> float | None:
    """확률 5%p 반올림(probit 점추정 가짜 정밀 가드)."""
    if p is None:
        return None
    return round(round(p * 20) / 20, 2)


def _separation(params: dict) -> float | None:
    """Hamilton regime 분리도 = (mu_exp − mu_con) / max(σ). mu-swap 으로 mu_exp ≥ mu_con."""
    try:
        muExp = params.get("mu_expansion")
        muCon = params.get("mu_contraction")
        sigMax = max(params.get("sigma_expansion", 0.0), params.get("sigma_contraction", 0.0))
        if muExp is None or muCon is None or sigMax <= 0:
            return None
        return round((muExp - muCon) / sigMax, 3)
    except (TypeError, ValueError):
        return None


def _extractForecast(forecast: dict, market: str, g) -> dict:
    """forecast 4모델 추출 + 신뢰성 게이트. 합산 필드 없음(verdict 차단)."""
    models: dict = {}
    missing: list = []
    isUs = market.upper() == "US"
    runDate = datetime.now(timezone.utc).date().isoformat()

    # probit (US 전용) — 항상 산출(스칼라 입력), zone 주역·확률 5%p 보조.
    if isUs:
        rp = forecast.get("recessionProb")
        if rp:
            models["probit"] = {
                "probability": rp.get("probability"),
                "probabilityRounded": _round5pct(rp.get("probability")),
                "zone": rp.get("zone"),
                "zoneLabel": rp.get("zoneLabel"),
                "spread": rp.get("spread"),
                "horizon": "12M",
                "timeKind": "leading",
                "precisionNote": "Estrella-Mishkin 고정계수·표준오차 미산출(점추정)",
                "asOf": _lastObsDate(g, "T10Y3M") or runDate,
                "seriesId": "T10Y3M",
                "staleAfterDays": _STALE_PROBIT,
            }
        else:
            models["probit"] = {"status": "데이터부족·표시 보류"}
    else:
        missing.append({"id": "probit", "status": "notApplicable", "reason": "US 전용"})

    # Sahm (US 전용) — result None(데이터부족) vs 정상계산 둘뿐(dead path 이중게이트 금지).
    if isUs:
        sr = forecast.get("sahmRule")
        if sr is None:
            models["sahm"] = {"status": "데이터부족·표시 보류"}
        else:
            models["sahm"] = {
                "value": sr.get("value"),
                "triggered": sr.get("triggered"),
                "zone": sr.get("zone"),
                "zoneLabel": sr.get("zoneLabel"),
                "horizon": "realtime",
                "timeKind": "trigger(동행)",
                "asOf": _lastObsDate(g, "UNRATE") or runDate,
                "seriesId": "UNRATE",
                "staleAfterDays": _STALE_SAHM,
            }
    else:
        missing.append({"id": "sahm", "status": "notApplicable", "reason": "US 전용"})

    # LEI — US=CB-LEI(개수 게이트), KR=CLI composite(shape 다름).
    lei = forecast.get("lei")
    if isUs:
        if lei:
            avail = lei.get("availableComponents") or 0
            total = lei.get("totalComponents") or 0
            ratio = (avail / total) if total else 0.0
            if ratio >= _LEI_COMPONENT_RATIO_MIN and lei.get("signalLabel") != "데이터부족":
                models["lei"] = {
                    "level": lei.get("level"),
                    "mom6m": lei.get("mom6m"),
                    "signal": lei.get("signal"),
                    "signalLabel": lei.get("signalLabel"),
                    "availableComponents": avail,
                    "totalComponents": total,
                    "overlapNote": "term-spread·initial-claims 내포(probit/Sahm 부분 상관)",
                    "horizon": "6-9M",
                    "timeKind": "leading",
                    "asOf": _lastObsDate(g, "PERMIT") or runDate,
                    "staleAfterDays": _STALE_LEI,
                }
            else:
                models["lei"] = {
                    "status": "구성요소 부족·표시 보류",
                    "availableComponents": avail,
                    "totalComponents": total,
                }
        else:
            models["lei"] = {"status": "구성요소 부족·표시 보류", "availableComponents": 0, "totalComponents": 10}
    else:
        if lei:
            models["lei"] = {
                "cliMomentum": lei.get("cliMomentum"),
                "cliLevel": lei.get("cliLevel"),
                "growthApprox": lei.get("growthApprox"),
                "growthLabel": lei.get("growthLabel"),
                "asOf": _lastObsDate(g, "CLI") or runDate,
                "staleAfterDays": _STALE_LEI,
            }
        else:
            missing.append({"id": "lei", "status": "데이터부족·표시 보류", "reason": "CLI composite 미산출"})

    # Hamilton — US: converged + 분리도 게이트. KR: 단위 parity 미확정·표면화 보류.
    if isUs:
        hr = forecast.get("hamiltonRegime")
        if hr:
            sep = _separation(hr.get("params", {}))
            base = {
                "timeKind": "retrospective",
                "horizon": "동행",
                "staleAfterDays": _STALE_QUARTER,
                "revisionLabel": "분기 GDP·수정 대상",
                "asOf": _lastObsDate(g, "A191RL1Q225SBEA") or runDate,
                "seriesId": "A191RL1Q225SBEA",
                "seriesSource": "FRED",
                "separation": sep,
            }
            if not hr.get("converged"):
                models["hamilton"] = {**base, "contractionProb": None, "converged": False, "status": "EM 미수렴"}
            elif sep is None or sep < _SEPARATION_MIN:
                models["hamilton"] = {**base, "contractionProb": None, "converged": True, "status": "레짐 분리 약함"}
            else:
                models["hamilton"] = {
                    **base,
                    "contractionProb": hr.get("contractionProb"),
                    "converged": True,
                    "iterations": hr.get("iterations"),
                }
        else:
            models["hamilton"] = {"status": "표본 부족·표시 보류"}
    else:
        missing.append(
            {
                "id": "hamilton",
                "status": "단위 parity 미확정·표시 보류",
                "reason": "GROWTH↔A191RL1Q225SBEA 단위 동일성 미확정",
            }
        )

    return {"models": models, "missing": missing}


def _extractRates(r: dict, forecast: dict | None, market: str, g) -> dict:
    """수익률곡선 1줄 — spread=probit.spread 재사용(yieldCurve에 spread 필드 없음),
    curveShape=interpretation enum 한국어 매핑(beta1 부호 직역 금지)."""
    if market.upper() != "US":
        return {"missing": [{"id": "yieldCurve", "status": "notApplicable", "reason": "US 전용"}]}
    yc = r.get("yieldCurve")
    rp = forecast.get("recessionProb") if forecast else None
    spread = rp.get("spread") if rp else None
    if yc is None or spread is None:
        return {"missing": [{"id": "yieldCurve", "status": "missing", "reason": "yieldCurve 또는 spread 부재"}]}
    shape = yc.get("interpretation")
    return {
        "spread10y3m": round(spread, 2),
        "sign": "+" if spread > 0 else "-" if spread < 0 else "",
        "curveShape": shape,
        "curveShapeLabel": _CURVE_LABEL.get(shape, shape),
        "curveSource": "NelsonSiegel.interpretation",
        "asOf": _lastObsDate(g, "T10Y3M") or datetime.now(timezone.utc).date().isoformat(),
        "seriesId": "T10Y3M",
        "staleAfterDays": _STALE_PROBIT,
        "missing": [],
    }


def _extractGaR(g, market: str) -> dict:
    """GaR 4Q 전향 조건부 분포 — growthAtRisk(FCI, GDP YoY%, horizon=4) 직접 호출
    (summary._addGrowthAtRisk 패턴). FCI=NFCI(National Financial Conditions Index)."""
    from dartlab.macro.crisis.growthAtRisk import growthAtRisk
    from dartlab.macro.seriesFetch import fetchSeriesList

    gdpSeries = fetchSeriesList(g, "GDP")
    if not (gdpSeries and len(gdpSeries) >= 20):
        return {"status": "표본 부족·표시 보류"}
    gdpGrowth = [
        ((gdpSeries[i] / gdpSeries[i - 4]) - 1) * 100
        for i in range(4, len(gdpSeries))
        if gdpSeries[i - 4] and gdpSeries[i - 4] > 0
    ]
    fci = fetchSeriesList(g, "NFCI")
    if not (fci and len(fci) >= 20) or not gdpGrowth:
        return {"status": "표본 부족·표시 보류"}
    gar = growthAtRisk(fci, gdpGrowth, horizon=4)
    if not gar:
        return {"status": "표본 부족·표시 보류"}
    return {
        "gar5": gar["currentGaR5"],
        "gar25": gar["currentGaR25"],
        "median": gar["median"],
        "gar75": gar["currentGaR75"],
        "gar95": gar["currentGaR95"],
        "skewness": gar["skewness"],
        "tailRisk": gar["tailRisk"],
        "tailRiskLabel": gar["tailRiskLabel"],
        "currentFCI": gar["currentFCI"],
        "observations": gar["observations"],
        "horizon": 4,
        "timeKind": "forward",
        "seriesNote": "FCI(NFCI 대용) 조건부 GDP 성장률 분위(점추정 아닌 조건부 분포)",
        "asOf": _lastObsDate(g, "GDP") or datetime.now(timezone.utc).date().isoformat(),
        "staleAfterDays": _STALE_QUARTER,
        "revisionLabel": "분기 GDP·수정 대상",
    }


def _extractRegimeBand(g, market: str) -> dict:
    """Hamilton regime band — analyzeForecast가 contractionProb 스칼라만 노출하고
    smoothedProbs 배열을 드롭하므로, cycles.regimeSwitching.hamiltonRegime 을 직접
    호출해 최근 ~24분기 수축확률 열(smoothedProbs[-24:, 1])을 추출한다."""
    from dartlab.macro.cycles.regimeSwitching import hamiltonRegime
    from dartlab.macro.seriesFetch import fetchSeriesList

    gdpVals = fetchSeriesList(g, "A191RL1Q225SBEA")
    if not (gdpVals and len(gdpVals) >= 20):
        return {"status": "표본 부족·표시 보류"}
    hr = hamiltonRegime(gdpVals, maxIter=50)
    sep = _separation(hr.params)
    asOf = _lastObsDate(g, "A191RL1Q225SBEA") or datetime.now(timezone.utc).date().isoformat()
    if not hr.converged:
        return {"status": "EM 미수렴", "converged": False, "separation": sep}
    if sep is None or sep < _SEPARATION_MIN:
        return {"status": "레짐 분리 약함", "converged": True, "separation": sep}
    band = [round(float(x), 4) for x in hr.smoothedProbs[-24:, 1]]
    return {
        "band": band,
        "converged": True,
        "separation": sep,
        "timeKind": "retrospective",
        "horizon": "동행",
        "asOf": asOf,
        "staleAfterDays": _STALE_QUARTER,
    }


def _analyzeRegime(market: str) -> dict:
    """단일 시장 regime payload — forecast 4모델 + rates 곡선 + GaR + regime band.
    축별 try/except(전체 중단 0·실패는 missing payload)."""
    from dartlab.macro.forecast.forecast import analyzeForecast
    from dartlab.macro.rates.rates import analyzeRates
    from dartlab.macro.seriesFetch import getGather

    g = getGather(None)
    out: dict = {"market": market.upper(), "computedAt": datetime.now(timezone.utc).isoformat()}

    forecast = None
    try:
        forecast = analyzeForecast(market=market)
        out["forecast"] = _extractForecast(forecast, market, g)
    except Exception as e:  # noqa: BLE001 — forecast 축 실패는 missing payload(전체 중단 0)
        out["forecast"] = {"models": {}, "missing": [_miss("forecast", e)]}

    try:
        r = analyzeRates(market=market)
        out["rates"] = _extractRates(r, forecast, market, g)
    except Exception as e:  # noqa: BLE001 — rates 축 실패는 missing payload
        out["rates"] = {"missing": [_miss("rates", e)]}

    if market.upper() == "US":
        try:
            out["gar"] = _extractGaR(g, market)
        except Exception as e:  # noqa: BLE001 — gar 축 실패는 missing payload
            out["gar"] = {"status": "표본 부족·표시 보류", "missing": [_miss("gar", e)]}
        try:
            out["regimeBand"] = _extractRegimeBand(g, market)
        except Exception as e:  # noqa: BLE001 — regimeBand 축 실패는 missing payload
            out["regimeBand"] = {"missing": [_miss("regimeBand", e)]}

    return out


def _buildRegime(outDir: Path) -> dict[str, Path]:
    """KR + US regime payload JSON 빌드."""
    outDir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for market in ("KR", "US"):
        t0 = time.time()
        print(f"[macroRegime] {market} analyzing …", flush=True)
        try:
            result = _analyzeRegime(market)
        except Exception as e:  # noqa: BLE001 — 시장 단위 실패 격리(다른 시장 진행)
            print(f"[macroRegime] {market} 실패: {type(e).__name__}: {e}", flush=True)
            continue
        path = outDir / f"{market.lower()}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=0), encoding="utf-8")
        kb = path.stat().st_size / 1024
        nModels = len(result.get("forecast", {}).get("models", {}))
        print(
            f"[macroRegime] {market}: models={nModels} → {path} ({kb:.1f}KB, {time.time() - t0:.0f}s)",
            flush=True,
        )
        written[market.lower()] = path

    return written


def runMacroRegime(*, upload: bool = True, token: str | None = None) -> StageResult:
    """KR/US forecast 4모델 + 수익률곡선 + GaR + Hamilton regime band JSON 빌드 + HF push.

    ``buildMacroRegime.py`` 흡수 — ``_analyzeRegime`` for KR/US →
    ``data/macro/regime/{kr,us}.json`` write → HF ``macro/regime/{kr,us}.json`` push.
    축별 try/except 는 헬퍼에 보존(전체 중단 0). 결과 0건이면 ``report.err``.

    Args:
        upload: HF 업로드 여부(False 면 push skip).
        token: HF 토큰(인자>env>.env).

    Returns:
        StageResult (report.ok=≥1 시장 산출, report.err=0건, report.fail=push 실패).

    Raises:
        없음 (빌드/업로드 예외는 StageResult 로 격리).

    Example:
        >>> runMacroRegime(upload=False)  # doctest: +SKIP
        StageResult(category='macroRegime', ...)
    """
    res = StageResult(category="macroRegime")
    outDir = Path(os.environ.get("DARTLAB_DATA_DIR", "data")) / "macro" / "regime"
    written = _buildRegime(outDir)
    if not written:
        res.report.err = 1
        res.report.failures.append("macroRegime: 결과 0 건")
        print("[macroRegime] 결과 0 건 — report.err", flush=True)
        return res
    res.report.ok = 1
    res.rows = len(written)
    if upload:
        try:
            _deployJson(written, subdir="regime", token=token)
        except Exception as exc:  # noqa: BLE001 — 업로드 실패 격리
            res.report.fail = 1
            res.report.failures.append(f"macroRegime push: {type(exc).__name__}: {exc}")
            print(f"[pipeline] macroRegime push 실패(격리): {exc}", flush=True)
    return res


# ──────────────────────────────────────────────────────────────────────────
# orchestrator — runMacro (runScript 제거, in-library 호출)
# ──────────────────────────────────────────────────────────────────────────
#
# ⛔ 거시 forward 시뮬(BVAR 팬)은 *별도 데이터 빌드/배선 금지* — 런타임 pyodide 에서
# `dartlab.macro('시뮬레이션')` 직접 실행(이미 클라이언트에 있는 observations 사용).
# 새 macro/sim 아티팩트·HF publish 없음. 엔진 = src/dartlab/macro/simulate (SSOT).


def runMacro(
    *, category: str = "macro", mode: PipelineMode = "recent", codes=None, upload: bool = True, token=None
) -> StageResult:
    """거시 FRED/ECOS/관세청 + cycle + regime — in-library 흡수 오케스트레이션.

    data(rc1) 성공 시에만 cycle·regime 빌드(둘 다 FRED bulk 캐시 공유). cycle·regime 은
    서로 독립 — cycle 실패가 regime 빌드를 막지 않는다. source 는 env ``MACRO_SOURCE``.

    Args:
        category: 카테고리 라벨.
        mode: 미사용.
        codes: 미사용.
        upload: HF 업로드 여부(하위 3 stage 로 전파).
        token: HF 토큰(하위 stage 로 전파).

    Returns:
        StageResult.

    Raises:
        없음.

    Example:
        >>> runMacro(upload=False)  # doctest: +SKIP
        StageResult(category='macro', ...)
    """
    source = os.environ.get("MACRO_SOURCE", "all")
    res = StageResult(category="macro")
    rData = runMacroData(source=source, upload=upload, token=token)
    cycleOk = regimeOk = True
    if rData.report.err == 0:  # rc1==0 게이트 (FRED bulk 캐시 공유)
        rCycle = runMacroCycle(upload=upload, token=token)  # cycle·regime 상호 독립
        rRegime = runMacroRegime(upload=upload, token=token)
        cycleOk = rCycle.report.err == 0
        regimeOk = rRegime.report.err == 0
    else:
        cycleOk = regimeOk = False
    if rData.report.err or rData.report.fail or not cycleOk or not regimeOk:
        res.report.err = 1
        res.report.failures.append(f"macro data:{rData.report.err}/cycle:{int(not cycleOk)}/regime:{int(not regimeOk)}")
    else:
        res.report.ok = 1
    return res
