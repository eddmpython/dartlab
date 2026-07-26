// 스캔 계약 - duckSql.CompanyChange 승격 (census A-10) + 소스 공급 포트 (02 §3.5).
// 원칙: 쿼리 실행 엔진(duckdb-wasm)은 surface 내부 구현 detail - port 는 데이터 소스 공급과 저장만.
// 진화 예약: 서버측 질의가 필요해지면 ScanPort.query() 승격 - 계약 개정 작업 단위로만 (02 §3.5).

export interface CompanyChange {
	fromPeriod: string;
	toPeriod: string;
	sectionTitle: string;
	changeType: string; // 'numeric' | 'structural' (parquet 실값)
	preview: string | null;
}

export type ScanSpecOp =
	| '>'
	| '>='
	| '<'
	| '<='
	| '=='
	| '!='
	| 'between'
	| 'contains'
	| 'exists'
	| 'not_exists';

export interface ScanSpecCondition {
	field: string;
	op: ScanSpecOp;
	value?: unknown;
	unit?: string;
	limit?: number;
}

export interface ScanDefineNode {
	op?: 'add' | 'sub' | 'mul' | 'div' | 'abs' | 'log' | 'clip' | 'winsorize' | 'yoy' | 'cagr' | 'slope' | 'mean' | 'min' | 'max' | 'percentile' | 'zscore';
	field?: string;
	left?: string | number;
	right?: string | number;
	years?: number;
	by?: 'industry';
	min?: number;
	max?: number;
	lower?: number;
	upper?: number;
}

export interface ScanScreenSpec {
	define?: Record<string, ScanDefineNode>;
	where?: ScanSpecCondition[];
	any?: ScanSpecCondition[];
	select?: string[];
	sort?: { field: string; desc?: boolean };
	limit?: number;
	asOf?: string;
}

export interface ScanScreenDefinition {
	id: string;
	version: number;
	schemaVersion: number;
	market: string;
	notify: boolean;
	title: string;
	tags: string[];
	evidence: string;
	spec: ScanScreenSpec;
}

/** 잠정 표면 - 단계-8(ScanSurface 추출) 착수 전 02 개정으로 확정 (07 원장 entry 의무). */
export interface ScanTableSource {
	id: string;
	label: string;
	url: string; // public = static/HF parquet, local = 로컬 서버 parquet URL
	kind: 'parquet';
}

/** 잠정 표면 - 단계-8 전 확정. */
export interface ScanPreset {
	id: string;
	label: string;
	payload: Record<string, unknown>;
}

export interface ScanPort {
	/** 회사 단위 변경 피드 - 해당 없음은 []. */
	changes(code: string, limit?: number): Promise<CompanyChange[]>;
	listTableSources(): Promise<ScanTableSource[]>;
	getPresets(): Promise<ScanPreset[]>;
	savePreset(preset: ScanPreset): Promise<void>;
}
