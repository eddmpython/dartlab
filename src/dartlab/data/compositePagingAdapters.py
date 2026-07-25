"""Composite production adapter 조합."""

from __future__ import annotations

from dartlab.data.compositePagingPlanAdapter import CompositePlanAdapterMixin
from dartlab.data.compositePagingRunAdapter import CompositeRunAdapterMixin


class _ProductionAdapters(CompositePlanAdapterMixin, CompositeRunAdapterMixin):
    """Lower owner 계획과 page 실행 adapter를 하나로 조합한다."""
