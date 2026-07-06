<script lang="ts">
	// 자본변동표 · 변동유형(행) × 자본구성요소(열), 선택 기간 1개. account×period 표로는 2D 를 못 담아 전용.
	import type { SceMatrixData } from '../lib/finance/types';

	let { data, period, divisor }: { data: SceMatrixData; period: string; divisor: number } = $props();

	const nf = new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 0 });
	const fmt = (v: number | null | undefined): string => (v == null ? '-' : nf.format(Math.round(v / divisor)));
	const rows = $derived(data.byPeriod[period] ?? []);
</script>

<div class="sce-scroll">
	<table class="sce">
		<thead>
			<tr>
				<th class="corner">변동유형</th>
				{#each data.components as c (c)}<th class="comp-h" class:tot={c === '자본총계'}>{c}</th>{/each}
			</tr>
		</thead>
		<tbody>
			{#each rows as row (row.label)}
				<tr>
					<th class="rt" title={row.label}>{row.label}</th>
					{#each data.components as c (c)}
						{@const v = row.values[c]}
						<td class="val" class:neg={v != null && v < 0} class:nil={v == null} class:tot={c === '자본총계'}>{fmt(v)}</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.sce-scroll {
		height: 100%;
		overflow: auto;
		background: #050811;
	}
	.sce {
		border-collapse: separate;
		border-spacing: 0;
		font-size: 12px;
		min-width: 100%;
	}
	.sce th,
	.sce td {
		border-right: 1px solid #161c2b;
		border-bottom: 1px solid #161c2b;
		padding: 4px 10px;
		white-space: nowrap;
	}
	thead th {
		position: sticky;
		top: 0;
		z-index: 20;
		background: #0d1320;
		color: #e2e8f0;
		font-weight: 600;
	}
	.comp-h {
		text-align: right;
		min-width: 96px;
		font-variant-numeric: tabular-nums;
	}
	.rt {
		position: sticky;
		left: 0;
		z-index: 10;
		background: #070b15;
		color: #e2e8f0;
		text-align: left;
		font-weight: 400;
		max-width: 240px;
		min-width: 160px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.corner {
		position: sticky;
		left: 0;
		top: 0;
		z-index: 30;
		text-align: left;
		min-width: 160px;
		background: #0d1320;
	}
	.val {
		text-align: right;
		font-variant-numeric: tabular-nums;
		color: #e2e8f0;
	}
	.val.neg {
		color: #f87171;
	}
	.val.nil {
		color: #64748b;
	}
	.comp-h.tot,
	.val.tot {
		font-weight: 700;
		color: #f8fafc;
		background: rgba(var(--amber-rgb), 0.06);
	}
	tbody tr:hover .rt {
		background: #0c1424;
	}
	tbody tr:hover td {
		background: rgba(var(--amber-rgb), 0.05);
	}
</style>
