"""원격 job query를 strict canonical DataQuery로 정규화한다."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any

from dartlab.dataHub.contracts import DataQuery, QueryBudget
from dartlab.dataHub.entry import _dataQuery
from dartlab.dataHub.materialization import MaterializationDirective
from dartlab.dataHub.paging.stateCodec import strictTree

from .errors import DataHubControlError
from .policy import MAX_RESULT_PAYLOAD_BYTES


def normalizeDurableQuery(query: Mapping[str, Any]) -> tuple[DataQuery, dict[str, Any]]:
    """Public mapping을 remote-safe refresh query와 canonical tree로 바꾼다."""

    if not isinstance(query, Mapping):
        raise DataHubControlError("DATA_HUB_INVALID")
    payload = dict(query)
    rawBudget = payload.get("budget")
    if rawBudget is None:
        budgetPayload: dict[str, Any] = {}
    elif isinstance(rawBudget, Mapping):
        budgetPayload = dict(rawBudget)
    else:
        raise DataHubControlError("DATA_HUB_INVALID")
    suppliedMaxBytes = budgetPayload.get("maxBytes")
    if type(suppliedMaxBytes) is int and suppliedMaxBytes > MAX_RESULT_PAYLOAD_BYTES:
        raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")
    budgetPayload.setdefault("maxBytes", MAX_RESULT_PAYLOAD_BYTES)
    payload["budget"] = budgetPayload
    try:
        parsed = _dataQuery(payload)
    except (TypeError, ValueError, KeyError):
        raise DataHubControlError("DATA_HUB_INVALID") from None
    if parsed is None:
        raise DataHubControlError("DATA_HUB_INVALID")
    if parsed.continuation is not None:
        raise DataHubControlError("DATA_HUB_PLAN_MISSING")
    if parsed.materialization.mode not in {"runtime", "refresh"} or parsed.materialization.receipt is not None:
        raise DataHubControlError("DATA_HUB_PLAN_MISSING")
    parsed = dataclasses.replace(
        parsed,
        budget=dataclasses.replace(parsed.budget, maxBytes=budgetPayload["maxBytes"]),
        materialization=MaterializationDirective(mode="refresh"),
    )
    try:
        tree = strictTree(parsed, context="remote query")
    except (TypeError, ValueError):
        raise DataHubControlError("DATA_HUB_INVALID") from None
    if not isinstance(tree, dict):
        raise DataHubControlError("DATA_HUB_INVALID")
    return parsed, tree


def logicalQuery(query: DataQuery) -> DataQuery:
    """실행 directive를 제거한 결과 의미 query를 반환한다."""

    if not isinstance(query, DataQuery):
        raise TypeError("query는 DataQuery여야 합니다")
    return dataclasses.replace(query, materialization=MaterializationDirective())


__all__ = ["logicalQuery", "normalizeDurableQuery"]
