"""Company facade 라우팅 단위 테스트.

company.py — canHandle 체인, provider discovery, priority ordering.
데이터 로드 없음, mock 전용.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


# ── _discover() ──


def test_discover_registers_providers():
    """_discover() 호출 후 _PROVIDERS에 DART/EDGAR가 등록된다."""
    import dartlab.company as mod

    # reset state
    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = False
        mod._PROVIDERS.clear()
        mod._discover()
        assert len(mod._PROVIDERS) >= 2
        assert mod._DISCOVERED is True
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_discover_runs_only_once():
    """_discover()는 최초 1회만 실행한다."""
    import dartlab.company as mod

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._discover()
        # _PROVIDERS는 비어있어야 함 — 이미 discovered이므로 등록 안 함
        assert len(mod._PROVIDERS) == 0
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_discover_sorts_by_priority():
    """_discover() 후 providers가 priority 순으로 정렬된다."""
    import dartlab.company as mod

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = False
        mod._PROVIDERS.clear()
        mod._discover()
        priorities = [cls.priority() for cls in mod._PROVIDERS if hasattr(cls, "priority")]
        assert priorities == sorted(priorities)
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


# ── Company() facade routing ──


def test_company_empty_input_raises():
    """빈 문자열은 ValueError를 발생시킨다."""
    from dartlab.company import Company

    with pytest.raises(ValueError, match="종목코드"):
        Company("")

    with pytest.raises(ValueError, match="종목코드"):
        Company("   ")


def test_company_routes_to_canhandle_provider():
    """canHandle이 True인 첫 번째 provider로 라우팅한다."""
    import dartlab.company as mod

    mock_cls = MagicMock()
    mock_cls.canHandle.return_value = True
    mock_cls.priority.return_value = 5
    mock_instance = MagicMock()
    mock_cls.return_value = mock_instance

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._PROVIDERS.append(mock_cls)

        result = mod.Company("005930")
        assert result is mock_instance
        mock_cls.canHandle.assert_called_once_with("005930")
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_company_skips_provider_on_value_error():
    """canHandle=True이지만 생성 시 ValueError → 다음 provider로 fallback."""
    import dartlab.company as mod

    failing_cls = MagicMock()
    failing_cls.canHandle.return_value = True
    failing_cls.side_effect = ValueError("no data")

    ok_cls = MagicMock()
    ok_cls.canHandle.return_value = True
    ok_instance = MagicMock()
    ok_cls.return_value = ok_instance

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend([failing_cls, ok_cls])

        result = mod.Company("005930")
        assert result is ok_instance
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_company_skips_provider_on_file_not_found():
    """canHandle=True이지만 FileNotFoundError → 다음 provider로 fallback."""
    import dartlab.company as mod

    failing_cls = MagicMock()
    failing_cls.canHandle.return_value = True
    failing_cls.side_effect = FileNotFoundError("missing")

    ok_cls = MagicMock()
    ok_cls.canHandle.return_value = True
    ok_instance = MagicMock()
    ok_cls.return_value = ok_instance

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend([failing_cls, ok_cls])

        result = mod.Company("XYZ")
        assert result is ok_instance
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_company_fallback_tries_all_providers():
    """canHandle이 모두 False일 때 fallback 루프로 모든 provider 시도."""
    import dartlab.company as mod

    # canHandle은 False이지만 직접 생성은 성공
    cls_a = MagicMock()
    cls_a.canHandle.return_value = False
    cls_a.side_effect = ValueError("nope")

    cls_b = MagicMock()
    cls_b.canHandle.return_value = False
    ok_instance = MagicMock()
    cls_b.return_value = ok_instance

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend([cls_a, cls_b])

        result = mod.Company("unknown_name")
        assert result is ok_instance
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_company_all_providers_fail_raises():
    """모든 provider가 실패하면 ValueError를 발생시킨다."""
    import dartlab.company as mod

    cls_a = MagicMock()
    cls_a.canHandle.return_value = False
    cls_a.side_effect = ValueError("nope a")

    cls_b = MagicMock()
    cls_b.canHandle.return_value = False
    cls_b.side_effect = ValueError("nope b")

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend([cls_a, cls_b])

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            mod.Company("ZZZZZZ")
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_company_oserror_continues_to_next():
    """OSError도 다음 provider로 넘어간다."""
    import dartlab.company as mod

    failing_cls = MagicMock()
    failing_cls.canHandle.return_value = True
    failing_cls.side_effect = OSError("disk error")

    ok_cls = MagicMock()
    ok_cls.canHandle.return_value = True
    ok_instance = MagicMock()
    ok_cls.return_value = ok_instance

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend([failing_cls, ok_cls])

        result = mod.Company("005930")
        assert result is ok_instance
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


def test_company_strips_whitespace():
    """입력 문자열의 앞뒤 공백이 제거된다."""
    import dartlab.company as mod

    mock_cls = MagicMock()
    mock_cls.canHandle.return_value = True
    mock_instance = MagicMock()
    mock_cls.return_value = mock_instance

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        mod._PROVIDERS.append(mock_cls)

        mod.Company("  005930  ")
        mock_cls.canHandle.assert_called_once_with("005930")
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)


# ── canHandle 체인 우선순위 ──


def test_canhandle_priority_respected():
    """첫 번째로 canHandle=True인 provider가 선택된다 (priority 순서 기준)."""
    import dartlab.company as mod

    cls_low = MagicMock()
    cls_low.canHandle.return_value = True
    low_instance = MagicMock(name="low")
    cls_low.return_value = low_instance

    cls_high = MagicMock()
    cls_high.canHandle.return_value = True
    high_instance = MagicMock(name="high")
    cls_high.return_value = high_instance

    old_discovered = mod._DISCOVERED
    old_providers = list(mod._PROVIDERS)
    try:
        mod._DISCOVERED = True
        mod._PROVIDERS.clear()
        # low priority first (as sorted)
        mod._PROVIDERS.extend([cls_low, cls_high])

        result = mod.Company("TEST")
        # Should match the first provider in the list
        assert result is low_instance
        cls_low.canHandle.assert_called_once()
    finally:
        mod._DISCOVERED = old_discovered
        mod._PROVIDERS.clear()
        mod._PROVIDERS.extend(old_providers)
