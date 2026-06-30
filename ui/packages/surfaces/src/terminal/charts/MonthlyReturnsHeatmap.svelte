<script lang="ts">
	// 월별 수익률 히트맵 · quant tearsheet 시그니처. equity+ts 파생(신규 수집 0).
	// 행=연도(오름차순 고정·수익순 정렬 금지) × 열=1~12월 + YTD. 셀 색=과거 사실(적녹 diverging).
	// ⛔ argmax 화살표·best 라벨·정렬 금지(04 §G4 정신) · '꾸준함 vs 한 방'을 보일 뿐, 특정 셀 강조 안 함.
	import type { Lang } from '../lib/types';
	import { monthlyReturns } from './chartFrame';

	interface Props {
		eq: number[]; // 평가창 non-null 전략 계좌가치(시작≈100)
		ts: string[]; // YYYYMMDD, eq 와 동일 인덱스
		lang: Lang;
	}
	let { eq, ts, lang }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	const MONTHS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];

	const mr = $derived(monthlyReturns(eq, ts));
	// 색: 양수 up·음수 dn, alpha=min(|ret|/8,1)*0.5 (8% 에서 포화). null=빈셀.
	function bg(ret: number | null): string {
		if (ret == null) return 'transparent';
		const a = (Math.min(Math.abs(ret) / 8, 1) * 0.5).toFixed(3);
		return ret >= 0 ? `rgba(52,211,153,${a})` : `rgba(240,97,111,${a})`;
	}
	const fmt = (r: number | null) => (r == null ? '' : (r >= 0 ? '+' : '') + r.toFixed(1));
	const tip = (y: number, m: number, r: number | null) => `${y}-${String(m).padStart(2, '0')} ${r == null ? T('자료 없음', 'no data') : fmt(r) + '%'}`;
</script>

<div class="heatWrap">
	{#if mr.years.length}
		<table class="heat">
			<thead>
				<tr>
					<th class="yh"></th>
					{#each MONTHS as m (m)}<th>{m}{T('월', '')}</th>{/each}
					<th class="ytdh">{T('연', 'YTD')}</th>
				</tr>
			</thead>
			<tbody>
				{#each mr.years as y (y)}
					{@const yr = mr.ytd(y)}
					<tr>
						<th class="yh">{y}</th>
						{#each MONTHS as _m, mi (mi)}
							{@const r = mr.cell(y, mi + 1)}
							<td class="cell" class:empty={r == null} style={`background:${bg(r)}`} title={tip(y, mi + 1, r)}>{fmt(r)}</td>
						{/each}
						<td class="cell ytd" class:empty={yr == null} style={`background:${bg(yr)}`} title={`${y} ${yr == null ? '' : fmt(yr) + '%'}`}><b>{fmt(yr)}</b></td>
					</tr>
				{/each}
			</tbody>
		</table>
		<div class="heatCap">{T('월별 가격수익(배당·정조정 제외) · 월말 계좌가치 기준 근사', 'monthly price return (excl. dividends/adj) · month-end account value approx.')}</div>
	{:else}
		<div class="heatEmpty">{T('월별 집계에 필요한 구간이 부족합니다.', 'window too short for monthly aggregation.')}</div>
	{/if}
</div>

<style>
	.heatWrap {
		width: 100%;
		overflow-x: auto;
	}
	.heat {
		border-collapse: collapse;
		font-family: var(--dl-font-mono, monospace);
		font-variant-numeric: tabular-nums;
		width: 100%;
	}
	.heat th {
		font-size: 11px;
		font-weight: 600;
		color: var(--dim, #8b94a3);
		padding: 3px 4px;
		text-align: center;
	}
	.heat th.yh {
		text-align: right;
		padding-right: 8px;
		color: #aeb6c2;
		min-width: 38px;
	}
	.heat th.ytdh {
		border-left: 1px solid var(--dl-line-strong, #2a3142);
		color: #aeb6c2;
	}
	.cell {
		font-size: 11px;
		color: var(--dl-ink, #c8cfdb);
		text-align: center;
		padding: 4px 5px;
		border: 1px solid rgba(27, 33, 48, 0.5);
		min-width: 38px;
		white-space: nowrap;
	}
	.cell.empty {
		color: transparent;
		background-image: repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(139, 145, 158, 0.06) 3px, rgba(139, 145, 158, 0.06) 4px);
	}
	.cell.ytd {
		border-left: 1px solid var(--dl-line-strong, #2a3142);
		background: rgba(255, 255, 255, 0.02);
	}
	.cell.ytd b {
		font-weight: 700;
	}
	.heatCap {
		font-size: 10px;
		color: var(--dim, #8b94a3);
		margin-top: 5px;
		line-height: 1.5;
	}
	.heatEmpty {
		font-size: 11px;
		color: var(--dimmer, #5b6573);
		padding: 14px;
		text-align: center;
	}
</style>
