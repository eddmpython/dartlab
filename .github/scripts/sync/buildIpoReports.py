"""신규상장 IPO 공모분석 리포트 베이크 + HF push. 퍼블릭 터미널 직독 SSOT.

상장 전 발행사(corp_cls=E)의 증권신고서(지분증권)는 allFilings(Y/K 한정)·panel 어디에도 없다.
퍼블릭 터미널(정적, 백엔드 0)은 DART 원문 fetch(키 비밀 + CORS)도 파이썬 파서(parseIpoProspectus)도
런타임에 못 돌린다. 그래서 퍼블릭엔 이 리포트의 SSOT 가 *부재*한다. 이 스크립트가 그 SSOT 를 처음
생산한다. online DART→parse→HF push (allFilings·scan 과 동일 sync 데이터모델, 우회 굽기 아님).

파서·렌더는 story.buildIpoReport 그대로 위임(엔진 재구현 0). 본 스크립트는 발굴·호출·직렬화·push 배관만.
최근 윈도(85 일, list.json 3 개월 제한)만 rebuild. 상장 후 발행사는 일반 Y/K 종목이 되어 aging out.
발행사 ~30 곳이라 파일 KB~수백KB(1.5MB 임계 하). HF 증식 아님(단일 파일 매 cron 덮어씀).

산출 = ``dart/ipo/reports.parquet`` (rcept 키). 컬럼: 발굴 메타 + 알림용 스칼라(왓치 eval_new_ipo 소비,
scan("ipo") 컬럼명 호환) + reportJson(터미널 ipoReportSource 직독, 전체 IpoReport). 왓치가 첫 관문:
notify-watch cron 이 이 베이크를 먼저 돌려(리포트 HF 등재) 그다음 푸시(딥링크 목적지 리포트가 이미 존재).

Usage:
    uv run python -X utf8 .github/scripts/sync/buildIpoReports.py [--no-push] [--date-from YYYYMMDD]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import polars as pl

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES, repoFor
from dartlab.core.logger import getLogger

_log = getLogger(__name__)

_KEY = "ipoReports"
_NAME = "reports.parquet"
_WINDOW_DAYS = 85  # list.json corp_code 없으면 3 개월 제한(실측 status 100). scan/ipo.py 와 동일.
_MAX_BYTES = 1_536 * 1024  # hfRange WHOLE_FILE_MAX_BYTES. 초과 시 whole-file GET 분기 falldown 가드.

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


def _discover(client, dateFrom: str | None, verbose: bool) -> list[dict]:
    """listFilings(corp_cls=E, C001) → 발행사별 {full 신고서, 확정공모가 doc}. classifyIpo 위임(재구현 0).

    TS groupIpoFilings 미러의 파이썬본: 발행사(corp_code)별 최신 FULL 신고서(초판·기재정정, 발행조건확정
    제외) + 최신 [발행조건확정] doc. FULL 이 윈도 밖(확정만 잔존)이면 제외(파싱 대상 없음).
    """
    from dartlab.gather.dart.disclosure import listFilings
    from dartlab.providers.dart.securitiesRegistration import classifyIpo

    end = date.today()
    start = end - timedelta(days=_WINDOW_DAYS)
    if dateFrom and len(dateFrom) == 8:
        cand = date(int(dateFrom[:4]), int(dateFrom[4:6]), int(dateFrom[6:8]))
        start = max(start, cand)
    df = listFilings(
        client,
        start=start.strftime("%Y%m%d"),
        end=end.strftime("%Y%m%d"),
        corpClass="E",
        filingType="C",
        fetchAll=True,
    )
    if df.height == 0:
        return []

    byCorp: dict[str, dict] = {}
    for r in df.iter_rows(named=True):
        reportNm = r.get("report_nm") or ""
        c = classifyIpo(reportNm, r.get("corp_cls") or "", r.get("stock_code") or "", r.get("corp_name") or "")
        if not c["isIpo"]:
            continue
        cc = r["corp_code"]
        slot = byCorp.setdefault(cc, {"full": None, "conf": None})
        if "발행조건확정" in reportNm:  # CORRECTION doc(6 섹션 없음). 확정공모가 병합용, 파싱 대상 아님.
            if slot["conf"] is None or r["rcept_no"] > slot["conf"]["rcept_no"]:
                slot["conf"] = r
        elif c["kind"] == "prospectus":
            if slot["full"] is None or r["rcept_no"] > slot["full"]["rcept_no"]:
                slot["full"] = {**r, "_isSpac": c["isSpac"]}
    out = [v for v in byCorp.values() if v["full"] is not None]
    if verbose:
        _log.info("IPO 발굴: %s~%s · 발행사 %d 곳", start, end, len(out))
    return out


def build(*, dateFrom: str | None = None, verbose: bool = True) -> Path:
    """발굴 → buildIpoReport(단일 파싱) → 구조화 typed reports.parquet(rcept 키). 로컬 경로 반환."""
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
    _log.info("[build] %d 발행사 → %s (%.0f KB)", dfOut.height, dest, size / 1024)
    return dest


def push(dest: Path, token: str) -> None:
    """reports.parquet → HF dart/ipo/. buildAllFilingsRecent.push 동형(retryHfCall + HfApi)."""
    from huggingface_hub import HfApi

    from dartlab.core.hfRetry import retryHfCall

    relDir = DATA_RELEASES[_KEY]["dir"]
    api = HfApi(token=token)
    retryHfCall(
        api.upload_file,
        path_or_fileobj=str(dest),
        path_in_repo=f"{relDir}/{_NAME}",
        repo_id=repoFor(_KEY),
        repo_type="dataset",
        commit_message=f"ipo {_NAME}: 신규상장 공모분석 리포트 (증권신고서 6카테고리 파싱본)",
    )
    _log.info("[HF up] pushed %s/%s -> %s", relDir, _NAME, repoFor(_KEY))


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

    dest = build(dateFrom=args.date_from)
    if args.no_push:
        return 0
    token = _resolveToken()
    if not token:
        # 미설정 = 롤아웃 전 graceful no-op (watch.py·send.py 동형). 로컬 parquet 은 빌드됨(왓치 직독).
        # genuine-failure(빌드·파싱·사이즈가드·push 예외)만 비-0 종료 → notify-watch assert 스텝이 job RED.
        print("[HF up] HF_TOKEN 없음. push skip (롤아웃 전 no-op, 로컬 빌드 완료)", file=sys.stderr)
        return 0
    push(dest, token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
