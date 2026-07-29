"""allFilings parquet ↔ HuggingFace 동기화 — push · 원격목록 · 양방향 reconcile.

``allFilingsCollector`` 가 DART 에서 일자별 본문 parquet 을 *수집* 한다면, 본 모듈은 그
산출물을 HF dataset 과 *동기화* 한다(수집/동기 분리, 단방향 의존 — sync → collector).
파일당 commit(128 commit/hr 한도)이 대량 백필 push 를 잘랐던 사고를 ``create_commit``
단일 배치로 해소하고, 로컬·HF 일자 집합 차분으로 양방향 reconcile 한다.

수집/조회(loadDay/loadAll/stats/collectedDates)는 ``allFilingsCollector`` 에 그대로 남는다.
"""

from __future__ import annotations

from pathlib import Path

import dartlab.config as _cfg
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.core.logger import getLogger
from dartlab.gather.dart.allFilingsCollector import (
    _ALLFILINGS_DIR_KEY,
    _META_SUFFIX,
    AllFilingsHfDownloadError,
    AllFilingsHfListingError,
    AllFilingsHfUnavailableError,
    AllFilingsHfUploadError,
    _allFilingsDir,
    collectedDates,
)

_log = getLogger(__name__)


def pushAllFilings(periods: list[str] | None = None, *, token: str | None = None) -> int:
    """allFilings parquet 을 HF dataset 에 **단일 commit 배치**로 업로드.

    Capabilities:
        - 로컬 ``data/dart/allFilings/{date}.parquet`` 을 HF dataset 으로 push. 파일당
          ``upload_file``(= 파일당 commit)이 HF 무료플랜 128 commit/hr 한도를 때려 대량
          백필이 partial 로 잘리는 것을 ``create_commit`` 배치(300 files/commit)로 해소.

    Args:
        periods: 업로드 일자 list (YYYYMMDD). None 이면 로컬 디렉토리의 모든 ``.parquet``
            (목록만 ``*_meta.parquet`` 제외).
        token: HF token. None 이면 env ``HF_TOKEN``.

    Returns:
        int — 업로드 성공 파일 수(성공 commit 에 포함된 파일 합).

    Raises:
        AllFilingsHfUnavailableError: 업로드 대상이 있지만 HF token/dependency를 사용할 수 없는 경우.
        AllFilingsHfUploadError: 배치 commit이 실패한 경우. 성공한 파일 수를 예외가 보존한다.

    Example:
        >>> pushAllFilings(["20260527", "20260528"], token=os.environ["HF_TOKEN"])  # doctest: +SKIP

    Guide:
        - ``retryHfCall`` 로 429·LFS-RuntimeError 백오프. 같은 경로 파일은 자동 덮어쓰기.

    When:
        - 로컬 수집/백필 후 HF 반영 시. 보통 ``reconcileAllFilings`` 의 push 방향이 호출.

    How:
        - 파일 → ``CommitOperationAdd`` 배치 → ``create_commit`` (배치당 commit 1).

    Requires:
        - ``HF_TOKEN`` + 네트워크 + 로컬 ``data/dart/allFilings/`` parquet.

    AIContext:
        배치 업로드 — AI 분석 흐름 아닌 운영자/CI 동기화. 토큰 평문 노출 X.

    SeeAlso:
        - ``reconcileAllFilings`` — 본 함수의 push 방향 호출자.
        - ``pipeline.hfUpload`` — 동일 create_commit 배치 패턴(다른 카테고리).
    """
    import os as _os

    outDir = _allFilingsDir()
    if periods is None:
        files = sorted(f for f in outDir.glob("*.parquet") if _META_SUFFIX not in f.stem)
    else:
        files = [outDir / f"{p}.parquet" for p in periods]
        files = [f for f in files if f.exists()]

    if not files:
        _log.info("[HF↑] 업로드 대상 0")
        return 0

    hfToken = token or _os.environ.get("HF_TOKEN", "")
    if not hfToken:
        raise AllFilingsHfUnavailableError(
            "allFilings HF 업로드에 필요한 HF_TOKEN이 없습니다",
            period=None,
        )

    try:
        from huggingface_hub import CommitOperationAdd, HfApi
        from huggingface_hub.errors import LocalEntryNotFoundError, OfflineModeIsEnabled
    except ImportError as exc:
        raise AllFilingsHfUnavailableError(
            "huggingface_hub optional dependency가 없어 allFilings HF 업로드를 사용할 수 없습니다",
            period=None,
        ) from exc

    from dartlab.core.dataConfig import repoFor
    from dartlab.core.hfRetry import retryHfCall

    try:
        relDir = DATA_RELEASES[_ALLFILINGS_DIR_KEY]["dir"]
        repo = repoFor(_ALLFILINGS_DIR_KEY)
        api = HfApi(token=hfToken)
    except Exception as exc:  # noqa: BLE001 — 원인을 typed boundary error로 보존
        raise AllFilingsHfUploadError(
            "allFilings HF 업로드 초기화에 실패했습니다",
            uploadedFiles=0,
            totalFiles=len(files),
        ) from exc

    batchSize = 300  # hfUpload 와 동일 — commit 당 파일 수 상한(128 commit/hr 한도 회피)
    total = (len(files) + batchSize - 1) // batchSize
    ok = 0
    for i in range(0, len(files), batchSize):
        batch = files[i : i + batchSize]
        n = i // batchSize + 1
        try:
            ops = [CommitOperationAdd(path_in_repo=f"{relDir}/{f.name}", path_or_fileobj=str(f)) for f in batch]
            retryHfCall(
                api.create_commit,
                repo_id=repo,
                repo_type="dataset",
                operations=ops,
                commit_message=f"allFilings push: {len(batch)} files ({n}/{total})",
            )
            ok += len(batch)
            _log.info("[HF↑] %d/%d 파일 commit (배치 %d/%d)", ok, len(files), n, total)
        except (LocalEntryNotFoundError, OfflineModeIsEnabled) as exc:
            raise AllFilingsHfUnavailableError(
                "offline/cache 상태에서 allFilings HF 업로드를 사용할 수 없습니다",
                period=None,
            ) from exc
        except Exception as exc:  # noqa: BLE001 — 원인을 typed boundary error로 보존
            raise AllFilingsHfUploadError(
                f"allFilings HF 업로드 배치가 실패했습니다: batch={n}/{total}, files={len(batch)}",
                uploadedFiles=ok,
                totalFiles=len(files),
            ) from exc
    _log.info("[HF↑] 완료: %d/%d 파일", ok, len(files))
    return ok


def _remoteDates(*, token: str | None = None) -> set[str]:
    """HF dataset 에 올라간 allFilings **본문** parquet 의 일자(YYYYMMDD) 집합.

    reconcile 의 "HF 가 가진 일자" 쪽. ``list_repo_tree`` scoped 열거(retryHfCall)로
    ``dart/allFilings/`` prefix 만 읽어 전체 dataset metadata 폭주(429)를 피한다.
    ``_meta``(목록만) parquet 은 제외 — 본문 완료(``{YYYYMMDD}.parquet``)만 SSOT.

    Args:
        token: HF 토큰. None 이면 env ``HF_TOKEN``.

    Returns:
        set[str] — 본문 완료 일자 집합 (예: ``{"20260603", "20260604"}``).
        원격 경로가 정상적으로 비어 있으면 빈 set.

    Raises:
        AllFilingsHfUnavailableError: optional HF dependency를 사용할 수 없는 경우.
        AllFilingsHfListingError: 원격 목록 조회·인증이 실패한 경우.

    Example:
        >>> _remoteDates()  # doctest: +SKIP
        {'20260601', '20260602'}
    """
    import os as _os

    tok = token or _os.environ.get("HF_TOKEN") or None
    relDir = DATA_RELEASES[_ALLFILINGS_DIR_KEY]["dir"]
    try:
        from huggingface_hub import HfApi
        from huggingface_hub.errors import (
            EntryNotFoundError,
            LocalEntryNotFoundError,
            OfflineModeIsEnabled,
        )
    except ImportError as exc:
        raise AllFilingsHfUnavailableError(
            "huggingface_hub optional dependency가 없어 allFilings HF 목록을 조회할 수 없습니다",
            period=None,
        ) from exc

    try:
        from dartlab.core.dataConfig import repoFor
        from dartlab.core.hfRetry import retryHfCall

        api = HfApi(token=tok)

        def _listTree() -> list:
            return list(
                api.list_repo_tree(
                    repo_id=repoFor(_ALLFILINGS_DIR_KEY),
                    path_in_repo=relDir,
                    repo_type="dataset",
                    recursive=False,
                    token=tok,
                )
            )

        entries = retryHfCall(_listTree)
    except (LocalEntryNotFoundError, OfflineModeIsEnabled) as exc:
        raise AllFilingsHfUnavailableError(
            "offline/cache 상태에서 allFilings HF 목록을 조회할 수 없습니다",
            period=None,
        ) from exc
    except EntryNotFoundError:
        return set()
    except Exception as exc:  # noqa: BLE001 — 원인을 typed boundary error로 보존
        raise AllFilingsHfListingError(
            "allFilings HF 원격 목록 조회에 실패했습니다",
            period=None,
        ) from exc

    dates: set[str] = set()
    for item in entries:
        rel = getattr(item, "path", "") or getattr(item, "rfilename", "")
        name = Path(str(rel)).name
        stem = name[:-8] if name.endswith(".parquet") else ""  # ".parquet" = 8자
        if len(stem) == 8 and stem.isdigit():
            dates.add(stem)
    return dates


def _pullDates(dates: list[str], *, token: str | None = None) -> int:
    """지정 일자들의 본문 parquet 을 HF→로컬 1회 snapshot_download(retry).

    reconcile 의 pull 방향 헬퍼 — 일자별 개별 호출 대신 ``allow_patterns`` 리스트로
    한 번에 받는다. tmp→rename atomic 은 huggingface_hub 가 보장.

    Args:
        dates: 받을 일자 list (YYYYMMDD).
        token: HF 토큰. None 이면 env ``HF_TOKEN``.

    Returns:
        int — 실제로 로컬에 떨어진 일자 수. 빈 입력이면 0.

    Raises:
        AllFilingsHfUnavailableError: optional HF dependency를 사용할 수 없는 경우.
        AllFilingsHfDownloadError: 원격 다운로드 실패 또는 요청 artifact 누락.

    Example:
        >>> _pullDates(["20260601", "20260602"])  # doctest: +SKIP
        2
    """
    if not dates:
        return 0

    import os as _os

    tok = token or _os.environ.get("HF_TOKEN") or None
    relDir = DATA_RELEASES[_ALLFILINGS_DIR_KEY]["dir"]
    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import LocalEntryNotFoundError, OfflineModeIsEnabled
    except ImportError as exc:
        raise AllFilingsHfUnavailableError(
            "huggingface_hub optional dependency가 없어 allFilings HF pull을 사용할 수 없습니다",
            period=None,
        ) from exc

    try:
        from dartlab.core.dataConfig import repoFor
        from dartlab.core.hfRetry import retryHfCall

        retryHfCall(
            snapshot_download,
            repo_id=repoFor(_ALLFILINGS_DIR_KEY),
            repo_type="dataset",
            allow_patterns=[f"{relDir}/{d}.parquet" for d in dates],
            local_dir=str(Path(_cfg.dataDir)),
            token=tok,
        )
    except (LocalEntryNotFoundError, OfflineModeIsEnabled) as exc:
        raise AllFilingsHfUnavailableError(
            "offline/cache 상태에서 allFilings HF pull을 사용할 수 없습니다",
            period=None,
        ) from exc
    except Exception as exc:  # noqa: BLE001 — 원인을 typed boundary error로 보존
        raise AllFilingsHfDownloadError(
            f"allFilings HF reconcile pull에 실패했습니다: requested={len(dates)}",
            period=None,
        ) from exc

    outDir = _allFilingsDir()
    missing = [date for date in dates if not (outDir / f"{date}.parquet").is_file()]
    if missing:
        raise AllFilingsHfDownloadError(
            f"allFilings HF pull 완료 후 artifact가 누락되었습니다: {missing}",
            period=None,
        )
    return len(dates)


def reconcileAllFilings(
    *,
    pull: bool = True,
    push: bool = True,
    token: str | None = None,
) -> dict:
    """로컬 ↔ HF allFilings parquet **양방향 reconcile** — 집합 차분, 부족분만 채움.

    Capabilities:
        - 로컬 본문 완료 일자(``collectedDates``)와 HF 일자(``_remoteDates``)를 집합
          비교해 한쪽에만 있는 일자를 반대쪽으로 채운다. HF 가 앞선 일자는 로컬로 pull,
          로컬이 앞선 일자는 HF 로 push, 양쪽 합집합으로 수렴. 이미 양쪽에 있는 일자는
          건드리지 않는다(idempotent).

    Args:
        pull: HF→로컬 (HF 가 앞선 일자 다운로드).
        push: 로컬→HF (로컬이 앞선 일자 업로드).
        token: HF 토큰. None 이면 env ``HF_TOKEN``.

    Returns:
        dict — ``{"localBefore", "remoteBefore", "pullDates", "pushDates", "pulled",
        "pushed", "localAfter", "inSync"}``. ``inSync`` 는 활성 방향 기준 처리 대상 0 여부.

    Raises:
        AllFilingsHfUnavailableError: HF dependency/token을 사용할 수 없는 경우.
        AllFilingsHfListingError: 원격 목록 조회 실패.
        AllFilingsHfDownloadError: pull 실패 또는 artifact 누락.
        AllFilingsHfUploadError: push 실패. 부분 업로드 수는 예외 속성에 보존.

    Example:
        >>> reconcileAllFilings()  # doctest: +SKIP
        {'localBefore': 225, 'remoteBefore': 230, 'pulled': 5, 'pushed': 0, ...}

    Guide:
        - 월 단위 백필 후 push 로 새 일자 HF 반영, 다른 머신/CI 가 수집한 일자는 pull 로 로컬 보강.

    When:
        - 운영자가 로컬 store 와 HF 를 일치시킬 때. 백필 직후 또는 머신 간 동기화 시점.

    How:
        - ``collectedDates`` ∆ ``_remoteDates`` → ``_pullDates``(HF→로컬) / ``pushAllFilings``(로컬→HF).

    Requires:
        - ``HF_TOKEN`` + 네트워크. 영속 로컬 store(운영자 머신) — ephemeral CI 는 pull 무의미.

    AIContext:
        운영자 동기화 명령 — AI 분석 흐름 아님. CI ephemeral runner 에서 부르면 pull 이
        전 이력 재다운로드라 무의미(daily forward+push job 이 CI 최신화 담당).

    SeeAlso:
        - ``pushAllFilings`` — push 방향. ``_remoteDates`` / ``_pullDates`` — 비교·pull 헬퍼.
        - ``allFilingsCollector.fillContent`` — 로컬 수집(본 reconcile 의 입력 생산).
    """
    localDates = set(collectedDates())
    remoteDates = _remoteDates(token=token)

    pullDates = sorted(remoteDates - localDates) if pull else []
    pushDates = sorted(localDates - remoteDates) if push else []

    pulledN = _pullDates(pullDates, token=token)
    pushedN = pushAllFilings(pushDates, token=token) if pushDates else 0

    return {
        "localBefore": len(localDates),
        "remoteBefore": len(remoteDates),
        "pullDates": pullDates,
        "pushDates": pushDates,
        "pulled": pulledN,
        "pushed": pushedN,
        "localAfter": len(collectedDates()),
        "inSync": not pullDates and not pushDates,
    }
