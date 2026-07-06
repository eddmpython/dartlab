"""판독 원장 : 주간 판독 행렬의 컬럼형 append-only parquet IO (L2.5 simulate).

판독은 주당 전상장사 x 전표면 = 수백만 행이라 expectationLedger 의 per-row JSON 방식에
얹을 수 없다. 컬럼형 연 샤드 parquet 로 담되 봉인 규율(발행 후 불변·issuedLive·재채점은
append)은 동형 상속한다. 유일 writer 는 readingCycle 이며 L2 엔진은 본 모듈을 import 하지
않는다 (하향 단방향 import 구조 보장).

Storage: ``{DARTLAB_DATA_DIR|data}/readings/{readings|readingScores}_{yyyy}.parquet``
(연 샤드, HF surface ``readings/`` 는 write end = CI sync only). 봉인 키 =
(week, stockCode, surface, issuedLive): 같은 키 재발행은 append-only 위반으로 거부한다.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

import polars as pl

from dartlab.simulate.reading import Reading

LEDGER_SUBDIR = "readings"

_READING_SCHEMA: dict[str, pl.DataType] = {
    "week": pl.Int64,
    "stockCode": pl.Utf8,
    "market": pl.Utf8,
    "surface": pl.Utf8,
    "asOf": pl.Utf8,
    "horizon": pl.Int64,
    "direction": pl.Int64,
    "score": pl.Float64,
    "abstainReason": pl.Utf8,
    "refs": pl.Utf8,
    "condition": pl.Utf8,
    "issuedAt": pl.Utf8,
    "issuedLive": pl.Boolean,
}
# 채점 행: 판독 지평 도래 시 실제 초과수익(원시·버킷중립)을 append. 재채점은 새 행.
_SCORE_SCHEMA: dict[str, pl.DataType] = {
    "week": pl.Int64,
    "stockCode": pl.Utf8,
    "surface": pl.Utf8,
    "scoredAt": pl.Utf8,
    "exRaw": pl.Float64,
    "exNeutral": pl.Float64,
    "costFloor": pl.Float64,
    "netExNeutral": pl.Float64,
    "error": pl.Utf8,
}


def ledgerDir(baseDir: Path | None = None) -> Path:
    """판독 원장 루트: 명시 baseDir > DARTLAB_DATA_DIR env > ./data."""
    if baseDir is not None:
        return baseDir
    root = os.environ.get("DARTLAB_DATA_DIR")
    return (Path(root) if root else Path("data")) / LEDGER_SUBDIR


def _writeShard(path: Path, new: pl.DataFrame) -> None:
    if path.exists():
        old = pl.read_parquet(path)
        new = pl.concat([old, new.select(old.columns)], how="vertical")
    tmp = path.with_suffix(".parquet.tmp")
    new.write_parquet(tmp)
    tmp.replace(path)


def appendReadings(
    rows: list[Reading],
    *,
    issuedAt: str,
    issuedLive: bool,
    baseDir: Path | None = None,
) -> list[Path]:
    """봉인 판독 행을 연 샤드에 append. 같은 (week,stockCode,surface,issuedLive) 재발행은 거부.

    Args:
        rows: 발행할 Reading 목록.
        issuedAt: 발행 봉인 시각 (UTC ISO).
        issuedLive: False = backfill (라이브 성적표 혼입 금지).
        baseDir: 원장 루트 override (테스트).

    Returns:
        기록된 샤드 경로.

    Raises:
        ValueError: 봉인 키 중복 (append-only 불변 위반).
    """
    if not rows:
        return []
    base = ledgerDir(baseDir)
    base.mkdir(parents=True, exist_ok=True)
    flat = []
    for r in rows:
        d = asdict(r)
        d["refs"] = " ".join(d.get("refs") or ())  # 튜플 → 공백 조인 Utf8 (재계산 계약 보존)
        flat.append({**d, "issuedAt": issuedAt, "issuedLive": issuedLive})
    df = pl.DataFrame(flat, schema=_READING_SCHEMA)
    written: list[Path] = []
    for (yyyy,), part in df.group_by(pl.col("week").floordiv(100).cast(pl.Utf8)):
        path = base / f"readings_{yyyy}.parquet"
        if path.exists():
            old = pl.read_parquet(path, columns=["week", "stockCode", "surface", "issuedLive"])
            key = pl.struct("week", "stockCode", "surface", "issuedLive")
            dup = old.with_columns(k=key).join(part.with_columns(k=key), on="k", how="semi")
            if dup.height:
                raise ValueError(
                    f"append-only 위반: 봉인 판독 키 중복 x{dup.height} "
                    f"(예 week={dup['week'][0]} {dup['stockCode'][0]} {dup['surface'][0]})"
                )
        _writeShard(path, part)
        written.append(path)
    return written


def appendReadingsFrame(
    frame: pl.DataFrame, *, issuedAt: str, issuedLive: bool, baseDir: Path | None = None
) -> list[Path]:
    """대량 판독을 DataFrame 으로 봉인 (opine 산출 직결). 같은 봉인 키 중복은 거부.

    Args:
        frame: (week, stockCode|code, market, surface, asOf, horizon, direction, score, abstainReason).
            opine 산출(code 열)을 받으면 stockCode 로 정규화한다.
        issuedAt: 발행 봉인 시각.
        issuedLive: False = backfill.
        baseDir: 원장 루트 override.

    Raises:
        ValueError: 봉인 키 중복 (append-only 불변 위반).
    """
    if frame.height == 0:
        return []
    if "stockCode" not in frame.columns and "code" in frame.columns:
        frame = frame.rename({"code": "stockCode"})
    if "refs" not in frame.columns:
        frame = frame.with_columns(refs=pl.lit(""))
    if "condition" not in frame.columns:
        frame = frame.with_columns(condition=pl.lit(None, dtype=pl.Utf8))
    frame = frame.with_columns(issuedAt=pl.lit(issuedAt), issuedLive=pl.lit(issuedLive)).select(list(_READING_SCHEMA))
    base = ledgerDir(baseDir)
    base.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for (yyyy,), part in frame.group_by(pl.col("week").floordiv(100).cast(pl.Utf8)):
        path = base / f"readings_{yyyy}.parquet"
        if path.exists():
            old = pl.read_parquet(path, columns=["week", "stockCode", "surface", "issuedLive"])
            key = pl.struct("week", "stockCode", "surface", "issuedLive")
            dup = old.with_columns(k=key).join(part.with_columns(k=key), on="k", how="semi")
            if dup.height:
                raise ValueError(f"append-only 위반: 봉인 판독 키 중복 x{dup.height}")
        _writeShard(path, part)
        written.append(path)
    return written


def appendReadingScores(rows: list[dict], *, baseDir: Path | None = None) -> list[Path]:
    """채점 행(_SCORE_SCHEMA dict)을 연 샤드에 append. 재채점은 새 행 (이력 보존)."""
    if not rows:
        return []
    base = ledgerDir(baseDir)
    base.mkdir(parents=True, exist_ok=True)
    df = pl.DataFrame(rows, schema=_SCORE_SCHEMA)
    written: list[Path] = []
    for (yyyy,), part in df.group_by(pl.col("week").floordiv(100).cast(pl.Utf8)):
        path = base / f"readingScores_{yyyy}.parquet"
        _writeShard(path, part)
        written.append(path)
    return written


def _readAll(base: Path, table: str) -> pl.DataFrame | None:
    files = sorted(base.glob(f"{table}_*.parquet"))
    if not files:
        return None
    return pl.concat([pl.read_parquet(f) for f in files], how="vertical")


def readReadings(
    *,
    week: int | None = None,
    live: bool | None = None,
    market: str | None = None,
    baseDir: Path | None = None,
) -> pl.DataFrame | None:
    """판독 행 읽기 (week·live·market 필터 선택. market 무필터 = 전 시장 혼합 주의)."""
    df = _readAll(ledgerDir(baseDir), "readings")
    if df is None:
        return None
    if week is not None:
        df = df.filter(pl.col("week") == week)
    if live is not None:
        df = df.filter(pl.col("issuedLive") == live)
    if market is not None and "market" in df.columns:
        df = df.filter(pl.col("market") == market)
    return df


def readReadingScores(*, baseDir: Path | None = None) -> pl.DataFrame | None:
    """채점 행 읽기."""
    return _readAll(ledgerDir(baseDir), "readingScores")


def unscoredReadings(*, baseDir: Path | None = None) -> pl.DataFrame | None:
    """아직 채점 안 된 판독 행 (지평 도래 채점 대상 후보)."""
    df = readReadings(baseDir=baseDir)
    if df is None:
        return None
    scores = readReadingScores(baseDir=baseDir)
    if scores is None:
        return df
    key = pl.struct("week", "stockCode", "surface")
    return (
        df.with_columns(k=key)
        .join(
            scores.select("week", "stockCode", "surface").unique().with_columns(k=key),
            on="k",
            how="anti",
        )
        .drop("k")
    )
