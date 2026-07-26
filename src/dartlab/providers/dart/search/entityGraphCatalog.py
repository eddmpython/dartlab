"""Offline entity graph catalog builder for search contentIndex artifacts."""

from __future__ import annotations

import gc
import json
import os
import shutil
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.core.logger import getLogger
from dartlab.providers.dart.search.entityGraph import ENTITY_GRAPH_CATALOG_NAME

_log = getLogger(__name__)

ENTITY_GRAPH_CATALOG_SCHEMA_VERSION = "searchEntityGraphCatalog.v1"


def prepareEntityGraphCatalogArtifact(
    outDir: str | Path,
    *,
    sourceCatalogPath: str | Path | None = None,
) -> dict[str, Any]:
    """Prepare the optional graph catalog artifact beside a content index.

    Args:
        outDir: Content index output directory.
        sourceCatalogPath: Optional search catalog snapshot used to derive seed
            stock codes when explicit graph build is enabled.

    Returns:
        dict[str, Any]: Preparation summary. ``mode="disabled"`` means no graph
        catalog was requested.

    Raises:
        OSError: If an explicit source file cannot be copied or the output
            artifact cannot be written.

    Example:
        >>> prepareEntityGraphCatalogArtifact("/tmp/missing-out")["mode"]
        'disabled'
    """
    base = Path(outDir)
    explicit = os.environ.get("DARTLAB_SEARCH_ENTITY_GRAPH_CATALOG", "").strip()
    target = base / ENTITY_GRAPH_CATALOG_NAME
    if explicit:
        src = Path(explicit)
        if src.exists():
            base.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
            return {"mode": "copied", "path": str(target), "source": str(src)}
        return {"mode": "missing", "path": str(target), "source": str(src)}

    if not _envFlag("DARTLAB_SEARCH_ENTITY_GRAPH_BUILD", default=False):
        return {"mode": "disabled"}

    seedCodes = _splitCodes(os.environ.get("DARTLAB_SEARCH_ENTITY_GRAPH_SEED_CODES", ""))
    if not seedCodes and sourceCatalogPath is not None:
        maxSeeds = int(os.environ.get("DARTLAB_SEARCH_ENTITY_GRAPH_MAX_SEEDS", "100"))
        seedCodes = seedCodesFromSearchCatalog(sourceCatalogPath, maxSeeds=maxSeeds)
    if not seedCodes:
        return {"mode": "empty", "path": str(target)}

    neighbors = int(os.environ.get("DARTLAB_SEARCH_ENTITY_GRAPH_NEIGHBORS", "3"))
    catalog = buildEntityGraphCatalog(seedCodes, neighborsPerSeed=neighbors)
    writeEntityGraphCatalog(catalog, target)
    return {"mode": "built", "path": str(target), "rows": catalog.height, "seedCodes": seedCodes}


def buildEntityGraphCatalog(
    seedCodes: Iterable[str],
    *,
    neighborsPerSeed: int = 3,
    companyFactory: Callable[[str], Any] | None = None,
    creditFn: Callable[[str], Mapping[str, Any]] | None = None,
    listing: pl.DataFrame | None = None,
    generatedAt: str | None = None,
) -> pl.DataFrame:
    """Build a compact entity graph catalog from deterministic engines.

    Args:
        seedCodes: Stock codes used to discover peer neighborhoods.
        neighborsPerSeed: Maximum peers to keep per seed.
        companyFactory: Optional factory with ``industry()`` for tests.
        creditFn: Optional credit function for tests.
        listing: Optional listing DataFrame used for code->name fallback.
        generatedAt: Optional deterministic timestamp for tests.

    Returns:
        pl.DataFrame: Entity rows keyed by stock code with JSON neighbor cards.

    Raises:
        없음. Per-company failures degrade to empty row attributes.

    Example:
        >>> buildEntityGraphCatalog([], generatedAt="2026").height
        0
    """
    if companyFactory is None or creditFn is None or listing is None:
        from dartlab.providers.dart.company import Company

        companyFactory = companyFactory or Company
        listing = listing if listing is not None else Company.listing()

    listingByCode = _listingByCode(listing)
    generated = generatedAt or datetime.now(UTC).isoformat()
    rowsByCode: dict[str, dict[str, Any]] = {}

    for seed in _dedupe(_stockCode(code) for code in seedCodes if str(code).strip()):
        industry = _industry(companyFactory, seed)
        peers = _peerRows(industry, limit=neighborsPerSeed)
        stageName = _stageName(industry)
        chainName = str(industry.get("chainName") or industry.get("chainId") or "") if industry else ""
        confidence = _safeFloat((industry or {}).get("confidence"))
        group = [{"stockCode": seed, "corpName": _nameForCode(seed, listingByCode), "role": "seed"}, *peers]
        summaries = []
        for node in group:
            code = _stockCode(node.get("stockCode"))
            if not code:
                continue
            credit = _credit(creditFn, companyFactory, code)
            summaries.append(
                {
                    "stockCode": code,
                    "corpName": str(node.get("corpName") or _nameForCode(code, listingByCode)),
                    "role": str(node.get("role") or "peer"),
                    "grade": credit.get("grade", ""),
                    "weakAxis": credit.get("weakAxis", ""),
                    "weakAxisScore": credit.get("weakAxisScore"),
                    "stageName": stageName,
                    "chainName": chainName,
                    "industryConfidence": confidence,
                }
            )
            gc.collect()
        for node in summaries:
            code = str(node["stockCode"])
            neighbors = [_neighborCard(other) for other in summaries if other["stockCode"] != code]
            row = rowsByCode.get(code)
            if row is None:
                rowsByCode[code] = {
                    "stockCode": code,
                    "corpName": node["corpName"],
                    "nameKey": _nameKey(node["corpName"]),
                    "grade": node["grade"],
                    "weakAxis": node["weakAxis"],
                    "weakAxisScore": node["weakAxisScore"],
                    "stageName": node["stageName"],
                    "chainName": node["chainName"],
                    "industryConfidence": node["industryConfidence"],
                    "neighborsJson": json.dumps(neighbors, ensure_ascii=False, separators=(",", ":")),
                    "catalogSourceJson": json.dumps(
                        {
                            "seedCode": seed,
                            "source": ["Company.industry()", "credit()"],
                            "mode": "offline-build",
                        },
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "generatedAt": generated,
                    "dataAsOf": generated[:10].replace("-", ""),
                }
            else:
                merged = _mergeNeighbors(_jsonList(row.get("neighborsJson")), neighbors, selfCode=code)
                row["neighborsJson"] = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
    return pl.DataFrame(list(rowsByCode.values()))


def seedCodesFromSearchCatalog(path: str | Path, *, maxSeeds: int = 100) -> list[str]:
    """Pick top stock codes from a search catalog snapshot.

    Args:
        path: Parquet catalog path.
        maxSeeds: Maximum stock codes to return.

    Returns:
        list[str]: Most frequent six-digit stock codes.

    Raises:
        OSError: If the parquet file cannot be read.

    Example:
        >>> seedCodesFromSearchCatalog("missing.parquet")
        Traceback (most recent call last):
        ...
        FileNotFoundError: ...
    """
    schema = set(pl.read_parquet_schema(path))
    column = "stockCode" if "stockCode" in schema else "stock_code" if "stock_code" in schema else ""
    if not column:
        return []
    # catalog에는 수백 MB의 searchText가 있으므로 종목코드 한 열만 projection한다.
    catalog = pl.read_parquet(path, columns=[column])
    if catalog.height == 0:
        return []
    return [
        code
        for code in (
            catalog.select(pl.col(column).cast(pl.Utf8).alias("stockCode"))
            .with_columns(pl.col("stockCode").map_elements(_stockCode, return_dtype=pl.Utf8))
            .filter(pl.col("stockCode").str.contains(r"^\d{6}$"))
            .group_by("stockCode")
            .len()
            .sort("len", descending=True)
            .head(max(0, int(maxSeeds)))["stockCode"]
            .to_list()
        )
        if code
    ]


def writeEntityGraphCatalog(catalog: pl.DataFrame, path: str | Path) -> None:
    """Write graph catalog parquet and a JSON manifest next to it.

    Args:
        catalog: Entity graph catalog rows.
        path: Output parquet path.

    Returns:
        None.

    Raises:
        OSError: If output files cannot be written.

    Example:
        >>> import polars as pl
        >>> tmp = __import__("tempfile").TemporaryDirectory()
        >>> writeEntityGraphCatalog(pl.DataFrame(), Path(tmp.name) / "entityGraphCatalog.parquet")
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_parquet(out)
    manifest = {
        "schemaVersion": ENTITY_GRAPH_CATALOG_SCHEMA_VERSION,
        "rows": catalog.height,
        "columns": catalog.columns,
        "generatedAt": datetime.now(UTC).isoformat(),
        "requestPath": "join-only; no live traversal",
    }
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _industry(companyFactory: Callable[[str], Any], code: str) -> dict[str, Any]:
    try:
        data = companyFactory(code).industry() or {}
    except Exception as exc:
        _log.warning("업종 조회 실패로 빈 결과 반환 (%s): %s: %s", code, type(exc).__name__, exc)
        return {}
    return dict(data) if isinstance(data, Mapping) else {}


def _credit(
    creditFn: Callable[[str], Mapping[str, Any]] | None,
    companyFactory: Callable[[str], Any],
    code: str,
) -> dict[str, Any]:
    try:
        raw = creditFn(code) if creditFn is not None else companyFactory(code).credit()
        raw = raw or {}
    except Exception as exc:
        return {"grade": "", "weakAxis": "", "weakAxisScore": None, "error": str(exc)[:80]}
    axes = [axis for axis in raw.get("axes", []) if isinstance(axis, Mapping) and axis.get("score") is not None]
    weak = max(axes, key=lambda axis: axis.get("score", 0), default={})
    return {
        "grade": str(raw.get("grade") or ""),
        "weakAxis": str(weak.get("name") or ""),
        "weakAxisScore": _safeFloat(weak.get("score")),
    }


def _peerRows(industry: Mapping[str, Any] | None, *, limit: int) -> list[dict[str, str]]:
    rows = []
    for peer in (industry or {}).get("peers", [])[: max(0, int(limit))]:
        code = _stockCode(peer.get("stockCode"))
        if not code:
            continue
        rows.append({"stockCode": code, "corpName": str(peer.get("corpName") or ""), "role": "peer"})
    return rows


def _stageName(industry: Mapping[str, Any] | None) -> str:
    if not industry:
        return ""
    return str(industry.get("stageName") or industry.get("stageLabel") or industry.get("stage") or "")


def _neighborCard(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stockCode": row.get("stockCode", ""),
        "corpName": row.get("corpName", ""),
        "role": row.get("role", ""),
        "grade": row.get("grade", ""),
        "weakAxis": row.get("weakAxis", ""),
        "weakAxisScore": row.get("weakAxisScore"),
        "stageName": row.get("stageName", ""),
        "chainName": row.get("chainName", ""),
        "industryConfidence": row.get("industryConfidence"),
    }


def _mergeNeighbors(
    existing: list[dict[str, Any]], new: list[dict[str, Any]], *, selfCode: str
) -> list[dict[str, Any]]:
    out = []
    seen = {selfCode}
    for row in [*existing, *new]:
        code = _stockCode(row.get("stockCode"))
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(row)
    return out


def _listingByCode(listing: pl.DataFrame | None) -> dict[str, str]:
    if listing is None or listing.height == 0:
        return {}
    out: dict[str, str] = {}
    for row in listing.iter_rows(named=True):
        code = _stockCode(row.get("종목코드") or row.get("stockCode") or row.get("stock_code"))
        name = str(row.get("회사명") or row.get("corpName") or row.get("corp_name") or "").strip()
        if code and name:
            out[code] = name
    return out


def _nameForCode(code: str, listingByCode: Mapping[str, str]) -> str:
    return str(listingByCode.get(_stockCode(code), "")).strip()


def _stockCode(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 6:
        return digits
    return text.zfill(6) if text.isdigit() and len(text) <= 6 else text


def _nameKey(value: Any) -> str:
    text = str(value or "").strip().lower()
    removable = set(" \t\r\n()[]{}㈜주식회사,.-_")
    return "".join(ch for ch in text if ch not in removable)


def _safeFloat(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _jsonList(raw: Any) -> list[dict[str, Any]]:
    if raw in (None, ""):
        return []
    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)]
    try:
        parsed = json.loads(str(raw))
    except json.JSONDecodeError:
        return []
    return [row for row in parsed if isinstance(row, dict)] if isinstance(parsed, list) else []


def _dedupe(values: Iterable[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _splitCodes(raw: str) -> list[str]:
    return [_stockCode(part) for part in str(raw or "").split(",") if str(part).strip()]


def _envFlag(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() not in {"0", "false", "no", "n"}
