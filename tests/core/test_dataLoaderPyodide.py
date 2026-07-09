"""pyodide 데이터 로더 순수 함수 계약.

브라우저(pyodide)에서만 도는 fetch tier 를 데스크톱에서 검증할 수 있는 부분만 고정한다.
동기 XHR 은 arraybuffer 를 못 받아 ``x-user-defined`` 텍스트로 받고 하위 8비트를 되돌린다.
그 복원이 **무손실**이어야 parquet 이 깨지지 않는다(옛 파이썬 루프 → numpy 벡터로 바꾼 뒤에도 불변).
"""

from __future__ import annotations

import random

import pytest

from dartlab.core.dataLoaderPyodide import _decodeUserDefined

pytestmark = [pytest.mark.unit]


def _asUserDefinedText(raw: bytes) -> str:
    """브라우저가 ``charset=x-user-defined`` 로 넘겨주는 문자열 재현 (0x80+ 는 U+F780~U+F7FF)."""
    return "".join(chr(b) if b < 0x80 else chr(0xF700 + b) for b in raw)


def test_decodeUserDefined_roundTrip_allByteValues() -> None:
    """0~255 전 바이트가 무손실 복원된다 (경계값 0x00·0x7F·0x80·0xFF 포함)."""
    raw = bytes(range(256))
    assert _decodeUserDefined(_asUserDefinedText(raw)) == raw


def test_decodeUserDefined_roundTrip_randomPayload() -> None:
    """임의 바이너리도 그대로 복원된다 (parquet 처럼 고바이트가 섞인 payload)."""
    rng = random.Random(20260709)
    raw = bytes(rng.randrange(256) for _ in range(8192))
    assert _decodeUserDefined(_asUserDefinedText(raw)) == raw


def test_decodeUserDefined_empty() -> None:
    """빈 응답은 빈 바이트."""
    assert _decodeUserDefined("") == b""


def test_decodeUserDefined_matchesLegacyLoop() -> None:
    """numpy 벡터 경로가 옛 파이썬 루프와 byte-identical (폴백 경로와 결과 일치)."""
    rng = random.Random(7)
    raw = bytes(rng.randrange(256) for _ in range(4096))
    text = _asUserDefinedText(raw)
    legacy = bytes(ord(c) & 0xFF for c in text)
    assert _decodeUserDefined(text) == legacy
