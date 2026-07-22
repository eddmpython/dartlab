"""Universe-scale Data Workbench query planning attempt.

카테고리
--------
기존 ``dartlab.data("query")`` 축에 전시장 universe selection을 넣기 위한
순수 계획 컴파일러다. 네트워크, 파일, owner 엔진을 호출하지 않는다.

가설
----
시장, membership, explicit ID만으로 universe를 결정적으로 표현하고,
owner capability에 따라 market bulk와 subject fanout을 섞어도 시장별 coverage와
동일한 plan ID를 만들 수 있다.

결과
----
날짜: 2026-07-22.
표본: KR DART 3종목, US EDGAR 2종목, owner asset 2개.
핵심 수치: 7 tasks, owner bulk 2, subject fanout 5, market coverage 4/4 complete.
결론: 공개 axis 추가 없이 deterministic universe plan을 만들 수 있다. 8 tests와 ruff가 통과했다.
다음 단계: DataQuery selector와 descriptor capability로 승격하고 실제 DART, EDGAR owner를 검증한다.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from typing import Literal

MembershipKind = Literal["active", "allKnown", "explicit"]
ExecutionMode = Literal["ownerBulk", "subjectFanout", "none"]
CoverageStatus = Literal["complete", "partial", "failed"]


def _normalizeMarket(value: str) -> str:
    market = value.strip().upper()
    if not market:
        raise ValueError("market이 비었습니다")
    return market


def _normalizeMemberId(value: str) -> str:
    memberId = value.strip()
    if not memberId or ":" in memberId:
        raise ValueError("member ID는 비어 있지 않은 시장 내부 ID여야 합니다")
    return memberId


def _parseExplicitId(value: str) -> tuple[str, str]:
    market, separator, memberId = value.strip().partition(":")
    if not separator:
        raise ValueError("explicit ID는 MARKET:ID 형식이어야 합니다")
    return _normalizeMarket(market), _normalizeMemberId(memberId)


def _canonicalBytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class UniverseSelection:
    """한 query가 대상으로 삼는 시장 universe를 표현한다.

    Capabilities:
        market membership 전체 또는 시장 접두 explicit ID 필터를 하나의 값으로 고정한다.

    Args:
        markets: KR, US 같은 시장 ID. 정렬과 중복 제거가 자동 적용된다.
        membership: active, allKnown, explicit 중 하나.
        explicitIds: KR:005930 같은 시장 접두 entity ID.

    Returns:
        정규화된 immutable UniverseSelection.

    Example:
        ``UniverseSelection(("KR", "US"), "active")``.

    Guide:
        전상장사는 active, 상장폐지 포함은 allKnown, 직접 목록만 쓰면 explicit을 선택한다.

    SeeAlso:
        UniverseSnapshot, compileUniversePlan.

    Requires:
        active와 allKnown은 하나 이상의 market을 요구한다. explicit은 explicitIds를 요구한다.

    AIContext:
        새 public axis가 아니라 기존 data query의 typed selector 후보 계약이다.

    LLM Specifications:
        AntiPatterns:
            - 접두 없는 ticker를 cross-market identity로 사용
            - explicit ID를 membership 합집합으로 해석
        Freshness:
            선택 값 자체는 immutable이며 membership 시점은 UniverseSnapshot이 소유한다.
        TargetMarkets:
            - KR (DART)
            - US (EDGAR)
    """

    markets: tuple[str, ...] = ()
    membership: MembershipKind = "active"
    explicitIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.membership not in {"active", "allKnown", "explicit"}:
            raise ValueError("membership가 유효하지 않습니다")
        markets = tuple(sorted({_normalizeMarket(market) for market in self.markets}))
        parsedIds = tuple(sorted({_parseExplicitId(value) for value in self.explicitIds}))
        explicitIds = tuple(f"{market}:{memberId}" for market, memberId in parsedIds)
        if self.membership == "explicit" and not explicitIds:
            raise ValueError("explicit membership에는 explicitIds가 필요합니다")
        if not markets and self.membership != "explicit":
            raise ValueError("membership universe에는 markets가 필요합니다")
        if not markets:
            markets = tuple(sorted({market for market, _ in parsedIds}))
        outsideMarkets = tuple(value for value in explicitIds if value.split(":", 1)[0] not in markets)
        if outsideMarkets:
            raise ValueError("explicitIds의 market이 selection markets 밖에 있습니다")
        object.__setattr__(self, "markets", markets)
        object.__setattr__(self, "explicitIds", explicitIds)


@dataclass(frozen=True, slots=True)
class MarketMembership:
    """한 market의 provider와 시점 고정 membership을 보존한다.

    Capabilities:
        DART 또는 EDGAR가 해소한 active와 all-known entity ID를 deterministic tuple로 만든다.

    Args:
        market: 시장 ID.
        provider: dart, edgar 같은 lower owner ID.
        activeIds: snapshot 시점의 활성 상장 entity ID.
        allKnownIds: 상장폐지 포함 알려진 entity ID. 비면 activeIds를 사용한다.

    Returns:
        시장과 provider에 결박된 immutable membership.

    Example:
        ``MarketMembership("KR", "dart", ("005930",), ("005930",))``.

    Guide:
        ID는 ticker 별칭보다 provider가 안정적으로 해소하는 entity ID를 사용한다.

    SeeAlso:
        UniverseSnapshot.

    Requires:
        activeIds는 allKnownIds의 부분집합이어야 한다.

    AIContext:
        실제 owner 조회를 하지 않는 planner input이다.

    LLM Specifications:
        AntiPatterns:
            - KR과 US ID를 접두 없이 한 배열에서 혼합
            - active entity를 allKnown에서 누락
        Freshness:
            snapshotId가 membership 기준 시점을 식별한다.
        TargetMarkets:
            - provider가 선언한 market
    """

    market: str
    provider: str
    activeIds: tuple[str, ...]
    allKnownIds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        market = _normalizeMarket(self.market)
        provider = self.provider.strip().lower()
        if not provider:
            raise ValueError("provider가 비었습니다")
        activeIds = tuple(sorted({_normalizeMemberId(value) for value in self.activeIds}))
        allKnownIds = tuple(sorted({_normalizeMemberId(value) for value in self.allKnownIds})) or activeIds
        if not set(activeIds).issubset(allKnownIds):
            raise ValueError("activeIds는 allKnownIds의 부분집합이어야 합니다")
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "activeIds", activeIds)
        object.__setattr__(self, "allKnownIds", allKnownIds)


@dataclass(frozen=True, slots=True)
class UniverseSnapshot:
    """여러 market membership을 하나의 revision에 결박한다.

    Capabilities:
        KR DART와 US EDGAR membership을 같은 query snapshot으로 계획하게 한다.

    Args:
        snapshotId: membership revision의 stable ID.
        markets: market별 membership tuple.

    Returns:
        market 순서가 정규화된 immutable snapshot.

    Example:
        ``UniverseSnapshot("u-1", (MarketMembership("KR", "dart", ("005930",)),))``.

    Guide:
        read와 refresh를 분리하고 planner에는 이미 해소된 snapshot만 전달한다.

    SeeAlso:
        UniverseSelection, compileUniversePlan.

    Requires:
        같은 market은 snapshot 안에서 한 번만 선언한다.

    AIContext:
        계획의 PIT와 재현성 근거이며 data payload가 아니다.

    LLM Specifications:
        AntiPatterns:
            - 계획 도중 live universe를 다시 조회
            - market별 서로 다른 revision을 snapshot ID 하나로 위장
        Freshness:
            외부 resolver가 발급한 snapshotId 기준.
        Dataflow:
            owner universe resolver -> UniverseSnapshot -> compileUniversePlan.
    """

    snapshotId: str
    markets: tuple[MarketMembership, ...]

    def __post_init__(self) -> None:
        snapshotId = self.snapshotId.strip()
        if not snapshotId:
            raise ValueError("snapshotId가 비었습니다")
        markets = tuple(sorted(self.markets, key=lambda item: item.market))
        marketIds = tuple(item.market for item in markets)
        if len(marketIds) != len(set(marketIds)):
            raise ValueError("snapshot market은 고유해야 합니다")
        object.__setattr__(self, "snapshotId", snapshotId)
        object.__setattr__(self, "markets", markets)


@dataclass(frozen=True, slots=True)
class OwnerCapability:
    """Asset owner의 market별 bulk와 fanout 실행 능력을 선언한다.

    Capabilities:
        membership-aware bulk pushdown과 subject fanout 지원 범위를 분리한다.

    Args:
        assetId: catalog stable asset ID.
        owner: lower owner engine ID.
        bulkMemberships: market과 membership 쌍. explicit filter가 있으면 bulk를 쓰지 않는다.
        fanoutMarkets: subject 단위 실행을 지원하는 market.

    Returns:
        정규화된 immutable owner capability.

    Example:
        ``OwnerCapability("scan.account", "scan", (("KR", "active"),), ("KR",))``.

    Guide:
        owner가 실제로 전시장 연산을 수행할 때만 bulkMemberships에 넣는다.

    SeeAlso:
        PlanTask, compileUniversePlan.

    Requires:
        assetId와 owner가 비어 있지 않아야 한다.

    AIContext:
        owner 이름 분기가 아니라 descriptor metadata로 승격할 후보 계약이다.

    LLM Specifications:
        AntiPatterns:
            - fanout loop를 bulk라고 표기
            - explicit filter를 지원하지 않는 bulk owner에 전체 market을 호출
        Freshness:
            catalog asset version과 함께 갱신해야 한다.
        TargetMarkets:
            - bulkMemberships와 fanoutMarkets에 선언된 market
    """

    assetId: str
    owner: str
    bulkMemberships: tuple[tuple[str, MembershipKind], ...] = ()
    fanoutMarkets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        assetId = self.assetId.strip()
        owner = self.owner.strip()
        if not assetId or not owner:
            raise ValueError("assetId와 owner는 비어 있을 수 없습니다")
        bulkMemberships = []
        for market, membership in self.bulkMemberships:
            if membership not in {"active", "allKnown", "explicit"}:
                raise ValueError("bulk membership가 유효하지 않습니다")
            bulkMemberships.append((_normalizeMarket(market), membership))
        object.__setattr__(self, "assetId", assetId)
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "bulkMemberships", tuple(sorted(set(bulkMemberships))))
        object.__setattr__(
            self,
            "fanoutMarkets",
            tuple(sorted({_normalizeMarket(market) for market in self.fanoutMarkets})),
        )


@dataclass(frozen=True, slots=True)
class PlanTask:
    """Universe query의 결정적 owner 실행 단위다.

    Capabilities:
        market bulk 한 번 또는 subject fanout 한 건을 snapshot digest와 결박한다.

    Args:
        ordinal: canonical plan 순번.
        assetId: 실행할 asset ID.
        owner: asset owner.
        market: 대상 market.
        provider: membership source owner.
        mode: ownerBulk 또는 subjectFanout.
        membership: 선택한 membership.
        snapshotId: universe snapshot ID.
        membershipDigest: market membership 내용 hash.
        subjectId: fanout일 때 MARKET:ID, bulk일 때 None.
        subjectCount: task가 대표하는 entity 수.

    Returns:
        executor가 소비할 immutable task.

    Example:
        ``PlanTask(0, "scan.account", "scan", "KR", "dart", "ownerBulk", "active", "u-1", "abc", None, 3000)``.

    Guide:
        bulk task의 subjectCount는 coverage용이며 payload 목록을 복제하지 않는다.

    SeeAlso:
        MarketCoverage, UniversePlan.

    Requires:
        planner가 canonical 순서로 생성한다.

    AIContext:
        실행과 결과 재조립 사이의 계획 영수증 후보 형태다.

    LLM Specifications:
        AntiPatterns:
            - bulk task에 전종목 ID 배열 복제
            - snapshot digest 없는 fanout
        Freshness:
            snapshotId와 membershipDigest에 고정된다.
        Dataflow:
            UniversePlan -> owner executor.
    """

    ordinal: int
    assetId: str
    owner: str
    market: str
    provider: str
    mode: Literal["ownerBulk", "subjectFanout"]
    membership: MembershipKind
    snapshotId: str
    membershipDigest: str
    subjectId: str | None
    subjectCount: int


@dataclass(frozen=True, slots=True)
class MarketCoverage:
    """Asset와 market 하나의 planning coverage를 설명한다.

    Capabilities:
        요청, membership 해소, 실행 계획 수와 gap을 market별로 분리한다.

    Args:
        assetId: catalog asset ID.
        market: market ID.
        provider: dart, edgar 또는 미해소 시 None.
        executionMode: ownerBulk, subjectFanout, none.
        expectedSubjects: selection이 요구한 entity 수.
        resolvedSubjects: membership snapshot에서 해소된 entity 수.
        plannedSubjects: task가 커버하는 entity 수.
        taskCount: 생성한 실행 task 수.
        status: complete, partial, failed.
        missingIds: membership에서 찾지 못한 explicit ID.
        gapCodes: machine-readable planning gap.

    Returns:
        immutable market coverage row.

    Example:
        ``coverage.status == "complete"``.

    Guide:
        전체 성공 여부보다 market별 plannedSubjects와 gapCodes를 먼저 본다.

    SeeAlso:
        PlanTask, UniversePlan.

    Requires:
        expectedSubjects보다 plannedSubjects가 클 수 없다.

    AIContext:
        DART 성공이 EDGAR 결손을 가리지 못하게 하는 결과 계약 후보다.

    LLM Specifications:
        AntiPatterns:
            - market coverage를 전체 합계 하나로 축약
            - 미해소 explicit ID를 성공 분모에서 제거
        Freshness:
            plan의 UniverseSnapshot과 동일하다.
        OutputSchema:
            - expectedSubjects : int, 요청 entity 수
            - plannedSubjects : int, 계획된 entity 수
            - gapCodes : tuple[str], 결손 코드
    """

    assetId: str
    market: str
    provider: str | None
    executionMode: ExecutionMode
    expectedSubjects: int
    resolvedSubjects: int
    plannedSubjects: int
    taskCount: int
    status: CoverageStatus
    missingIds: tuple[str, ...] = ()
    gapCodes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UniversePlan:
    """Universe query의 canonical plan과 coverage envelope다.

    Capabilities:
        selection, snapshot, tasks, market coverage를 stable plan ID에 결박한다.

    Args:
        planId: canonical payload SHA-256 ID.
        snapshotId: universe revision ID.
        selection: 정규화된 universe selection.
        tasks: canonical owner task tuple.
        coverage: asset와 market별 coverage tuple.

    Returns:
        외부 query runner가 직렬화할 수 있는 immutable plan.

    Example:
        ``plan.toDict()["planId"]``.

    Guide:
        planId가 같으면 owner 호출 순서와 market coverage가 같다.

    SeeAlso:
        compileUniversePlan.

    Requires:
        compileUniversePlan으로 생성한다.

    AIContext:
        query contract hash에 universe execution plan을 포함하기 위한 후보 envelope다.

    LLM Specifications:
        AntiPatterns:
            - planId 계산 뒤 task 순서를 변경
            - coverage 없이 task 배열만 전달
        Freshness:
            snapshotId에 고정된다.
        OutputSchema:
            - planId : str, deterministic plan hash
            - tasks : tuple[PlanTask], owner 실행 단위
            - coverage : tuple[MarketCoverage], market별 성적표
    """

    planId: str
    snapshotId: str
    selection: UniverseSelection
    tasks: tuple[PlanTask, ...]
    coverage: tuple[MarketCoverage, ...]

    def toDict(self) -> dict[str, object]:
        """Plan을 JSON-compatible mapping으로 변환한다.

        Capabilities:
            dataclass tuple을 외부 프로세스가 직렬화 가능한 mapping으로 만든다.

        Args:
            없음.

        Returns:
            planId, snapshotId, selection, tasks, coverage mapping.

        Example:
            ``json.dumps(plan.toDict())``.

        Guide:
            실행 전 receipt 또는 디버그 출력에 사용한다.

        SeeAlso:
            compileUniversePlan.

        Requires:
            없음.

        AIContext:
            별도 API가 아니라 prototype transport helper다.

        LLM Specifications:
            AntiPatterns:
                - mapping 일부만 보존해 planId 재현성을 잃음
            Freshness:
                UniversePlan과 동일하다.
        """
        return dataclasses.asdict(self)


@dataclass(frozen=True, slots=True)
class _MarketResolution:
    market: str
    provider: str | None
    expectedIds: tuple[str, ...]
    resolvedIds: tuple[str, ...]
    missingIds: tuple[str, ...]
    membershipDigest: str
    gapCodes: tuple[str, ...]


def _resolveMarket(
    selection: UniverseSelection,
    snapshot: UniverseSnapshot,
    market: str,
) -> _MarketResolution:
    marketIndex = {entry.market: entry for entry in snapshot.markets}
    membership = marketIndex.get(market)
    explicitIds = tuple(
        memberId
        for explicitId in selection.explicitIds
        for explicitMarket, memberId in (_parseExplicitId(explicitId),)
        if explicitMarket == market
    )
    if membership is None:
        expectedIds = tuple(f"{market}:{memberId}" for memberId in explicitIds)
        return _MarketResolution(
            market,
            None,
            expectedIds,
            (),
            expectedIds,
            "",
            ("MEMBERSHIP_UNAVAILABLE",),
        )

    if selection.membership == "explicit":
        sourceIds = explicitIds
        expectedIds = tuple(f"{market}:{memberId}" for memberId in explicitIds)
        resolvedIds = expectedIds
        missingIds: tuple[str, ...] = ()
    else:
        sourceIds = membership.activeIds if selection.membership == "active" else membership.allKnownIds
        if selection.explicitIds:
            expectedIds = tuple(f"{market}:{memberId}" for memberId in explicitIds)
            resolvedIds = tuple(f"{market}:{memberId}" for memberId in explicitIds if memberId in set(sourceIds))
            missingIds = tuple(value for value in expectedIds if value not in set(resolvedIds))
        else:
            expectedIds = tuple(f"{market}:{memberId}" for memberId in sourceIds)
            resolvedIds = expectedIds
            missingIds = ()

    digestPayload = {
        "market": market,
        "provider": membership.provider,
        "membership": selection.membership,
        "sourceIds": sourceIds,
        "snapshotId": snapshot.snapshotId,
    }
    membershipDigest = hashlib.sha256(_canonicalBytes(digestPayload)).hexdigest()
    gapCodes = []
    if missingIds:
        gapCodes.append("MEMBERSHIP_ID_NOT_FOUND")
    if not resolvedIds:
        gapCodes.append("EMPTY_UNIVERSE")
    return _MarketResolution(
        market,
        membership.provider,
        expectedIds,
        resolvedIds,
        missingIds,
        membershipDigest,
        tuple(gapCodes),
    )


def compileUniversePlan(
    selection: UniverseSelection,
    snapshot: UniverseSnapshot,
    capabilities: tuple[OwnerCapability, ...],
) -> UniversePlan:
    """UniverseSelection을 owner bulk와 subject fanout 실행 plan으로 컴파일한다.

    Capabilities:
        두 public axis를 늘리지 않고 query 내부 selection을 market별 owner task로 만든다.
        full membership은 owner bulk를 우선하고, 지원하지 않는 owner만 subject fanout한다.
        explicit ID 필터는 owner over-fetch를 막기 위해 fanout만 허용한다.

    Args:
        selection: market, membership, explicit IDs query selector.
        snapshot: DART와 EDGAR membership revision.
        capabilities: asset owner별 bulk와 fanout 지원 범위.

    Returns:
        UniversePlan. task는 assetId, market, subjectId 순으로 결정적이며 coverage가 동봉된다.

    Example:
        ``plan = compileUniversePlan(selection, snapshot, capabilities)``.

    Guide:
        all-market scan은 bulk capability를 선언하고, 회사별 분석은 fanout market을 선언한다.

    SeeAlso:
        UniverseSelection, OwnerCapability, UniversePlan.

    Requires:
        snapshot은 실행 전 해소되어야 하며 capability assetId는 고유해야 한다.

    AIContext:
        본진 승격 시 DataQuery 안에 selection을 추가하고 descriptor metadata로 capability를 공급한다.

    LLM Specifications:
        AntiPatterns:
            - 새 universe public axis 추가
            - owner bulk가 있는데 Python Company loop 실행
            - explicit filter를 무시하고 전시장 bulk 실행
        Freshness:
            plan은 snapshotId와 membershipDigest에 고정된다.
        Dataflow:
            data query -> UniverseSelection -> UniverseSnapshot -> compile -> owner tasks -> coverage.
        TargetMarkets:
            - KR (DART)
            - US (EDGAR)
    """
    if not capabilities:
        raise ValueError("capabilities가 비었습니다")
    sortedCapabilities = tuple(sorted(capabilities, key=lambda item: (item.assetId, item.owner)))
    assetIds = tuple(item.assetId for item in sortedCapabilities)
    if len(assetIds) != len(set(assetIds)):
        raise ValueError("capability assetId는 고유해야 합니다")

    resolutions = {market: _resolveMarket(selection, snapshot, market) for market in selection.markets}
    tasks: list[PlanTask] = []
    coverageRows: list[MarketCoverage] = []
    hasExplicitFilter = bool(selection.explicitIds)
    for capability in sortedCapabilities:
        bulkMemberships = set(capability.bulkMemberships)
        fanoutMarkets = set(capability.fanoutMarkets)
        for market in selection.markets:
            resolution = resolutions[market]
            gapCodes = list(resolution.gapCodes)
            mode: ExecutionMode = "none"
            taskCount = 0
            plannedSubjects = 0
            canBulk = (
                not hasExplicitFilter
                and (market, selection.membership) in bulkMemberships
                and bool(resolution.resolvedIds)
                and resolution.provider is not None
            )
            canFanout = market in fanoutMarkets and bool(resolution.resolvedIds) and resolution.provider is not None
            if canBulk:
                mode = "ownerBulk"
                tasks.append(
                    PlanTask(
                        ordinal=len(tasks),
                        assetId=capability.assetId,
                        owner=capability.owner,
                        market=market,
                        provider=resolution.provider,
                        mode="ownerBulk",
                        membership=selection.membership,
                        snapshotId=snapshot.snapshotId,
                        membershipDigest=resolution.membershipDigest,
                        subjectId=None,
                        subjectCount=len(resolution.resolvedIds),
                    )
                )
                taskCount = 1
                plannedSubjects = len(resolution.resolvedIds)
            elif canFanout:
                mode = "subjectFanout"
                for subjectId in resolution.resolvedIds:
                    tasks.append(
                        PlanTask(
                            ordinal=len(tasks),
                            assetId=capability.assetId,
                            owner=capability.owner,
                            market=market,
                            provider=resolution.provider,
                            mode="subjectFanout",
                            membership=selection.membership,
                            snapshotId=snapshot.snapshotId,
                            membershipDigest=resolution.membershipDigest,
                            subjectId=subjectId,
                            subjectCount=1,
                        )
                    )
                taskCount = len(resolution.resolvedIds)
                plannedSubjects = len(resolution.resolvedIds)
            elif resolution.resolvedIds:
                if hasExplicitFilter and (market, selection.membership) in bulkMemberships:
                    gapCodes.append("OWNER_FILTER_UNSUPPORTED")
                else:
                    gapCodes.append("OWNER_MARKET_UNSUPPORTED")

            gapCodes = list(dict.fromkeys(gapCodes))
            expectedSubjects = len(resolution.expectedIds)
            if plannedSubjects == expectedSubjects and expectedSubjects > 0 and not gapCodes:
                status: CoverageStatus = "complete"
            elif plannedSubjects > 0:
                status = "partial"
            else:
                status = "failed"
            coverageRows.append(
                MarketCoverage(
                    assetId=capability.assetId,
                    market=market,
                    provider=resolution.provider,
                    executionMode=mode,
                    expectedSubjects=expectedSubjects,
                    resolvedSubjects=len(resolution.resolvedIds),
                    plannedSubjects=plannedSubjects,
                    taskCount=taskCount,
                    status=status,
                    missingIds=resolution.missingIds,
                    gapCodes=tuple(gapCodes),
                )
            )

    payload = {
        "snapshotId": snapshot.snapshotId,
        "selection": dataclasses.asdict(selection),
        "tasks": [dataclasses.asdict(task) for task in tasks],
        "coverage": [dataclasses.asdict(row) for row in coverageRows],
    }
    planId = f"universe-plan:{hashlib.sha256(_canonicalBytes(payload)).hexdigest()}"
    return UniversePlan(
        planId=planId,
        snapshotId=snapshot.snapshotId,
        selection=selection,
        tasks=tuple(tasks),
        coverage=tuple(coverageRows),
    )


def _demoPlan() -> UniversePlan:
    snapshot = UniverseSnapshot(
        "universe-2026-07-22",
        (
            MarketMembership("US", "edgar", ("0000320193", "0000789019")),
            MarketMembership("KR", "dart", ("000660", "005930", "035420")),
        ),
    )
    selection = UniverseSelection(("US", "KR"), "active")
    capabilities = (
        OwnerCapability(
            "scan.account",
            "scan",
            (("KR", "active"), ("US", "active")),
            ("KR", "US"),
        ),
        OwnerCapability("analysis.simulationInputs", "analysis", (), ("KR", "US")),
    )
    return compileUniversePlan(selection, snapshot, capabilities)


if __name__ == "__main__":
    print(json.dumps(_demoPlan().toDict(), ensure_ascii=False, indent=2))
