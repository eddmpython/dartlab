// 보고서 전용 순수 시계열 해석 헬퍼 · build.ts 에서 격리(format.ts·market.ts 동일 패턴).
// coverage/detectOneOff/finite/readTrend/cagr: Num[] → 값·문장·플래그. 모듈 상태·클로저 0(behavior-preserving 이동).
import type { Num } from '@dartlab/ui-contracts';

// 금액 표(단일 단위 스케일) · 빈 행 자동 제거. 유효 행 0이면 null.
export function coverage(values: Num[]): number {
	return values.filter((v) => v != null && Number.isFinite(v)).length;
}

// 일회성 스파이크 탐지 · 한 칸이 본업 추세를 압도(중앙값 4배 초과 & 절대 60 초과)하면 {연도,값}.
// 값은 *건드리지 않고*(정직), 본문에 맥락 각주만 붙인다(NAVER FY21 순이익률 241.7% 등).
export function detectOneOff(values: Num[], yearCols: string[]): { year: string; value: number } | null {
	const pairs = values
		.map((v, i) => ({ v, year: yearCols[i] }))
		.filter((p): p is { v: number; year: string } => p.v != null && Number.isFinite(p.v));
	if (pairs.length < 3) return null;
	const absSorted = pairs.map((p) => Math.abs(p.v)).sort((a, b) => a - b);
	const med = absSorted[Math.floor(absSorted.length / 2)] || 1;
	for (const p of pairs) {
		if (Math.abs(p.v) > 60 && Math.abs(p.v) > med * 4) return { year: p.year, value: p.v };
	}
	return null;
}

// ── 시계열 해석 헬퍼(사전적 정의가 아니라 *이 회사 값*을 읽어 주는 문장) ──────
export function finite(values: Num[]): number[] {
	return values.filter((v): v is number => v != null && Number.isFinite(v));
}

// 추세 1문장 · risingIsGood=false 면 상승을 '약화'로(부채비율 등 역방향 지표).
// 변동성(부호 전환 빈도+진폭)·장기방향·직전해방향을 합쳐 회사별 reading 을 만든다.
export function readTrend(values: Num[], risingIsGood = true): string | null {
	const v = finite(values);
	if (v.length < 3) return null;
	const first = v[0];
	const last = v[v.length - 1];
	const prev = v[v.length - 2];
	let flips = 0;
	for (let i = 2; i < v.length; i++) if ((v[i - 1] - v[i - 2]) * (v[i] - v[i - 1]) < 0) flips++;
	const span = Math.max(...v) - Math.min(...v);
	const base = Math.abs(v.reduce((s, x) => s + x, 0) / v.length) || 1;
	const volatile = flips >= Math.max(2, Math.ceil((v.length - 2) * 0.6)) && span > base * 0.4;
	const eps = 0.02;
	const recentUp = last > prev * (1 + eps);
	const recentDown = last < prev * (1 - eps);
	const netUp = last > first * (1 + eps);
	const netDown = last < first * (1 - eps);
	const word = (up: boolean) => ((up ? risingIsGood : !risingIsGood) ? '개선' : '약화');
	if (volatile) return '여러 해에 걸쳐 등락이 커 일정한 추세를 잡기 어렵습니다';
	if (netUp && recentUp) return `여러 해에 걸쳐 ${word(true)}되는 흐름입니다`;
	if (netDown && recentDown) return `여러 해에 걸쳐 ${word(false)}되는 흐름입니다`;
	if (recentUp && netDown) return `장기적으로는 낮아졌으나 직전 해 반등했습니다`;
	if (recentDown && netUp) return `장기적으로는 높아졌으나 직전 해 주춤했습니다`;
	if (netUp) return `완만히 ${word(true)}되는 흐름입니다`;
	if (netDown) return `완만히 ${word(false)}되는 흐름입니다`;
	return '대체로 비슷한 수준을 유지했습니다';
}

// 연평균 성장률(CAGR, %) · 첫·끝 모두 양수일 때만(음수 시작은 CAGR 무의미 → null).
export function cagr(values: Num[]): number | null {
	const v = finite(values).filter((x) => x > 0);
	if (v.length < 2) return null;
	return (Math.pow(v[v.length - 1] / v[0], 1 / (v.length - 1)) - 1) * 100;
}
