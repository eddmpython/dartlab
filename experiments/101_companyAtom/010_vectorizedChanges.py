"""
실험 ID: 101-010
실험명: changes 벡터화 — Python 루프 제거, Polars 네이티브 속도

목적:
- 008의 Python for문(4.6초/1.4초)을 Polars 벡터 연산으로 대체
- sections → changes 변환을 0.5초 이내로

가설:
1. Polars hash + unpivot + join으로 Python 루프 없이 변환 가능
2. 0.5초 이내 달성

방법:
1. 기간 컬럼을 unpivot(melt)하여 long format으로
2. Polars hash()로 벡터화 비교
3. shift()로 인접 기간 비교 — 루프 없음

결과 (2026-03-27):
- 벡터화 0.15초 vs 루프 1.9초 → **12x 빠름** (최소 0.15초)
- 행수 22,060 완전 일치 (5종 유형 분포도 동일)
- 메모리: 벡터화 4.14MB vs 루프 4.91MB (메타 컬럼 추가에도 더 작음)
- 초기 버그: (1) null 조기 필터링으로 appeared/disappeared 누락 → null 보존 패턴으로 해결
  (2) UInt32 뺄셈 오버플로우로 structural/wording 분류 오류 + sizeDelta 음수 깨짐 → Int64 캐스트로 해결

결론:
- 가설 1 확인: Polars unpivot + hash + shift().over()로 Python 루프 완전 대체 가능
- 가설 2 확인: 0.15초 (0.5초 목표 대폭 초과 달성)
- **핵심 패턴**: wide→long unpivot → null-safe hash/len → shift().over() 인접비교 → 벡터화 분류
- 주의점: Polars UInt32/Categorical 타입은 뺄셈/문자열 연산 전 명시 캐스트 필수

실험일: 2026-03-27
"""

import sys
import time
import re

sys.path.insert(0, "c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab/src")

import polars as pl

PERIOD_RE = re.compile(r"^\d{4}$")


def buildChangesVectorized(sections):
    """Polars 벡터화로 changes 생성. Python 루프 없음."""
    annualCols = sorted([c for c in sections.columns if PERIOD_RE.match(c)])
    metaCols = ["topic"]
    if "textPathKey" in sections.columns:
        metaCols.append("textPathKey")
    if "blockType" in sections.columns:
        metaCols.append("blockType")
    if "blockOrder" in sections.columns:
        metaCols.append("blockOrder")

    # 행 인덱스 추가
    work = sections.with_row_index("_row")

    # unpivot: wide → long (topic, _row, period, text)
    long = work.select(["_row"] + metaCols + annualCols).unpivot(
        index=["_row"] + metaCols,
        on=annualCols,
        variable_name="period",
        value_name="text",
    )

    # Categorical → String 캐스트 (null 유지 — appeared/disappeared 감지 위해)
    long = long.with_columns(pl.col("text").cast(pl.Utf8))

    # hash + len 계산 (null은 null 유지)
    long = long.with_columns(
        pl.when(pl.col("text").is_not_null())
        .then(pl.col("text").hash())
        .otherwise(pl.lit(None, dtype=pl.UInt64))
        .alias("_hash"),
        pl.when(pl.col("text").is_not_null())
        .then(pl.col("text").str.len_chars())
        .otherwise(pl.lit(None, dtype=pl.UInt32))
        .alias("_len"),
        pl.when(pl.col("text").is_not_null())
        .then(pl.col("text").str.slice(0, 200))
        .otherwise(pl.lit(None, dtype=pl.Utf8))
        .alias("preview"),
    )

    # 같은 행(_row) 내에서 기간순 정렬 후 이전 기간과 비교
    long = long.sort(["_row", "period"])
    long = long.with_columns([
        pl.col("period").shift(1).over("_row").alias("_prevPeriod"),
        pl.col("_hash").shift(1).over("_row").alias("_prevHash"),
        pl.col("_len").shift(1).over("_row").alias("_prevLen"),
        pl.col("text").shift(1).over("_row").alias("_prevText"),
    ])

    # 변화 필터: 이전 기간이 있고, 둘 다 null이 아니고, hash가 다르거나 한쪽만 null
    changes = long.filter(
        pl.col("_prevPeriod").is_not_null()
        & ~(pl.col("text").is_null() & pl.col("_prevText").is_null())
        & (
            (pl.col("_hash") != pl.col("_prevHash"))
            | pl.col("text").is_null()
            | pl.col("_prevText").is_null()
        )
    )

    # 변화 유형 분류 (벡터화)
    # 숫자만 변화: 숫자를 N으로 치환한 텍스트가 동일
    numPattern = r"[\d,.]+"
    changes = changes.with_columns([
        pl.col("text").str.replace_all(numPattern, "N").alias("_stripped"),
        pl.col("_prevText").str.replace_all(numPattern, "N").alias("_prevStripped"),
    ])

    changes = changes.with_columns(
        pl.when(pl.col("_prevText").is_null())
        .then(pl.lit("appeared"))
        .when(pl.col("text").is_null())
        .then(pl.lit("disappeared"))
        .when(pl.col("_stripped") == pl.col("_prevStripped"))
        .then(pl.lit("numeric"))
        .when(
            (pl.col("_prevLen") > 0)
            & ((pl.col("_len").cast(pl.Int64) - pl.col("_prevLen").cast(pl.Int64)).abs().cast(pl.Float64) / pl.col("_prevLen").cast(pl.Float64) > 0.5)
        )
        .then(pl.lit("structural"))
        .otherwise(pl.lit("wording"))
        .alias("changeType")
    )

    # 최종 컬럼 선택
    resultCols = ["_prevPeriod", "period", "changeType", "_prevLen", "_len", "preview"] + metaCols
    renameMap = {"_prevPeriod": "fromPeriod", "period": "toPeriod", "_prevLen": "sizeA", "_len": "sizeB"}

    result = changes.select(resultCols).rename(renameMap)
    result = result.with_columns(
        (pl.col("sizeB").cast(pl.Int64) - pl.col("sizeA").cast(pl.Int64)).alias("sizeDelta")
    )

    return result


def buildChangesLoop(sections):
    """기존 008 방식 (Python 루프)."""
    import hashlib
    annualCols = sorted([c for c in sections.columns if PERIOD_RE.match(c)])
    topics = sections.get_column("topic").to_list()

    rows = []
    for i in range(len(annualCols) - 1):
        colA, colB = annualCols[i], annualCols[i + 1]
        for rowIdx in range(sections.height):
            textA = sections[rowIdx, colA]
            textB = sections[rowIdx, colB]
            if textA is None and textB is None:
                continue
            hashA = hashlib.md5(textA.encode("utf-8")).hexdigest() if textA else None
            hashB = hashlib.md5(textB.encode("utf-8")).hexdigest() if textB else None
            if hashA == hashB:
                continue
            strippedA = re.sub(r"[\d,.]+", "N", textA) if textA else None
            strippedB = re.sub(r"[\d,.]+", "N", textB) if textB else None
            if textA is None:
                ct = "appeared"
            elif textB is None:
                ct = "disappeared"
            elif strippedA == strippedB:
                ct = "numeric"
            elif len(textA) > 0 and abs(len(textB) - len(textA)) / len(textA) > 0.5:
                ct = "structural"
            else:
                ct = "wording"
            rows.append({
                "fromPeriod": colA, "toPeriod": colB,
                "topic": topics[rowIdx], "changeType": ct,
                "sizeDelta": (len(textB) if textB else 0) - (len(textA) if textA else 0),
                "preview": ((textB or textA) or "")[:200],
            })
    return pl.DataFrame(rows)


def run():
    import dartlab

    c = dartlab.Company("005930")
    sections = c.docs.sections

    # 워밍업
    _ = buildChangesVectorized(sections)

    # 벡터화 측정
    times_v = []
    for trial in range(5):
        t0 = time.perf_counter()
        result_v = buildChangesVectorized(sections)
        elapsed = time.perf_counter() - t0
        times_v.append(elapsed)

    # 루프 측정
    times_l = []
    for trial in range(3):
        t0 = time.perf_counter()
        result_l = buildChangesLoop(sections)
        elapsed = time.perf_counter() - t0
        times_l.append(elapsed)

    print("=" * 60)
    print("속도 비교")
    print("=" * 60)
    avgV = sum(times_v) / len(times_v)
    avgL = sum(times_l) / len(times_l)
    print(f"  벡터화 (Polars): {avgV:.3f}초  (최소 {min(times_v):.3f}초)")
    print(f"  루프 (Python):   {avgL:.3f}초  (최소 {min(times_l):.3f}초)")
    print(f"  배수:            {avgL/avgV:.1f}x 빠름")
    print()

    print("=" * 60)
    print("결과 비교")
    print("=" * 60)
    print(f"  벡터화: {result_v.height}행 × {result_v.width}열, {result_v.estimated_size('mb'):.2f}MB")
    print(f"  루프:   {result_l.height}행 × {result_l.width}열, {result_l.estimated_size('mb'):.2f}MB")
    print()

    # 변화 유형 분포 비교
    print("  벡터화 유형 분포:")
    print(result_v.group_by("changeType").agg(pl.len().alias("count")).sort("count", descending=True))
    print()
    print("  루프 유형 분포:")
    print(result_l.group_by("changeType").agg(pl.len().alias("count")).sort("count", descending=True))
    print()

    print(result_v.head(5))


if __name__ == "__main__":
    run()
