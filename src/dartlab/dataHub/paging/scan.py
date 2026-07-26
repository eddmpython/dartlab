"""Continuation page를 한 lazy Python 소비 흐름으로 연결한다."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from dartlab.dataHub.contracts import AssetRef, DataResult

if TYPE_CHECKING:
    import pyarrow as pa

_DEFAULT_MAX_PAGES = 10_000
_DEFAULT_MAX_PAGE_RETRIES = 2
_RETRY_BACKOFF_SECONDS = 0.5
_MAX_PAGE_RETRIES_LIMIT = 16

_ERROR_MESSAGES = {
    "PAGE_SCAN_ARGUMENT_INVALID": "page scan 인자가 유효하지 않습니다",
    "PAGE_SCAN_RESULT_INVALID": "page scan 결과 계약이 유효하지 않습니다",
    "PAGE_SCAN_PAGE_FAILED": "page scan continuation page가 실패했습니다",
    "PAGE_SCAN_MAX_PAGES": "page scan page 상한을 초과했습니다",
    "PAGE_SCAN_DEADLINE": "page scan 실행 기한을 초과했습니다",
    "PAGE_SCAN_TOKEN_LOOP": "page scan continuation token이 순환했습니다",
    "PAGE_SCAN_IDENTITY_DRIFT": "page scan chain identity가 변경됐습니다",
    "PAGE_SCAN_RESUME_FAILED": "page scan continuation 호출에 실패했습니다",
}

PageQueryCaller = Callable[[str], DataResult]


class PageScanError(RuntimeError):
    """Token이나 owner 예외 원문을 노출하지 않는 page scan 오류다.

    Args:
        code: 등록된 ``PAGE_SCAN_*`` 오류 코드.

    Raises:
        ValueError: 등록되지 않은 code일 때.

    AIContext:
        외부 process가 code로 실패를 분기하되 bearer token과 내부 owner 오류를 보지 않게 한다.
    """

    def __init__(self, code: str):
        if code not in _ERROR_MESSAGES:
            raise ValueError("등록되지 않은 page scan 오류 코드입니다")
        self.code = code
        super().__init__(_ERROR_MESSAGES[code])

    def __repr__(self) -> str:
        """비밀값 없이 안정적인 오류 표현을 반환한다."""

        return f"PageScanError(code={self.code!r})"


@dataclass(frozen=True, slots=True)
class PageScanCheckpoint:
    """검증을 마친 page와 다음 resume token의 immutable checkpoint다.

    ``nextToken``은 repr에서 제외한다. Callback은 page가 사용자에게 yield되기 직전에 한 번 호출된다.
    따라서 checkpoint는 전달 예정 page의 identity와 그 다음 page resume 위치를 뜻한다.
    """

    pageNumber: int
    snapshotId: str
    contractHash: str
    assets: tuple[tuple[str, str], ...]
    universeSnapshotId: str | None
    complete: bool
    nextToken: str | None = field(repr=False)


@dataclass(frozen=True, slots=True)
class _ChainIdentity:
    snapshotId: str
    contractHash: str
    assets: tuple[tuple[str, str], ...]
    universeSnapshotId: str | None


def _assetIdentity(assets: tuple[AssetRef, ...]) -> tuple[tuple[str, str], ...]:
    if any(not isinstance(asset, AssetRef) for asset in assets):
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    identity = tuple((asset.assetId, asset.assetVersionId) for asset in assets)
    if any(not assetId or not versionId for assetId, versionId in identity):
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    return identity


def _identity(page: DataResult) -> _ChainIdentity:
    if type(page.snapshotId) is not str or not page.snapshotId:
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    if type(page.contractHash) is not str or not page.contractHash:
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    if page.universeSnapshotId is not None and type(page.universeSnapshotId) is not str:
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    return _ChainIdentity(
        snapshotId=page.snapshotId,
        contractHash=page.contractHash,
        assets=_assetIdentity(page.assets),
        universeSnapshotId=page.universeSnapshotId,
    )


def _continuation(page: DataResult) -> str | None:
    if page.status == "failed":
        raise PageScanError("PAGE_SCAN_PAGE_FAILED")
    if type(page.status) is not str or page.status not in {"ok", "partial"}:
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    token = page.continuation
    if token is not None and (type(token) is not str or not token.strip()):
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    if token is not None and page.status != "partial":
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    return token


def _validatedDeadline(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    if type(deadline) not in {int, float}:
        raise PageScanError("PAGE_SCAN_ARGUMENT_INVALID")
    value = float(deadline)
    if not math.isfinite(value):
        raise PageScanError("PAGE_SCAN_ARGUMENT_INVALID")
    return value


def _requireDeadline(deadline: float | None) -> None:
    if deadline is not None and time.monotonic() >= deadline:
        raise PageScanError("PAGE_SCAN_DEADLINE")


def _defaultQueryCaller(token: str) -> DataResult:
    import dartlab

    hub = cast(Callable[..., Any], getattr(dartlab, "dataHub"))
    return cast(DataResult, hub("query", query={"continuation": token}))


def _validateArguments(
    maxPages: int,
    deadline: float | None,
    checkpoint: Callable[[PageScanCheckpoint], None] | None,
    queryCaller: PageQueryCaller | None,
    maxPageRetries: int = _DEFAULT_MAX_PAGE_RETRIES,
) -> tuple[float | None, PageQueryCaller]:
    if type(maxPages) is not int or maxPages <= 0:
        raise PageScanError("PAGE_SCAN_ARGUMENT_INVALID")
    if type(maxPageRetries) is not int or maxPageRetries < 0 or maxPageRetries > _MAX_PAGE_RETRIES_LIMIT:
        raise PageScanError("PAGE_SCAN_ARGUMENT_INVALID")
    normalizedDeadline = _validatedDeadline(deadline)
    if checkpoint is not None and not callable(checkpoint):
        raise PageScanError("PAGE_SCAN_ARGUMENT_INVALID")
    if queryCaller is not None and not callable(queryCaller):
        raise PageScanError("PAGE_SCAN_ARGUMENT_INVALID")
    return normalizedDeadline, queryCaller or _defaultQueryCaller


def _resumeOnce(caller: PageQueryCaller, token: str) -> DataResult:
    """Token 하나로 다음 page를 한 번 받아 계약을 검증한다."""

    try:
        resumed = caller(token)
    except PageScanError:
        raise
    except Exception:
        raise PageScanError("PAGE_SCAN_RESUME_FAILED") from None
    if not isinstance(resumed, DataResult):
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")
    if resumed.status == "failed":
        raise PageScanError("PAGE_SCAN_PAGE_FAILED")
    return resumed


def _resumeWithRetry(
    caller: PageQueryCaller,
    token: str,
    *,
    maxPageRetries: int,
    deadline: float | None,
) -> DataResult:
    """실패한 page를 같은 token으로 bounded 재시도한다.

    Continuation token은 실패해도 소모되지 않는다. commit된 page는 원천 접촉 없이 동일하게
    replay되고 실패한 page는 애초에 commit되지 않으므로 같은 token 재사용이 중복이나 누락을
    만들지 않는다. 재시도가 없으면 120 page 순회에서 한 page의 일시 실패가 전체 sweep을
    끝내므로 전종목 완주 자체가 성립하지 않는다.

    ``PAGE_SCAN_PAGE_FAILED``와 ``PAGE_SCAN_RESUME_FAILED``만 재시도한다. identity drift,
    token 순환, 계약 위반은 재시도해도 같은 결과라 즉시 올린다.
    """

    attempt = 0
    while True:
        _requireDeadline(deadline)
        try:
            return _resumeOnce(caller, token)
        except PageScanError as error:
            transient = error.code in {"PAGE_SCAN_PAGE_FAILED", "PAGE_SCAN_RESUME_FAILED"}
            if not transient or attempt >= maxPageRetries:
                raise
            attempt += 1
            backoff = _RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
            if deadline is not None and time.monotonic() + backoff >= deadline:
                raise PageScanError("PAGE_SCAN_DEADLINE") from None
            time.sleep(backoff)


def iterDataResultPages(
    initial: DataResult,
    *,
    maxPages: int = _DEFAULT_MAX_PAGES,
    deadline: float | None = None,
    checkpoint: Callable[[PageScanCheckpoint], None] | None = None,
    queryCaller: PageQueryCaller | None = None,
    maxPageRetries: int = _DEFAULT_MAX_PAGE_RETRIES,
) -> Iterator[DataResult]:
    """초기 DataResult부터 완료 page까지 token-only continuation을 lazy 순회한다.

    Capabilities:
        초기 page를 즉시 yield하고 다음 page가 요구될 때만 ``dartlab.dataHub("query")``를 호출한다.
        Page 수와 monotonic deadline을 제한하며 token loop, 실패 page, catalog snapshot, query contract,
        asset revision set과 universe snapshot drift를 fail closed한다.

    Args:
        initial: 이미 발급된 첫 ``DataResult`` page.
        maxPages: 초기 page를 포함한 최대 page 수.
        deadline: ``time.monotonic()`` 기준 절대 실행 기한. None이면 helper 자체 기한은 없다.
        checkpoint: 검증된 page를 yield하기 직전에 호출할 callback.
        queryCaller: token 하나만 받는 resume seam. None이면 public ``dartlab.dataHub``를 사용한다.
        maxPageRetries: 일시 실패한 page를 같은 token으로 재시도할 최대 횟수. 0이면 재시도하지 않는다.

    Returns:
        동일 chain의 ``DataResult`` page iterator.

    Raises:
        PageScanError: 인자, page, token 진행, identity 또는 deadline 계약이 깨질 때.

    Example:
        ``for page in iterDataResultPages(first): consume(page)``.

    Guide:
        Callback의 ``nextToken``을 durable checkpoint로 저장하면 process restart 후 token-only query로
        재개할 수 있다. Callback 호출은 page 처리 완료 acknowledgement가 아니라 page 전달 직전이다.

    When:
        Full-universe query가 continuation을 반환했고 caller가 수동 token loop 없이 모든 page를 소비할 때.

    How:
        초기 identity를 고정하고 page를 하나씩 검증한 뒤 다음 token만 public query에 전달한다.

    SeeAlso:
        ``iterDataArrowBatches``와 ``DataResult.iterArrowBatches``.

    Requires:
        Resume owner는 같은 snapshotId, contractHash, assets와 universeSnapshotId를 보존해야 한다.

    AIContext:
        사용자는 continuation loop를 직접 쓰지 않지만 각 page는 기존 bounded source 계약을 그대로 따른다.
    """

    normalizedDeadline, caller = _validateArguments(
        maxPages,
        deadline,
        checkpoint,
        queryCaller,
        maxPageRetries,
    )
    if not isinstance(initial, DataResult):
        raise PageScanError("PAGE_SCAN_RESULT_INVALID")

    baseline: _ChainIdentity | None = None
    seenTokens: set[str] = set()
    page = initial
    pageNumber = 1

    while True:
        _requireDeadline(normalizedDeadline)
        if not isinstance(page, DataResult):
            raise PageScanError("PAGE_SCAN_RESULT_INVALID")
        currentIdentity = _identity(page)
        if baseline is None:
            baseline = currentIdentity
        elif currentIdentity != baseline:
            raise PageScanError("PAGE_SCAN_IDENTITY_DRIFT")
        nextToken = _continuation(page)
        if nextToken is not None:
            if nextToken in seenTokens:
                raise PageScanError("PAGE_SCAN_TOKEN_LOOP")
            seenTokens.add(nextToken)

        currentCheckpoint = PageScanCheckpoint(
            pageNumber=pageNumber,
            snapshotId=currentIdentity.snapshotId,
            contractHash=currentIdentity.contractHash,
            assets=currentIdentity.assets,
            universeSnapshotId=currentIdentity.universeSnapshotId,
            complete=nextToken is None,
            nextToken=nextToken,
        )
        if checkpoint is not None:
            checkpoint(currentCheckpoint)
        yield page

        if nextToken is None:
            return
        if pageNumber >= maxPages:
            raise PageScanError("PAGE_SCAN_MAX_PAGES")
        resumed = _resumeWithRetry(
            caller,
            nextToken,
            maxPageRetries=maxPageRetries,
            deadline=normalizedDeadline,
        )
        _requireDeadline(normalizedDeadline)
        page = resumed
        pageNumber += 1


def iterDataArrowBatches(
    initial: DataResult,
    *,
    maxPages: int = _DEFAULT_MAX_PAGES,
    deadline: float | None = None,
    checkpoint: Callable[[PageScanCheckpoint], None] | None = None,
    queryCaller: PageQueryCaller | None = None,
    maxPageRetries: int = _DEFAULT_MAX_PAGE_RETRIES,
    maxRows: int = 65_536,
    maxBytes: int = 8 * 1024 * 1024,
) -> Iterator[tuple[str, pa.RecordBatch]]:
    """Continuation chain 전체를 bounded Arrow RecordBatch로 lazy 순회한다.

    Args:
        initial: 이미 발급된 첫 ``DataResult`` page.
        maxPages: 초기 page를 포함한 최대 page 수.
        deadline: ``time.monotonic()`` 기준 절대 실행 기한.
        checkpoint: 각 page 검증 뒤 첫 batch보다 먼저 호출할 callback.
        queryCaller: token-only resume seam.
        maxPageRetries: 일시 실패한 page를 같은 token으로 재시도할 최대 횟수.
        maxRows: 반환 batch 하나의 row 상한.
        maxBytes: 반환 batch 하나의 Arrow logical byte 상한.

    Returns:
        기존 ``DataResult.iterArrowBatches``와 같은 ``(partitionKey, RecordBatch)`` iterator.

    Raises:
        PageScanError: page chain 계약 위반 시.
        ValueError: Arrow batch 예산이 유효하지 않거나 한 행이 byte 상한을 넘을 때.

    Guide:
        같은 request partition key가 여러 page에서 반복될 수 있으며 전체 순서가 원천 순서다.

    Requires:
        각 표 partition이 ``DataResult.iterArrowBatches``로 변환 가능해야 한다.

    Example:
        ``for key, batch in iterDataArrowBatches(first): consume(key, batch)``.

    SeeAlso:
        ``iterDataResultPages``와 ``DataResult.iterArrowBatches``.

    AIContext:
        전체 universe를 한 table로 합치지 않고 기존 page와 batch 이중 상한을 유지한다.
    """

    if type(maxRows) is not int or type(maxBytes) is not int or maxRows <= 0 or maxBytes <= 0:
        raise PageScanError("PAGE_SCAN_ARGUMENT_INVALID")
    for page in iterDataResultPages(
        initial,
        maxPages=maxPages,
        deadline=deadline,
        checkpoint=checkpoint,
        queryCaller=queryCaller,
        maxPageRetries=maxPageRetries,
    ):
        yield from page.iterArrowBatches(maxRows=maxRows, maxBytes=maxBytes)


__all__ = [
    "PageQueryCaller",
    "PageScanCheckpoint",
    "PageScanError",
    "iterDataArrowBatches",
    "iterDataResultPages",
]
