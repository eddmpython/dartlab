// Python src/dartlab/ai/runtime/schema.py에서 생성. 직접 수정하지 않는다.
export type AgentEventKind = 'sessionStarted' | 'sessionResumed' | 'turnStarted' | 'messageDelta' | 'reasoningDelta' | 'toolStarted' | 'toolCompleted' | 'approvalRequested' | 'artifactProduced' | 'turnCompleted' | 'runtimeError' | 'eventGap' | 'native';
export type RuntimeState = 'ready' | 'missing' | 'unavailable' | 'authRequired' | 'unknown';
export type ProductOutcomeState = 'started' | 'scoped' | 'grounded' | 'delivered' | 'verified' | 'retained';

export interface AgentEvent {
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
}

export interface RuntimeProbe {
  runtimeId: string;
  state: RuntimeState;
  executable?: string | null;
  version?: string | null;
  checkedAt: string;
  detail?: string | null;
}

export interface ProductOutcomeReceipt {
  outcomeId: string;
  feature: string;
  state: ProductOutcomeState;
  createdAt: string;
  updatedAt: string;
}
