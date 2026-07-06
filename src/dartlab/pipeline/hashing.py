"""스냅샷 해시 diff — full-rebuild 후 무엇이 바뀌었는지 산출.

옛 ``syncData.py`` 의 hash-diff 스냅샷 정본. full(88분기) 같은 전수 재빌드는
changed.txt 를 못 만드므로, 빌드 전/후 파일 해시 스냅샷을 떠 차이를 변경목록으로
환원한다(증분 업로드 입력). blake2b(빠르고 충돌 안전)로 내용 해시.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def fileHash(path: Path, *, chunkSize: int = 1 << 20) -> str:
    """파일 내용의 blake2b 해시(16-byte digest hex).

    Args:
        path: 대상 파일.
        chunkSize: 스트리밍 청크 바이트(기본 1MB — 대형 parquet 메모리 안전).

    Returns:
        hex digest 문자열.

    Raises:
        OSError: 읽기 실패.

    Example:
        >>> isinstance(fileHash(Path(__file__)), str)
        True
    """
    h = hashlib.blake2b(digest_size=16)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunkSize), b""):
            h.update(chunk)
    return h.hexdigest()


def partialFileHash(path: Path, *, headBytes: int = 65536) -> str:
    """파일 앞부분(headBytes) + 크기의 SHA-256 해시(빠른 변경 감지용, 전체 read 회피).

    대형 parquet 을 매 sync 마다 전량 해시하지 않고 앞 64KB + 파일크기로 변경을 추정한다. 같은 run 의
    before/after 스냅샷 diff(diffChanged) 전용. 앞부분+크기 동일한 내용변경은 놓칠 수 있으나(설계 트레이드
    오프) 재빌드 산출은 크기/헤더가 함께 바뀌어 실무상 충분. 영구 무결성엔 fileHash(전체 blake2b) 사용.
    syncData·syncNewStocks·syncRecent 공유 SSOT(옛 각 스크립트 로컬 _fileHash 복붙 통합).

    Args:
        path: 대상 파일.
        headBytes: 해시에 넣을 앞부분 바이트(기본 64KB).

    Returns:
        hex digest 문자열.

    Raises:
        OSError: 읽기 실패.

    Example:
        >>> isinstance(partialFileHash(Path(__file__)), str)
        True
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(headBytes))
    h.update(str(path.stat().st_size).encode())
    return h.hexdigest()


def snapshotHashes(root: Path, *, pattern: str = "**/*.parquet") -> dict[str, str]:
    """``root`` 하위 매칭 파일의 {상대경로: 해시} 스냅샷.

    Args:
        root: 스냅샷 기준 디렉토리.
        pattern: glob 패턴(기본 모든 parquet).

    Returns:
        {posix 상대경로: blake2b hex} dict. root 부재 시 빈 dict.

    Raises:
        없음.

    Example:
        >>> snapshotHashes(Path("__none__"))
        {}
    """
    if not root.exists():
        return {}
    out: dict[str, str] = {}
    for p in root.glob(pattern):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = fileHash(p)
    return out


def diffChanged(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """두 스냅샷의 차이(신규 + 내용 변경) 상대경로 목록(정렬).

    삭제는 업로드 대상이 아니므로 제외 — after 기준 added/modified 만.

    Args:
        before: 빌드 전 {상대경로: 해시}.
        after: 빌드 후 {상대경로: 해시}.

    Returns:
        신규·변경된 상대경로 정렬 list.

    Raises:
        없음.

    Example:
        >>> diffChanged({"a": "1"}, {"a": "2", "b": "9"})
        ['a', 'b']
    """
    return sorted(rel for rel, h in after.items() if before.get(rel) != h)
