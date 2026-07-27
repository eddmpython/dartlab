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

from dartlab.dataHub.catalog.discovery import discoverOwnerProviders
from dartlab.dataHub.contracts import DataGap, UniverseSelection

# resolver 가 자기 사정을 code 로 올려 보낼 수 있는 값은 이 셋뿐이다. 그 밖의 예외는
# 전부 UNIVERSE_RESOLUTION_FAILED 로 모으고 사정은 message 로만 전한다.
_UNIVERSE_GAP_CODES = frozenset(
    {
        "UNIVERSE_MARKET_UNSUPPORTED",
        "UNIVERSE_MEMBERSHIP_UNSUPPORTED",
        "UNIVERSE_PIT_UNSUPPORTED",
    }
)


@dataclass(frozen=True, slots=True)
class ResolvedMarket:
    """한 market의 revision-fixed membership identity."""

    market: str
    provider: str
    entityIds: tuple[str, ...]
    membershipDigest: str
    sourceEntityIds: tuple[tuple[str, str], ...] = ()
    entityParams: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()

    def sourceIdByEntity(self) -> dict[str, str]:
        """공개 entity ID를 owner 원천 식별자로 연결한다.

        Args:
            없음.

        Returns:
            Canonical entity ID에서 source entity ID로 가는 새 mapping.

        Raises:
            없음.

        Example:
            ``membership.sourceIdByEntity()["AAPL"]``.
        """

        return dict(self.sourceEntityIds)

    def paramsByEntity(self) -> dict[str, tuple[tuple[str, str], ...]]:
        """공개 entity ID별 snapshot-bound executor parameter를 반환한다.

        Args:
            없음.

        Returns:
            Canonical entity ID에서 정렬된 parameter tuple로 가는 mapping.

        Raises:
            없음.

        Example:
            ``membership.paramsByEntity()["005930"]``.
        """

        return dict(self.entityParams)


@dataclass(frozen=True, slots=True)
class ResolvedUniverse:
    """여러 market membership과 gap을 같은 snapshot에 결박한다."""

    snapshotId: str
    selection: UniverseSelection
    markets: tuple[ResolvedMarket, ...]
    gaps: tuple[DataGap, ...]

    def byMarket(self) -> dict[str, ResolvedMarket]:
        """해소된 membership을 market key mapping으로 반환한다.

        Args:
            없음.

        Returns:
            Market code에서 revision-fixed membership으로 가는 mapping.

        Raises:
            없음.

        Example:
            ``resolved.byMarket()["US"]``.
        """

        return {item.market: item for item in self.markets}


def _canonical(value: Any) -> bytes:
    def serializeDefault(item: Any) -> Any:
        """Universe snapshot 값을 결정적 JSON 표현으로 변환한다.

        Args:
            item: JSON encoder가 직접 처리하지 못한 값.

        Returns:
            Dataclass, mapping 또는 collection의 결정적 표현.

        Raises:
            없음.

        Example:
            ``serializeDefault(selection)``.
        """

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


def _missingResolverGap(selection: UniverseSelection, market: str) -> DataGap:
    """resolver 자체가 없을 때의 gap. 무엇이 없어서 없는지까지 code 로 구분한다."""
    code = (
        "UNIVERSE_PIT_UNSUPPORTED"
        if selection.asOf is not None
        else "UNIVERSE_MEMBERSHIP_UNSUPPORTED"
        if selection.membership == "allKnown"
        else "UNIVERSE_MARKET_UNSUPPORTED"
    )
    return DataGap(code, f"{market} {selection.membership} universe resolver가 없습니다", systemic=True)


def _callResolver(spec: Mapping[str, Any], selection: UniverseSelection, market: str):
    """resolver 를 불러 프레임을 받는다. 실패는 gap 으로 돌린다.

    Returns:
        ``(frame, gap)``. 둘 중 하나만 값이 있다.
    """
    try:
        module = importlib.import_module(str(spec["module"]))
        resolver = getattr(module, str(spec["attribute"]))
        return resolver(market=market, membership=selection.membership, asOf=selection.asOf), None
    except Exception as exc:
        message = str(exc)
        # 예외 문구를 통째로 code 로 쓰면 code 공간이 무한해지고, 경로 같은 내부 사정이
        # 공개 결과에 실려 나간다. 앞머리만 떼어 정해진 code 집합에 맞추고 나머지는
        # message 에 남긴다. code 는 기계가 읽는 자리다.
        head = message.split(":", 1)[0].strip()
        code = head if head in _UNIVERSE_GAP_CODES else "UNIVERSE_RESOLUTION_FAILED"
        return None, DataGap(code, f"{market}: {type(exc).__name__}: {message}", systemic=True)


def _entityParamsFromFrame(
    normalized, paramColumns: tuple[str, ...], market: str
) -> tuple[tuple[tuple[str, tuple[tuple[str, str], ...]], ...] | None, DataGap | None]:
    """entity 별 파라미터를 모은다. 같은 entity 가 서로 다른 값을 들고 오면 gap.

    한 종목이 두 벌의 파라미터를 갖는 것은 universe 정의 자체가 어긋난 것이라 부분 성공으로
    넘기지 않는다.
    """
    paramsByEntity: dict[str, tuple[tuple[str, str], ...]] = {}
    for row in normalized.select("entityId", *paramColumns).iter_rows(named=True):
        entityId = str(row["entityId"])
        params = tuple(
            (column.removeprefix("param_"), str(row[column]))
            for column in paramColumns
            if row[column] is not None and str(row[column])
        )
        previous = paramsByEntity.get(entityId)
        if previous is not None and previous != params:
            return None, DataGap(
                "UNIVERSE_RESOLUTION_FAILED",
                f"{market} entity parameter가 충돌합니다: {entityId}",
                systemic=True,
            )
        paramsByEntity[entityId] = params
    return tuple(sorted(paramsByEntity.items())), None


def _readMembershipFrame(frame, market: str):
    """resolver 프레임에서 식별자, 원천 식별자, entity 파라미터를 꺼낸다.

    프레임을 읽는 일과 그 결과로 무엇을 고를지 정하는 일을 나눈다. 앞은 자료 모양을 알고
    뒤는 선택 규칙을 안다. 한 함수에 있으면 열 이름 하나 늘 때마다 선택 규칙 쪽을 지나며
    읽게 된다.

    Returns:
        ``(ids, sourceIds, entityParams, gap)``. gap 이 있으면 앞 셋은 쓰지 않는다.
    """
    normalized = frame.with_columns(pl.col("entityId").cast(pl.Utf8))
    ids = tuple(sorted({str(value) for value in normalized["entityId"].drop_nulls().to_list() if str(value)}))
    sourceIds: tuple[tuple[str, str], ...] = ()
    if "sourceEntityId" in normalized.columns:
        sourceIds = tuple(
            sorted(
                {
                    (str(row["entityId"]), str(row["sourceEntityId"]))
                    for row in normalized.select("entityId", "sourceEntityId").drop_nulls().iter_rows(named=True)
                    if str(row["entityId"]) and str(row["sourceEntityId"])
                }
            )
        )
    paramColumns = tuple(sorted(column for column in normalized.columns if column.startswith("param_")))
    entityParams: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()
    if paramColumns:
        entityParams, paramGap = _entityParamsFromFrame(normalized, paramColumns, market)
        if paramGap is not None:
            return (), (), (), paramGap
    return ids, sourceIds, entityParams, None


def _loadMembership(selection: UniverseSelection, market: str) -> tuple[ResolvedMarket | None, DataGap | None]:
    spec = _resolverSpec("listedEquity", market, selection.membership)
    if spec is None:
        return None, _missingResolverGap(selection, market)
    frame, callGap = _callResolver(spec, selection, market)
    if callGap is not None:
        return None, callGap
    if not isinstance(frame, pl.DataFrame) or "entityId" not in frame.columns:
        # resolver 가 망가진 것은 한 종목의 결손이 아니라 그 시장 전체가 안 나오는 사건이다.
        # systemic 을 안 달면 다른 asset 하나가 성공했다는 이유로 partial 로 내려간다.
        return None, DataGap(
            "UNIVERSE_RESOLUTION_FAILED", f"{market} resolver schema가 유효하지 않습니다", systemic=True
        )
    provider = (
        str(frame["provider"][0])
        if frame.height and "provider" in frame.columns
        else str(spec.get("provider") or "unknown")
    )
    ids, sourceIds, entityParams, paramGap = _readMembershipFrame(frame, market)
    if paramGap is not None:
        return None, paramGap
    explicit = tuple(value.split(":", 1)[1] for value in selection.explicitIds if value.startswith(f"{market}:"))
    missing = tuple(value for value in explicit if value not in set(ids))
    if explicit:
        ids = tuple(value for value in explicit if value in set(ids))
        selected = set(ids)
        sourceIds = tuple(item for item in sourceIds if item[0] in selected)
        entityParams = tuple(item for item in entityParams if item[0] in selected)
    digest = hashlib.sha256(
        _canonical(
            {
                "market": market,
                "provider": provider,
                "membership": selection.membership,
                "ids": ids,
                "sourceIds": sourceIds,
                "entityParams": entityParams,
            }
        )
    ).hexdigest()
    gap = None
    if missing:
        sample = ", ".join(f"{market}:{value}" for value in missing[:8])
        gap = DataGap("UNIVERSE_ENTITY_NOT_FOUND", sample, systemic=False)
    return ResolvedMarket(
        market=market,
        provider=provider,
        entityIds=ids,
        membershipDigest=digest,
        sourceEntityIds=sourceIds,
        entityParams=entityParams,
    ), gap


def _explicitMarket(selection: UniverseSelection, market: str) -> ResolvedMarket:
    ids = tuple(value.split(":", 1)[1] for value in selection.explicitIds if value.startswith(f"{market}:"))
    provider = "dart" if market == "KR" else "edgar" if market == "US" else "explicit"
    digest = hashlib.sha256(
        _canonical({"market": market, "provider": provider, "membership": "explicit", "ids": ids})
    ).hexdigest()
    return ResolvedMarket(market, provider, ids, digest)


def resolveUniverse(selection: UniverseSelection) -> ResolvedUniverse:
    """Owner-declared resolver로 market membership을 한 번 해소한다.

    Args:
        selection: Market, membership 종류와 optional as-of scope.

    Returns:
        Membership, gap과 content-bound snapshot을 가진 resolved universe.

    Raises:
        없음. Resolver 실패는 구조화된 gap으로 반환한다.

    Example:
        ``resolved = resolveUniverse(UniverseSelection(("US",)))``.
    """

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
    """Owner native output에서 market universe identity를 보수적으로 추출한다.

    Args:
        value: Owner가 반환한 native output.
        market: Entity 정규화에 사용할 market code.

    Returns:
        확인된 canonical entity 집합 또는 검증 불가 시 ``None``.

    Raises:
        없음.

    Example:
        ``observed = entityIds(frame, "US")``.
    """

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
