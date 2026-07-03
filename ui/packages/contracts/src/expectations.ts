// 기대치 격자(Expectation Grid) 성적표 계약 · HF expectations/scorecard.json 의 형.
// 원장 정본 = HF expectations/ (append-only) · 산출 = dartlab.simulate.expectationCycle.buildScorecard.
// 표시 계약: verified=false 그룹은 성과 숫자 렌더링 금지(고정 '미검증' 라벨만) · live/backfill 혼합 금지.

export interface ExpectationGroupCalibration {
	n: number;
	verified: boolean;
	errorRows?: number;
	coverage90?: number;
	coverage50?: number;
	meanPit?: number;
	meanCrps?: number;
	meanSkill?: number | null;
	meanBrier?: number;
	nDirection?: number;
}

export interface ExpectationScorecard {
	schemaVersion: number;
	generatedAt: string;
	displayPolicy: string;
	totals: { issued: number; scored: number; unscored: number; errorRows: number };
	/** key = `{domain}.{variable}.h{horizon}.{live|backfill}` */
	groups: Record<string, ExpectationGroupCalibration>;
}

/** 원장 발행 행 (expectations_{yyyy}.parquet 1행 · quantiles/direction 은 파싱된 형태). */
export interface ExpectationRow {
	expectationId: string;
	domain: string; // "macro" | "revenue" | "earnings" | "credit" | "price"
	variable: string; // 예 "KR.CPI" · "005930.revenue"
	unit: string;
	freq: string;
	horizon: number;
	targetPeriod: string;
	issuedAt: string;
	issuedLive: boolean;
	kind: string; // "quantiles" | "direction"
	quantiles: Record<number, number> | null;
	direction: { prob: number; predicted: string; issuePrice?: number; fromGrade?: string } | null;
	warnings: string[];
}

/** 원장 채점 행 (scores_{yyyy}.parquet 1행). */
export interface ExpectationScoreRow {
	expectationId: string;
	scoredAt: string;
	actual: string | null;
	coverageHit90: boolean | null;
	coverageHit50: boolean | null;
	skill: number | null;
	brier: number | null;
	error: string | null;
}

/** E-3표 정렬 뷰 행 (estimateStatements.parquet). 매핑·라벨·순서 = 라이브러리 SSOT
 * (dartlab.simulate.estimateStatements). 표면은 rowKey 매칭 + 렌더만 한다. value 단위 = 원. */
export interface EstimateStatementRow {
	code: string;
	targetPeriod: string; // "FY2026"
	quantile: number; // 25 | 50 | 75
	statement: string; // "IS" | "BS" | "CF"
	rowKey: string; // 재무제표 표시 계약 정본 키 (예 "revenue", "costOfSales")
	labelKr: string;
	labelEn: string;
	sortOrder: number;
	value: number;
	parentId: string;
}

export interface ExpectationsPort {
	/** 미발간/조회 실패 = null (패널이 빈상태 문구로 정직 표기). */
	getScorecard(): Promise<ExpectationScorecard | null>;
	/** 라이브 발행 행 + 채점 행 (현재 연도 shard). 미발간 = null. */
	getLedger(): Promise<{ expectations: ExpectationRow[]; scores: ExpectationScoreRow[] } | null>;
	/** 한 회사의 E-3표 정렬 뷰 행 (라이브 발행분). 미발행 회사 = 빈 배열, 뷰 미발간 = null. */
	getEstimateStatements(code: string): Promise<EstimateStatementRow[] | null>;
}
