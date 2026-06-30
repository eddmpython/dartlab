// 거래순서 몬테카를로(경로운) · 실현 거래 수익률만 순서 재배열해 최종수익·최대낙폭의 백분위 분포.
// 정직: 예측 아님(미래 분포 가정 0), "한 경로는 한 번의 운"을 보여줄 뿐. 표본<15면 null(거짓 좁은 밴드 금지).
// 순수함수(브라우저 앱 코드 · Math.random 허용, 워크플로 스크립트 아님). BacktestReport 가 결과 거래로 호출.

export interface ShuffleCone {
	p5: number; // 최종수익 5분위 (%)
	p50: number; // 중앙
	p95: number; // 95분위
	mddP95: number; // 최악 5% 시나리오의 최대낙폭 (%, ≤0) · 자본 사이징 기준
	n: number; // 거래 수
}

/** 실현 거래 수익률(%) 순서 재배열 부트스트랩. 표본<15 → null. */
export function tradeShuffleCone(retsPct: number[], iters = 2000): ShuffleCone | null {
	const rets = retsPct.filter((r) => Number.isFinite(r));
	if (rets.length < 15) return null;
	const terminals: number[] = [];
	const mdds: number[] = [];
	for (let k = 0; k < iters; k++) {
		const order = rets.slice();
		for (let i = order.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			const t = order[i];
			order[i] = order[j];
			order[j] = t;
		}
		let eq = 1;
		let peak = 1;
		let mdd = 0;
		for (const r of order) {
			eq *= 1 + r / 100;
			if (eq > peak) peak = eq;
			const dd = eq / peak - 1;
			if (dd < mdd) mdd = dd;
		}
		terminals.push((eq - 1) * 100);
		mdds.push(mdd * 100);
	}
	terminals.sort((a, b) => a - b);
	mdds.sort((a, b) => a - b);
	const q = (arr: number[], p: number) => arr[Math.max(0, Math.min(arr.length - 1, Math.floor(p * (arr.length - 1))))];
	return { p5: q(terminals, 0.05), p50: q(terminals, 0.5), p95: q(terminals, 0.95), mddP95: q(mdds, 0.05), n: rets.length };
}
