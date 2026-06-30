// 정량재무제표 다이얼로그 데이터 계약 · dart/finance(공식 OpenDART) parquet 을 DuckDB-WASM 으로 pivot 한 결과.

export type FinanceKind = 'IS' | 'BS' | 'CF' | 'CIS' | 'SCE'; // 손익·재무상태·현금흐름·포괄손익·자본변동
export type FinanceFreq = 'annual' | 'quarter' | 'cumulative'; // 연간 / 분기(단독) / 누적(YTD)
export type FinanceScope = 'CFS' | 'OFS'; // 연결 / 별도

export interface FinanceStmtRow {
	accountId: string; // account_id (기간 정합 pivot 키)
	label: string; // account_nm (표시)
	ord: number; // 재무제표 표시순서
	depth: number; // 들여쓰기 깊이(순수 구조) · IS 본류(매출액~당기순이익) 균일 1, 리프 2+. SSOT level mirror
	isTotal: boolean; // 총계 강조(굵게+상단보더). depth 와 분리 · IS 당기순이익/총포괄손익은 depth 1 이어도 true
	values: Record<string, number | null>; // period → 금액(원). null = 해당기간 미보고
}

export interface FinanceStatement {
	kind: FinanceKind;
	scope: FinanceScope;
	freq: FinanceFreq;
	periods: string[]; // 최신좌측 (YYYY 또는 YYYYQn)
	rows: FinanceStmtRow[];
	unit: string; // 'KRW'(원) / 'USD'
}

// statement 별 가용 빈도 · BS(시점)는 누적 없음, SCE 는 연간 위주.
export const FREQ_BY_KIND: Record<FinanceKind, FinanceFreq[]> = {
	IS: ['annual', 'quarter', 'cumulative'],
	CIS: ['annual', 'quarter', 'cumulative'],
	CF: ['annual', 'cumulative'],
	BS: ['annual', 'quarter'],
	SCE: ['annual', 'cumulative']
};

export const KIND_LABELS: Record<FinanceKind, string> = {
	IS: '손익계산서',
	BS: '재무상태표',
	CF: '현금흐름표',
	CIS: '포괄손익',
	SCE: '자본변동표'
};
export const FREQ_LABELS: Record<FinanceFreq, string> = { annual: '연간', quarter: '분기', cumulative: '누적' };
export const SCOPE_LABELS: Record<FinanceScope, string> = { CFS: '연결', OFS: '별도' };

// 단위 스케일 · 큰 금액 가독성. 백만원 기본(대기업 표준).
export type FinanceUnit = '원' | '백만' | '억';
export const UNIT_DIVISORS: Record<FinanceUnit, number> = { 원: 1, 백만: 1e6, 억: 1e8 };
export const UNIT_LABELS: Record<FinanceUnit, string> = { 원: '원', 백만: '백만원', 억: '억원' };

// 자본변동표(SCE) · 변동유형(행) × 자본구성요소(열) × period 3D. 기간 1개를 골라 2D matrix 로 렌더.
export interface SceRow {
	label: string; // 변동유형 (account_nm) · 기초자본·당기순이익·배당·자기주식취득 등
	ord: number;
	values: Record<string, number | null>; // 자본구성요소 → 금액
}
export interface SceMatrixData {
	scope: FinanceScope;
	periods: string[]; // 가용 연도 (최신좌측)
	components: string[]; // 자본구성요소 열 (자본금→…→자본총계 순)
	byPeriod: Record<string, SceRow[]>; // period → 변동유형 행
	unit: string;
}
