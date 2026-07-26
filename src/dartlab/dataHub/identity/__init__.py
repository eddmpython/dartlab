"""DataHub 결과 identity 계층. 내용 봉인과 vintage 참조.

dataHub 안에서 아무것도 import 하지 않는 leaf 이므로 어느 계층에서도 안전하게 쓴다.
"""

from __future__ import annotations

from dartlab.dataHub.identity.contentSeal import (
    ContentSealError,
    contentHash,
    executionReceipt,
    resultSnapshotId,
)
from dartlab.dataHub.identity.vintage import (
    VintageError,
    VintageRef,
    isExactAsKnown,
    validateVintageRef,
)

__all__ = [
    "ContentSealError",
    "VintageError",
    "VintageRef",
    "contentHash",
    "executionReceipt",
    "isExactAsKnown",
    "resultSnapshotId",
    "validateVintageRef",
]
