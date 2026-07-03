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

export interface ExpectationsPort {
	/** 미발간/조회 실패 = null (패널이 빈상태 문구로 정직 표기). */
	getScorecard(): Promise<ExpectationScorecard | null>;
}
