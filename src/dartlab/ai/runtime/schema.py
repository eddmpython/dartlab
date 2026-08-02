"""Python 런타임 계약에서 UI TypeScript 계약을 생성한다."""

from __future__ import annotations

from typing import Any, get_args

from pydantic import BaseModel, Field

from dartlab.productOutcome import OutcomeState

from .contracts import EventKind, RuntimeState


class AgentEventModel(BaseModel):
    """서버 직렬화 검증용 Pydantic AgentEvent 모델."""

    schemaVersion: str = "1.0"
    sessionId: str
    turnId: str
    eventId: str
    sequence: int = Field(ge=1)
    runtimeId: str
    kind: EventKind
    timestamp: str
    payload: dict[str, Any] = Field(default_factory=dict)
    nativeType: str | None = None


class RuntimeProbeModel(BaseModel):
    """UI Runtime Center가 소비하는 probe 모델."""

    runtimeId: str
    state: RuntimeState
    executable: str | None = None
    version: str | None = None
    checkedAt: str
    detail: str | None = None


class ProductOutcomeReceiptModel(BaseModel):
    """UI가 exact evidence 확인 뒤 받는 content-free outcome receipt."""

    outcomeId: str
    feature: str
    state: OutcomeState
    createdAt: str
    updatedAt: str


def runtimeJsonSchemas() -> dict[str, dict[str, Any]]:
    """Sig: runtimeJsonSchemas() -> dict[str, dict[str, Any]].

    Args: 없음.
    Returns: 이름으로 색인한 Pydantic JSON Schema다.
    Example: `schemas = runtimeJsonSchemas()`.
    """
    return {
        "AgentEvent": AgentEventModel.model_json_schema(),
        "RuntimeProbe": RuntimeProbeModel.model_json_schema(),
        "ProductOutcomeReceipt": ProductOutcomeReceiptModel.model_json_schema(),
    }


def generateTypeScriptContracts() -> str:
    """Sig: generateTypeScriptContracts() -> str.

    Args: 없음.
    Returns: UI용 결정론적 TypeScript 계약 소스다.
    Example: `path.write_text(generateTypeScriptContracts())`.
    """
    eventKinds = " | ".join(f"'{item}'" for item in get_args(EventKind))
    runtimeStates = " | ".join(f"'{item}'" for item in get_args(RuntimeState))
    outcomeStates = " | ".join(f"'{item}'" for item in get_args(OutcomeState))
    return f"""// Python src/dartlab/ai/runtime/schema.py에서 생성. 직접 수정하지 않는다.
export type AgentEventKind = {eventKinds};
export type RuntimeState = {runtimeStates};
export type ProductOutcomeState = {outcomeStates};

export interface AgentEvent {{
  schemaVersion: string;
  sessionId: string;
  turnId: string;
  eventId: string;
  sequence: number;
  runtimeId: string;
  kind: AgentEventKind;
  timestamp: string;
  payload: Record<string, unknown>;
  nativeType?: string | null;
}}

export interface RuntimeProbe {{
  runtimeId: string;
  state: RuntimeState;
  executable?: string | null;
  version?: string | null;
  checkedAt: string;
  detail?: string | null;
}}

export interface ProductOutcomeReceipt {{
  outcomeId: string;
  feature: string;
  state: ProductOutcomeState;
  createdAt: string;
  updatedAt: string;
}}
"""
