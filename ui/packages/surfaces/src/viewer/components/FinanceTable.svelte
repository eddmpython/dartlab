<script lang="ts">
	// 정량재무제표 순수 표 · 계정 행 × 기간 열. sticky 첫 열(계정)+sticky 헤더(기간), 숫자 우측정렬·천단위 콤마·음수 빨강.
	import type { FinanceStatement } from '../lib/finance/types';

	let { statement, divisor = 1 }: { statement: FinanceStatement; divisor?: number } = $props();

	const nf = new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 0 });
	const fmt = (v: number | null | undefined): string => (v == null ? '-' : nf.format(Math.round(v / divisor)));
</script>

<div class="ftable-scroll">
	<table class="ftable">
		<thead>
			<tr>
				<th class="corner">계정</th>
				{#each statement.periods as p (p)}<th class="period-h">{p}</th>{/each}
			</tr>
		</thead>
		<tbody>
			{#each statement.rows as row (row.accountId)}
				<tr class:total={row.isTotal} class:sub={!row.isTotal && row.depth <= 1}>
					<th class="acct-c" style="padding-left: {10 + row.depth * 16}px" title={row.label}>{row.label}</th>
					{#each statement.periods as p (p)}
						{@const v = row.values[p]}
						<td class="val" class:neg={v != null && v < 0} class:nil={v == null}>{fmt(v)}</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	/* --fin-* 토큰: 미정의 시 fallback = 기존 viewer 값. 터미널은 .dlTermFinSkin 오버라이드. */
	.ftable-scroll {
		height: 100%;
		overflow: auto;
		background: var(--fin-bg, #050811);
	}
	.ftable {
		border-collapse: separate;
		border-spacing: 0;
		font-size: 12px;
		min-width: 100%;
	}
	.ftable th,
	.ftable td {
		border-right: 1px solid var(--fin-bd-soft, #161c2b);
		border-bottom: 1px solid var(--fin-bd-soft, #161c2b);
		padding: 4px 10px;
		white-space: nowrap;
	}
	/* sticky 헤더(기간) */
	thead th {
		position: sticky;
		top: 0;
		z-index: 20;
		background: var(--fin-bg-raised, #0d1320);
		color: var(--fin-txt-soft, #cbd5e1);
		font-weight: 600;
		text-align: right;
	}
	.period-h {
		min-width: 104px;
		font-variant-numeric: tabular-nums;
		font-family: var(--fin-mono, inherit);
	}
	/* sticky 첫 열(계정) */
	.acct-c {
		position: sticky;
		left: 0;
		z-index: 10;
		background: var(--fin-bg-acct, #070b15);
		color: var(--fin-txt-soft, #cbd5e1);
		font-weight: 400;
		text-align: left;
		max-width: 280px;
		min-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	/* 좌상 교차(헤더+첫열 동시) */
	.corner {
		position: sticky;
		left: 0;
		top: 0;
		z-index: 30;
		text-align: left;
		min-width: 200px;
		max-width: 280px;
		background: var(--fin-bg-raised, #0d1320);
	}
	.val {
		text-align: right;
		font-variant-numeric: tabular-nums;
		font-family: var(--fin-mono, inherit);
		color: var(--fin-val, #e2e8f0);
	}
	.val.neg {
		color: #f87171;
	}
	.val.nil {
		color: #475569;
	}
	/* 구조 · 총계(isTotal) 굵게+상단 보더, 소계(비총계 depth≤1) 굵게. 들여쓰기는 depth(inline padding-left). */
	tr.total .acct-c,
	tr.total .val {
		font-weight: 700;
		color: #f8fafc;
		border-top: 1px solid #2a3650;
	}
	tr.sub .acct-c,
	tr.sub .val {
		font-weight: 600;
		color: #eef2f7;
	}
	tbody tr:hover .acct-c {
		background: #0c1424;
	}
	tbody tr:hover td {
		background: rgba(var(--amber-rgb), 0.05);
	}
</style>
