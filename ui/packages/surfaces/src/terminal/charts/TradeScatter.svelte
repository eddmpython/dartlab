<script lang="ts">
	// 거래별 MAE/MFE 산점도 · 데스크탑 백테스터(TradeStation·MT5·AmiBroker) 시그니처 시각.
	// x=최대역행(MAE%, 보유 중 worst 미실현), y=실현수익%. 점=거래(초록 승/빨강 패). 점 클릭 → 해당 진입봉.
	// "이 승자는 거의 손절당할 뻔"(왼쪽 위) / "곱게 순항한 거래"(오른쪽 위)를 한눈에 · 닫힌 P&L 숫자가 못 보여주는 보유 중 열(heat).
	// EquityChart 와 동일 실측 px 좌표계(preserveAspectRatio 왜곡 박멸) · niceTicks 그리드.
	import type { Lang } from '../lib/types';
	import { niceTicks } from './chartFrame';

	interface TradePt {
		entryT: string;
		retPct: number;
		maePct?: number;
		mfePct?: number;
	}
	interface Props {
		trades: TradePt[];
		lang: Lang;
		onPick?: (t: string) => void;
	}
	let { trades, lang, onPick }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	// MAE 가 있는 거래만(엔진이 산출). 없으면 빈 상태.
	const pts = $derived(trades.filter((t): t is TradePt & { maePct: number } => t.maePct != null));

	let cw = $state(0);
	let svgEl: SVGSVGElement | null = $state(null);
	const AX = { l: 46, r: 14, t: 12, b: 26 };
	const H = 248;
	const plotW = $derived(Math.max(120, cw - AX.l - AX.r));
	const plotH = H - AX.t - AX.b;

	// x 도메인 = [minMAE, 0] (MAE ≤ 0, 왼쪽이 깊은 역행). y 도메인 = 실현수익 min/max(0 포함).
	const dom = $derived.by(() => {
		if (!pts.length) return { xlo: -10, xhi: 0, ylo: -5, yhi: 5 };
		let xlo = 0;
		let ylo = 0;
		let yhi = 0;
		for (const p of pts) {
			if (p.maePct < xlo) xlo = p.maePct;
			if (p.retPct < ylo) ylo = p.retPct;
			if (p.retPct > yhi) yhi = p.retPct;
		}
		const xpad = (0 - xlo) * 0.06 || 1;
		const ypadv = (yhi - ylo) * 0.08 || 1;
		return { xlo: xlo - xpad, xhi: Math.min(0, 0) + xpad * 0.3, ylo: ylo - ypadv, yhi: yhi + ypadv };
	});
	const xAt = (v: number) => AX.l + plotW * ((v - dom.xlo) / ((dom.xhi - dom.xlo) || 1));
	const yAt = (v: number) => AX.t + plotH * (1 - (v - dom.ylo) / ((dom.yhi - dom.ylo) || 1));
	const xt = $derived(niceTicks(dom.xlo, dom.xhi, 4));
	const yt = $derived(niceTicks(dom.ylo, dom.yhi, 5));
	const zeroY = $derived(dom.ylo < 0 && dom.yhi > 0 ? yAt(0) : null);

	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	const fmtD = (t: string) => (t && t.length >= 8 ? `${t.slice(2, 4)}.${t.slice(4, 6)}.${t.slice(6, 8)}` : '');

	let hover = $state<number | null>(null);
	const hv = $derived(hover == null || hover >= pts.length ? null : pts[hover]);
	const tipLeft = $derived.by(() => {
		if (hv == null) return 0;
		const x = xAt(hv.maePct as number);
		const fullW = AX.l + plotW + AX.r;
		return Math.max(4, Math.min(x > AX.l + plotW / 2 ? x - 168 : x + 12, fullW - 160));
	});
</script>

{#if pts.length}
	<div class="tsWrap" bind:clientWidth={cw}>
		<svg bind:this={svgEl} width="100%" height={H} role="img" aria-label={T('거래별 MAE 산점도', 'per-trade MAE scatter')}>
			<!-- y 그리드 + 라벨(실현수익%) -->
			{#each yt as tick (tick)}
				<line x1={AX.l} y1={yAt(tick)} x2={AX.l + plotW} y2={yAt(tick)} stroke="rgba(139,145,158,0.09)" stroke-width="1" />
				<text class="tsAx" x={AX.l - 5} y={yAt(tick) + 3} text-anchor="end">{sgn(tick, 0)}%</text>
			{/each}
			<!-- x 그리드 + 라벨(MAE%) -->
			{#each xt as tick (tick)}
				<line x1={xAt(tick)} y1={AX.t} x2={xAt(tick)} y2={AX.t + plotH} stroke="rgba(139,145,158,0.06)" stroke-width="1" />
				<text class="tsAx" x={xAt(tick)} y={H - AX.b + 14} text-anchor="middle">{tick.toFixed(0)}%</text>
			{/each}
			<!-- 손익분기 y=0 -->
			{#if zeroY != null}
				<line x1={AX.l} y1={zeroY} x2={AX.l + plotW} y2={zeroY} stroke="rgba(139,145,158,0.32)" stroke-width="1" stroke-dasharray="2 3" />
			{/if}
			<!-- 점 · 초록 승 / 빨강 패. 클릭 → 진입봉. -->
			{#each pts as p, i (p.entryT + '-' + i)}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<circle
					class="tsDot"
					cx={xAt(p.maePct)}
					cy={yAt(p.retPct)}
					r={hover === i ? 5 : 3.2}
					fill={p.retPct >= 0 ? 'rgba(52,211,153,0.78)' : 'rgba(240,97,111,0.78)'}
					stroke={hover === i ? '#c8cfdb' : 'none'}
					stroke-width="1"
					role="button"
					tabindex="-1"
					aria-label={fmtD(p.entryT)}
					onmouseenter={() => (hover = i)}
					onmouseleave={() => (hover = null)}
					onclick={() => onPick?.(p.entryT)}
				/>
			{/each}
		</svg>
		<!-- 축 캡션 -->
		<div class="tsCap">
			<span>{T('← 깊은 역행(MAE) 견딤', '← deeper drawdown endured')}</span>
			<span class="tsCapY">{T('↑ 실현 수익', '↑ realized return')}</span>
		</div>
		{#if hv != null}
			<div class="tsTip" style={`left:${tipLeft}px`}>
				<div class="tsTipD">{fmtD(hv.entryT)}</div>
				<div class="tsTipR"><i>{T('실현', 'ret')}</i><b class={hv.retPct >= 0 ? 'u' : 'd'}>{sgn(hv.retPct)}%</b></div>
				<div class="tsTipR"><i>{T('최대역행 MAE', 'MAE')}</i><b class="d">{(hv.maePct as number).toFixed(1)}%</b></div>
				{#if hv.mfePct != null}<div class="tsTipR"><i>{T('최대순행 MFE', 'MFE')}</i><b class="u">+{hv.mfePct.toFixed(1)}%</b></div>{/if}
				<div class="tsTipJump">{T('클릭 → 차트', 'click → chart')}</div>
			</div>
		{/if}
	</div>
{:else}
	<div class="tsEmpty">{T('MAE/MFE 산출 거래가 없습니다.', 'no trades with MAE/MFE.')}</div>
{/if}

<style>
	.tsWrap {
		position: relative;
		width: 100%;
		background: rgba(8, 11, 18, 0.55);
		border: 1px solid var(--dl-line, #1b2130);
		border-radius: 5px;
		padding: 2px 0 4px;
	}
	.tsWrap svg {
		display: block;
		width: 100%;
	}
	.tsAx {
		font-family: var(--dl-font-mono, monospace);
		font-size: 11px;
		fill: var(--dimmer, #5b6573);
		font-variant-numeric: tabular-nums;
	}
	.tsDot {
		cursor: pointer;
		transition: r 0.08s;
	}
	.tsCap {
		display: flex;
		justify-content: space-between;
		font-size: 10px;
		color: var(--dimmer, #5b6573);
		padding: 0 10px 2px;
	}
	.tsCapY {
		color: var(--dim, #8b94a3);
	}
	.tsTip {
		position: absolute;
		top: 8px;
		width: 150px;
		background: var(--dl-bg-raised, #0e141f);
		border: 1px solid var(--dl-line-strong, #2a3142);
		border-radius: 4px;
		padding: 5px 8px;
		pointer-events: none;
		font-family: var(--dl-font-mono, monospace);
		font-variant-numeric: tabular-nums;
		z-index: 3;
	}
	.tsTipD {
		font-size: 11px;
		color: var(--dl-ink, #c8cfdb);
		font-weight: 700;
		margin-bottom: 3px;
	}
	.tsTipR {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		font-size: 11px;
	}
	.tsTipR i {
		font-style: normal;
		color: var(--dim, #8b94a3);
	}
	.tsTipR b {
		font-weight: 700;
	}
	.tsTipR .u {
		color: var(--up, #34d399);
	}
	.tsTipR .d {
		color: var(--dn, #f0616f);
	}
	.tsTipJump {
		font-size: 9.5px;
		color: var(--dimmer, #5b6573);
		margin-top: 3px;
	}
	.tsEmpty {
		font-size: 11px;
		color: var(--dimmer, #5b6573);
		padding: 14px;
		text-align: center;
	}
</style>
