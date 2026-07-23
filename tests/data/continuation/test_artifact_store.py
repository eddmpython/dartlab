"""Continuation private CAS atomicity and integrity locks."""

from __future__ import annotations

import hashlib
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import pytest

from dartlab.data.continuation import ArtifactStore, ContinuationError
from dartlab.data.continuation.privateStorage import (
    currentWindowsUserSid,
    securePrivatePath,
    verifyPrivatePath,
    windowsDaclSids,
)


def _putFromProcess(root: str, payload: bytes) -> str:
    return ArtifactStore(Path(root)).putBytes(payload)


def testConcurrentSamePayloadWritesOneVerifiedObject(tmp_path):
    store = ArtifactStore(tmp_path / "cas")
    payload = b"shared-private-state"
    with ThreadPoolExecutor(max_workers=12) as pool:
        digests = list(pool.map(store.putBytes, [payload] * 24))

    assert len(set(digests)) == 1
    assert store.readBytes(digests[0]) == payload
    assert store.iterDigests() == (digests[0],)


def testConcurrentProcessesPublishOneVerifiedObject(tmp_path):
    root = tmp_path / "cas"
    payload = b"shared-private-state"
    with ProcessPoolExecutor(max_workers=6, mp_context=get_context("spawn")) as pool:
        digests = list(pool.map(_putFromProcess, [str(root)] * 12, [payload] * 12))

    store = ArtifactStore(root)
    assert len(set(digests)) == 1
    assert store.readBytes(digests[0]) == payload
    assert store.iterDigests() == (digests[0],)


def testArtifactDigestAndSizeAreVerified(tmp_path):
    store = ArtifactStore(tmp_path / "cas")
    digest = store.putBytes(b"bounded")

    with pytest.raises(ContinuationError) as sizeError:
        store.readBytes(digest, maxBytes=2)
    assert sizeError.value.code == "CONTINUATION_STATE_BUDGET"

    store.pathForDigest(digest).write_bytes(b"tampered")
    with pytest.raises(ContinuationError) as digestError:
        store.readBytes(digest)
    assert digestError.value.code == "CONTINUATION_CORRUPT"


def testArtifactDeletionIsIdempotent(tmp_path):
    store = ArtifactStore(tmp_path / "cas")
    digest = store.putBytes(b"expired")

    assert store.deleteBytes(digest) == (True, len(b"expired"))
    assert store.deleteBytes(digest) == (False, 0)


def testArtifactPublishUsesShortTemporaryNameNearWindowsPathLimit(tmp_path):
    payload = b"long-control-plane-path"
    digest = hashlib.sha256(payload).hexdigest()
    root = tmp_path / "cas"
    destination = root.joinpath(
        "objects",
        "sha256-v3",
        digest[:2],
        digest[2:4],
        digest[4:6],
        digest[6:8],
        digest,
    )
    while len(str(destination)) < 225:
        root /= "deep"
        destination = root.joinpath(
            "objects",
            "sha256-v3",
            digest[:2],
            digest[2:4],
            digest[4:6],
            digest[6:8],
            digest,
        )
    assert len(str(destination)) < 240

    store = ArtifactStore(root)
    storedDigest = store.putBytes(payload)

    assert storedDigest == digest
    assert store.readBytes(digest) == payload


@pytest.mark.skipif(os.name != "nt", reason="Windows DACL integration lock")
def testWindowsCasDaclAllowsOnlyCurrentUserAndSystem(tmp_path):
    store = ArtifactStore(tmp_path / "cas")
    digest = store.putBytes(b"private")
    expected = {"S-1-5-18", currentWindowsUserSid()}

    for path in (store.root, store.root / "objects", store.objectRoot, store.pathForDigest(digest)):
        actual = {"S-1-5-18" if sid == "SY" else sid for sid in windowsDaclSids(path)}
        assert actual == expected
        assert verifyPrivatePath(path)


@pytest.mark.skipif(os.name != "nt", reason="Windows DACL integration lock")
def testWindowsDaclBroadeningFailsClosedAndCanBeRestored(tmp_path):
    store = ArtifactStore(tmp_path / "cas")
    path = store.pathForDigest(store.putBytes(b"private"))
    subprocess.run(
        ["icacls", str(path), "/grant", "*S-1-1-0:(R)"],
        check=True,
        capture_output=True,
        text=True,
    )

    with pytest.raises(ContinuationError) as error:
        verifyPrivatePath(path)
    assert error.value.code == "CONTINUATION_SECURITY_FAILED"

    securePrivatePath(path)
    assert verifyPrivatePath(path)
