// 전문 리포트 서사 문법 SSOT - Python story.buildReportModel 과 TS build.ts 가 둘 다 conform.
// 분석 report model 계약. 기존 report.ts의 ReportPort와 역할을 분리한다.
// 기존 8 블록(랜딩 model.ts) + 신규 10 블록(00-PRD §7). 신규는 전부 optional/graceful-skip - 구 렌더러 무회귀.
import type { Num } from './runtime';
import type { EvidenceRef } from './evidence';
import type { LensProductBundle, LensSummaryRow } from './lensProduct';

// ── 기존 8 블록 (landing model.ts 에서 이주, 동치) ──
export type ReportBlockLegacy =
  | { type: 'heading'; title: string }
  | { type: 'text'; text: string; refs?: EvidenceRef[] }
  | { type: 'metrics'; metrics: { label: string; value: string }[] }
  | { type: 'table'; label?: string; data: Record<string, string>[]; snapshot?: boolean; unit?: string; refs?: EvidenceRef[] }
  | { type: 'flags'; kind: 'warning' | 'opportunity'; flags: string[] }
  | { type: 'bars'; label?: string; rows: { label: string; value: number; display: string; tone?: 'neg' }[] }
  | { type: 'line'; label?: string; series: number[]; xLabels?: [string, string]; markers?: { label: string; v: number }[]; valueFmt?: 'won' }
  | { type: 'share'; label?: string; rows: { year: string; segs: { label: string; pct: number; key: string }[] }[]; legend: { label: string; key: string }[] };

// ── 신규 10 블록 (00-PRD §7) - 전부 optional 추가, 구 렌더러 graceful-skip ──
export type ReportBlockPro =
  | { type: 'thesis'; thesis: Thesis }
  | { type: 'exhibit'; n: number; title: string; takeaway: string; source: string; unit?: string; child: ReportBlock; refs?: EvidenceRef[] }
  | { type: 'callout'; tone: 'warn' | 'opportunity' | 'neutral'; title: string; body: string; refs?: EvidenceRef[] }
  | { type: 'verdict'; noComposite: true; rows: VerdictRow[]; caption?: string }
  | { type: 'scenario'; set: ScenarioSet }
  | { type: 'valuationBridge'; view: ValuationView }
  | { type: 'creditPanel'; view: CreditView }
  | { type: 'peerScatter'; xLabel: string; yLabel: string; points: PeerPoint[]; subjectCode: string }
  | { type: 'driverTree'; root: DriverNode }
  | { type: 'excerpt'; source: string; rceptNo?: string; text: string; sourceType: 'dart' | 'edgar' | 'external' }
  | { type: 'transition'; from: string; to: string; line: string };

export type ReportBlock = ReportBlockLegacy | ReportBlockPro;

// ── 구조화 객체 ──
export interface ThesisPillar {
  claim: string; // 메커니즘 1문장 (형용사 금지)
  sectionKey: string; // 이 기둥을 증명하는 본문 섹션 (결박)
  refs: EvidenceRef[];
}
export interface Thesis {
  central: string; // 중심논거 1문장 (검증가능 인과)
  pillars: ThesisPillar[]; // 지지기둥 3
  bearCase: string; // 약세론 (thesis 와 동등 무게)
  triggers: string[]; // 관점전환 트리거
  call: string | null; // 콜 (내재가치·등급·상대위치) - 매매지시 아님. 미산출 null.
}

export interface VerdictRow {
  axis: string;
  latest: string;
  range: string;
  threshold: string;
  verdict: '양호' | '주의' | '산출 불가' | string;
}

export interface ScenarioLeg {
  key: 'bear' | 'base' | 'bull';
  label: string;
  growth: Num;
  margin: Num;
  wacc: Num;
  intrinsic: Num;
  upside: Num;
}
export interface ScenarioSet {
  current: Num;
  legs: ScenarioLeg[];
  note: string;
}

export interface ValuationView {
  model: 'DCF' | 'DDM' | 'RIM' | 'relative';
  intrinsic: Num;
  current: Num;
  wacc: Num;
  waccBreakdown: { rf: Num; erp: Num; beta: Num; costDebt: Num; taxRate: Num; weightE: Num };
  g: Num; // 재투자 묶인 성장 (g = 재투자율 × ROIC)
  reinvestRate: Num;
  roic: Num;
  fadeYears: number;
  bridge: { label: string; value: Num }[];
  reverseDcf: { impliedGrowth: Num; supportedGrowth: Num; verdict: string } | null;
}

export interface DriverNode { label: string; value: string; contribution?: Num; children?: DriverNode[] }
export interface PeerPoint { code: string; name: string; x: Num; y: Num }

// dCR 신용 패킷 (02e P1e 가드③: grade·gradeRaw·axes·pdEstimate·outlook·confidence 명시 정의).
// 소스 = Python credit engine(evaluateCompany) 단일. TS 재구현 금지(가드②).
export interface CreditAxis { name: string; weight: Num; score: Num }
export interface CreditView {
  grade: string; // "dCR-AA+"
  gradeRaw: string; // "AA+" (chip 표시용)
  score: Num; // 0..100 위험점수 (0 = 최우량)
  healthScore: Num; // 100 - score (UI 양의 방향)
  pdEstimate: Num; // 1 년 부도확률 (%)
  outlook: string; // 안정적/긍정적/부정적
  investmentGrade: boolean | null;
  axes: CreditAxis[]; // 7(또는 5) 축 name/weight/score
  confidence: Num; // 0..100
  confidenceMethod: string; // "ratio"
}

export type InvestmentDimensionStatus = 'usable' | 'partial' | 'blocked' | 'notObserved';
export interface InvestmentDimension {
  status: InvestmentDimensionStatus;
  asOf: string;
  claim: string;
  evidenceRefs: string[];
  gaps: string[];
  details: Record<string, unknown>;
}
export interface InvestmentDecision {
  schemaVersion: 1;
  asOf: string;
  decisionStatus: 'supported' | 'mixed' | 'insufficient';
  evidenceStrength: 'strong' | 'moderate' | 'weak';
  usableDimensionCount: number;
  requiredDimensionCount: 9;
  dimensions: {
    thesis: InvestmentDimension;
    counterThesis: InvestmentDimension;
    earningsInflection: InvestmentDimension;
    industryMacroTransmission: InvestmentDimension;
    valuation: InvestmentDimension;
    scenarios: InvestmentDimension;
    catalysts: InvestmentDimension;
    risks: InvestmentDimension;
    monitoringTripwires: InvestmentDimension;
  };
  summary: {
    thesis: string;
    earningsInflection: string;
    scenarioAsymmetry: Partial<Record<'bear' | 'base' | 'bull', { intrinsic: Num; upside: Num }>>;
    counterThesis: string;
    nextCheck: string;
  };
  gaps: Record<string, unknown>[];
  policy: {
    personalizedTradeInstruction: false;
    scenarioProbabilitiesPublished: false;
    statusVocabulary: InvestmentDimensionStatus[];
  };
}

// ── ReportModel / Section / Overview (마이그레이션 안전 - 신규 전부 optional) ──
export type ReportSourceEngine =
  | 'analysis' | 'credit' | 'quant' | 'industry' | 'macro' | 'story' | 'valuation' | 'forecast';

export interface ReportSection {
  key: string;
  title: string;
  sourceEngine: ReportSourceEngine;
  blocks: ReportBlock[];
  emph?: boolean;
  arcStep?: number; // 아크 위치 0..10 (PRD §3). 부재 시 기존 평면 순서.
}

export interface ReportModel {
  stockCode: string;
  corpName: string;
  asOf: string;
  dataBasis: string;
  industry?: string;
  perspectiveKey: string;
  perspectiveLabel: string;
  conclusion: string;
  headlineKpis: { label: string; value: string }[];
  narrativeOverview: string;
  keyFindings: { key: string; finding: string; sourceEngine: ReportSourceEngine }[];
  sections: ReportSection[];
  closing: { label: string; engine: ReportSourceEngine; line: string }[];
  provenance: { engines: Record<string, { label: string; sections: number; blocks: number }>; status?: string; note: string };
  assumptionsNote: string;
  qualityLabel: 'verified' | 'conditional' | 'partial' | 'strong' | 'moderate' | 'weak';
  focusQuestions: string[];
  pending?: boolean;
  // 신규 (전부 optional - 구 렌더러 무회귀)
  thesis?: Thesis; // narrativeOverview(string) 의 구조화 후계. 둘 다 채우면 thesis 우선.
  schemaVersion?: number; // 1=레거시, 2=pro 아크. 부재=1.
  lensProducts?: LensProductBundle; // 엔진별 독립 판단 원문. 통합 점수 없음.
  lensSummary?: LensSummaryRow[]; // 제품 직접 필드의 표시용 투영.
  investmentDecision?: InvestmentDecision; // 투자 전용 9차원 판단·결손·정책 계약.
  gaps?: Record<string, unknown>[];
}

export interface OverviewModel {
  corpName: string;
  stockCode: string;
  asOf: string;
  dataBasis: string;
  industry?: string;
  thesis: string; // 기존 string 유지(구 렌더러 폴백) - 항상 채움
  thesisStruct?: Thesis; // 신규 구조화 (pro 렌더러 우선)
  takes: { key: string; label: string; line: string; engine: ReportSourceEngine }[];
}

export interface ReportSkipped { skipped: true; stockCode: string; reason: string }
export type ReportResult = ReportModel | ReportSkipped;
export function isSkipped(r: ReportResult): r is ReportSkipped {
  return (r as ReportSkipped).skipped === true;
}
