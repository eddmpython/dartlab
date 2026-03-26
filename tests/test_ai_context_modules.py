from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

import polars as pl

from dartlab.ai.context.finance_context import _QUESTION_MODULES, _extract_module_context


class _PrimaryOnlyCompany:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def _get_primary(self, name: str):
        self.calls.append(("primary", name))
        if name == "segments":
            return pl.DataFrame({"year": [2024], "revenue": [100]})
        return None

    def show(self, name: str):
        self.calls.append(("show", name))
        raise AssertionError("registry 모듈은 show()보다 _get_primary()를 우선해야 한다.")


class _TopicOnlyCompany:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []
        self.topics = pl.DataFrame(
            {
                "topic": ["businessOverview"],
                "source": ["docs"],
                "blocks": [1],
                "periods": [1],
            }
        )

    def show(self, name: str):
        self.calls.append(("show", name))
        if name == "businessOverview":
            return pl.DataFrame({"2024": ["사업 개요"]})
        return None


def test_extract_module_context_prefers_registry_primary_over_show():
    company = _PrimaryOnlyCompany()

    text = _extract_module_context(company, "segments")

    assert text is not None
    assert "## 부문정보" in text
    assert company.calls == [("primary", "segments")]


def test_extract_module_context_uses_show_only_for_real_topics():
    company = _TopicOnlyCompany()

    text = _extract_module_context(company, "businessOverview")

    assert text is not None
    assert "사업 개요" in text
    assert company.calls == [("show", "businessOverview")]


def test_question_module_overrides_do_not_include_stale_operational_asset():
    all_modules = {module for modules in _QUESTION_MODULES.values() for module in modules}

    assert "operationalAsset" not in all_modules
