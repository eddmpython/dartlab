"""Expectation ledger : append-only parquet IO for issued expectations and their scores.

The ledger is the verification spine of the simulate engine (mainPlan/expectation-grid).
Rows are ExpectationSpec (sealed at issuance, immutable) and ExpectationScore (appended when
actuals arrive; re-scoring appends a new row, never rewrites). There are deliberately no
update or delete functions: a wrong issuance is history too, annotated only via warnings.

Layer: L2.5 simulate owns the ledger because it is the sole writer (the collector calls L2
engine verbs and seals their output; L2 engines never import this module, which the
downward-only import contract enforces).

Storage: ``{DARTLAB_DATA_DIR|data}/expectations/{expectations|scores}_{yyyy}.parquet``
(flat year shards, HF surface ``expectations/`` via DATA_RELEASES, write end = CI sync only).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import polars as pl

from dartlab.synth.expectationSpec import ExpectationScore, ExpectationSpec

LEDGER_SUBDIR = "expectations"
_JSON_FIELDS = {"quantiles", "direction", "baselines", "sourceRefs", "warnings", "crpsBaseline"}


def ledgerDir(baseDir: Path | None = None) -> Path:
    """Resolve the ledger root: explicit baseDir > DARTLAB_DATA_DIR env > ./data."""
    if baseDir is not None:
        return baseDir
    root = os.environ.get("DARTLAB_DATA_DIR")
    return (Path(root) if root else Path("data")) / LEDGER_SUBDIR


def _flatten(row: ExpectationSpec | ExpectationScore) -> dict:
    d = asdict(row)
    for k in list(d):
        if k in _JSON_FIELDS:
            d[k] = json.dumps(d[k], ensure_ascii=False)
        elif d[k] is not None and not isinstance(d[k], (str, int, float, bool)):
            d[k] = str(d[k])
    return d


def _append(rows: list, base: Path, table: str, stampField: str, *, uniqueId: bool) -> list[Path]:
    base.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    byYear: dict[str, list[dict]] = {}
    for r in rows:
        byYear.setdefault(getattr(r, stampField)[:4], []).append(_flatten(r))
    for yyyy, flat in sorted(byYear.items()):
        path = base / f"{table}_{yyyy}.parquet"
        new = pl.DataFrame(flat)
        if path.exists():
            old = pl.read_parquet(path)
            if uniqueId:
                dup = set(old.get_column("expectationId").to_list()) & set(new.get_column("expectationId").to_list())
                if dup:
                    raise ValueError(
                        f"append-only violation (duplicate expectationId x{len(dup)}): {sorted(dup)[:3]} ..."
                    )
            new = pl.concat([old, new.select(old.columns)], how="vertical")
        tmp = path.with_suffix(".parquet.tmp")
        new.write_parquet(tmp)
        tmp.replace(path)
        written.append(path)
    return written


def appendExpectations(rows: list[ExpectationSpec], *, baseDir: Path | None = None) -> list[Path]:
    """Append sealed issuance rows. A duplicate expectationId raises ValueError (immutability)."""
    if not rows:
        return []
    return _append(rows, ledgerDir(baseDir), "expectations", "issuedAt", uniqueId=True)


def appendScores(rows: list[ExpectationScore], *, baseDir: Path | None = None) -> list[Path]:
    """Append score rows. Re-scoring after an actual revision appends a new row (history kept)."""
    if not rows:
        return []
    return _append(rows, ledgerDir(baseDir), "scores", "scoredAt", uniqueId=False)


def _readAll(base: Path, table: str) -> pl.DataFrame | None:
    files = sorted(base.glob(f"{table}_*.parquet"))
    if not files:
        return None
    return pl.concat([pl.read_parquet(f) for f in files], how="vertical")


def readExpectations(*, baseDir: Path | None = None, unscoredOnly: bool = False) -> pl.DataFrame | None:
    """Read issuance rows across year shards; unscoredOnly keeps rows with no score yet."""
    base = ledgerDir(baseDir)
    df = _readAll(base, "expectations")
    if df is None or not unscoredOnly:
        return df
    scores = _readAll(base, "scores")
    if scores is None:
        return df
    done = set(scores.get_column("expectationId").to_list())
    return df.filter(~pl.col("expectationId").is_in(sorted(done)))


def readScores(*, baseDir: Path | None = None) -> pl.DataFrame | None:
    """Read score rows across year shards."""
    return _readAll(ledgerDir(baseDir), "scores")


def specFromRow(row: dict) -> ExpectationSpec:
    """Rehydrate a ledger row dict (as read from parquet) back into an ExpectationSpec."""
    quantiles = json.loads(row["quantiles"]) if row.get("quantiles") else None
    return ExpectationSpec(
        expectationId=row["expectationId"],
        domain=row["domain"],
        variable=row["variable"],
        unit=row["unit"],
        freq=row["freq"],
        horizon=row["horizon"],
        targetPeriod=row["targetPeriod"],
        issuedAt=row["issuedAt"],
        issuedLive=row["issuedLive"],
        asOf=row["asOf"],
        engine=row["engine"],
        engineVersion=row["engineVersion"],
        kind=row["kind"],
        quantiles={int(k): float(v) for k, v in quantiles.items()} if quantiles else None,
        direction=json.loads(row["direction"]) if row.get("direction") else None,
        baselines={
            name: ({int(k): float(v) for k, v in b.items()} if isinstance(b, dict) else b)
            for name, b in json.loads(row.get("baselines") or "{}").items()
        },
        sourceRefs=tuple(json.loads(row.get("sourceRefs") or "[]")),
        warnings=tuple(json.loads(row.get("warnings") or "[]")),
        schemaVersion=row.get("schemaVersion", 1),
    )
