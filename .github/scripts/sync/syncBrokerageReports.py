"""증권사 리서치 메타 sync — gather 수집 + 월별 parquet write + changed manifest + HF push + 헬스 게이트.

online sync (외부 게시판 → 로컬 parquet → HF). 별도빌드 금지: 스크랩·파싱·ticker 해소는
``gather.sources.brokerage`` 가 소유하고, 본 스크립트는 ``g.brokerageReports()`` 호출 + 적재 +
**깨짐 감지(헬스 게이트)** 만 한다. 사용법: ``python syncBrokerageReports.py [--no-upload]``.

헬스 게이트(PRD 03 §4): 수집·업로드 후 증권사별/카테고리별 수율 + 파싱 완전성을 점검해
GitHub Step Summary 에 표로 남기고, **깨짐이면 exit 1** → 워크플로 RED → 운영자 자동 알림.
데이터는 알림 전에 이미 push 되어 보존된다(부분 데이터 > 무데이터).
"""

from __future__ import annotations

import argparse
import os

import polars as pl

from dartlab.gather import getDefaultGather
from dartlab.gather.sources.brokerage.config import enabledBrokers
from dartlab.gather.sources.brokerage.fetch import _healthProblems, _lastFetchOutcomes, _networkFailures
from dartlab.gather.sources.brokerage.io import writeMonthly
from dartlab.pipeline.changed import writeChanged
from dartlab.pipeline.hfUpload import uploadCategoryToHf

_CATEGORY = "brokerageReports"


def _catCounts(df: pl.DataFrame) -> dict[str, dict[str, int]]:
    """수집 df → broker → {category(report_type): 행수} 중첩 dict."""
    out: dict[str, dict[str, int]] = {}
    if df.is_empty():
        return out
    for broker, rtype, n in df.group_by(["broker", "report_type"]).len().iter_rows():
        out.setdefault(broker, {})[rtype] = int(n)
    return out


def _completeness(df: pl.DataFrame, brokers: list[str]) -> dict[str, float]:
    """broker 별 필수필드(title·url·pub_date) 모두 채워진 비율 0~1 (0행이면 0.0)."""
    out: dict[str, float] = {}
    for broker in brokers:
        sub = df.filter(pl.col("broker") == broker) if not df.is_empty() else df
        if sub.height == 0:
            out[broker] = 0.0
            continue
        ok = sub.filter(
            (pl.col("title").fill_null("") != "")
            & (pl.col("url").fill_null("") != "")
            & (pl.col("pub_date").fill_null("") != "")
        ).height
        out[broker] = ok / sub.height
    return out


def _writeStepSummary(
    df: pl.DataFrame,
    catCounts: dict[str, dict[str, int]],
    completeness: dict[str, float],
    problems: list[str],
    networkNotices: list[str] | None = None,
) -> None:
    """GitHub Step Summary($GITHUB_STEP_SUMMARY) 에 수율·완전성 표 + 깨짐 사유를 markdown 으로 append.

    Actions 외(로컬) 에선 env 부재라 no-op. 운영자가 워크플로 실행 화면에서 한눈에 본다.
    """
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = ["## 증권사 리서치 sync 헬스", "", f"- 총 **{df.height}건** 수집 ({len(catCounts)}개사)", ""]
    lines += ["| 증권사 | 카테고리 | 행수 | 완전성 |", "|---|---|---:|---:|"]
    for broker in sorted(catCounts):
        comp = completeness.get(broker, 1.0)
        for cat in sorted(catCounts[broker]):
            n = catCounts[broker][cat]
            lines.append(f"| {broker} | {cat} | {n} {'✅' if n else '❌'} | {comp:.0%} |")
    if problems:
        lines += ["", "### ❌ 깨짐 감지 — 셀렉터/URL 점검 필요", ""] + [f"- {p}" for p in problems]
    else:
        lines += ["", "### ✅ 전 증권사 정상"]
    if networkNotices:
        lines += ["", "### ⚠️ 네트워크 장애로 이번 run 에서 못 받은 보드 (깨짐 아님, 다음 run 재수집)", ""]
        lines += [f"- {notice}" for notice in networkNotices]
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    """수집 → 월별 write → manifest → (옵션) HF push → 헬스 게이트. 반환 = exit code(깨짐이면 1)."""
    parser = argparse.ArgumentParser(description="증권사 리서치 메타 sync")
    parser.add_argument("--no-upload", action="store_true", help="HF push 생략 (로컬 빌드만)")
    args = parser.parse_args()

    gather = getDefaultGather()
    df = gather.brokerageReports()
    changed = writeMonthly(df)
    writeChanged(_CATEGORY, changed)
    print(f"[brokerageReports] {df.height} rows · {len(changed)} months changed: {changed}", flush=True)

    # 업로드 먼저 — 건강한 증권사 데이터는 알림(exit 1) 전에 보존.
    if changed and not args.no_upload:
        pushed = uploadCategoryToHf(_CATEGORY)
        print(f"[brokerageReports] HF push: {pushed} files", flush=True)

    # 헬스 게이트 (PRD 03 §4) — 수율 0행/카테고리 0행/완전성<90% 조용한 깨짐 감지.
    # 동적 report_type 브로커(NH)는 카테고리별 검사 생략([]) — 총량·완전성만. 정적 브로커는 config 라벨.
    enabledCats = {
        k: ([] if v.get("dynamicReportType") else list(v["categories"].keys())) for k, v in enabledBrokers().items()
    }
    catCounts = _catCounts(df)
    completeness = _completeness(df, list(enabledCats))
    print(f"[brokerageReports] 수율: {catCounts}", flush=True)
    print(f"[brokerageReports] 완전성: {{{', '.join(f'{k}={v:.0%}' for k, v in completeness.items())}}}", flush=True)
    # 카테고리별 요청 결과로 네트워크 장애(DNS·연결·타임아웃) 0 행과 셀렉터 깨짐 0 행을 가른다.
    # 네트워크 장애는 경고만 남기고(다음 run 재수집), 전 증권사가 0 행이면 원인과 무관하게 깨짐으로 본다.
    fetchOutcomes = _lastFetchOutcomes()
    networkNotices = _networkFailures(enabledCats, fetchOutcomes)
    for notice in networkNotices:
        print(f"::warning::brokerageReports 네트워크 장애(깨짐 아님): {notice}", flush=True)
    problems = _healthProblems(catCounts, completeness, enabledCats, fetchOutcomes=fetchOutcomes)
    _writeStepSummary(df, catCounts, completeness, problems, networkNotices)
    if problems:
        for p in problems:
            print(f"::error::brokerageReports 깨짐 — {p}", flush=True)
        print(f"[brokerageReports] ⚠ {len(problems)}건 깨짐 감지 — exit 1(워크플로 RED→알림)", flush=True)
        return 1
    print("[brokerageReports] ✅ 헬스 정상 — 전 증권사 수율·완전성 OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
