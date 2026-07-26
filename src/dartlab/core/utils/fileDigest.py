"""파일 내용 해시. 도메인 중립 primitive.

원래 `pipeline.hashing` 에 있었다. 그런데 `providers` 가 이 함수 하나 때문에 `pipeline`
을 top-level 로 import 했고, `pipeline` 은 다시 `providers` 를 쓰기 때문에 두 패키지가
양방향으로 묶였다. 상태 없는 blake2b 래퍼가 계층 cycle 을 만들 이유가 없어 L0 으로
내린다. `pipeline.hashing` 은 재export 로 남아 기존 호출자는 그대로다.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

_DEFAULT_CHUNK_BYTES = 1 << 20


def fileHash(path: Path, *, chunkSize: int = _DEFAULT_CHUNK_BYTES) -> str:
    """파일 내용의 blake2b 해시를 16 byte digest hex 로 낸다.

    Capabilities:
        대형 parquet 도 메모리에 통째로 올리지 않고 청크 스트리밍으로 해시한다.

    AIContext:
        내용 기반 식별자다. 경로나 mtime 이 아니라 바이트가 같으면 같은 값이 나온다.

    Guide:
        스냅샷 diff 와 무결성 확인 양쪽에서 같은 함수를 쓴다.

    When:
        빌드 전후 산출물 비교, 원천 무결성 증명, 증분 업로드 입력 산출.

    How:
        `chunkSize` 만큼 읽어 blake2b 에 갱신한다. 기본 1MB.

    Args:
        path: 대상 파일.
        chunkSize: 스트리밍 청크 바이트.

    Returns:
        hex digest 문자열.

    Raises:
        OSError: 읽기 실패.

    Example:
        >>> isinstance(fileHash(Path(__file__)), str)
        True

    See Also:
        `dartlab.pipeline.hashing.snapshotHashes`.
    """

    digest = hashlib.blake2b(digest_size=16)
    with path.open("rb") as source:
        while True:
            chunk = source.read(chunkSize)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
