<script lang="ts">
	// 연간 수익률 막대 · 전략 vs 보유(B&H) 캘린더 연도별. QuantStats·PortfolioVisualizer·QuantConnect 공통 시각.
	// CAGR 한 숫자가 가리는 '연도 의존성'을 드러냄 · 한두 해 몰아주기인지, 매년 꾸준한지. monthlyReturns().ytd 재사용(중복 계산 0).
	// EquityChart 와 동일 실측 px 좌표계 · niceTicks y 그리드. 첫 해는 구간 시작부터의 부분 연도(라벨 *).
	import type { Lang } from '../lib/types';
	import { niceTicks, monthlyReturns } from './chartFrame';

	interface Props {
		eq: number[]; // 전략 계좌가치(시작≈100), 평가창 non-null 슬라이스
		bhq: number[]; // 보유(B&H) 동일 길이
		ts: string[]; // YYYYMMDD, eq 와 동일 인덱스
		lang: Lang;
	}
	let { eq, bhq, ts, lang }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	const rows = $derived.by(() => {
		const ms = monthlyReturns(eq, ts);
		const mb = monthlyReturns(bhq, ts);
		const firstYear = ts.length ? +ts[0].slice(0, 4) : null;
		return ms.years.map((y) => ({
			year: y,
			strat: ms.ytd(y),
			bh: mb.ytd(y),
			partial: y === firstYear && ts.length > 0 && ts[0].slice(4, 6) !== '01'
		}));
	});

	let cw = $state(0);
	const AX = { l: 46, r: 14, t: 12, b: 22 };
	const H = 200;
	const plotW = $derived(Math.max(120, cw - AX.l - AX.r));
	const plotH = H - AX.t - AX.b;

	const dom = $derived.by(() => {
		let lo = 0;
		let hi = 0;
		for (const r of rows) {
			for (const v of [r.strat, r.bh]) if (v != null) { if (v < lo) lo = v; if (v > hi) hi = v; }
		}
		const pad = (hi - lo) * 0.08 || 1;
		return { lo: lo - pad, hi: hi + pad };
	});
	const yAt = (v: number) => AX.t + plotH * (1 - (v - dom.lo) / ((dom.hi - dom.lo) || 1));
	const yt = $derived(niceTicks(dom.lo, dom.hi, 5));
	const zeroY = $derived(yAt(0));

	// 연도 슬롯 · 그룹(전략·B&H 2막대). 슬롯폭/막대폭 px.
	const slotW = $derived(rows.length ? plotW / rows.length : plotW);
	const barW = $derived(Math.min(18, Math.max(4, (slotW - 6) / 2)));
	const slotX = (i: number) => AX.l + slotW * (i + 0.5);

	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	let hover = $state<number | null>(null);
</script>

{#if rows.length}
	<div class="yrWrap" bind:clientWidth={cw}>
		<svg width="100%" height={H} role="img" aria-label={T('연간 수익률', 'yearly returns')}>
			{#each yt as tick (tick)}
				<line x1={AX.l} y1={yAt(tick)} x2={AX.l + plotW} y2={yAt(tick)} stroke="rgba(139,145,158,0.09)" stroke-width="1" />
				<text class="yrAx" x={AX.l - 5} y={yAt(tick) + 3} text-anchor="end">{sgn(tick, 0)}%</text>
			{/each}
			<line x1={AX.l} y1={zeroY} x2={AX.l + plotW} y2={zeroY} stroke="rgba(139,145,158,0.32)" stroke-width="1" />
			{#each rows as r, i (r.year)}
				{@const cx = slotX(i)}
				<!-- 전략 막대(좌) -->
				{#if r.strat != null}
					<rect
						class="yrBar"
						x={cx - barW - 1}
						y={Math.min(yAt(r.strat), zeroY)}
						width={barW}
						height={Math.max(1, Math.abs(yAt(r.strat) - zeroY))}
						fill={r.strat >= 0 ? 'rgba(52,211,153,0.85)' : 'rgba(240,97,111,0.85)'}
						opacity={hover == null || hover === i ? 1 : 0.45}
						onmouseenter={() => (hover = i)}
						onmouseleave={() => (hover = null)}
						role="presentation"
					/>
				{/if}
				<!-- B&H 막대(우, 회색 윤곽) -->
				{#if r.bh != null}
					<rect
						class="yrBar"
						x={cx + 1}
						y={Math.min(yAt(r.bh), zeroY)}
						width={barW}
						height={Math.max(1, Math.abs(yAt(r.bh) - zeroY))}
						fill="rgba(139,145,158,0.32)"
						stroke="rgba(139,145,158,0.6)"
						stroke-width="1"
						opacity={hover == null || hover === i ? 1 : 0.45}
						onmouseenter={() => (hover = i)}
						onmouseleave={() => (hover = null)}
						role="presentation"
					/>
				{/if}
				<text class="yrAx yrYear" x={cx} y={H - AX.b + 14} text-anchor="middle">{String(r.year).slice(2)}{r.partial ? '*' : ''}</text>
			{/each}
		</svg>
		<div class="yrLeg">
			<span class="yrLk strat"></span>{T('전략', 'strategy')}
			<span class="yrLk bh"></span>{T('보유(B&H)', 'B&H')}
			{#if rows.some((r) => r.partial)}<i class="yrPart">{T('* 부분 연도(구간 시작)', '* partial year')}</i>{/if}
		</div>
		{#if hover != null && rows[hover]}
			{@const r = rows[hover]}
			<div class="yrTip">
				<b>{r.year}{r.partial ? '*' : ''}</b>
				<span class={(r.strat ?? 0) >= 0 ? 'u' : 'd'}>{T('전략', 'strat')} {r.strat != null ? sgn(r.strat) + '%' : '·'}</span>
				<span class={(r.bh ?? 0) >= 0 ? 'u' : 'd'}>{T('보유', 'B&H')} {r.bh != null ? sgn(r.bh) + '%' : '·'}</span>
			</div>
		{/if}
	</div>
{:else}
	<div class="yrEmpty">{T('연 단위 집계할 구간이 부족합니다.', 'window too short for yearly bars.')}</div>
{/if}

<style>
	.yrWrap {
		position: relative;
		width: 100%;
		background: rgba(8, 11, 18, 0.55);
		border: 1px solid var(--dl-line, #1b2130);
		border-radius: 5px;
		padding: 2px 0 4px;
	}
	.yrWrap svg {
		display: block;
		width: 100%;
	}
	.yrAx {
		font-family: var(--dl-font-mono, monospace);
		font-size: 11px;
		fill: var(--dimmer, #5b6573);
		font-variant-numeric: tabular-nums;
	}
	.yrYear {
		fill: var(--dim, #8b94a3);
	}
	.yrBar {
		cursor: default;
	}
	.yrLeg {
		display: flex;
		align-items: center;
		gap: 5px;
		font-size: 11px;
		color: #aeb6c2;
		padding: 3px 10px 1px;
	}
	.yrLk {
		display: inline-block;
		width: 11px;
		height: 11px;
		border-radius: 2px;
		margin-left: 9px;
	}
	.yrLeg .yrLk:first-child {
		margin-left: 0;
	}
	.yrLk.strat {
		background: rgba(52, 211, 153, 0.85);
	}
	.yrLk.bh {
		background: rgba(139, 145, 158, 0.32);
		border: 1px solid rgba(139, 145, 158, 0.6);
	}
	.yrPart {
		font-style: normal;
		font-size: 10px;
		color: var(--dimmer, #5b6573);
		margin-left: 6px;
	}
	.yrTip {
		position: absolute;
		top: 8px;
		right: 14px;
		display: flex;
		gap: 10px;
		align-items: baseline;
		background: var(--dl-bg-raised, #0e141f);
		border: 1px solid var(--dl-line-strong, #2a3142);
		border-radius: 4px;
		padding: 4px 9px;
		pointer-events: none;
		font-family: var(--dl-font-mono, monospace);
		font-variant-numeric: tabular-nums;
		font-size: 11px;
		z-index: 3;
	}
	.yrTip b {
		color: var(--dl-ink, #c8cfdb);
		font-weight: 700;
	}
	.yrTip .u {
		color: var(--up, #34d399);
	}
	.yrTip .d {
		color: var(--dn, #f0616f);
	}
	.yrEmpty {
		font-size: 11px;
		color: var(--dimmer, #5b6573);
		padding: 14px;
		text-align: center;
	}
</style>
