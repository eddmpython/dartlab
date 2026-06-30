<script lang="ts">
	// 블로그 회사글 재무 섹션 · 데이터 SSOT(dart/finance) 를 빌드타임에 표준화한 companyFinance(+page.server.ts)를
	// +page.svelte 가 context 로 내려준다(중첩 mdsvex 컴포넌트 SSR 안전). 숫자를 .md 에 박지 않는다 → 화석화 불가.
	import { getContext } from 'svelte';
	import ComboChart from './ComboChart.svelte';
	import StackBar from './StackBar.svelte';
	import HFDataLink from './HFDataLink.svelte';
	import type { AnnualStmtRow, CompanyAnnualFinance } from '@dartlab/ui-runtime/data/finance/annual';

	interface Props {
		code: string;
	}
	let { code }: Props = $props();

	const finGetter = getContext<(() => CompanyAnnualFinance | null) | undefined>('blogCompanyFinance');
	const fin = $derived(finGetter ? finGetter() : null);

	function cell(v: number | null): string {
		if (v == null) return '·';
		if (Math.abs(v) >= 1) return Math.round(v).toLocaleString('ko-KR');
		return v.toFixed(1);
	}

	const bsStack = $derived(
		fin && fin.code === code
			? fin.charts.bs.map((d) => ({
					year: d.year,
					segments: [
						{ label: '부채', value: d.부채 ?? 0, color: '#ef4444' },
						{ label: '자본', value: d.자본 ?? 0, color: '#22c55e' }
					]
				}))
			: []
	);
</script>

{#if fin && fin.code === code}
	<h2 id="재무제표">재무제표 · 최근 5개년</h2>
	<blockquote class="cf-note">
		<p>아래는 최근 5개년 요약입니다(단위 억원, 연결 기준). 전체 기간·분기별 데이터는 dartlab에서 직접 확인할 수 있습니다:</p>
		<pre><code>import dartlab
c = dartlab.Company("{code}")
c.select("IS", freq="Y")  # 손익계산서 (연간)
c.select("BS", freq="Y")  # 재무상태표
c.select("CF", freq="Y")  # 현금흐름표</code></pre>
	</blockquote>

	{#snippet table(rows: AnnualStmtRow[], years: string[])}
		<div class="cf-tablewrap">
			<table class="cf-table">
				<thead>
					<tr>
						<th>항목</th>
						{#each years as y (y)}<th class="num">{y}</th>{/each}
					</tr>
				</thead>
				<tbody>
					{#each rows as r (r.key)}
						<tr>
							<td>{r.label}</td>
							{#each r.values as v, i (i)}<td class="num">{cell(v)}</td>{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/snippet}

	<h3>손익계산서 (IS) · 단위 억원</h3>
	<ComboChart
		data={fin.charts.is}
		lineKeys={['매출액']}
		barKeys={['영업이익', '당기순이익']}
		lineColors={['#22c55e']}
		barColors={['#3b82f6', '#f59e0b']}
		title="매출(라인) vs 영업이익·당기순이익(막대)"
		unit="억원"
	/>
	{@render table(fin.is, fin.years)}

	<h3>재무상태표 (BS) · 단위 억원</h3>
	<StackBar data={bsStack} title="부채 vs 자본 구조" unit="억원" />
	{@render table(fin.bs, fin.years)}

	<h3>현금흐름표 (CF) · 단위 억원</h3>
	<ComboChart
		data={fin.charts.cf}
		barKeys={['영업CF', '투자CF', '재무CF']}
		barColors={['#22c55e', '#ef4444', '#3b82f6']}
		title="영업·투자·재무 현금흐름"
		unit="억원"
		dualAxis={false}
	/>
	{@render table(fin.cf, fin.years)}

	<p class="cf-src">
		최신 · dartlab 실측(HF 공개 데이터 · 연결{fin.scope === 'OFS' ? '→별도' : ''}) · 데이터 기준 {fin.asOf}년 · 빌드 시점 자동 갱신
	</p>
	<HFDataLink {code} kind="finance" />
{:else}
	<p class="cf-src">재무 데이터는 dartlab HF 공개 데이터셋에서 직접 확인하세요.</p>
	<HFDataLink {code} kind="finance" />
{/if}

<style>
	.cf-note pre {
		overflow-x: auto;
	}
	.cf-tablewrap {
		overflow-x: auto;
		margin: 0.75rem 0 1.5rem;
	}
	.cf-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.86rem;
		font-variant-numeric: tabular-nums;
	}
	.cf-table th,
	.cf-table td {
		padding: 0.4rem 0.7rem;
		border-bottom: 1px solid var(--border, #1e293b);
		white-space: nowrap;
	}
	.cf-table thead th {
		color: var(--text-muted, #94a3b8);
		font-weight: 600;
		border-bottom: 1px solid var(--border, #334155);
	}
	.cf-table .num {
		text-align: right;
	}
	.cf-table tbody td:first-child {
		color: var(--text, #e2e8f0);
	}
	.cf-src {
		font-size: 0.78rem;
		color: var(--text-muted, #94a3b8);
		margin: 0.5rem 0;
	}
</style>
