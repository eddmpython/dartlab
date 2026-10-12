"""HF dataset → 로컬 parquet seed (idempotent) — 옛 ``seedFromHf.seedCategory`` 정본.

HF 를 single source of truth 로: category prefix tree 1회 + 로컬 size-대조 + 누락분만
GET 으로 cold-start death-spiral 차단(snapshot_download 의 파일당 HEAD rate-limit 회피).
429 는 Retry-After/310s window 존중, 5xx/네트워크는 지수 백오프, tmp→rename atomic.
``upload`` 의 ``core.hfRetry`` 와 별 경로(여긴 urllib GET, hf_hub 아님)라 둘 다 보존.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


def _download(url: str, dest: Path, token: str | None, timeout: int = 60) -> int | None:
    """단일 파일 HTTP GET — 429/5xx/네트워크 transient 재시도, tmp→rename atomic.

    Args:
        url: HF resolve URL.
        dest: 저장 경로.
        token: HF 토큰(있으면 Authorization 헤더).
        timeout: 소켓 타임아웃 초.

    Returns:
        다운로드 바이트 수. HF tree/resolve drift 로 404가 나면 None.

    Raises:
        urllib.error.HTTPError: 404가 아닌 비-transient 또는 재시도 소진.

    Example:
        >>> _download("https://example/x", Path("/tmp/x"), None)  # doctest: +SKIP
        1024
    """
    import http.client
    import urllib.error
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    maxRetries = 5
    baseWait = 310.0  # HF rate-limit window 5분 + 버퍼
    transientCodes = {500, 502, 503, 504}

    for attempt in range(maxRetries):
        try:
            req = urllib.request.Request(url)
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            bytesWritten = 0
            with urllib.request.urlopen(req, timeout=timeout) as resp, tmp.open("wb") as f:
                while chunk := resp.read(1 << 20):
                    f.write(chunk)
                    bytesWritten += len(chunk)
            tmp.replace(dest)
            return bytesWritten
        except urllib.error.HTTPError as e:
            if e.code == 404:
                try:
                    tmp.unlink()
                except FileNotFoundError:
                    pass
                print(f"[seed] 404 skip ({dest.name}) — HF tree/resolve drift", flush=True)
                return None
            if e.code == 429 and attempt < maxRetries - 1:
                retryAfter = e.headers.get("Retry-After")
                try:
                    wait = max(float(retryAfter), baseWait) if retryAfter else baseWait * (1 + attempt * 0.5)
                except ValueError:
                    wait = baseWait * (1 + attempt * 0.5)
                print(f"[seed] 429 ({dest.name}) — {wait:.0f}s 후 재시도 {attempt + 1}/{maxRetries}", flush=True)
                time.sleep(wait)
                continue
            if e.code in transientCodes and attempt < maxRetries - 1:
                wait = min(30.0 * (2**attempt), 180.0)
                print(
                    f"[seed] HTTP {e.code} ({dest.name}) — {wait:.0f}s 후 재시도 {attempt + 1}/{maxRetries}", flush=True
                )
                time.sleep(wait)
                continue
            raise
        # 응답 없는 끊김(RemoteDisconnected, ConnectionResetError)과 본문 중단(IncompleteRead)은 urllib 가
        # URLError 로 감싸지 않고 그대로 올린다. 그래서 재시도 없이 Deploy Landing 시드 단계가 죽었다(2026-10-12).
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
            if attempt == maxRetries - 1:
                raise
            wait = min(15.0 * (2**attempt), 120.0)
            print(f"[seed] network ({dest.name}) — {wait:.0f}s 후 재시도 {attempt + 1}/{maxRetries}: {e}", flush=True)
            time.sleep(wait)
    return 0


def _seedOne(category: str, dataDir: Path, token: str | None) -> tuple[int, int, float]:
    from huggingface_hub import HfApi

    from dartlab.core.dataConfig import DATA_RELEASES, repoFor
    from dartlab.core.hfRetry import retryHfCall

    if category not in DATA_RELEASES:
        raise ValueError(f"unknown category '{category}' — {list(DATA_RELEASES)}")

    dirPath = DATA_RELEASES[category]["dir"]
    repo = repoFor(category)  # 전용 repo(dartOriginal 등) 존중 — HF_REPO 하드코딩 시 빈 seed
    api = HfApi(token=token)
    print(f"[seed] {category}: list-tree {repo}/{dirPath}/", flush=True)
    remoteFiles = _remoteTreeFiles(api, repo=repo, dirPath=dirPath, token=token)
    print(f"[seed] {category}: HF {len(remoteFiles)}개 발견", flush=True)

    missing = [(rel, size) for rel, size in remoteFiles.items() if not _isFresh(dataDir / rel, size)]
    downloadedBytes = 0
    downloadedCount = 0
    skipped404 = 0
    if missing:
        print(f"[seed] {category}: {len(missing)}개 다운로드", flush=True)
        baseUrl = f"https://huggingface.co/datasets/{repo}/resolve/main"
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_download, f"{baseUrl}/{rel}", dataDir / rel, token): rel for rel, _ in missing}
            for fut in as_completed(futures):
                bytesWritten = fut.result()
                if bytesWritten is None:
                    skipped404 += 1
                    continue
                downloadedCount += 1
                downloadedBytes += bytesWritten
    else:
        print(f"[seed] {category}: 로컬 모두 최신 — skip", flush=True)

    localCat = dataDir / dirPath
    total = sum(1 for p in localCat.rglob("*") if p.is_file()) if localCat.exists() else 0
    mb = downloadedBytes / 1024 / 1024
    skipped = f", 404-skip {skipped404}개" if skipped404 else ""
    print(f"[seed] {category}: 로컬 {total}개, 신규 {downloadedCount}개{skipped} / {mb:.1f}MB", flush=True)
    return total, downloadedCount, mb


def _remoteTreeFiles(api: Any, *, repo: str, dirPath: str, token: str | None) -> dict[str, int]:
    """HF dataset 의 특정 category prefix 아래 파일만 열거한다.

    ``repo_info(files_metadata=True)`` 는 dataset 전체 siblings metadata 를 읽어
    ``/api/datasets/{repo}?blobs=True`` 쿼터를 크게 소모한다. prebuild 의 panel seed 는
    이 경로에서 반복적으로 429 를 맞았으므로, category path 로 scope 된 tree endpoint 만
    사용한다.
    """

    from dartlab.core.hfRetry import retryHfCall

    def _listTree() -> list[Any]:
        return list(
            api.list_repo_tree(
                repo_id=repo,
                path_in_repo=dirPath,
                repo_type="dataset",
                recursive=True,
                expand=True,
                token=token,
            )
        )

    entries = retryHfCall(_listTree)
    files: dict[str, int] = {}
    for item in entries:
        rel = getattr(item, "rfilename", None) or getattr(item, "path", "")
        if not rel or rel.endswith("/"):
            continue
        size = getattr(item, "size", 0) or 0
        files[str(rel)] = int(size)
    return files


def _isFresh(local: Path, size: int) -> bool:
    return local.exists() and local.stat().st_size == size


def seedCategoriesFromHf(
    categories: list[str],
    *,
    dataDir: str | None = None,
    token: str | None = None,
) -> dict[str, tuple[int, int, float]]:
    """여러 category 를 HF 에서 idempotent seed — 로컬 누락/크기불일치만 다운로드.

    Args:
        categories: DATA_RELEASES 카테고리명 목록.
        dataDir: 데이터 루트(기본 env/`./data`).
        token: HF 토큰(없으면 public rate-limit 완화만 못 받음).

    Returns:
        {category: (로컬총수, 신규다운로드수, 다운로드MB)} dict.

    Raises:
        ValueError: 미등록 category.

    Example:
        >>> seedCategoriesFromHf(["finance"])  # doctest: +SKIP
        {'finance': (2900, 12, 4.3)}
    """
    root = Path(dataDir or os.environ.get("DARTLAB_DATA_DIR") or "./data").resolve()
    root.mkdir(parents=True, exist_ok=True)
    tok = token or os.environ.get("HF_TOKEN") or None
    return {c.strip(): _seedOne(c.strip(), root, tok) for c in categories if c and c.strip()}


def listRemoteFiles(category: str, *, token: str | None = None) -> dict[str, int]:
    """카테고리 prefix 아래 HF 파일을 다운로드 없이 1회 열거한다 — 증분 변경 감지용.

    panel 같은 대용량 카테고리를 전량 받지 않고 ``{rel: size}`` 스냅샷만 얻어 직전 빌드
    ledger 와 size 비교 → 변경/삭제 종목을 가린다. ``retryHfCall`` 로 감싼 scoped tree
    열거(``_remoteTreeFiles``)라 전체 dataset metadata 폭주(429)를 일으키지 않는다.

    Args:
        category: ``DATA_RELEASES`` 카테고리 키 (예: ``"panel"``).
        token: HF 토큰. None 이면 ``HF_TOKEN`` env.

    Returns:
        ``{repoRelPath: sizeBytes}`` dict (예: ``{"dart/panel/005930.parquet": 12345}``).

    Raises:
        ValueError: 미등록 category.

    Example:
        >>> listRemoteFiles("panel")  # doctest: +SKIP
        {'dart/panel/005930.parquet': 123456, ...}
    """
    from huggingface_hub import HfApi

    from dartlab.core.dataConfig import DATA_RELEASES, repoFor

    if category not in DATA_RELEASES:
        raise ValueError(f"unknown category '{category}' — {list(DATA_RELEASES)}")
    tok = token or os.environ.get("HF_TOKEN") or None
    api = HfApi(token=tok)
    return _remoteTreeFiles(api, repo=repoFor(category), dirPath=DATA_RELEASES[category]["dir"], token=tok)


def downloadCategoryFiles(
    category: str,
    relPaths: list[str],
    *,
    dataDir: str | None = None,
    token: str | None = None,
) -> tuple[int, int]:
    """카테고리의 *지정 파일만* 로컬로 받는다(전량 seed 회피) — 증분 prebuild 의 변경분 충전.

    ``seedCategoriesFromHf`` 가 카테고리 전체를 idempotent 충전한다면, 본 함수는 호출자가
    가린 변경 파일 목록만 받는다. ``_download`` (429/5xx/네트워크 재시도 + tmp→rename atomic)
    를 4-워커로 재사용한다.

    Args:
        category: ``DATA_RELEASES`` 카테고리 키.
        relPaths: 받을 repo-상대 경로 목록 (``listRemoteFiles`` 키와 동형).
        dataDir: 데이터 루트. None 이면 env/``./data``.
        token: HF 토큰. None 이면 ``HF_TOKEN`` env.

    Returns:
        ``(다운로드수, 404-skip수)``.

    Raises:
        ValueError: 미등록 category.

    Example:
        >>> downloadCategoryFiles("panel", ["dart/panel/005930.parquet"])  # doctest: +SKIP
        (1, 0)
    """
    from dartlab.core.dataConfig import DATA_RELEASES, repoFor

    if category not in DATA_RELEASES:
        raise ValueError(f"unknown category '{category}' — {list(DATA_RELEASES)}")
    if not relPaths:
        return 0, 0
    root = Path(dataDir or os.environ.get("DARTLAB_DATA_DIR") or "./data").resolve()
    tok = token or os.environ.get("HF_TOKEN") or None
    baseUrl = f"https://huggingface.co/datasets/{repoFor(category)}/resolve/main"

    downloaded = 0
    skipped404 = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_download, f"{baseUrl}/{rel}", root / rel, tok): rel for rel in relPaths}
        for fut in as_completed(futures):
            bytesWritten = fut.result()
            if bytesWritten is None:
                skipped404 += 1
                continue
            downloaded += 1
    return downloaded, skipped404
