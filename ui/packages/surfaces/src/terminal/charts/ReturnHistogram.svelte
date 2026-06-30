<script lang="ts">
	// 거래별 수익률 분포 히스토그램 · QuantStats·pyfolio·QuantConnect 공통. Sharpe·평균이 가리는 꼬리(skew)·치우침을 드러냄.
	// 높은 평균이라도 왼쪽 긴 꼬리(드문 큰 손실)면 다른 베팅 · 막대 색은 손익분기(0) 기준 빨강/초록, 평균선 점선.
	// argmax 강조 없음(사실 분포만) · 실측 px 좌표 · niceTicks. 빈 도수 0 막대 유지(거짓 연속 금지).
	import type { Lang } from '../lib/types';
	import { niceTicks } from './chartFrame';

	interface Props {
		rets: number[]; // 거래별 실현 수익률 % (또는 월별 수익률)
		lang: Lang;
		unitLabel?: string; // x축 의미(기본: 거래 수익률)
	}
	let { rets, lang, unitLabel }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	const mean = $derived(rets.length ? rets.reduce((s, v) => s + v, 0) / rets.length : 0);

	// 빈 경계 · [lo,hi] 를 nice step 으로 잡고 0 이 경계에 오도록 정렬(손익 분리 명확).
	const bins = $derived.by(() => {
		if (rets.length < 2) return null;
		let lo = Math.min(...rets);
		let hi = Math.max(...rets);
		if (hi - lo < 1e-6) { lo -= 1; hi += 1; }
		const ticks = niceTicks(lo, hi, 8);
		const step = ticks.length >= 2 ? ticks[1] - ticks[0] : (hi - lo) / 8 || 1;
		const start = Math.floor(lo / step) * step;
		const end = Math.ceil(hi / step) * step;
		const k = Math.max(1, Math.round((end - start) / step));
		const counts = new Array(k).fill(0);
		for (const v of rets) {
			let bi = Math.floor((v - start) / step);
			if (bi < 0) bi = 0;
			if (bi >= k) bi = k - 1;
			counts[bi]++;
		}
		return { start, step, k, counts, maxCount: Math.max(...counts) };
	});

	let cw = $state(0);
	const AX = { l: 30, r: 14, t: 12, b: 22 };
	const H = 188;
	const plotW = $derived(Math.max(120, cw - AX.l - AX.r));
	const plotH = H - AX.t - AX.b;

	const xAt = (v: number) => {
		if (!bins) return AX.l;
		const span = bins.step * bins.k || 1;
		return AX.l + plotW * ((v - bins.start) / span);
	};
	const yCount = (c: number) => (bins && bins.maxCount > 0 ? plotH * (c / bins.maxCount) : 0);
	const cyt = $derived(bins ? niceTicks(0, bins.maxCount, 4).filter((v) => Number.isInteger(v)) : []);

	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	const binLabelTicks = $derived(bins ? niceTicks(bins.start, bins.start + bins.step * bins.k, 5) : []);
	let hover = $state<number | null>(null);
</script>

{#if bins}
	<div class="rhWrap" bind:clientWidth={cw}>
		<svg width="100%" height={H} role="img" aria-label={T('수익률 분포', 'return distribution')}>
			<!-- y 도수 그리드 -->
			{#each cyt as c (c)}
				<line x1={AX.l} y1={AX.t + plotH - yCount(c)} x2={AX.l + plotW} y2={AX.t + plotH - yCount(c)} stroke="rgba(139,145,158,0.09)" stroke-width="1" />
				<text class="rhAx" x={AX.l - 4} y={AX.t + plotH - yCount(c) + 3} text-anchor="end">{c}</text>
			{/each}
			<!-- 막대 · 빈 중심 부호로 색 -->
			{#each bins.counts as c, i (i)}
				{@const x0 = xAt(bins.start + i * bins.step)}
				{@const x1 = xAt(bins.start + (i + 1) * bins.step)}
				{@const mid = bins.start + (i + 0.5) * bins.step}
				<rect
					class="rhBar"
					x={x0 + 0.5}
					y={AX.t + plotH - yCount(c)}
					width={Math.max(0.5, x1 - x0 - 1)}
					height={yCount(c)}
					fill={mid >= 0 ? 'rgba(52,211,153,0.7)' : 'rgba(240,97,111,0.7)'}
					opacity={hover == null || hover === i ? 1 : 0.5}
					onmouseenter={() => (hover = i)}
					onmouseleave={() => (hover = null)}
					role="presentation"
				/>
			{/each}
			<!-- 손익분기 0 세로선 -->
			{#if bins.start < 0 && bins.start + bins.step * bins.k > 0}
				<line x1={xAt(0)} y1={AX.t} x2={xAt(0)} y2={AX.t + plotH} stroke="rgba(139,145,158,0.4)" stroke-width="1" />
			{/if}
			<!-- 평균 점선 -->
			<line x1={xAt(mean)} y1={AX.t} x2={xAt(mean)} y2={AX.t + plotH} stroke="var(--amber, var(--amber))" stroke-width="1" stroke-dasharray="3 3" />
			<text class="rhMean" x={xAt(mean)} y={AX.t - 2} text-anchor="middle">{T('평균', 'mean')} {sgn(mean)}%</text>
			<!-- x 라벨 -->
			{#each binLabelTicks as tick (tick)}
				<text class="rhAx" x={xAt(tick)} y={H - AX.b + 14} text-anchor="middle">{sgn(tick, 0)}%</text>
			{/each}
		</svg>
		{#if hover != null && bins.counts[hover] != null}
			<div class="rhTip">
				{sgn(bins.start + hover * bins.step, 0)}% ~ {sgn(bins.start + (hover + 1) * bins.step, 0)}%
				· <b>{bins.counts[hover]}</b>{T('건', '')}
			</div>
		{/if}
		<div class="rhCap">{unitLabel ?? T('거래별 실현 수익률 · 막대=거래 수, 점선=평균', 'per-trade realized return · bars = count, dashed = mean')}</div>
	</div>
{:else}
	<div class="rhEmpty">{T('분포를 그릴 거래가 부족합니다.', 'too few trades for a distribution.')}</div>
{/if}

<style>
	.rhWrap {
		position: relative;
		width: 100%;
		background: rgba(8, 11, 18, 0.55);
		border: 1px solid var(--dl-line, #1b2130);
		border-radius: 5px;
		padding: 2px 0 4px;
	}
	.rhWrap svg {
		display: block;
		width: 100%;
	}
	.rhAx {
		font-family: var(--dl-font-mono, monospace);
		font-size: 11px;
		fill: var(--dimmer, #5b6573);
		font-variant-numeric: tabular-nums;
	}
	.rhMean {
		font-family: var(--dl-font-mono, monospace);
		font-size: 10px;
		fill: var(--amber, var(--amber));
	}
	.rhBar {
		cursor: default;
	}
	.rhTip {
		position: absolute;
		top: 8px;
		right: 14px;
		background: var(--dl-bg-raised, #0e141f);
		border: 1px solid var(--dl-line-strong, #2a3142);
		border-radius: 4px;
		padding: 4px 9px;
		pointer-events: none;
		font-family: var(--dl-font-mono, monospace);
		font-variant-numeric: tabular-nums;
		font-size: 11px;
		color: #aeb6c2;
		z-index: 3;
	}
	.rhTip b {
		color: var(--dl-ink, #c8cfdb);
		font-weight: 700;
	}
	.rhCap {
		font-size: 10px;
		color: var(--dimmer, #5b6573);
		padding: 0 10px 2px;
	}
	.rhEmpty {
		font-size: 11px;
		color: var(--dimmer, #5b6573);
		padding: 14px;
		text-align: center;
	}
</style>
