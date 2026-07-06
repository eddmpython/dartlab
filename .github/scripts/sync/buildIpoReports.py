"""신규상장 IPO 공모분석 리포트 베이크 + HF push. 퍼블릭 터미널 직독 SSOT.

상장 전 발행사(corp_cls=E)의 증권신고서(지분증권)는 allFilings(Y/K 한정)·panel 어디에도 없다.
퍼블릭 터미널(정적, 백엔드 0)은 DART 원문 fetch(키 비밀 + CORS)도 파이썬 파서(parseIpoProspectus)도
런타임에 못 돌린다. 그래서 퍼블릭엔 이 리포트의 SSOT 가 *부재*한다. 이 스크립트가 그 SSOT 를 처음
생산한다. online DART→parse→HF push (allFilings·scan 과 동일 sync 데이터모델, 우회 굽기 아님).

발굴/그룹핑은 scan.ipo._discoverIpoIssuers(단일 SSOT), 파서·렌더는 story.buildIpoReport 위임(재구현 0).
본 스크립트는 호출·직렬화·push 배관만. 발굴 윈도는 최근 85 일(list.json 3 개월 제한). 상장 후 발행사는
일반 Y/K 종목이 되어 윈도 밖으로 나간다.

산출 2 파일 (buildAllFilingsRecent 의 recent/market_recent 2파일 분리 미러):
  - ``dart/ipo/reports.parquet`` = 라이브 롤링(최근 85 일, 발행사 ~30 곳, 수백KB). 터미널 whole-file 직독 +
    왓치 eval_new_ipo 소비(scan("ipo") 컬럼명 호환 스칼라) + reportJson(전체 IpoReport). 매 cron 덮어씀.
  - ``dart/ipo/history.parquet`` = 누적 아카이브(전 발행사 영구, rcept 키). 기존 HF history 를 baseline 으로
    merge·dedup·무trim 하여 윈도 밖으로 나간 발행사 리포트도 영구 보존(aging out 소실 방지). corpCode 정렬
    row-group range-fetch 대상이라 1.5MB whole-file 게이트 미적용. 이력이 커지면 실측 후 연 샤딩 승격.

왓치가 첫 관문: notify-watch cron 이 이 베이크를 먼저 돌려(리포트 HF 등재) 그다음 푸시(딥링크 목적지 리포트가 이미 존재).

Usage:
    uv run python -X utf8 .github/scripts/sync/buildIpoReports.py [--no-push] [--date-from YYYYMMDD]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import polars as pl

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES, repoFor
from dartlab.core.logger import getLogger

# 발굴/그룹핑은 scan.ipo._discoverIpoIssuers(단일 SSOT) 위임, 파싱은 story.buildIpoReport 위임. datetime 직접 불요.

_log = getLogger(__name__)

_KEY = "ipoReports"
_NAME = "reports.parquet"  # 라이브 롤링(최근 85일, 터미널 whole-file 직독, 1.5MB 게이트).
_HISTORY_NAME = "history.parquet"  # 누적 아카이브(전 발행사 영구, rcept 키, HF baseline merge, range-fetch).
_WINDOW_DAYS = 85  # = dartlab.scan.ipo.IPO_WINDOW_DAYS (SSOT). test_buildIpoReports 가 동치 강제(드리프트 가드).
_MAX_BYTES = 1_536 * 1024  # hfRange WHOLE_FILE_MAX_BYTES. reports.parquet(라이브) 한정 가드.
_HISTORY_ROW_GROUP = 1_000  # history 는 corpCode row-group range-fetch 대상. whole-file 1.5MB 게이트 미적용.

# 알림 스칼라는 scan("ipo") 컬럼명과 동일(왓치 eval_new_ipo 가 df 무변경 소비) + 발굴 메타 + reportJson.
_SCHEMA = {
    "rcept": pl.Utf8,
    "corpCode": pl.Utf8,
    "corpName": pl.Utf8,
    "rceptDt": pl.Utf8,
    "isSpac": pl.Boolean,
    "corrected": pl.Boolean,
    "confirmationRcept": pl.Utf8,
    "priceBandLow": pl.Float64,
    "priceBandHigh": pl.Float64,
    "subscription": pl.Utf8,
    "appliedPer": pl.Float64,
    "reportJson": pl.Utf8,
}


def ipoReportsPath() -> Path:
    """로컬 reports.parquet 경로. 왓치가 같은 runner 에서 직독(HF 왕복 회피). DATA_RELEASES SSOT 경유."""
    d = Path(_cfg.dataDir) / DATA_RELEASES[_KEY]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d / _NAME


def _historyPath() -> Path:
    """로컬 history.parquet 경로(누적 아카이브). reports 와 같은 DATA_RELEASES dir."""
    d = Path(_cfg.dataDir) / DATA_RELEASES[_KEY]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d / _HISTORY_NAME


def _hfHistoryBase() -> pl.DataFrame | None:
    """기존 HF history.parquet (있으면). append 누적의 baseline. buildAllFilingsRecent._hfBaseFrame 미러.

    최초 빌드(파일 부재)·영구 실패면 None(다음 cron 자가복구). transient 는 retryHfCall 이 흡수.
    """
    from dartlab.core.hfRetry import retryHfCall

    relDir = DATA_RELEASES[_KEY]["dir"]
    url = f"https://huggingface.co/datasets/{repoFor(_KEY)}/resolve/main/{relDir}/{_HISTORY_NAME}"
    try:
        return retryHfCall(pl.read_parquet, url)
    except Exception:  # noqa: BLE001 . 부재/영구실패 = None(첫 빌드 또는 다음 cron 복구)
        return None


def buildHistory(dfLive: pl.DataFrame, *, mergeHf: bool = True) -> Path:
    """라이브 롤링 프레임 + 기존 HF history baseline 을 rcept 로 union·dedup → 무trim 영구 아카이브.

    reports.parquet(85일 라이브, 터미널 직독)은 불변. 윈도 밖으로 나간 발행사 리포트까지 rcept 키로 영구
    보존(list.json 3개월 제한이라 재발굴 불가, 소실 시 되돌릴 수 없음). buildAllFilingsRecent recent.parquet
    누적 패턴 미러. corpCode 정렬 row-group range-fetch 대상(whole-file 1.5MB 게이트 없음).
    """
    frames = [dfLive]
    if mergeHf:
        base = _hfHistoryBase()
        if base is not None:
            frames.append(base)
    hist = pl.concat(frames, how="diagonal_relaxed")
    # 각 신고서(rcept) 1행. 정정본·확정본도 별 rcept 라 전 lifecycle 보존. dfLive 먼저라 재파싱 개선분 우선.
    hist = hist.unique(subset=["rcept"], keep="first")
    hist = hist.sort(["corpCode", "rceptDt"], descending=[False, True])
    dest = _historyPath()
    hist.write_parquet(dest, compression="zstd", row_group_size=_HISTORY_ROW_GROUP)
    _log.info("[history] %d 신고서 누적 -> %s (%.0f KB)", hist.height, dest, dest.stat().st_size / 1024)
    return dest


def _discover(client, dateFrom: str | None, verbose: bool) -> list[dict]:
    """발행사별 {full 신고서, 확정공모가 doc}. scan.ipo._discoverIpoIssuers 위임(발굴/그룹핑 단일 SSOT, 재구현 0)."""
    from dartlab.scan.ipo import _discoverIpoIssuers

    issuers, _asOf = _discoverIpoIssuers(client, dateFrom=dateFrom, includeConfirmation=True, verbose=verbose)
    return issuers


def build(*, dateFrom: str | None = None, verbose: bool = True) -> tuple[Path, Path]:
    """발굴 → buildIpoReport(단일 파싱) → 라이브 reports.parquet + 누적 history.parquet. (라이브, 아카이브) 경로."""
    from dartlab.core.dartClient import DartClient
    from dartlab.story.ipoReport import buildIpoReport

    client = DartClient()
    issuers = _discover(client, dateFrom, verbose)
    rows: list[dict] = []
    for i, it in enumerate(issuers, start=1):
        full = it["full"]
        conf = it["conf"]
        rcept = full["rcept_no"]
        corpName = full.get("corp_name")
        confRcept = conf["rcept_no"] if conf else None
        if verbose:
            _log.info("  [%d/%d] %s 리포트 빌드", i, len(issuers), corpName)
        report = buildIpoReport(rcept, corpName=corpName, confirmationRcept=confRcept)
        summary = report.get("summary") or {}
        band = summary.get("priceBand") or [None, None]
        rows.append(
            {
                "rcept": rcept,
                "corpCode": full.get("corp_code"),
                "corpName": corpName,
                "rceptDt": full.get("rcept_dt"),
                "isSpac": bool(full.get("_isSpac")),
                "corrected": "기재정정" in (full.get("report_nm") or ""),
                "confirmationRcept": confRcept,
                "priceBandLow": band[0] if band else None,
                "priceBandHigh": band[1] if band else None,
                "subscription": summary.get("subscription"),
                "appliedPer": summary.get("peerPer"),
                "reportJson": json.dumps(report, ensure_ascii=False),
            }
        )

    dfOut = pl.DataFrame(rows, schema_overrides=_SCHEMA)
    if dfOut.height:
        dfOut = dfOut.sort("rceptDt", descending=True)
    dest = ipoReportsPath()
    dfOut.write_parquet(dest, compression="zstd")
    size = dest.stat().st_size
    if size > _MAX_BYTES:
        raise SystemExit(
            f"[ipo] {dest.name} {size / 1e6:.2f}MB > {_MAX_BYTES / 1e6:.2f}MB 임계. whole-file GET 분기 "
            f"falldown 위험. 윈도(_WINDOW_DAYS={_WINDOW_DAYS}) 축소 또는 reportJson 슬림 필요."
        )
    _log.info("[build] %d 발행사 라이브 -> %s (%.0f KB)", dfOut.height, dest, size / 1024)
    # 누적 아카이브(영구, rcept 키, HF baseline merge). reports.parquet 라이브 경로는 위에서 이미 확정.
    histDest = buildHistory(dfOut)
    return dest, histDest


def push(dest: Path, token: str, name: str = _NAME) -> None:
    """parquet -> HF dart/ipo/{name}. buildAllFilingsRecent.push 동형(retryHfCall + HfApi, 파일당 name)."""
    from huggingface_hub import HfApi

    from dartlab.core.hfRetry import retryHfCall

    relDir = DATA_RELEASES[_KEY]["dir"]
    api = HfApi(token=token)
    retryHfCall(
        api.upload_file,
        path_or_fileobj=str(dest),
        path_in_repo=f"{relDir}/{name}",
        repo_id=repoFor(_KEY),
        repo_type="dataset",
        commit_message=f"ipo {name}: 신규상장 공모분석 리포트 (증권신고서 6카테고리 파싱본)",
    )
    _log.info("[HF up] pushed %s/%s -> %s", relDir, name, repoFor(_KEY))


def _resolveToken() -> str:
    token = os.environ.get("HF_TOKEN", "")
    if token:
        return token
    envp = Path(_cfg.__file__).resolve().parents[2] / ".env"
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="신규상장 IPO 공모분석 리포트 베이크 + HF push")
    ap.add_argument("--no-push", action="store_true", help="빌드만, HF push 생략")
    ap.add_argument("--date-from", default=None, help="YYYYMMDD 이상만(기본 최근 85 일)")
    args = ap.parse_args()

    dest, histDest = build(dateFrom=args.date_from)
    if args.no_push:
        return 0
    token = _resolveToken()
    if not token:
        # 미설정 = 롤아웃 전 graceful no-op (watch.py·send.py 동형). 로컬 parquet 은 빌드됨(왓치 직독).
        # genuine-failure(빌드·파싱·사이즈가드·push 예외)만 비-0 종료 -> notify-watch assert 스텝이 job RED.
        print("[HF up] HF_TOKEN 없음. push skip (롤아웃 전 no-op, 로컬 빌드 완료)", file=sys.stderr)
        return 0
    push(dest, token, _NAME)  # 라이브 롤링(터미널 직독)
    push(histDest, token, _HISTORY_NAME)  # 누적 아카이브(영구 보존)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
