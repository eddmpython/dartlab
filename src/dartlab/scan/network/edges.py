"""엣지 구축 — investedCompany, majorHolder 원본 → 정제 엣지 테이블."""

from __future__ import annotations

import re

import polars as pl

from dartlab.scan.network.scanner import _normalize_company_name

# ── investedCompany 엣지 ───────────────────────────────────


def build_invest_edges(
    raw: pl.DataFrame,
    name_to_code: dict[str, str],
    code_to_name: dict[str, str],
) -> pl.DataFrame:
    """investedCompany 원본 → 정제 엣지 테이블.

    Returns:
        DataFrame[from_code, from_name, to_name, to_name_norm, to_code,
                  is_listed, ownership_pct, book_value, purpose, year]
    """
    noise_names = {"-", "합계", "소계", "", " "}
    df = raw.filter(pl.col("inv_prm").is_not_null() & ~pl.col("inv_prm").is_in(list(noise_names)))

    # 지분율
    if df["trmend_blce_qota_rt"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_blce_qota_rt")
            .str.replace_all(",", "")
            .str.replace_all("-", "")
            .cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )
    else:
        df = df.with_columns(pl.col("trmend_blce_qota_rt").cast(pl.Float64, strict=False).alias("ownership_pct"))
    df = df.with_columns(
        pl.when(pl.col("ownership_pct").is_between(0, 100))
        .then(pl.col("ownership_pct"))
        .otherwise(None)
        .alias("ownership_pct")
    )

    # 장부가액
    if df["trmend_blce_acntbk_amount"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_blce_acntbk_amount")
            .str.replace_all(",", "")
            .str.replace_all("-", "")
            .cast(pl.Float64, strict=False)
            .alias("book_value")
        )
    else:
        df = df.with_columns(pl.col("trmend_blce_acntbk_amount").cast(pl.Float64, strict=False).alias("book_value"))

    # 투자목적
    purpose_map = {
        "경영참여": "경영참여",
        "단순투자": "단순투자",
        "일반투자": "단순투자",
        "투자": "단순투자",
    }
    df = df.with_columns(
        pl.col("invstmnt_purps")
        .map_elements(
            lambda v: purpose_map.get(v, "기타") if v and v != "-" else "기타",
            return_dtype=pl.Utf8,
        )
        .alias("purpose")
    )

    # 법인명 매칭
    norms, codes, listed = [], [], []
    for name in df["inv_prm"].to_list():
        norm = _normalize_company_name(name)
        code = name_to_code.get(name) or name_to_code.get(norm)
        norms.append(norm)
        codes.append(code)
        listed.append(code is not None)

    df = df.with_columns(
        pl.Series("to_name_norm", norms),
        pl.Series("to_code", codes),
        pl.Series("is_listed", listed),
        pl.col("stockCode").map_elements(lambda c: code_to_name.get(c, c), return_dtype=pl.Utf8).alias("from_name"),
    )

    return df.select(
        [
            pl.col("stockCode").alias("from_code"),
            "from_name",
            pl.col("inv_prm").alias("to_name"),
            "to_name_norm",
            "to_code",
            "is_listed",
            "ownership_pct",
            "book_value",
            "purpose",
            "year",
        ]
    )


def deduplicate_edges(edges: pl.DataFrame) -> pl.DataFrame:
    """최신 연도, (from, to) 중복 제거."""
    latest_year = edges["year"].max()
    return (
        edges.filter(pl.col("year") == latest_year)
        .sort("ownership_pct", descending=True, nulls_last=True)
        .unique(subset=["from_code", "to_name_norm"], keep="first")
    )


# ── majorHolder 엣지 ──────────────────────────────────────


_CORP_PATTERNS = re.compile(
    r"㈜|주식회사|\(주\)|법인|조합|재단|기금|공사|은행|증권|보험|캐피탈|투자|펀드|"
    r"[A-Z]{2,}|Co\.|Corp|Ltd|Inc|LLC|PTE|Fund|Trust|Bank"
)
_NOISE_NAMES = {"합계", "-", "소계", "", "계", "기타"}


def _classify_holder(name: str) -> str:
    """주주 유형: 'corp' | 'person' | 'noise'."""
    if not name or name in _NOISE_NAMES:
        return "noise"
    if _CORP_PATTERNS.search(name):
        return "corp"
    hangul = re.sub(r"[^가-힣]", "", name)
    if 2 <= len(hangul) <= 4 and len(name) <= 6:
        return "person"
    if len(name) > 8:
        return "corp"
    return "person"


def build_holder_edges(
    raw: pl.DataFrame,
    name_to_code: dict[str, str],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """majorHolder → (corp_edges, person_edges)."""
    df = raw.filter(pl.col("nm").is_not_null() & ~pl.col("nm").is_in(list(_NOISE_NAMES)))
    latest_year = df["year"].max()
    df = df.filter(pl.col("year") == latest_year)

    # 지분율
    if df["trmend_posesn_stock_qota_rt"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_posesn_stock_qota_rt")
            .str.replace_all(",", "")
            .str.replace_all("-", "")
            .cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )
    else:
        df = df.with_columns(
            pl.col("trmend_posesn_stock_qota_rt").cast(pl.Float64, strict=False).alias("ownership_pct")
        )

    types, holder_codes = [], []
    for row in df.iter_rows(named=True):
        nm = row["nm"]
        t = _classify_holder(nm)
        types.append(t)
        if t == "corp":
            norm = _normalize_company_name(nm)
            holder_codes.append(name_to_code.get(nm) or name_to_code.get(norm))
        else:
            holder_codes.append(None)

    df = df.with_columns(
        pl.Series("holder_type", types),
        pl.Series("holder_code", holder_codes),
    )

    corp = df.filter(pl.col("holder_type") == "corp")
    corp_edges = corp.select(
        [
            pl.col("holder_code").alias("from_code"),
            pl.col("nm").alias("from_name"),
            pl.col("stockCode").alias("to_code"),
            pl.col("relate"),
            pl.col("ownership_pct"),
            pl.col("year"),
        ]
    )

    person = df.filter(pl.col("holder_type") == "person")
    person_edges = person.select(
        [
            pl.col("nm").alias("person_name"),
            pl.col("stockCode").alias("to_code"),
            pl.col("relate"),
            pl.col("ownership_pct"),
            pl.col("year"),
        ]
    )

    return corp_edges, person_edges
