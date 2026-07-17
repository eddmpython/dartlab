"""gov/prices date 샤드 → gov/prices/universe-monthly.parquet (유니버스 백테스터 floor 패널).

terminal-strategy-lab 05 §3·§11(G-M1). 전종목 일별(2010~, survivorship-clean)을 **월말 리샘플**
+ 가격/기술 신호 선계산해 floor(브라우저 DuckDB-wasm)가 1파일로 크로스섹셔널 랭킹 백테스트를
돌리게 한다. 라이브 일별 17샤드(~1,200만행)는 iOS 즉사라 floor 불가 → 월말(~수십만행) 근사.

⛔ 신호는 **월간 종가** 파생(floor 근사 — 일별 정밀은 local Python bonus). 재무 팩터 EXCLUDE
(상폐사 재무 13.9%만 = 생존편향, 05 §4). prebuild offline 규약(외부 API 0, HF 다운로드만).

출력 스키마 (long-form, 월말 1행/종목/월)::

    ym(202601) · stockCode · close · mktcap · turnover(월평균 거래대금)
    · momMonthly(12-1, 월간 종가) · volMonthly6m(월수익 변동성 연환산)
    · high52wProx(close / 최근12개월 최고 월말종가) · retFwd1m · retFwd3m
    · delistReason(none/merger/unknown — 05 §3.1 F1; 합병=last-close 제외, unknown=양극단 밴드)

    ⚠ F1(합병식별)은 allFilings 공시 커버리지(2024-09+) 한정 휴리스틱 — 그 이전 폐지는 unknown(밴드).
    ⚠ F2(forward-return)는 완전 월 그리드 reindex 후 shift = 정지월 건너뛴 구간왜곡 차단(05 §3.1).

실행::

    uv run python -X utf8 .github/scripts/prebuild/buildUniversePanel.py [--skip-upload]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _hfRetry import retryHfCall  # noqa: E402

HF_REPO = "eddmpython/dartlab-data"
PATH_IN_REPO = "gov/prices/universe-monthly.parquet"
OUT_LOCAL = ROOT / "data" / "gov" / "prices" / "universe-monthly.parquet"
LOCAL_DATE_DIR = ROOT / "data" / "gov" / "prices" / "date"
START_YEAR = 2010


def _env(name: str) -> str:
    import os
    import re

    val = os.environ.get(name, "").strip()
    if val:
        return val
    envPath = ROOT / ".env"
    if envPath.exists():
        m = dict(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", envPath.read_text(encoding="utf-8"), re.M))
        return m.get(name, "").strip().strip('"').strip("'")
    return ""


def _loadYearShard(year: int) -> pl.DataFrame | None:
    """date 샤드 1개 — 로컬 우선, 없으면 HF 다운로드(offline 규약 허용)."""
    local = LOCAL_DATE_DIR / f"{year}.parquet"
    if local.exists():
        return pl.read_parquet(local)
    try:
        from huggingface_hub import hf_hub_download

        cached = retryHfCall(
            hf_hub_download,
            repo_id=HF_REPO,
            repo_type="dataset",
            filename=f"gov/prices/date/{year}.parquet",
            token=_env("HF_TOKEN") or None,
        )
        return pl.read_parquet(cached)
    except Exception as exc:  # noqa: BLE001 — 미존재 연도는 정상
        print(f"[universe] {year} 부재 ({type(exc).__name__})")
        return None


def _monthEnd(year: int) -> pl.DataFrame | None:
    """한 연도 샤드 → 월말 리샘플(종목·월별 마지막 거래봉). 일별 프레임은 즉시 버려 메모리 안전."""
    raw = _loadYearShard(year)
    if raw is None or raw.is_empty():
        return None
    df = (
        raw.select(["BAS_DD", "ISU_CD", "TDD_CLSPRC", "MKTCAP", "ACC_TRDVAL"])
        .with_columns(pl.col("ISU_CD").cast(pl.Utf8).str.replace(r"^A", "").alias("stockCode"))
        .filter(pl.col("stockCode").str.contains(r"^\d{6}$"))
        .with_columns(
            pl.col("BAS_DD").cast(pl.Utf8).str.slice(0, 6).alias("ym"),
            pl.col("TDD_CLSPRC").cast(pl.Float64, strict=False).alias("close"),
            pl.col("MKTCAP").cast(pl.Float64, strict=False).alias("mktcap"),
            pl.col("ACC_TRDVAL").cast(pl.Float64, strict=False).alias("tradval"),
        )
        .filter(pl.col("close") > 0)
        .sort(["stockCode", "ym", "BAS_DD"])
    )
    # 월말 = 그 월 마지막 거래봉(캘린더 월말 아님). turnover = 월평균 거래대금.
    monthly = df.group_by(["stockCode", "ym"], maintain_order=True).agg(
        pl.col("close").last(),
        pl.col("mktcap").last(),
        pl.col("tradval").mean().alias("turnover"),
    )
    return monthly


def _ymIdx(col: pl.Expr) -> pl.Expr:
    """ym(YYYYMM str) → 월 인덱스 정수(연*12+월) — ±N개월 윈도 산술용."""
    return col.str.slice(0, 4).cast(pl.Int32) * 12 + col.str.slice(4, 6).cast(pl.Int32)


def _loadAllFilings() -> pl.DataFrame | None:
    """allFilings 코드 파티션(수시공시 - report_nm·rcept_dt). 로컬 우선·HF fallback.
    ⚠ 커버리지 2024-09+ → 그 이전 폐지의 합병 식별 불가(unknown 처리)."""
    cols = ["stock_code", "rcept_dt", "report_nm"]
    localDir = ROOT / "data" / "dart" / "allFilings"
    localPartitions = sorted((localDir / "byCode").glob("*_recent.parquet"))
    if localPartitions:
        return pl.concat([pl.read_parquet(path, columns=cols) for path in localPartitions], how="vertical_relaxed")
    legacy = localDir / "recent.parquet"
    if legacy.exists():
        return pl.read_parquet(legacy, columns=cols)
    try:
        from huggingface_hub import hf_hub_download

        manifestPath = retryHfCall(
            hf_hub_download,
            repo_id=HF_REPO,
            repo_type="dataset",
            filename="dart/allFilings/byCode/manifest.json",
            token=_env("HF_TOKEN") or None,
        )
        manifest = json.loads(Path(manifestPath).read_text(encoding="utf-8"))
        files = [
            str(item["file"]) for item in manifest.get("partitions", []) if isinstance(item, dict) and item.get("file")
        ]
        cached = [
            retryHfCall(
                hf_hub_download,
                repo_id=HF_REPO,
                repo_type="dataset",
                filename=f"dart/allFilings/byCode/{name}",
                token=_env("HF_TOKEN") or None,
            )
            for name in files
        ]
        if cached:
            return pl.concat([pl.read_parquet(path, columns=cols) for path in cached], how="vertical_relaxed")
    except Exception as exc:  # noqa: BLE001
        print(f"[universe] allFilings 파티션 부재 ({type(exc).__name__}), legacy fallback")
    try:
        from huggingface_hub import hf_hub_download

        cached = retryHfCall(
            hf_hub_download,
            repo_id=HF_REPO,
            repo_type="dataset",
            filename="dart/allFilings/recent.parquet",
            token=_env("HF_TOKEN") or None,
        )
        return pl.read_parquet(cached, columns=cols)
    except Exception as exc:  # noqa: BLE001
        print(f"[universe] allFilings 부재 ({type(exc).__name__})")
        return None


def _mergerStocks(lastYm: pl.DataFrame, globalMaxYm: str) -> set[str]:
    """폐지 종목(last < globalMax) 중 폐지일 ±3개월에 mna 공시(합병/영업양수도) = **합병 추정**.
    event.py _EVENT_RULES mna 키워드 재사용. 휴리스틱(방향·종목귀속 완벽판정 불가) → "합병 추정" 라벨.
    allFilings 커버리지 밖(2024-09 이전) 폐지는 미검출 = unknown(밴드). 05 §3.1 F1."""
    af = _loadAllFilings()
    if af is None:
        print("[universe] allFilings 부재 — 합병 식별 생략(전 폐지=unknown, 밴드 보수)")
        return set()
    delisted = lastYm.filter(pl.col("_lastYm") < globalMaxYm).with_columns(_ymIdx(pl.col("_lastYm")).alias("_li"))
    mna = (
        af.filter(pl.col("report_nm").cast(pl.Utf8).str.contains("합병|영업양수|영업양도"))
        .with_columns(
            pl.col("stock_code").cast(pl.Utf8).str.replace(r"^A", "").alias("stockCode"),
            _ymIdx(pl.col("rcept_dt").cast(pl.Utf8).str.slice(0, 6)).alias("_fi"),
        )
        .select(["stockCode", "_fi"])
    )
    hit = (
        delisted.join(mna, on="stockCode", how="inner")
        .filter((pl.col("_fi") - pl.col("_li")).abs() <= 3)
        .select("stockCode")
        .unique()
    )
    return set(hit["stockCode"].to_list())


def buildPanel() -> pl.DataFrame:
    """전 연도 월말 리샘플 누적 + 완전 월 그리드 reindex(F2) + 종목별 신호 + delistReason(F1)."""
    frames: list[pl.DataFrame] = []
    for year in range(START_YEAR, date.today().year + 1):
        m = _monthEnd(year)
        if m is not None and not m.is_empty():
            frames.append(m)
            print(f"[universe] {year}: {m.height}행(월말)")
    if not frames:
        raise SystemExit("[universe] date 샤드 0건")
    observed = pl.concat(frames, how="diagonal_relaxed").sort(["stockCode", "ym"])
    # ★F2: 완전 월 그리드 reindex — 정지로 빠진 월을 null 로 채워 shift 가 캘린더 정확(05 §3.1 F2).
    #   안 하면 retFwd1m 이 건너뛴 다음 *존재월*(2~3개월)을 가리켜 조용한 구간왜곡/look-ahead.
    allYms = observed.select("ym").unique().sort("ym")
    ranges = observed.group_by("stockCode").agg(pl.col("ym").min().alias("_fy"), pl.col("ym").max().alias("_ly"))
    grid = (
        ranges.join(allYms, how="cross")
        .filter((pl.col("ym") >= pl.col("_fy")) & (pl.col("ym") <= pl.col("_ly")))
        .select(["stockCode", "ym"])
    )
    panel = grid.join(observed, on=["stockCode", "ym"], how="left").sort(["stockCode", "ym"])
    # 종목별 신호(완전 그리드 위 — 결측월 null 이라 shift 가 캘린더 정확). over("stockCode"), ym 정렬 전제.
    panel = panel.with_columns(
        (pl.col("close").shift(1) / pl.col("close").shift(12) - 1).over("stockCode").alias("momMonthly"),
        (pl.col("close").shift(-1) / pl.col("close") - 1).over("stockCode").alias("retFwd1m"),
        (pl.col("close").shift(-3) / pl.col("close") - 1).over("stockCode").alias("retFwd3m"),
        (pl.col("close") / pl.col("close").rolling_max(window_size=12, min_samples=1))
        .over("stockCode")
        .alias("high52wProx"),
        (pl.col("close") / pl.col("close").shift(1)).log().over("stockCode").alias("_lr"),
    )
    panel = panel.with_columns(
        (pl.col("_lr").rolling_std(window_size=6, min_samples=3) * (12**0.5)).over("stockCode").alias("volMonthly6m")
    ).drop("_lr")
    # 신호 계산 후 관측월만 출력(reindex 한 null-close 월은 floor 로 안 보냄).
    panel = panel.filter(pl.col("close").is_not_null())
    # ★F1: delisted bool → delistReason enum(none/merger/unknown). 합병=last-close 제외, unknown=양극단 밴드.
    #   05 §3.1·§7 U-G1. globalMaxYm 미만에서 끝난 종목이 폐지 후보, 그중 mna 근접 = 합병 추정.
    globalMaxYm = observed["ym"].max()
    lastYm = panel.group_by("stockCode").agg(pl.col("ym").max().alias("_lastYm"))
    mergers = _mergerStocks(lastYm, globalMaxYm)
    panel = (
        panel.join(lastYm, on="stockCode")
        .with_columns(
            pl.when(pl.col("_lastYm") >= globalMaxYm)
            .then(pl.lit("none"))
            .when(pl.col("stockCode").is_in(list(mergers)) if mergers else pl.lit(False))
            .then(pl.lit("merger"))
            .otherwise(pl.lit("unknown"))
            .alias("delistReason")
        )
        .drop("_lastYm")
    )
    panel = panel.with_columns(pl.col("close").round(4))
    # 헤드룸: close(회계)만 Float64, 나머지 float은 Float32(랭킹·신호 정밀도 충분, 파일 ~40% 축소).
    f32 = ["mktcap", "turnover", "momMonthly", "volMonthly6m", "high52wProx", "retFwd1m", "retFwd3m"]
    panel = panel.with_columns([pl.col(c).cast(pl.Float32) for c in f32 if c in panel.columns])
    return panel.select(
        [
            "ym",
            "stockCode",
            "close",
            "mktcap",
            "turnover",
            "momMonthly",
            "volMonthly6m",
            "high52wProx",
            "retFwd1m",
            "retFwd3m",
            "delistReason",
        ]
    ).sort(["ym", "stockCode"])


def main() -> None:
    from dartlab.core.offlineGuard import enforceOffline

    enforceOffline()  # prebuild = offline only (HF 다운로드만)

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-upload", action="store_true", help="로컬 parquet 만 생성 (G-M1 실측용)")
    args = parser.parse_args()

    panel = buildPanel()
    OUT_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(OUT_LOCAL, compression="zstd")
    mb = OUT_LOCAL.stat().st_size / 1e6
    nStocks = panel["stockCode"].n_unique()
    byReason = {r: panel.filter(pl.col("delistReason") == r)["stockCode"].n_unique() for r in ("merger", "unknown")}
    print(
        f"[universe] {panel.height}행 · {nStocks}종목(폐지: 합병추정 {byReason['merger']}·unknown {byReason['unknown']})"
        f" · ym {panel['ym'].min()}~{panel['ym'].max()} → {OUT_LOCAL} ({mb:.2f}MB)"
    )
    print(f"[G-M4] 밴드=unknown {byReason['unknown']}종목(합병추정 {byReason['merger']} 제외). U-G1 폐지의존도")
    print(f"[G-M1] parquet {mb:.2f}MB (<20MB={'PASS' if mb < 20 else 'FAIL→팩터축소/시총컷'}) · 행 {panel.height:,}")

    if args.skip_upload:
        return
    token = _env("HF_TOKEN")
    if not token:
        raise SystemExit("[universe] HF_TOKEN 없음 — --skip-upload 로 로컬만")
    from huggingface_hub import HfApi

    retryHfCall(
        HfApi(token=token).upload_file,
        path_or_fileobj=str(OUT_LOCAL),
        path_in_repo=PATH_IN_REPO,
        repo_id=HF_REPO,
        repo_type="dataset",
        commit_message=f"갱신: universe-monthly {panel['ym'].max()} ({panel.height}행)",
    )
    print(f"[universe] HF 업로드 → {PATH_IN_REPO}")


if __name__ == "__main__":
    main()
