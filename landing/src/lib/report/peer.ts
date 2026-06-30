// 보고서 전용 동종업종 백분위 · build.ts 에서 격리(순수, NEVER-CLAIM 안전: peer 좌표지 목표가 아님).
// pctRank/industryTopPct/distFromValues 는 모듈 내부, IndDist/PeerCtx/ValPeer·topPctLabel·valuationPos·buildValPeer·peerCompareTable 공개.
import type { Num, ValuationSnapshot, IndexRow } from '@dartlab/ui-contracts';
import type { ReportBlock } from './model';

// ── 동종업종 백분위 (industryStats.json 분포) · peer 좌표(목표가 아님, NEVER-CLAIM 안전) ──
export interface IndDist {
	n: number;
	p10: number;
	p25: number;
	median: number;
	p75: number;
	p90: number;
	mean: number;
	std: number;
}
export interface PeerCtx {
	name: string; // 업종명(한글)
	count: number; // 업종 종목 수
	dist: Record<string, IndDist | null>;
}
// 분포 앵커(p10..p90) 선형보간으로 값의 백분위 순위(0~100, 업종 내 *이하* 비율) 추정.
function pctRank(v: number, d: IndDist | null | undefined): number | null {
	if (!d) return null;
	const pts: [number, number][] = ([[10, d.p10], [25, d.p25], [50, d.median], [75, d.p75], [90, d.p90]] as [number, number][]).filter((x) => x[1] != null && Number.isFinite(x[1]));
	if (pts.length < 2) return null;
	if (v <= pts[0][1]) return Math.max(1, pts[0][0] / 2);
	if (v >= pts[pts.length - 1][1]) return Math.min(99, (pts[pts.length - 1][0] + 100) / 2);
	for (let i = 1; i < pts.length; i++) {
		const [r0, x0] = pts[i - 1];
		const [r1, x1] = pts[i];
		if (v <= x1) return x1 === x0 ? r1 : r0 + ((r1 - r0) * (v - x0)) / (x1 - x0);
	}
	return 95;
}
// '상위 X%' · goodHigh 면 높을수록 상위, 아니면(부채비율 등) 낮을수록 상위. tail = 분포 꼬리(정밀 순위 추정불가).
function industryTopPct(v: Num, d: IndDist | null | undefined, goodHigh: boolean): { top: number; median: number; tail: boolean; n: number } | null {
	if (v == null || !Number.isFinite(v) || !d) return null;
	const pr = pctRank(v as number, d);
	if (pr == null) return null;
	const top = Math.round(Math.max(1, Math.min(99, goodHigh ? 100 - pr : pr)));
	return { top, median: d.median, tail: top <= 6 || top >= 94, n: d.n };
}
// 꼬리 정직 라벨 · p90 초과/p10 미만은 "상위 10% 이내"로(거짓 정밀 회피, 기관 지적).
export function topPctLabel(r: { top: number; tail: boolean }): string {
	if (r.tail) return r.top <= 6 ? '상위 10% 이내' : '하위 10% 이내';
	return `상위 ${r.top}%`;
}
// 값 목록 → 분포 통계(p10/p25/median/p75/p90/mean/std/n). 빌더 buildIndustryMap.py `_distribution` 미러.
// 표본 < 3 이면 null(의미 없는 분포 · honest-n 게이트). 동종 밸류에이션 분포를 조회 시점에 계산.
function distFromValues(vs: Num[]): IndDist | null {
	const c = vs.filter((v): v is number => v != null && Number.isFinite(v)).sort((a, b) => a - b);
	const n = c.length;
	if (n < 3) return null;
	const q = (p: number): number => {
		if (n === 1) return c[0];
		const pos = p * (n - 1);
		const lo = Math.floor(pos);
		const hi = Math.min(lo + 1, n - 1);
		return c[lo] * (1 - (pos - lo)) + c[hi] * (pos - lo);
	};
	const mean = c.reduce((s, x) => s + x, 0) / n;
	const std = Math.sqrt(c.reduce((s, x) => s + (x - mean) ** 2, 0) / n);
	const r2 = (x: number) => Math.round(x * 100) / 100;
	return { n, p10: r2(q(0.1)), p25: r2(q(0.25)), median: r2(q(0.5)), p75: r2(q(0.75)), p90: r2(q(0.9)), mean: r2(mean), std: r2(std) };
}
// 밸류에이션 위치 · PER/PBR 분포 내 좌표. 높을수록 시장이 '더 비싸게' 매긴 것(고평가/매수 판단 아님).
// 꼬리(p90↑/p10↓)는 거짓 정밀 회피로 '상위/하위 10% 이내'. 중앙값 위=비싼 쪽, 아래=싼 쪽.
export function valuationPos(v: Num, d: IndDist | null | undefined): { label: string; n: number } | null {
	if (v == null || !Number.isFinite(v) || !d) return null;
	const pr = pctRank(v as number, d);
	if (pr == null) return null;
	const tail = pr >= 94 || pr <= 6;
	const expensive = (v as number) >= d.median;
	const topExp = Math.round(Math.max(1, Math.min(99, 100 - pr)));
	const botCheap = Math.round(Math.max(1, Math.min(99, pr)));
	const label = expensive
		? tail
			? '업종 상위 10% 이내 (비싼 쪽)'
			: `업종 상위 ${topExp}% (비싼 쪽)`
		: tail
			? '업종 하위 10% 이내 (싼 쪽)'
			: `업종 하위 ${botCheap}% (싼 쪽)`;
	return { label, n: d.n };
}
// 동종 밸류에이션 컨텍스트 · 주체 PER/PBR + 업종 분포(런타임 산출). market 관점이 소비.
export interface ValPeer {
	industryName: string;
	per: { v: Num; dist: IndDist | null };
	pbr: { v: Num; dist: IndDist | null };
}
// valuation 스냅샷(전 종목 per/pbr) + search-index 업종 멤버십 → 주체 per/pbr + 동종 분포(조회 시점).
// 같은 업종(search-index industry) 종목들의 per/pbr 을 모아 분포화 · peer n<3 또는 분포 둘 다 null 이면 생략.
export function buildValPeer(snap: ValuationSnapshot | null, universe: IndexRow[] | null, code: string, industry: string | undefined, industryName: string | undefined): ValPeer | null {
	if (!snap || !industry || !universe) return null;
	// 동종 멤버십 = 같은 업종, *주체 자신 제외*('대비'는 나머지 동종 대비 · 작은 업종·극단값이 자기 분포를 끌어올려 위치를 덜 극단으로 보이게 하는 self-inclusion 편향 차단).
	const peers = universe.filter((r) => r.industry === industry && r.stockCode !== code).map((r) => r.stockCode);
	if (peers.length < 3) return null;
	// per/pbr 은 양수만 분포 편입 · per 는 네이버가 적자사 null, pbr 음수(자본잠식)는 좌측 꼬리를 오염시켜 위기기업을 '싼 쪽'으로 오표시하므로 명시 제외.
	const pos = (v: Num): Num => (v != null && Number.isFinite(v) && (v as number) > 0 ? v : null);
	const subj = snap[code] ?? null;
	const per = { v: pos(subj?.per ?? null), dist: distFromValues(peers.map((c) => pos(snap[c]?.per ?? null))) };
	const pbr = { v: pos(subj?.pbr ?? null), dist: distFromValues(peers.map((c) => pos(snap[c]?.pbr ?? null))) };
	if (!per.dist && !pbr.dist) return null;
	return { industryName: industryName ?? industry, per, pbr };
}

// 동종업종 비교표 · 지표 × (회사값·업종 중앙값·업종 내 위치). 백분위는 *측정 좌표*이지 투자판단 아님.
export function peerCompareTable(
	rows: { label: string; value: Num; key: string; goodHigh: boolean; fmt: (v: Num) => string }[],
	peer: PeerCtx
): { block: ReportBlock; phrases: { label: string; top: number; tail: boolean; median: string; goodHigh: boolean; valFmt: string; n: number }[] } | null {
	const data: Record<string, string>[] = [];
	const phrases: { label: string; top: number; tail: boolean; median: string; goodHigh: boolean; valFmt: string; n: number }[] = [];
	let maxN = 0;
	for (const r of rows) {
		if (r.value == null || !Number.isFinite(r.value)) continue;
		const d = peer.dist[r.key];
		const rank = industryTopPct(r.value, d, r.goodHigh);
		data.push({ 지표: r.label, 회사값: r.fmt(r.value), '업종 중앙값': d ? r.fmt(d.median) : '-', '업종 내 위치': rank ? topPctLabel(rank) : '-' });
		if (rank) { phrases.push({ label: r.label, top: rank.top, tail: rank.tail, median: r.fmt(d!.median), goodHigh: r.goodHigh, valFmt: r.fmt(r.value), n: rank.n }); maxN = Math.max(maxN, rank.n); }
	}
	if (!data.length) return null;
	return { block: { type: 'table', label: `동종업종 비교 · ${peer.name} (지표별 유효 표본 n≈${maxN}사, 연간·결손 제외)`, snapshot: true, data }, phrases };
}
