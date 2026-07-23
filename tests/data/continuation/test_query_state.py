"""Private continuation query-state codec locks."""

from __future__ import annotations

import pytest

from dartlab.data.continuation import (
    ContinuationError,
    ContinuationQueryState,
    decodeQueryState,
    encodeQueryState,
)


def testQueryStateRoundTripsWithoutPlaintextRepr():
    state = ContinuationQueryState(b'{"asset":"scan.account"}', b"keyset:US:AAPL:2025")
    encoded = encodeQueryState(state, maxBytes=1024)
    restored = decodeQueryState(encoded, maxBytes=1024)

    assert restored == state
    assert b"scan.account" in encoded
    assert "scan.account" not in repr(restored)
    assert "US:AAPL" not in repr(restored)


def testQueryStateBudgetIsEnforcedOnEncodeAndDecode():
    state = ContinuationQueryState(b"q" * 64, b"c" * 64)
    with pytest.raises(ContinuationError) as encodedError:
        encodeQueryState(state, maxBytes=32)
    assert encodedError.value.code == "CONTINUATION_STATE_BUDGET"

    encoded = encodeQueryState(state, maxBytes=1024)
    with pytest.raises(ContinuationError) as decodedError:
        decodeQueryState(encoded, maxBytes=32)
    assert decodedError.value.code == "CONTINUATION_STATE_BUDGET"


@pytest.mark.parametrize("maxBytes", (True, 1.5, "1024"))
def testQueryStateBudgetRequiresExactPositiveInteger(maxBytes):
    state = ContinuationQueryState(b"query", b"cursor")

    with pytest.raises(ValueError):
        encodeQueryState(state, maxBytes=maxBytes)
    with pytest.raises(ValueError):
        decodeQueryState(b"", maxBytes=maxBytes)


def testCorruptStateFailsWithoutEchoingPayload():
    private = b"private-query-and-cursor"
    with pytest.raises(ContinuationError) as error:
        decodeQueryState(private, maxBytes=1024)
    assert error.value.code == "CONTINUATION_CORRUPT"
    assert private.decode() not in str(error.value)
    assert private.decode() not in repr(error.value)
