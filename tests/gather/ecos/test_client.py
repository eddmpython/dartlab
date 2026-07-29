"""dartlab.gather.ecos.client mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.ecos.client`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.ecos.client")


def test_parse_response_valid_empty() -> None:
    """INFO-200만 정상 무데이터로 해석한다."""
    from dartlab.gather.ecos.client import EcosClient

    assert EcosClient._parseResponse({"RESULT": {"CODE": "INFO-200", "MESSAGE": "없음"}}) == []


def test_parse_response_missing_statistic_search_raises() -> None:
    """성공처럼 보이지만 payload가 없는 응답은 schema 오류다."""
    from dartlab.gather.ecos.client import EcosClient
    from dartlab.gather.ecos.types import EcosError

    with pytest.raises(EcosError, match="StatisticSearch"):
        EcosClient._parseResponse({})


def test_parse_response_rejects_non_object_rows() -> None:
    """ECOS row 손상이 정상 빈 결과로 사라지지 않는다."""
    from dartlab.gather.ecos.client import EcosClient
    from dartlab.gather.ecos.types import EcosError

    with pytest.raises(EcosError, match="row"):
        EcosClient._parseResponse({"StatisticSearch": {"row": ["broken"]}})


def test_network_failure_is_wrapped_as_ecos_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """재시도 후 네트워크 원인을 EcosError에 연결한다."""
    import httpx

    from dartlab.gather.ecos.client import EcosClient
    from dartlab.gather.ecos.types import EcosError

    class FailingSession:
        def get(self, *args, **kwargs):
            raise httpx.ConnectError("offline")

    client = object.__new__(EcosClient)
    client._key = "key"
    client._session = FailingSession()
    client._timestamps = []
    monkeypatch.setattr(EcosClient, "_backoff", staticmethod(lambda attempt: None))

    with pytest.raises(EcosError) as excInfo:
        client.get("T", "D", "20260101", "20260102")

    assert isinstance(excInfo.value.__cause__, httpx.ConnectError)
