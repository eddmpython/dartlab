"""Data Workbench universe snapshot resolution과 coverage helpers."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import polars as pl

from dartlab.data.contracts import DataGap, UniverseSelection
from dartlab.data.discovery import discoverOwnerProviders


@dataclass(frozen=True, slots=True)
class ResolvedMarket:
    """한 market의 revision-fixed membership identity."""

    market: str
    provider: str
    entityIds: tuple[str, ...]
    membershipDigest: str


@dataclass(frozen=True, slots=True)
class ResolvedUniverse:
    """여러 market membership과 gap을 같은 snapshot에 결박한다."""

    snapshotId: str
    selection: UniverseSelection
    markets: tuple[ResolvedMarket, ...]
    gaps: tuple[DataGap, ...]

    def byMarket(self) -> dict[str, ResolvedMarket]:
        """해소된 membership을 market key mapping으로 반환한다."""

        return {item.market: item for item in self.markets}


def _canonical(value: Any) -> bytes:
    def serializeDefault(item: Any) -> Any:
        """Universe snapshot 값을 결정적 JSON 표현으로 변환한다."""

        if dataclasses.is_dataclass(item):
            return {field.name: getattr(item, field.name) for field in dataclasses.fields(item)}
        if isinstance(item, Mapping):
            return dict(item)
        if isinstance(item, (tuple, set, frozenset)):
            return list(item)
        return str(item)

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=serializeDefault,
    ).encode()


def _resolverSpec(universeKind: str, market: str, membership: str) -> Mapping[str, Any] | None:
    providers, _ = discoverOwnerProviders()
    for provider in providers:
        for spec in provider.get("universeResolvers", ()):
            if not isinstance(spec, Mapping):
                continue
            if str(spec.get("universeKind")) != universeKind:
                continue
            markets = {str(value).upper() for value in spec.get("markets", ())}
            memberships = {str(value) for value in spec.get("memberships", ())}
            if market in markets and membership in memberships:
                return spec
    return None


def _loadMembership(selection: UniverseSelection, market: str) -> tuple[ResolvedMarket | None, DataGap | None]:
    spec = _resolverSpec("listedEquity", market, selection.membership)
    if spec is None:
        code = (
            "UNIVERSE_PIT_UNSUPPORTED"
            if selection.asOf is not None
            else "UNIVERSE_MEMBERSHIP_UNSUPPORTED"
            if selection.membership == "allKnown"
            else "UNIVERSE_MARKET_UNSUPPORTED"
        )
        return None, DataGap(code, f"{market} {selection.membership} universe resolver가 없습니다", systemic=True)
    try:
        module = importlib.import_module(str(spec["module"]))
        resolver = getattr(module, str(spec["attribute"]))
        frame = resolver(market=market, membership=selection.membership, asOf=selection.asOf)
    except Exception as exc:
        message = str(exc)
        code = message if message.startswith("UNIVERSE_") else "UNIVERSE_RESOLUTION_FAILED"
        return None, DataGap(code, f"{market}: {type(exc).__name__}: {message}", systemic=True)
    if not isinstance(frame, pl.DataFrame) or "entityId" not in frame.columns:
        return None, DataGap("UNIVERSE_RESOLUTION_FAILED", f"{market} resolver schema가 유효하지 않습니다")
    provider = (
        str(frame["provider"][0])
        if frame.height and "provider" in frame.columns
        else str(spec.get("provider") or "unknown")
    )
    ids = tuple(sorted({str(value) for value in frame["entityId"].drop_nulls().to_list() if str(value)}))
    explicit = tuple(value.split(":", 1)[1] for value in selection.explicitIds if value.startswith(f"{market}:"))
    missing = tuple(value for value in explicit if value not in set(ids))
    if explicit:
        ids = tuple(value for value in explicit if value in set(ids))
    digest = hashlib.sha256(
        _canonical({"market": market, "provider": provider, "membership": selection.membership, "ids": ids})
    ).hexdigest()
    gap = None
    if missing:
        sample = ", ".join(f"{market}:{value}" for value in missing[:8])
        gap = DataGap("UNIVERSE_ENTITY_NOT_FOUND", sample, systemic=False)
    return ResolvedMarket(market, provider, ids, digest), gap


def _explicitMarket(selection: UniverseSelection, market: str) -> ResolvedMarket:
    ids = tuple(value.split(":", 1)[1] for value in selection.explicitIds if value.startswith(f"{market}:"))
    provider = "dart" if market == "KR" else "edgar" if market == "US" else "explicit"
    digest = hashlib.sha256(
        _canonical({"market": market, "provider": provider, "membership": "explicit", "ids": ids})
    ).hexdigest()
    return ResolvedMarket(market, provider, ids, digest)


def resolveUniverse(selection: UniverseSelection) -> ResolvedUniverse:
    """Owner-declared resolver로 market membership을 한 번 해소한다."""

    markets: list[ResolvedMarket] = []
    gaps: list[DataGap] = []
    for market in selection.markets:
        if selection.membership == "explicit":
            resolved = _explicitMarket(selection, market)
            gap = None
        else:
            resolved, gap = _loadMembership(selection, market)
        if resolved is not None:
            markets.append(resolved)
            if not resolved.entityIds:
                gaps.append(DataGap("EMPTY_UNIVERSE", f"{market} universe가 비었습니다", systemic=True))
        if gap is not None:
            gaps.append(gap)
    payload = {
        "selection": selection,
        "markets": tuple(markets),
    }
    snapshotId = f"universe-snapshot:{hashlib.sha256(_canonical(payload)).hexdigest()}"
    return ResolvedUniverse(snapshotId, selection, tuple(markets), tuple(gaps))


def entityIds(value: Any, market: str) -> frozenset[str] | None:
    """Owner native output에서 market universe identity를 보수적으로 추출한다."""

    if not isinstance(value, pl.DataFrame):
        return None
    candidates = (
        ("종목코드", "stockCode", "ticker", "entityId")
        if market == "KR"
        else ("stockCode", "ticker", "entityId", "종목코드")
    )
    column = next((name for name in candidates if name in value.columns), None)
    if column is None:
        return None
    values = value[column].cast(pl.Utf8, strict=False).drop_nulls().to_list()
    if market == "US":
        return frozenset(str(item).strip().upper() for item in values if str(item).strip())
    return frozenset(str(item).strip().zfill(6) for item in values if str(item).strip())


__all__ = ["ResolvedMarket", "ResolvedUniverse", "entityIds", "resolveUniverse"]
