// 펀더게이트 PIT 시계열 · gov/fundamental-gate.parquet 행 + 캔들 날짜 → 봉별 Piotroski(계단).
// terminal-strategy-lab W2 (간판②). "재무 튼튼할 때만 진입"(Piotroski≥6 등) · 가격 백테스터가 못 하는 panel moat.
// ★공시일(rceptDt) 이후 봉부터 그 회계연도 값, 첫 공시 전 null(진입 미평가 = look-ahead 0). 계단(매끈한 선 금지).
// 차별 = "재무를 쓴다"(TradingView request.financial 존재)가 아니라 DART 계정정규화 + 학술팩터 사전구현 + PIT 정직 라벨.

export interface GateRow {
	rceptDt: string; // YYYYMMDD · 공시일(rcept_no[:8], PIT 앵커)
	piotroski: number; // 0~9
}

/** 캔들 날짜(YYYYMMDD) → 봉별 Piotroski 값(계단, PIT). rceptDt ≤ 봉날짜인 가장 최근 공시값, 첫 공시 전 null.
 *  candleDatesYmd·rows 정렬 가정 없음(내부 정렬). 공시일 이후만 채워 look-ahead 구조 차단. */
export function buildGateSeries(candleDatesYmd: string[], rows: GateRow[]): (number | null)[] {
	const sorted = [...rows].sort((a, b) => a.rceptDt.localeCompare(b.rceptDt));
	const out: (number | null)[] = new Array(candleDatesYmd.length).fill(null);
	let ri = 0;
	let cur: number | null = null;
	for (let i = 0; i < candleDatesYmd.length; i++) {
		const d = candleDatesYmd[i];
		while (ri < sorted.length && sorted[ri].rceptDt <= d) {
			cur = sorted[ri].piotroski;
			ri++;
		}
		out[i] = cur;
	}
	return out;
}

/** 룰에 fundGate 조건이 있나 · 게이트 시계열 로드 필요 여부(UI 가드). */
export function ruleUsesGate(rule: { entry: { left: string }[]; exit: { left: string }[] }): boolean {
	return [...rule.entry, ...rule.exit].some((c) => c.left === 'fundGate');
}
