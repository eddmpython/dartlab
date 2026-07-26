// 다섯 공개 분석 렌즈가 공유하는 제품 결과 계약 v1.
// 엔진별 payload와 driver 의미는 보존하고 Story/Report는 공통 외피만 소비한다.

export type LensEngine = 'analysis' | 'credit' | 'industry' | 'quant' | 'macro';
export type LensStatus = 'usable' | 'partial' | 'blocked' | 'notApplicable';
export type LensConfidenceLevel = 'high' | 'medium' | 'low' | 'blocked' | 'unknown';
export type LensClaimDirection = 'supportive' | 'neutral' | 'adverse' | 'unknown';
export type LensClaimStatus = 'observed' | 'derived' | 'estimated' | 'missing' | 'blocked';

export interface LensIdentity {
  target: string;
  market: string;
  engine: LensEngine;
  axis: string;
  version: string;
}

export interface LensTime {
  asOf: string | null;
  dataAsOf: string | Record<string, unknown> | null;
  period: string | null;
  knowledgeBoundary: string | null;
}

export interface LensGap {
  id: string;
  status: 'missing' | 'partial' | 'blocked' | 'stale' | 'unsupported' | 'notApplicable';
  reason: string;
  sourceRef?: string;
}

export interface LensEvidence {
  id: string;
  kind: string;
  sourceRef: string;
  status: 'observed' | 'derived' | 'estimated' | 'missing' | 'blocked';
  observedAt?: string | null;
  detail?: string;
}

export interface LensClaim {
  id: string;
  label: string;
  comparisonKey: string;
  basis: string;
  direction: LensClaimDirection;
  horizon: string;
  asOf: string;
  dataAsOf: string | Record<string, unknown> | null;
  period: string | null;
  status: LensClaimStatus;
  sourceRef: string;
  evidenceRefs: string[];
  falsifierRefs: string[];
  value?: unknown;
  unit?: string;
  relation?: string;
}

export interface LensProduct {
  schemaVersion: 1;
  identity: LensIdentity;
  time: LensTime;
  status: LensStatus;
  conclusion: { label: string; summary: string };
  /** 하위 호환 이름이다. score는 예측 확률이 아니라 판단 근거 충족도다. */
  confidence: { level: LensConfidenceLevel; score: number | null; method: string };
  drivers: Record<string, unknown>[];
  claims?: LensClaim[];
  evidence: LensEvidence[];
  assumptions: Record<string, unknown>[];
  gaps: LensGap[];
  scenarios: Record<string, unknown>[];
  falsifiers: Record<string, unknown>[];
  payload: Record<string, unknown>;
}

export interface LensCollectionGap {
  engine: LensEngine;
  status: string;
  reason: string;
}

export interface LensTensionSide {
  engine: LensEngine;
  claimId: string;
  label: string;
  comparisonKey: string;
  basis: string;
  direction: LensClaimDirection;
  horizon: string;
  asOf: string;
  dataAsOf: string | Record<string, unknown> | null;
  period: string | null;
  status: LensClaimStatus;
  sourceRef: string;
  evidenceRefs: string[];
  value?: unknown;
  unit?: string;
}

export interface LensTensionItem {
  schemaVersion: 1;
  id: string;
  target: string;
  patternId: string;
  kind: 'divergence' | 'tradeoff' | 'counterforce';
  status: 'active';
  asOf: string;
  headline: { kr: string; en: string };
  mechanism: { kr: string; en: string };
  question: { kr: string; en: string };
  sides: LensTensionSide[];
  falsifiers: { id: string; condition: string; sourceRef?: string; driverRef?: string }[];
  gaps: { id: string; status: string; reason: string; sourceRef?: string }[];
  algorithmVersion: string;
  noComposite: true;
}

export interface LensTensionEvaluation {
  patternId: string;
  status: 'active' | 'clear' | 'blocked';
  reason: string;
}

export interface LensTensionBundle {
  schemaVersion: 1;
  items: LensTensionItem[];
  evaluations: LensTensionEvaluation[];
  noComposite: true;
}

export interface LensProductBundle {
  schemaVersion: 1;
  target: string;
  market: string;
  engines: LensEngine[];
  products: Partial<Record<LensEngine, LensProduct>>;
  tensions: LensTensionBundle;
  statusCounts: Record<string, number>;
  gaps: LensCollectionGap[];
  noComposite: true;
}

export interface LensSummaryRow {
  engine: LensEngine;
  status: LensStatus;
  label: string;
  summary: string;
  confidenceLevel: LensConfidenceLevel;
  confidenceScore: number | null;
  asOf: string | null;
  dataAsOf: string | Record<string, unknown> | null;
  period: string | null;
}

export interface LensPort {
  /** 엔진이 계산한 대표 제품만 반환한다. UI에서 렌즈 의미를 재구현하지 않는다. */
  products(code: string): Promise<LensProductBundle | null>;
}
