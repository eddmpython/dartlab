<script lang="ts">
	/**
	 * 셀 hover 시 1년 sparkline + 회사명·메트릭값 popover.
	 *
	 * Grid.svelte 가 마우스 dwell 200ms 후 이 컴포넌트 렌더. position 은 호버한 셀의
	 * bounding rect 기준 (top/left absolute).
	 */
	import Sparkline from './Sparkline.svelte';
	import { METRICS_BY_KEY } from './metrics';

	interface Props {
		stockCode: string;
		label: string;
		metricKey: string;
		formattedValue: string;
		spark: number[];
		x: number;
		y: number;
	}

	let { stockCode, label, metricKey, formattedValue, spark, x, y }: Props = $props();

	let metric = $derived(METRICS_BY_KEY[metricKey]);
	let trend = $derived.by(() => {
		if (spark.length < 2) return 'flat';
		const first = spark[0];
		const last = spark[spark.length - 1];
		if (last > first * 1.005) return 'up';
		if (last < first * 0.995) return 'down';
		return 'flat';
	});
	// 한국 증시 정서 · 상승 빨강, 하락 파랑
	let trendColor = $derived(
		trend === 'up' ? '#ef4444' : trend === 'down' ? '#3b82f6' : '#94a3b8'
	);
	let trendPct = $derived.by(() => {
		if (spark.length < 2 || spark[0] === 0) return null;
		const v = (spark[spark.length - 1] / spark[0] - 1) * 100;
		return v.toLocaleString('ko-KR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	});
	let isSparkCell = $derived(metricKey === 'spark' || metricKey === 'spark30' || metricKey === 'spark60');
	let periodLabel = $derived(
		metricKey === 'spark30'
			? '30거래일 종가 추이'
			: metricKey === 'spark60'
				? '60거래일 종가 추이'
				: '1년 종가 추이'
	);
</script>

<div class="cell-tooltip" style:left="{x}px" style:top="{y}px" role="tooltip">
	<div class="t-head">
		<span class="t-label">{label}</span>
		<span class="t-code">{stockCode}</span>
	</div>
	{#if !isSparkCell}
		<div class="t-metric">
			<span class="t-mlbl">{metric?.label ?? metricKey}</span>
			<span class="t-mval">{formattedValue}</span>
		</div>
	{/if}
	{#if spark.length >= 2}
		<div class="t-spark" style:color={trendColor}>
			<Sparkline data={spark} width={220} height={56} stroke="currentColor" smooth />
		</div>
		<div class="t-foot">
			<span class="t-period">{periodLabel}</span>
			{#if trendPct !== null}
				<span class="t-trend" style:color={trendColor}>
					{trend === 'up' ? '+' : ''}{trendPct}%
				</span>
			{/if}
		</div>
	{:else}
		<div class="t-noprice">1Y 추세 로딩/없음</div>
	{/if}
</div>

<style>
	.cell-tooltip {
		position: fixed;
		min-width: 200px;
		max-width: 240px;
		padding: 10px 12px;
		background: #0f172a;
		border: 1px solid #334155;
		border-radius: 6px;
		box-shadow: 0 12px 28px -10px rgba(0, 0, 0, 0.8);
		z-index: 200;
		pointer-events: none;
		animation: fadein 100ms ease-out;
		font-size: 11px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.t-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
	}
	.t-label {
		font-size: 12px;
		font-weight: 600;
		color: #f1f5f9;
	}
	.t-code {
		font-family: monospace;
		color: #64748b;
		font-size: 10px;
	}
	.t-metric {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		padding: 4px 0;
		border-top: 1px solid #1e2433;
	}
	.t-mlbl {
		color: #94a3b8;
	}
	.t-mval {
		font-family: monospace;
		font-weight: 600;
		color: #f1f5f9;
		font-variant-numeric: tabular-nums;
	}
	.t-spark {
		margin-top: 2px;
	}
	.t-foot {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 10px;
		font-family: monospace;
	}
	.t-period {
		color: #64748b;
	}
	.t-trend {
		font-weight: 600;
	}
	.t-noprice {
		color: #64748b;
		font-size: 10px;
		text-align: center;
		padding: 8px 0;
		border-top: 1px solid #1e2433;
	}
	@keyframes fadein {
		from {
			opacity: 0;
			transform: translateY(-4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
