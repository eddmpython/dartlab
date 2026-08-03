"""회사 캐시는 공식 AI runtime이 아니라 엔진/데이터 계층이 소유한다."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_agent_runtime_does_not_expose_company_cache():
    import dartlab.ai.runtime as runtime

    assert not hasattr(runtime, "CompanyCache")
    assert not hasattr(runtime, "companyCache")


def test_engine_call_blocks_private_api():
    from dartlab.ai.tools.engineCall import engineCall

    result = engineCall({"apiRef": "Company._private", "target": "005930"})

    assert result.ok is False
    assert result.error == "private_api_blocked"
