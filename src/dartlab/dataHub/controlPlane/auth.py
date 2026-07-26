"""DataHub client와 worker의 role 분리 bearer 인증."""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass

from .errors import DataHubControlError


def _validToken(value: str | None) -> bool:
    return isinstance(value, str) and 32 <= len(value) <= 4096 and "\x00" not in value


@dataclass(frozen=True, slots=True)
class DataHubAuthPolicy:
    """Client와 worker token을 서로 다른 role로 검증한다."""

    clientToken: str
    workerToken: str

    def __post_init__(self) -> None:
        if not _validToken(self.clientToken) or not _validToken(self.workerToken):
            raise ValueError("DataHub token은 32자 이상이어야 합니다")
        if hmac.compare_digest(self.clientToken, self.workerToken):
            raise ValueError("DataHub client와 worker token은 달라야 합니다")

    @classmethod
    def fromEnvironment(cls) -> DataHubAuthPolicy:
        """환경변수에서 role 분리 인증 정책을 읽는다."""

        clientToken = os.environ.get("DARTLAB_DATA_HUB_CLIENT_TOKEN")
        workerToken = os.environ.get("DARTLAB_DATA_HUB_WORKER_TOKEN")
        if not _validToken(clientToken) or not _validToken(workerToken):
            raise DataHubControlError("DATA_HUB_AUTH_REQUIRED")
        return cls(clientToken=clientToken, workerToken=workerToken)

    def authorize(self, authorization: str | None, *, role: str) -> str:
        """Bearer token을 검증하고 로그 안전 digest를 반환한다."""

        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            raise DataHubControlError("DATA_HUB_AUTH_REQUIRED")
        supplied = authorization[7:]
        expected = self.clientToken if role == "client" else self.workerToken if role == "worker" else None
        if expected is None or not hmac.compare_digest(supplied, expected):
            raise DataHubControlError("DATA_HUB_AUTH_REQUIRED")
        return hashlib.sha256(supplied.encode("utf-8")).hexdigest()
