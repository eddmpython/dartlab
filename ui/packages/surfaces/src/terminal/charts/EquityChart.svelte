<script lang="ts">
	// 자산곡선 + 언더워터(낙폭) · 실측 px 좌표계로 preserveAspectRatio="none" 왜곡 박멸.
	// y niceTicks 가로 그리드 · x 연경계 세로 그리드 · 두 패널 x 공유 · 크로스헤어 + 호버 값박스.
	// 데이터 파생(eqRange·dd·splitFrac)은 BacktestDialog 가 계산해 props 로 전달(산출 동치, 회귀 0).
	// 모달은 고정폭이라 ResizeObserver 불필요 · bind:clientWidth 만으로 충분. 조합 곡선은 .bdCombo 배너 담당(여기 미표시).
	import type { Lang } from '../lib/types';
	import { niceTicks, yearTicks, nearestIdx } from './chartFrame';

	interface Props {
		eq: number[]; // 전략 계좌가치(시작≈100), 평가창 non-null 슬라이스
		bhq: number[]; // 보유(B&H) 동일 길이
		dd: number[]; // 낙폭(≤0) 동일 길이
		ts: string[]; // YYYYMMDD, eq 와 동일 인덱스(평가창 슬라이스)
		splitFrac: number | null; // OOS 분할 위치(0..1) · 검증구간 음영
		eqRange: { lo: number; hi: number };
		ddMin: number;
		stratColor?: string; // 포커스 전략 색(STRAT_COLORS) · strip·캔버스 레전드와 색 일치
		lang: Lang;
	}
	let { eq, bhq, dd, ts, splitFrac, eqRange, ddMin, stratColor = '#fbbf24', lang }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	let cw = $state(0);
	let eqSvg: SVGSVGElement | null = $state(null); // 크로스헤어 좌표 기준(테두리 오프셋 제거)
	const AX = { l: 46, r: 14, t: 10, b: 6 };
	const H_EQ = 232;
	const H_DD = 82;
	const n = $derived(eq.length);
	const plotW = $derived(Math.max(120, cw - AX.l - AX.r));
	const plotHeq = H_EQ - AX.t - AX.b;
	const plotHdd = H_DD - AX.t - AX.b;

	const xAt = (i: number) => AX.l + (n < 2 ? 0 : (i / (n - 1)) * plotW);
	const yEq = (v: number) => AX.t + plotHeq * (1 - (v - eqRange.lo) / ((eqRange.hi - eqRange.lo) || 1));
	const yDd = (v: number) => AX.t + plotHdd * (1 - (v - ddMin) / ((0 - ddMin) || 1));

	function linePath(arr: number[], yf: (v: number) => number): string {
		let d = '';
		for (let i = 0; i < arr.length; i++) d += (i ? 'L' : 'M') + xAt(i).toFixed(1) + ',' + yf(arr[i]).toFixed(1);
		return d;
	}
	function areaPath(arr: number[], yf: (v: number) => number): string {
		if (arr.length < 2) return '';
		const y0 = yf(0);
		let d = 'M' + xAt(0).toFixed(1) + ',' + y0.toFixed(1);
		for (let i = 0; i < arr.length; i++) d += 'L' + xAt(i).toFixed(1) + ',' + yf(arr[i]).toFixed(1);
		return d + 'L' + xAt(arr.length - 1).toFixed(1) + ',' + y0.toFixed(1) + 'Z';
	}

	const eqPath = $derived(linePath(eq, yEq));
	const bhPath = $derived(linePath(bhq, yEq));
	const ddPath = $derived(linePath(dd, yDd));
	const ddFill = $derived(areaPath(dd, yDd));
	const yt = $derived(niceTicks(eqRange.lo, eqRange.hi, 5));
	const xt = $derived(yearTicks(ts, 8));
	const base100Y = $derived(eqRange.lo <= 100 && eqRange.hi >= 100 ? yEq(100) : null);
	const splitX = $derived(splitFrac == null ? null : AX.l + splitFrac * plotW);

	let hoverIdx = $state<number | null>(null);
	function onMove(e: PointerEvent) {
		// SVG 자체 rect 기준 · .eqWrap 테두리(1px) 오프셋 제거.
		const r = (eqSvg ?? (e.currentTarget as HTMLElement)).getBoundingClientRect();
		hoverIdx = nearestIdx(e.clientX - r.left, AX.l, plotW, n);
	}
	function onLeave() {
		hoverIdx = null;
	}

	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	const fmtD = (t: string) => (t && t.length >= 8 ? `${t.slice(2, 4)}.${t.slice(4, 6)}.${t.slice(6, 8)}` : '');
	const hv = $derived(
		hoverIdx == null || hoverIdx >= n
			? null
			: { t: ts[hoverIdx] ?? '', s: (eq[hoverIdx] ?? 100) - 100, b: (bhq[hoverIdx] ?? 100) - 100, d: dd[hoverIdx] ?? 0, x: xAt(hoverIdx) }
	);
	const fullW = $derived(AX.l + plotW + AX.r);
	// 툴팁: 우반이면 좌측 배치 + 양끝 클램프(클립 방지)
	const tipLeft = $derived(hv == null ? 0 : Math.max(4, Math.min(hv.x > AX.l + plotW / 2 ? hv.x - 184 : hv.x + 12, fullW - 176)));
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="eqWrap" bind:clientWidth={cw} onpointermove={onMove} onpointerleave={onLeave} role="img" aria-label={T('자산 곡선', 'equity curve')}>
	<!-- 상단: 자산곡선 -->
	<svg class="eqSvg" bind:this={eqSvg} width="100%" height={H_EQ} role="presentation">
		<!-- OOS 검증구간 음영 -->
		{#if splitX != null}
			<rect x={splitX} y="0" width={Math.max(0, AX.l + plotW - splitX)} height={H_EQ} fill="rgba(96,165,250,0.06)" />
			<line x1={splitX} y1="0" x2={splitX} y2={H_EQ} stroke="rgba(96,165,250,0.5)" stroke-width="1" stroke-dasharray="4 3" />
			<text class="ax oos" x={splitX + 4} y={AX.t + 9}>OOS</text>
		{/if}
		<!-- y 그리드 + 우측 %라벨(시작 100 대비) -->
		{#each yt as tick (tick)}
			<line x1={AX.l} y1={yEq(tick)} x2={AX.l + plotW} y2={yEq(tick)} stroke="rgba(139,145,158,0.09)" stroke-width="1" />
			<text class="ax" x={AX.l - 5} y={yEq(tick) + 3} text-anchor="end">{sgn(tick - 100, 0)}%</text>
		{/each}
		<!-- 100 손익분기선 -->
		{#if base100Y != null}
			<line x1={AX.l} y1={base100Y} x2={AX.l + plotW} y2={base100Y} stroke="rgba(139,145,158,0.32)" stroke-width="1" stroke-dasharray="2 3" />
		{/if}
		<!-- x 연경계 세로선 -->
		{#each xt as x (x.idx)}
			<line x1={xAt(x.idx)} y1={AX.t} x2={xAt(x.idx)} y2={H_EQ - AX.b} stroke="rgba(139,145,158,0.06)" stroke-width="1" />
		{/each}
		<!-- B&H(점선) → 전략(승자 굵기강조 금지) -->
		<path d={bhPath} fill="none" stroke="#8b919e" stroke-width="1.4" stroke-dasharray="5 3" />
		<path d={eqPath} fill="none" stroke={stratColor} stroke-width="2" />
		<!-- 크로스헤어 -->
		{#if hv != null}
			<line x1={hv.x} y1={AX.t} x2={hv.x} y2={H_EQ - AX.b} stroke="rgba(200,207,219,0.35)" stroke-width="1" />
			<circle cx={hv.x} cy={yEq(eq[hoverIdx ?? 0] ?? 100)} r="2.6" fill={stratColor} />
			<circle cx={hv.x} cy={yEq(bhq[hoverIdx ?? 0] ?? 100)} r="2.6" fill="#8b919e" />
		{/if}
	</svg>

	<!-- 하단: 언더워터(낙폭) · 상단과 동일 x -->
	<svg class="ddSvg" width="100%" height={H_DD} role="presentation">
		<path d={ddFill} fill="rgba(240,97,111,0.16)" stroke="none" />
		<path d={ddPath} fill="none" stroke="#f0616f" stroke-width="1.4" />
		<text class="ax dn" x={AX.l - 5} y={yDd(ddMin) + 3} text-anchor="end">{ddMin.toFixed(0)}%</text>
		{#each xt as x (x.idx)}
			<line x1={xAt(x.idx)} y1={AX.t} x2={xAt(x.idx)} y2={H_DD - AX.b} stroke="rgba(139,145,158,0.06)" stroke-width="1" />
		{/each}
		{#if hv != null}
			<line x1={hv.x} y1={AX.t} x2={hv.x} y2={H_DD - AX.b} stroke="rgba(200,207,219,0.35)" stroke-width="1" />
			<circle cx={hv.x} cy={yDd(dd[hoverIdx ?? 0] ?? 0)} r="2.6" fill="#f0616f" />
		{/if}
	</svg>

	<!-- x 연도 라벨 -->
	<div class="eqXax">
		{#each xt as x (x.idx)}<span class="eqXlab" style={`left:${xAt(x.idx)}px`}>{x.label}</span>{/each}
	</div>

	<!-- 범례 -->
	<div class="eqLeg">
		<span class="lk" style={`border-top-color:${stratColor}`}></span>{T('전략', 'strategy')}
		<span class="lk bh"></span>{T('보유(B&H)·동일비용', 'B&H · same costs')}
		<span class="lk ddk"></span>{T('낙폭', 'drawdown')}
	</div>

	<!-- 호버 값박스 -->
	{#if hv != null}
		<div class="eqTip" style={`left:${tipLeft}px`}>
			<div class="eqTipD">{fmtD(hv.t)}</div>
			<div class="eqTipR"><i style={`color:${stratColor}`}>{T('전략', 'strat')}</i><b class={hv.s >= 0 ? 'u' : 'd'}>{sgn(hv.s)}%</b></div>
			<div class="eqTipR"><i style="color:#8b919e">{T('보유', 'B&H')}</i><b class={hv.b >= 0 ? 'u' : 'd'}>{sgn(hv.b)}%</b></div>
			<div class="eqTipR"><i>{T('초과', 'excess')}</i><b class={hv.s - hv.b >= 0 ? 'u' : 'd'}>{sgn(hv.s - hv.b)}%p</b></div>
			<div class="eqTipR"><i>{T('낙폭', 'DD')}</i><b class="d">{hv.d.toFixed(1)}%</b></div>
		</div>
	{/if}
</div>

<style>
	.eqWrap {
		position: relative;
		width: 100%;
		background: rgba(8, 11, 18, 0.55);
		border: 1px solid var(--dl-line, #1b2130);
		border-radius: 5px;
		padding: 2px 0 4px;
		cursor: crosshair;
	}
	.eqSvg,
	.ddSvg {
		display: block;
		width: 100%;
	}
	.ax {
		font-family: var(--dl-font-mono, monospace);
		font-size: 11px;
		fill: var(--dimmer, #5b6573);
		font-variant-numeric: tabular-nums;
	}
	.ax.dn {
		fill: rgba(240, 97, 111, 0.85);
	}
	.ax.oos {
		fill: #60a5fa;
		text-anchor: start;
	}
	.eqXax {
		position: relative;
		height: 15px;
		margin: 1px 0 0;
	}
	.eqXlab {
		position: absolute;
		transform: translateX(-50%);
		font-family: var(--dl-font-mono, monospace);
		font-size: 11px;
		color: var(--dimmer, #5b6573);
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.eqLeg {
		display: flex;
		align-items: center;
		gap: 5px;
		font-size: 11px;
		color: #aeb6c2;
		padding: 3px 10px 1px;
	}
	.eqLeg .lk {
		display: inline-block;
		width: 15px;
		height: 0;
		border-top-width: 2px;
		border-top-style: solid;
		border-top-color: #8b919e;
		margin: 0 1px 0 9px;
	}
	.eqLeg .lk:first-child {
		margin-left: 0;
	}
	.eqLeg .lk.bh {
		border-top-color: #8b919e;
		border-top-style: dashed;
	}
	.eqLeg .lk.ddk {
		border-top-color: #f0616f;
	}
	.eqTip {
		position: absolute;
		top: 6px;
		width: 172px;
		background: var(--dl-bg-raised, #0e141f);
		border: 1px solid var(--dl-line-strong, #2a3142);
		border-radius: 4px;
		padding: 5px 8px;
		pointer-events: none;
		font-family: var(--dl-font-mono, monospace);
		font-variant-numeric: tabular-nums;
		z-index: 3;
	}
	.eqTipD {
		font-size: 11px;
		color: var(--dl-ink, #c8cfdb);
		margin-bottom: 3px;
		font-weight: 700;
	}
	.eqTipR {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		font-size: 11px;
	}
	.eqTipR i {
		font-style: normal;
		color: var(--dim, #8b94a3);
	}
	.eqTipR b {
		font-weight: 700;
	}
	.eqTipR .u {
		color: var(--up, #34d399);
	}
	.eqTipR .d {
		color: var(--dn, #f0616f);
	}
</style>
