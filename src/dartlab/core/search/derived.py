"""파생 지식 레이어 — 역인덱스에서 추출한 집계 데이터 로드/조회.

stemIndex 빌드 시 함께 생성되는 파생물:
- companyProfile.parquet: 기업별 공시 압축 프로필 (~500KB)
- eventTimeline.parquet: 유형×월 빈도 시계열 (~50KB)

검색(search) 없이 역인덱스의 메타데이터에서 추출한 "지식".
파생물 합계 ~600KB — OOM 위험 없음.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from dartlab.core.search.ngramIndex import _stemIndexDir

# ── 캐시 ──

_cachedProfile: pl.DataFrame | None = None
_cachedTimeline: pl.DataFrame | None = None
_cachedDna: dict | None = None  # {"vectors": np.ndarray, "stockCodes": list[str]}

# ── 희귀 이벤트 유형 (위기/특수 시그널) ──

_RARE_TYPES = frozenset({
    "관리종목지정",
    "상장폐지",
    "회생절차",
    "감자",
    "파산",
    "횡령",
    "부정",
    "제재",
    "소송",
    "채권은행",
    "자사주소각",
})


# ── companyProfile ──


def buildCompanyProfile(meta: pl.DataFrame, outDir: Path) -> pl.DataFrame:
    """meta.parquet에서 기업별 공시 프로필을 집계하여 저장."""
    global _cachedProfile

    af = meta.filter(
        (pl.col("source") == "allFilings") & (pl.col("stock_code") != "")
    )

    if af.height == 0:
        return pl.DataFrame()

    # 정규화된 유형별 건수
    typeCounts = (
        af.group_by("stock_code", "report_nm")
        .len()
        .sort("len", descending=True)
    )

    # 기업별 집계
    profile = (
        af.group_by("stock_code")
        .agg(
            pl.col("corp_name").first(),
            pl.len().alias("total_filings"),
            pl.col("rcept_dt").min().alias("first_dt"),
            pl.col("rcept_dt").max().alias("last_dt"),
        )
        .filter(pl.col("stock_code").is_not_null())
    )

    # top3 유형
    top3 = (
        typeCounts.group_by("stock_code")
        .agg(
            pl.col("report_nm").head(3).alias("top3_types"),
            pl.col("len").head(3).alias("top3_counts"),
        )
    )

    # 연도별 건수
    yearly = (
        af.with_columns(pl.col("rcept_dt").str.slice(0, 4).alias("year"))
        .group_by("stock_code", "year")
        .len()
        .sort("year")
        .group_by("stock_code")
        .agg(
            pl.col("year").alias("yearly_years"),
            pl.col("len").alias("yearly_counts"),
        )
    )

    # 희귀 이벤트
    rareFiltered = typeCounts.filter(
        pl.col("report_nm").is_in(list(_RARE_TYPES))
    )
    rareAgg = (
        rareFiltered.group_by("stock_code")
        .agg(pl.col("report_nm").alias("rare_events"))
    )

    # 병합
    result = (
        profile
        .join(top3, on="stock_code", how="left")
        .join(yearly, on="stock_code", how="left")
        .join(rareAgg, on="stock_code", how="left")
    )

    result.write_parquet(outDir / "companyProfile.parquet")
    _cachedProfile = result
    return result


def loadProfile(stockCode: str | None = None) -> dict | pl.DataFrame:
    """기업별 공시 프로필 로드.

    stockCode 지정 시 해당 기업 1행을 dict로 반환.
    미지정 시 전체 DataFrame 반환.
    """
    global _cachedProfile

    if _cachedProfile is None:
        path = _stemIndexDir() / "companyProfile.parquet"
        if not path.exists():
            raise FileNotFoundError(f"companyProfile.parquet 없음: {path}")
        _cachedProfile = pl.read_parquet(path)

    if stockCode is None:
        return _cachedProfile

    row = _cachedProfile.filter(pl.col("stock_code") == stockCode)
    if row.height == 0:
        return None

    d = row.row(0, named=True)

    # 편의 필드 생성
    top3 = d.get("top3_types") or []
    top3c = d.get("top3_counts") or []
    d["top3_summary"] = ", ".join(
        f"{t}({c}건)" for t, c in zip(top3, top3c)
    ) if top3 else "없음"

    # velocity: 최근 연도 / 직전 연도
    years = d.get("yearly_years") or []
    counts = d.get("yearly_counts") or []
    if len(years) >= 2:
        last = counts[-1]
        prev = counts[-2]
        if prev > 0:
            vel = last / prev
            d["velocity"] = round(vel, 2)
            pct = (vel - 1) * 100
            sign = "+" if pct >= 0 else ""
            d["velocity_text"] = f"최근 {last}건 (전년 대비 {sign}{pct:.0f}%)"
        else:
            d["velocity"] = None
            d["velocity_text"] = f"최근 {last}건"
    elif len(years) == 1:
        d["velocity"] = None
        d["velocity_text"] = f"{counts[0]}건"
    else:
        d["velocity"] = None
        d["velocity_text"] = "정보 없음"

    # rare_events 텍스트
    rare = d.get("rare_events") or []
    d["rare_text"] = ", ".join(rare) if rare else "없음"

    return d


# ── eventTimeline ──


def buildEventTimeline(meta: pl.DataFrame, outDir: Path) -> pl.DataFrame:
    """유형×월 빈도 시계열을 집계하여 저장."""
    global _cachedTimeline

    af = meta.filter(
        (pl.col("source") == "allFilings")
        & (pl.col("rcept_dt") != "")
        & (pl.col("rcept_dt").str.len_chars() >= 6)
    )

    if af.height == 0:
        return pl.DataFrame()

    timeline = (
        af.with_columns(pl.col("rcept_dt").str.slice(0, 6).alias("period"))
        .group_by("period", "report_nm")
        .agg(
            pl.len().alias("count"),
            pl.col("stock_code").n_unique().alias("corp_count"),
        )
        .sort("period", "count", descending=[False, True])
    )

    timeline.write_parquet(outDir / "eventTimeline.parquet")
    _cachedTimeline = timeline
    return timeline


def loadTimeline(
    typeFilter: str | None = None,
    periodFilter: str | None = None,
) -> pl.DataFrame:
    """유형×월 빈도 시계열 로드."""
    global _cachedTimeline

    if _cachedTimeline is None:
        path = _stemIndexDir() / "eventTimeline.parquet"
        if not path.exists():
            raise FileNotFoundError(f"eventTimeline.parquet 없음: {path}")
        _cachedTimeline = pl.read_parquet(path)

    result = _cachedTimeline
    if typeFilter:
        result = result.filter(pl.col("report_nm").str.contains(typeFilter))
    if periodFilter:
        result = result.filter(pl.col("period").str.starts_with(periodFilter))
    return result


def pulse(topK: int = 10) -> pl.DataFrame:
    """최근 월의 공시 유형별 건수 + 전월 대비 변화.

    Returns
    -------
    pl.DataFrame
        columns: type_norm, current, previous, change_pct, corp_count
    """
    tl = loadTimeline()
    if tl.height == 0:
        return pl.DataFrame()

    periods = tl["period"].unique().sort(descending=True)
    if len(periods) < 2:
        return tl.head(topK)

    current = periods[0]
    previous = periods[1]

    cur = tl.filter(pl.col("period") == current).select(
        pl.col("report_nm").alias("type_norm"),
        pl.col("count").alias("current"),
        pl.col("corp_count"),
    )
    prev = tl.filter(pl.col("period") == previous).select(
        pl.col("report_nm").alias("type_norm"),
        pl.col("count").alias("previous"),
    )

    merged = cur.join(prev, on="type_norm", how="left").with_columns(
        pl.col("previous").fill_null(0),
    ).with_columns(
        pl.when(pl.col("previous") > 0)
        .then(((pl.col("current") - pl.col("previous")) / pl.col("previous") * 100).round(1))
        .otherwise(None)
        .alias("change_pct")
    ).sort("current", descending=True)

    return merged.head(topK)


# ── Disclosure DNA ──


def buildDna(meta: pl.DataFrame, outDir: Path) -> dict:
    """114개 유형 빈도 분포를 기업별 114차원 벡터로 인코딩."""
    global _cachedDna

    af = meta.filter(
        (pl.col("source") == "allFilings") & (pl.col("stock_code") != "")
    )

    if af.height == 0:
        return {}

    # 정규화 유형 목록 (고정 순서)
    allTypes = sorted(af["report_nm"].unique().to_list())
    typeToIdx = {t: i for i, t in enumerate(allTypes)}
    nTypes = len(allTypes)

    # 기업별 유형 건수
    counts = (
        af.group_by("stock_code", "report_nm")
        .len()
    )
    totals = af.group_by("stock_code").len().rename({"len": "total"})
    counts = counts.join(totals, on="stock_code")

    # 기업별 벡터 빌드
    stockCodes = sorted(counts["stock_code"].unique().to_list())
    vectors = np.zeros((len(stockCodes), nTypes), dtype=np.float32)
    stockToIdx = {s: i for i, s in enumerate(stockCodes)}

    for row in counts.iter_rows(named=True):
        si = stockToIdx[row["stock_code"]]
        ti = typeToIdx.get(row["report_nm"])
        if ti is not None and row["total"] > 0:
            vectors[si, ti] = row["len"] / row["total"]

    # 저장
    np.savez_compressed(
        outDir / "dna.npz",
        vectors=vectors,
        stockCodes=np.array(stockCodes),
        typeNames=np.array(allTypes),
    )

    _cachedDna = {
        "vectors": vectors,
        "stockCodes": stockCodes,
        "typeNames": allTypes,
    }
    return _cachedDna


def _loadDna() -> dict:
    global _cachedDna

    if _cachedDna is not None:
        return _cachedDna

    path = _stemIndexDir() / "dna.npz"
    if not path.exists():
        raise FileNotFoundError(f"dna.npz 없음: {path}")

    loaded = np.load(path, allow_pickle=True)
    _cachedDna = {
        "vectors": loaded["vectors"],
        "stockCodes": loaded["stockCodes"].tolist(),
        "typeNames": loaded["typeNames"].tolist(),
    }
    return _cachedDna


def dna(stockCode: str) -> dict:
    """기업의 Disclosure DNA (114차원 유형 빈도 벡터).

    Returns
    -------
    dict
        keys: stockCode, vector (list[float]), topTypes (list[tuple[str, float]])
    """
    data = _loadDna()
    if stockCode not in data["stockCodes"]:
        return None

    idx = data["stockCodes"].index(stockCode)
    vec = data["vectors"][idx]
    typeNames = data["typeNames"]

    # 상위 5개 유형
    topIndices = np.argsort(vec)[::-1][:5]
    topTypes = [(typeNames[i], round(float(vec[i]), 4)) for i in topIndices if vec[i] > 0]

    return {
        "stockCode": stockCode,
        "vector": vec.tolist(),
        "topTypes": topTypes,
    }


def similarCompanies(stockCode: str, topK: int = 5) -> pl.DataFrame:
    """공시 패턴이 유사한 기업 탐색 (코사인 유사도).

    Returns
    -------
    pl.DataFrame
        columns: stock_code, similarity
    """
    data = _loadDna()
    if stockCode not in data["stockCodes"]:
        return pl.DataFrame()

    idx = data["stockCodes"].index(stockCode)
    target = data["vectors"][idx]

    # 코사인 유사도
    norms = np.linalg.norm(data["vectors"], axis=1)
    targetNorm = np.linalg.norm(target)
    if targetNorm == 0:
        return pl.DataFrame()

    sims = data["vectors"] @ target / (norms * targetNorm + 1e-10)
    sims[idx] = -1  # 자기 자신 제외

    topIndices = np.argsort(sims)[::-1][:topK]

    rows = []
    for i in topIndices:
        if sims[i] <= 0:
            break
        rows.append({
            "stock_code": data["stockCodes"][i],
            "similarity": round(float(sims[i]), 4),
        })

    if not rows:
        return pl.DataFrame()

    # corp_name 붙이기
    result = pl.DataFrame(rows)
    try:
        profile = loadProfile()
        if isinstance(profile, pl.DataFrame) and "corp_name" in profile.columns:
            result = result.join(
                profile.select("stock_code", "corp_name"),
                on="stock_code",
                how="left",
            )
    except FileNotFoundError:
        pass

    return result
