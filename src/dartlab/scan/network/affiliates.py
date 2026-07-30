"""Prebuilt 계열회사 artifact의 clustering과 runtime loading."""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import ScanDataError, ensureScanArtifact
from dartlab.scan.network.classifier import WELL_KNOWN_EXT

_MEMBERSHIP_COLUMNS = {"sourceStockCode", "affiliateStockCode"}
AFFILIATE_DOCS_SCHEMA = {
    "sourceStockCode": pl.Utf8,
    "affiliateStockCode": pl.Utf8,
    "sourcePeriod": pl.Utf8,
    "sourceRceptNo": pl.Utf8,
    "groupName": pl.Utf8,
    "datasetAsOf": pl.Utf8,
    "schemaVersion": pl.Int16,
}
AFFILIATE_DOCS_SCHEMA_VERSION = 2
_MIN_SHARED_AFFILIATES = 3


class _UnionFind:
    """경로 압축과 rank를 사용하는 작은 disjoint-set."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def find(self, value: str) -> str:
        """값이 속한 component root를 경로 압축으로 찾는다.

        Capabilities:
            새 노드를 등록하고 기존 parent 경로를 root로 압축한다.

        AIContext:
            계열회사 membership component를 선형에 가깝게 합칠 때 쓰는 내부 연산이다.

        Guide:
            ``union``과 ``components``를 통해서만 상태를 조립한다.

        When:
            노드의 현재 component를 조회하거나 두 component를 합치기 직전.

        How:
            미등록 값은 자기 자신을 parent로 등록한 뒤 root까지 재귀 탐색한다.

        Requires:
            hash 가능한 문자열 종목코드.

        Args:
            value: 찾을 종목코드.

        Returns:
            component root 종목코드.

        Raises:
            없음.

        Example:
            >>> _UnionFind().find("005930")
            '005930'

        SeeAlso:
            ``union`` · ``components``.
        """

        if value not in self.parent:
            self.parent[value] = value
            self.rank[value] = 0
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        """두 종목코드의 component를 rank 기준으로 합친다.

        Capabilities:
            rank가 낮은 component를 높은 component 아래에 합친다.

        AIContext:
            공유 affiliate 기준을 통과한 source 쌍만 같은 기업집단 후보로 묶는다.

        Guide:
            두 값이 이미 같은 root이면 상태를 바꾸지 않는다.

        When:
            두 source가 최소 공유 affiliate 계약을 충족했을 때.

        How:
            ``find``로 root를 구하고 rank를 비교해 parent를 갱신한다.

        Requires:
            문자열 종목코드 두 개.

        Args:
            left: 왼쪽 종목코드.
            right: 오른쪽 종목코드.

        Returns:
            없음.

        Raises:
            없음.

        Example:
            >>> groups = _UnionFind()
            >>> groups.union("005930", "006400")

        SeeAlso:
            ``find`` · ``components``.
        """

        leftRoot = self.find(left)
        rightRoot = self.find(right)
        if leftRoot == rightRoot:
            return
        if self.rank[leftRoot] < self.rank[rightRoot]:
            leftRoot, rightRoot = rightRoot, leftRoot
        self.parent[rightRoot] = leftRoot
        if self.rank[leftRoot] == self.rank[rightRoot]:
            self.rank[leftRoot] += 1

    def components(self) -> list[list[str]]:
        """현재 component를 정렬된 종목코드 목록으로 반환한다.

        Capabilities:
            등록된 모든 노드를 root별로 모아 결정적인 정렬 결과를 만든다.

        AIContext:
            membership source 집합을 최종 기업집단 label 계산 단위로 변환한다.

        Guide:
            모든 ``union``이 끝난 뒤 한 번 호출한다.

        When:
            component별 affiliate 합집합과 label을 계산하기 직전.

        How:
            각 노드의 압축된 root를 구해 group에 추가하고 내부 목록을 정렬한다.

        Requires:
            앞선 ``find`` 또는 ``union``으로 등록된 노드.

        Args:
            없음.

        Returns:
            component별 정렬된 종목코드 목록.

        Raises:
            없음.

        Example:
            >>> groups = _UnionFind()
            >>> groups.union("A", "B")
            >>> groups.components()
            [['A', 'B']]

        SeeAlso:
            ``find`` · ``union``.
        """

        grouped: dict[str, list[str]] = defaultdict(list)
        for value in self.parent:
            grouped[self.find(value)].append(value)
        return [sorted(values) for values in grouped.values()]


def _pairOverlapCounts(sourceAffiliates: dict[str, set[str]]) -> Counter[tuple[str, str]]:
    """역색인으로 source 쌍의 공유 affiliate 수를 센다."""

    sourcesByAffiliate: dict[str, list[str]] = defaultdict(list)
    for source, affiliates in sourceAffiliates.items():
        for affiliate in affiliates:
            sourcesByAffiliate[affiliate].append(source)

    overlapCounts: Counter[tuple[str, str]] = Counter()
    for sources in sourcesByAffiliate.values():
        uniqueSources = sorted(set(sources))
        overlapCounts.update(combinations(uniqueSources, 2))
    return overlapCounts


def _groupLabel(
    affiliateCodes: set[str],
    codeToName: dict[str, str],
    fallbackCode: str,
) -> str | None:
    """well-known label, 공통 회사명 접두사, 대표 회사명 순으로 label을 정한다."""

    knownLabels = {WELL_KNOWN_EXT[code] for code in affiliateCodes if code in WELL_KNOWN_EXT}
    if len(knownLabels) > 1:
        return None
    if knownLabels:
        return knownLabels.pop()

    names = sorted(codeToName[code] for code in affiliateCodes if code in codeToName)
    if len(names) >= 2:
        prefix = names[0]
        for name in names[1:]:
            while prefix and not name.startswith(prefix):
                prefix = prefix[:-1]
            if not prefix:
                break
        if len(prefix) >= 2:
            return prefix.rstrip()
    return codeToName.get(fallbackCode, fallbackCode)


def _resolveGroupCandidates(
    candidates: dict[str, list[tuple[str, bool]]],
) -> dict[str, str]:
    """affiliate별 복수 component 후보를 자기 공시만으로 판정한다.

    같은 상장사가 인수 시점 차이 또는 표 오류로 서로 다른 기업집단 문서에 함께 등장할 수 있다.
    해당 회사가 직접 공시한 source component는 identity가 확정되므로 우선한다. 이름만 일치한
    서로 다른 label 후보는 반복 횟수가 많아도 같은 법인이라는 근거가 아니므로 분류에서 제외한다.
    """

    resolved: dict[str, str] = {}
    for code, codeCandidates in candidates.items():
        ownLabels = {label for label, isOwnSource in codeCandidates if isOwnSource}
        if len(ownLabels) == 1:
            resolved[code] = ownLabels.pop()
            continue
        candidateLabels = {label for label, _ in codeCandidates}
        if len(candidateLabels) == 1:
            resolved[code] = candidateLabels.pop()
    return resolved


def compileAffiliateGroups(
    memberships: pl.DataFrame,
    codeToName: dict[str, str],
    listingCodes: set[str],
) -> dict[str, str]:
    """membership 행을 종목코드별 기업집단 label로 컴파일한다.

    두 source가 상장 affiliate를 세 곳 이상 함께 공시했을 때 같은 component로 묶는다.
    모든 source 쌍을 비교하지 않고 affiliate 역색인에서 실제로 겹치는 쌍만 센다.

    Capabilities:
        membership 검증, 역색인 overlap 계산, component label 결정을 수행한다.

    AIContext:
        panel 파생 membership을 runtime이 바로 읽는 작은 graph ground truth로 컴파일한다.

    Guide:
        상장 종목만 component 계산에 포함한다. 여러 component가 같은 affiliate를 주장하면
        자기 공시만 우선하며 회사명 일치만으로 해소할 수 없는 충돌은 임의 분류하지 않는다.

    When:
        full 또는 incremental affiliateDocs artifact를 발행하기 직전.

    How:
        affiliate별 source 역색인, threshold union, well-known 또는 회사명 label 순서로 계산한다.

    Requires:
        sourceStockCode와 affiliateStockCode 컬럼 및 현재 listing 코드 집합.

    Args:
        memberships: source와 affiliate 종목코드 membership 행.
        codeToName: 종목코드별 회사명.
        listingCodes: 현재 상장 종목코드.

    Returns:
        종목코드별 기업집단 label.

    Raises:
        ScanDataError: membership schema가 누락됐을 때.

    Example:
        >>> compileAffiliateGroups(memberships, codeToName, listingCodes)  # doctest: +SKIP

    SeeAlso:
        ``loadAffiliateGroups`` · ``dartlab.scan.builders.kr.network.buildAffiliateDocs``.
    """

    if memberships.is_empty():
        return {}
    missing = sorted(_MEMBERSHIP_COLUMNS - set(memberships.columns))
    if missing:
        raise ScanDataError(
            "affiliate_membership_schema",
            f"missing columns: {', '.join(missing)}",
        )

    sourceAffiliates: dict[str, set[str]] = defaultdict(set)
    for source, affiliate in memberships.select("sourceStockCode", "affiliateStockCode").iter_rows():
        if source in listingCodes and affiliate in listingCodes:
            sourceAffiliates[source].add(affiliate)

    unionFind = _UnionFind()
    for (left, right), overlap in _pairOverlapCounts(sourceAffiliates).items():
        if overlap >= _MIN_SHARED_AFFILIATES:
            unionFind.union(left, right)

    candidates: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    for sources in unionFind.components():
        affiliates: set[str] = set()
        for source in sources:
            affiliates.update(sourceAffiliates[source])
        if len(affiliates) < 2:
            continue
        label = _groupLabel(affiliates, codeToName, sources[0])
        if label is None:
            continue
        for code in affiliates:
            candidates[code].append((label, code in sources))
    return _resolveGroupCandidates(candidates)


def validateAffiliateDocsArtifact(frame: pl.DataFrame, source: str) -> None:
    """artifact의 canonical schema, version, 단일 group 계약을 검증한다.

    Capabilities:
        컬럼 순서와 dtype, schema version, affiliate별 group label 유일성을 함께 검사한다.

    AIContext:
        prebuild writer, CI cache 재사용, 공개 runtime reader가 공유하는 artifact 검증 SSOT다.

    Guide:
        artifact를 보존하거나 소비하기 전에 호출하고 오류를 빈 결과로 바꾸지 않는다.

    When:
        affiliateDocs 발행 직전과 기존 artifact 재사용 또는 runtime load 직후.

    How:
        canonical schema와 실제 frame을 비교하고 version 및 group 충돌을 집계한다.

    Requires:
        ``AFFILIATE_DOCS_SCHEMA`` 순서를 유지하는 Polars DataFrame.

    Args:
        frame: 검증할 affiliateDocs DataFrame.
        source: 오류에 포함할 artifact 위치.

    Returns:
        없음.

    Raises:
        ScanDataError: schema, version 또는 group 유일성 계약이 깨졌을 때.

    Example:
        >>> validateAffiliateDocsArtifact(frame, "affiliateDocs.parquet")  # doctest: +SKIP

    SeeAlso:
        ``isCurrentAffiliateDocsArtifact`` · ``loadAffiliateGroups``.
    """

    expectedColumns = list(AFFILIATE_DOCS_SCHEMA)
    actualSchema = frame.schema
    if frame.columns != expectedColumns:
        raise ScanDataError(
            "affiliate_docs_schema",
            f"columns={frame.columns}, expected={expectedColumns}",
            source=source,
        )
    dtypeMismatches = [
        f"{column}={actualSchema[column]}/{expectedDtype}"
        for column, expectedDtype in AFFILIATE_DOCS_SCHEMA.items()
        if actualSchema[column] != expectedDtype
    ]
    if dtypeMismatches:
        raise ScanDataError(
            "affiliate_docs_schema",
            f"dtype mismatch: {', '.join(dtypeMismatches)}",
            source=source,
        )

    versions = frame["schemaVersion"].drop_nulls().unique().to_list()
    if not frame.is_empty() and versions != [AFFILIATE_DOCS_SCHEMA_VERSION]:
        raise ScanDataError(
            "affiliate_docs_schema",
            f"unsupported schemaVersion values: {versions}",
            source=source,
        )

    groups = frame.filter(pl.col("groupName").is_not_null()).select("affiliateStockCode", "groupName").unique()
    conflicts = groups.group_by("affiliateStockCode").len().filter(pl.col("len") > 1)
    if not conflicts.is_empty():
        sample = conflicts["affiliateStockCode"].head(5).to_list()
        raise ScanDataError(
            "affiliate_docs_conflict",
            f"affiliate has conflicting groups: {sample}",
            source=source,
        )


def _readAffiliateDocsArtifact(source: str | Path) -> pl.DataFrame:
    """affiliateDocs를 canonical schema로 읽고 검증한다."""

    try:
        lazy = pl.scan_parquet(source)
        sourceSchema = lazy.collect_schema()
        expectedColumns = list(AFFILIATE_DOCS_SCHEMA)
        if sourceSchema.names() != expectedColumns:
            raise ScanDataError(
                "affiliate_docs_schema",
                f"columns={sourceSchema.names()}, expected={expectedColumns}",
                source=source,
            )
        artifact = lazy.select(expectedColumns).collect(engine="streaming")
    except ScanDataError:
        raise
    except (pl.exceptions.PolarsError, OSError) as exc:
        raise ScanDataError(
            "affiliate_docs_read",
            f"{type(exc).__name__}: {exc}",
            source=source,
        ) from exc
    validateAffiliateDocsArtifact(artifact, str(source))
    return artifact


def isCurrentAffiliateDocsArtifact(source: str | Path) -> bool:
    """artifact가 현재 runtime 계약과 완전히 호환되는지 판정한다.

    Capabilities:
        파일 부재, parquet read, canonical schema, version, group 충돌을 하나의 판정으로 합친다.

    AIContext:
        CI cache와 증분 prebuild가 구형 network artifact를 보존하지 않도록 하는 SSOT다.

    Guide:
        False이면 호출자가 full rebuild 또는 bootstrap으로 전환한다.

    When:
        기존 affiliateDocs를 재사용하기 직전.

    How:
        strict reader와 validator를 그대로 호출하고 계약 오류만 False로 변환한다.

    Requires:
        로컬 affiliateDocs parquet 후보 경로.

    Args:
        source: 검사할 parquet 경로.

    Returns:
        현재 계약과 완전히 호환되면 True.

    Raises:
        없음.

    Example:
        >>> isCurrentAffiliateDocsArtifact("affiliateDocs.parquet")  # doctest: +SKIP
        True

    SeeAlso:
        ``validateAffiliateDocsArtifact`` · ``loadAffiliateGroups``.
    """

    if not Path(source).is_file():
        return False
    try:
        _readAffiliateDocsArtifact(source)
    except ScanDataError:
        return False
    return True


def loadAffiliateGroups() -> dict[str, str]:
    """작은 prebuild artifact를 읽어 기업집단 ground truth를 반환한다.

    Capabilities:
        artifact 확보, strict read, canonical 검증, 종목별 group mapping 생성을 수행한다.

    AIContext:
        공개 network graph가 raw panel 순회 없이 계열회사 ground truth를 사용할 때 호출한다.

    Guide:
        artifact 부재와 손상은 빈 dict로 바꾸지 않고 ``ScanDataError``로 전파한다.

    When:
        ``buildGraph``가 report edge를 조립한 뒤 기업집단 분류를 시작할 때.

    How:
        공통 scan artifact 확보 후 필요한 컬럼만 streaming collect하고 dict로 변환한다.

    Requires:
        ``network/affiliateDocs.parquet`` 또는 이를 받을 수 있는 scan data source.

    Args:
        없음.

    Returns:
        affiliate 종목코드별 기업집단 label.

    Raises:
        ScanDataError: artifact 다운로드, read, schema 또는 group이 잘못됐을 때.

    Example:
        >>> loadAffiliateGroups()  # doctest: +SKIP
        {'005930': '삼성'}

    SeeAlso:
        ``compileAffiliateGroups`` · ``dartlab.scan.network.buildGraph``.
    """

    source = ensureScanArtifact("network/affiliateDocs.parquet")
    artifact = _readAffiliateDocsArtifact(source)
    groups = artifact.filter(pl.col("groupName").is_not_null()).select(
        "affiliateStockCode",
        "groupName",
    )
    groups = groups.unique()
    return dict(groups.iter_rows())
