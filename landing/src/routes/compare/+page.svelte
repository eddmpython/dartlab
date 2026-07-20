<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { FreshnessBadge } from '@dartlab/ui-surfaces/map';
	import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// URL ?codes=A,B,C,D (최대 4) | legacy ?a=&b=
	let codes = $derived.by(() => {
		const q = page.url.searchParams;
		const cs = q.get('codes');
		if (cs) return cs.split(',').filter(Boolean).slice(0, 4);
		const a = q.get('a');
		const b = q.get('b');
		return [a, b].filter(Boolean) as string[];
	});

	let companies: any[] = $state([]); // [{node, detail}]
	let loading = $state(false);

	async function load() {
		if (codes.length === 0) return;
		loading = true;
		const nodeById = new Map(
			((data as any).ecosystem?.nodes || []).map((n: any) => [n.id, n])
		);
		const results: any[] = [];
		for (const c of codes) {
			const node = nodeById.get(c);
			if (!node) continue;
			const detail = await loadJson<any>(`map/companies/${c}.json`, { fetchFn: fetch });
			results.push({ node, detail });
		}
		companies = results;
		loading = false;
	}

	onMount(() => {
		load();
	});

	$effect(() => {
		// URL 변경 시 재로드
		if (codes.length && companies.length !== codes.length) {
			load();
		}
	});

	// ── 지표 행 정의 ──
	interface Row {
		section: string;
		key: string;
		label: string;
		valueOf: (c: any) => number | null | undefined;
		fmt: (v: any) => string;
		metric?: 'roe' | 'opMargin' | 'debtRatio' | 'revCagr';
		invertGoodness?: boolean;
	}

	function pct(v: number | null | undefined, digits = 1): string {
		if (v === null || v === undefined || isNaN(v)) return '-';
		return `${v.toFixed(digits)}%`;
	}

	function fmtKor(v: number | null | undefined): string {
		if (v === null || v === undefined || isNaN(v)) return '-';
		const abs = Math.abs(v);
		if (abs >= 1e12) return `${(v / 1e12).toFixed(1)}조`;
		if (abs >= 1e8) return `${Math.round(v / 1e8).toLocaleString()}억`;
		return v.toLocaleString();
	}

	const ROWS: Row[] = [
		{ section: '규모', key: 'revenue', label: '매출', valueOf: (c) => c.node?.revenue, fmt: fmtKor },
		{ section: '규모', key: 'marketShare', label: '상장사매출비중', valueOf: (c) => c.node?.marketShare, fmt: (v) => pct(v, 1) },
		{ section: '규모', key: 'industryRank', label: '산업 순위', valueOf: (c) => c.node?.industryRank, fmt: (v) => v ? `${v}위` : '-' },
		{ section: '수익성', key: 'roe', label: 'ROE', valueOf: (c) => c.node?.roe, fmt: pct, metric: 'roe' },
		{ section: '수익성', key: 'opMargin', label: '영업이익률', valueOf: (c) => c.node?.opMargin, fmt: pct, metric: 'opMargin' },
		{ section: '수익성', key: 'roeDelta', label: 'ROE YoY', valueOf: (c) => c.node?.roeDelta, fmt: (v) => v != null ? `${v > 0 ? '+' : ''}${v}%p` : '-' },
		{ section: '성장', key: 'revenueYoyPct', label: '매출 YoY', valueOf: (c) => c.node?.revenueYoyPct, fmt: (v) => v != null ? `${v > 0 ? '+' : ''}${v}%` : '-' },
		{ section: '성장', key: 'revCagr', label: '매출 CAGR 3Y', valueOf: (c) => c.node?.revCagr, fmt: pct, metric: 'revCagr' },
		{ section: '건전성', key: 'debtRatio', label: '부채비율', valueOf: (c) => c.node?.debtRatio, fmt: (v) => pct(v, 0), metric: 'debtRatio', invertGoodness: true },
		{ section: '건전성', key: 'debtRatioDelta', label: '부채 YoY', valueOf: (c) => c.node?.debtRatioDelta, fmt: (v) => v != null ? `${v > 0 ? '+' : ''}${v}%p` : '-' },
		{ section: '공급망', key: 'supplierCount', label: '공급사 수', valueOf: (c) => c.detail?.supplyInsights?.supplierCount, fmt: (v) => v != null ? `${v}` : '-' },
		{ section: '공급망', key: 'customerCount', label: '고객사 수', valueOf: (c) => c.detail?.supplyInsights?.customerCount, fmt: (v) => v != null ? `${v}` : '-' },
		{ section: '공급망', key: 'hhi', label: '공급 HHI', valueOf: (c) => c.detail?.supplyInsights?.hhi, fmt: (v) => v != null ? `${Math.round(v)}` : '-', invertGoodness: true },
		{ section: '공급망', key: 'top1Ratio', label: 'Top1 의존', valueOf: (c) => c.detail?.supplyInsights?.top1Ratio, fmt: pct, invertGoodness: true }
	];

	// 각 행에서 min/max/CV 계산해서 자동 하이라이트
	function rowStats(row: Row): { max: number | null; min: number | null; cv: number } {
		const vals = companies
			.map((c) => row.valueOf(c))
			.filter((v): v is number => typeof v === 'number' && !isNaN(v));
		if (vals.length === 0) return { max: null, min: null, cv: 0 };
		const max = Math.max(...vals);
		const min = Math.min(...vals);
		const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
		const variance = vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length;
		const std = Math.sqrt(variance);
		const cv = Math.abs(mean) > 0.01 ? std / Math.abs(mean) : 0;
		return { max, min, cv };
	}

	// 행 분류: 공통 (CV < 0.2) / 차별 (CV > 0.6)
	function rowClass(stats: ReturnType<typeof rowStats>): string {
		if (stats.cv > 0.6) return 'differentiator';
		if (stats.cv < 0.2 && stats.max !== null) return 'common';
		return '';
	}

	// 특정 회사의 업종 정규화 percentile (색상용)
	function percentileFor(company: any, metric: string | undefined): number | null {
		if (!metric || !company.node) return null;
		const indStat = (data as any).industryStats?.[company.node.industry];
		if (!indStat?.distribution?.[metric]) return null;
		const dist = indStat.distribution[metric];
		const val = company.node[metric];
		if (val == null) return null;
		if (val <= dist.p10) return 10;
		if (val >= dist.p90) return 90;
		if (val <= dist.p25) return 10 + ((val - dist.p10) / (dist.p25 - dist.p10 || 1)) * 15;
		if (val >= dist.p75) return 75 + ((val - dist.p75) / (dist.p90 - dist.p75 || 1)) * 15;
		if (val <= dist.median) return 25 + ((val - dist.p25) / (dist.median - dist.p25 || 1)) * 25;
		return 50 + ((val - dist.median) / (dist.p75 - dist.median || 1)) * 25;
	}

	function cellColor(row: Row, company: any): string {
		if (!row.metric) return 'transparent';
		const p = percentileFor(company, row.metric);
		if (p === null) return 'transparent';
		const good = row.invertGoodness ? 100 - p : p;
		if (good >= 80) return 'rgba(52, 211, 153, 0.18)';
		if (good >= 50) return 'rgba(132, 204, 22, 0.14)';
		if (good >= 20) return 'rgba(245, 158, 11, 0.14)';
		return 'rgba(239, 68, 68, 0.16)';
	}

	// 공통 공급사/고객사 교집합
	let commonSuppliers = $derived.by(() => {
		if (companies.length < 2) return [];
		const sets = companies.map((c) => new Set((c.detail?.suppliers || []).map((s: any) => s.stockCode)));
		const common = [...sets[0]].filter((x) => sets.every((s) => s.has(x)));
		return common
			.map((code) => {
				const first = companies[0].detail?.suppliers?.find((s: any) => s.stockCode === code);
				return first ? { stockCode: code, corpName: first.corpName, product: first.product } : null;
			})
			.filter(Boolean) as any[];
	});

	let commonCustomers = $derived.by(() => {
		if (companies.length < 2) return [];
		const sets = companies.map((c) => new Set((c.detail?.customers || []).map((s: any) => s.stockCode)));
		const common = [...sets[0]].filter((x) => sets.every((s) => s.has(x)));
		return common
			.map((code) => {
				const first = companies[0].detail?.customers?.find((s: any) => s.stockCode === code);
				return first ? { stockCode: code, corpName: first.corpName } : null;
			})
			.filter(Boolean) as any[];
	});

	// Markdown 테이블 복사
	function copyMarkdown() {
		const header = `| 지표 | ${companies.map((c) => c.node?.label || '-').join(' | ')} |\n`;
		const sep = `|---|${companies.map(() => '---').join('|')}|\n`;
		const rows: string[] = [];
		let currentSection = '';
		for (const row of ROWS) {
			if (row.section !== currentSection) {
				rows.push(`| **${row.section}** |${companies.map(() => '').join('|')}|`);
				currentSection = row.section;
			}
			const cells = companies.map((c) => row.fmt(row.valueOf(c)));
			rows.push(`| ${row.label} | ${cells.join(' | ')} |`);
		}
		const footer = `\n> 출처: dartlab ${base}/compare?codes=${codes.join(',')} · ${new Date().toISOString().slice(0, 10)}`;
		const text = header + sep + rows.join('\n') + footer;
		navigator.clipboard.writeText(text);
	}

	function groupedRows(): { section: string; rows: Row[] }[] {
		const out: { section: string; rows: Row[] }[] = [];
		for (const row of ROWS) {
			const last = out[out.length - 1];
			if (last && last.section === row.section) last.rows.push(row);
			else out.push({ section: row.section, rows: [row] });
		}
		return out;
	}
</script>

<svelte:head>
	<title>기업 비교 | dartlab 전자공시</title>
	<meta name="description" content="한국 상장사 최대 4사 비교 · 재무/공급망/AI 분석 나란히." />
	<meta property="og:type" content="website" />
	<meta property="og:title" content="기업 비교 · dartlab" />
	<meta property="og:description" content="4사 재무·공급망·AI 나란히. 공통 공급사 교집합 자동." />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta name="twitter:card" content="summary_large_image" />
</svelte:head>

<div class="page">
	<header class="head">
		<div class="head-left">
			<a class="back" href="{base}/map">← 산업지도</a>
			<h1>기업 비교</h1>
			{#if companies.length > 0}
				<p class="lead">
					{companies.map((c) => c.node?.label || '-').join(' · ')}
				</p>
			{/if}
		</div>
		{#if (data as any).meta?.dataAsOf}
			<FreshnessBadge dataAsOf={(data as any).meta.dataAsOf} variant="compact" />
		{/if}
	</header>

	{#if loading}
		<div class="loading">데이터 로드 중…</div>
	{:else if codes.length === 0}
		<div class="empty">
			<p>비교할 회사를 선택해주세요.</p>
			<p>URL 예시: <code>?codes=005930,000660,005380</code></p>
			<a class="cta" href="{base}/map">산업지도에서 회사 선택하기 →</a>
		</div>
	{:else if companies.length === 0}
		<div class="empty">
			<p>해당 종목코드로 회사를 찾지 못했습니다.</p>
			<a class="cta" href="{base}/map">산업지도로 돌아가기 →</a>
		</div>
	{:else}
		<!-- Hero 카드 나열 -->
		<div class="hero" style:grid-template-columns="repeat({companies.length}, minmax(0, 1fr))">
			{#each companies as c (c.node?.id)}
				<div class="hero-card">
					<div class="hero-head">
						<h2>
							<a href="{base}/map?focus={c.node?.id}">{c.node?.label}</a>
						</h2>
						<span class="code">{c.node?.id}</span>
					</div>
					<div class="badges">
						<span class="badge industry" style:background="{c.node?.color}20" style:color={c.node?.color}>
							{c.node?.industryName}
						</span>
						{#if c.node?.stageName}
							<span class="badge stage">{c.node.stageName}</span>
						{/if}
					</div>
					{#if c.detail?.aiInsight?.verdict}
						<div class="verdict">{c.detail.aiInsight.verdict}</div>
					{/if}
				</div>
			{/each}
		</div>

		<!-- 비교 테이블 -->
		<div class="table-bar">
			<div class="legend">
				<span class="legend-item"><span class="sw common"></span>공통 (편차 낮음)</span>
				<span class="legend-item"><span class="sw differentiator"></span>차별 (편차 큼)</span>
				<span class="legend-item">셀 색상: 업종 대비 분위</span>
			</div>
			<button class="copy-md" onclick={copyMarkdown}>📋 Markdown 복사</button>
		</div>

		<div class="table-wrap">
			<table>
				<thead>
					<tr>
						<th>지표</th>
						{#each companies as c (c.node?.id)}
							<th>
								<div class="th-name">{c.node?.label}</div>
								<div class="th-sub">{c.node?.industryName || ''}</div>
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each groupedRows() as group (group.section)}
						<tr class="section-row">
							<td colspan={companies.length + 1}>{group.section}</td>
						</tr>
						{#each group.rows as row (row.key)}
							{@const stats = rowStats(row)}
							{@const cls = rowClass(stats)}
							<tr class={cls}>
								<td class="label">{row.label}</td>
								{#each companies as c (c.node?.id)}
									{@const v = row.valueOf(c)}
									{@const isMax = stats.max !== null && v === stats.max && companies.length > 1}
									{@const isMin = stats.min !== null && v === stats.min && companies.length > 1}
									<td class="val" style:background={cellColor(row, c)}>
										<span class="val-text">{row.fmt(v)}</span>
										{#if typeof v === 'number' && !isNaN(v)}
											{#if isMax && !row.invertGoodness}<span class="mark good">▲</span>{/if}
											{#if isMin && !row.invertGoodness}<span class="mark bad">▼</span>{/if}
											{#if isMax && row.invertGoodness}<span class="mark bad">▼</span>{/if}
											{#if isMin && row.invertGoodness}<span class="mark good">▲</span>{/if}
										{/if}
									</td>
								{/each}
							</tr>
						{/each}
					{/each}
				</tbody>
			</table>
		</div>

		<!-- 공통 파트너 교집합 -->
		{#if commonSuppliers.length > 0 || commonCustomers.length > 0}
			<div class="commons">
				{#if commonSuppliers.length > 0}
					<div class="common-group">
						<h3>공통 공급사 ({commonSuppliers.length})</h3>
						<p class="common-desc">이 회사들 모두가 공통으로 받아쓰는 공급사 · 같은 밸류체인/경쟁 관계의 지표.</p>
						<ul>
							{#each commonSuppliers as s (s.stockCode)}
								<li>
									<a href="{base}/map?focus={s.stockCode}">{s.corpName}</a>
									{#if s.product}<span class="prod">· {s.product}</span>{/if}
								</li>
							{/each}
						</ul>
					</div>
				{/if}
				{#if commonCustomers.length > 0}
					<div class="common-group">
						<h3>공통 고객사 ({commonCustomers.length})</h3>
						<p class="common-desc">이 회사들 모두가 판매하는 고객사 · 수요 집중 리스크.</p>
						<ul>
							{#each commonCustomers as c (c.stockCode)}
								<li><a href="{base}/map?focus={c.stockCode}">{c.corpName}</a></li>
							{/each}
						</ul>
					</div>
				{/if}
			</div>
		{/if}

		<!-- 공유 URL -->
		<div class="share">
			<span>이 비교 공유:</span>
			<code>{page.url.pathname}?codes={codes.join(',')}</code>
		</div>

		<div class="disclaimer">
			dartlab 은 공시·재무 데이터를 시각화합니다. 투자 자문 아님. 자동 하이라이트(▲▼)는 비교 대상 중 상대값 · 업종 전체 평균 아님.
		</div>
	{/if}
</div>

<style>
	.page {
		max-width: 1400px;
		margin: 0 auto;
		padding: 32px 24px 80px;
		color: #f1f5f9;
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 24px;
		margin-bottom: 24px;
	}
	.back {
		font-size: 12px;
		color: #60a5fa;
		text-decoration: none;
		display: inline-block;
		margin-bottom: 8px;
	}
	.back:hover {
		text-decoration: underline;
	}
	.head h1 {
		margin: 0 0 6px;
		font-size: 28px;
		font-weight: 700;
	}
	.lead {
		margin: 0;
		font-size: 14px;
		color: #cbd5e1;
	}

	.loading,
	.empty {
		text-align: center;
		padding: 80px 24px;
		color: #94a3b8;
	}
	.empty code {
		background: #1e2433;
		padding: 2px 8px;
		border-radius: 4px;
		color: #60a5fa;
		font-size: 13px;
	}
	.empty .cta {
		display: inline-block;
		margin-top: 16px;
		padding: 8px 16px;
		background: #60a5fa;
		color: #050811;
		border-radius: 6px;
		text-decoration: none;
		font-weight: 600;
	}

	.hero {
		display: grid;
		gap: 12px;
		margin-bottom: 24px;
	}
	.hero-card {
		padding: 14px 16px;
		background: #0f1219;
		border: 1px solid #1e2433;
		border-radius: 8px;
	}
	.hero-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 8px;
	}
	.hero-card h2 {
		margin: 0;
		font-size: 16px;
	}
	.hero-card h2 a {
		color: #f1f5f9;
		text-decoration: none;
	}
	.hero-card h2 a:hover {
		color: #60a5fa;
	}
	.code {
		font-family: monospace;
		font-size: 11px;
		color: #64748b;
	}
	.badges {
		display: flex;
		gap: 4px;
		margin-top: 6px;
		flex-wrap: wrap;
	}
	.badge {
		font-size: 10px;
		padding: 2px 6px;
		border-radius: 3px;
	}
	.badge.stage {
		background: rgba(52, 211, 153, 0.15);
		color: #34d399;
	}
	.verdict {
		margin-top: 10px;
		padding: 8px 10px;
		background: rgba(96, 165, 250, 0.08);
		border-left: 2px solid #60a5fa;
		border-radius: 4px;
		font-size: 12px;
		line-height: 1.5;
		color: #cbd5e1;
	}

	.table-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 8px;
		gap: 16px;
		flex-wrap: wrap;
	}
	.legend {
		display: flex;
		gap: 16px;
		font-size: 11px;
		color: #64748b;
	}
	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: 5px;
	}
	.sw {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
	}
	.sw.common {
		background: rgba(96, 165, 250, 0.25);
	}
	.sw.differentiator {
		background: rgba(251, 191, 36, 0.25);
	}
	.copy-md {
		padding: 6px 12px;
		background: #1e2433;
		border: 1px solid #334155;
		border-radius: 6px;
		color: #cbd5e1;
		font-size: 12px;
		cursor: pointer;
	}
	.copy-md:hover {
		background: #2a3142;
		color: #f1f5f9;
	}

	.table-wrap {
		background: #0f1219;
		border: 1px solid #1e2433;
		border-radius: 8px;
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
	}
	thead th {
		padding: 10px 12px;
		text-align: left;
		border-bottom: 1px solid #1e2433;
		background: #050811;
		position: sticky;
		top: 0;
	}
	.th-name {
		font-weight: 600;
		color: #f1f5f9;
	}
	.th-sub {
		font-size: 10px;
		color: #64748b;
		font-weight: 400;
	}
	tbody td {
		padding: 8px 12px;
		border-bottom: 1px solid #1e2433;
	}
	tbody td.label {
		color: #94a3b8;
		font-size: 12px;
	}
	tbody td.val {
		font-family: monospace;
		font-weight: 600;
		position: relative;
	}
	.val-text {
		margin-right: 4px;
	}
	.mark {
		font-size: 10px;
	}
	.mark.good {
		color: #34d399;
	}
	.mark.bad {
		color: #f87171;
	}
	.section-row td {
		background: #050811;
		color: #60a5fa;
		font-weight: 600;
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 6px 12px;
	}
	tr.common td.label {
		color: #60a5fa;
	}
	tr.differentiator td.label {
		color: #fbbf24;
	}

	.commons {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
		margin-top: 24px;
	}
	.common-group {
		padding: 14px 16px;
		background: #0f1219;
		border: 1px solid #1e2433;
		border-radius: 8px;
	}
	.common-group h3 {
		margin: 0 0 6px;
		font-size: 13px;
		color: #f1f5f9;
	}
	.common-desc {
		margin: 0 0 8px;
		font-size: 11px;
		color: #64748b;
		line-height: 1.5;
	}
	.common-group ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.common-group li {
		padding: 4px 0;
		font-size: 12px;
		border-bottom: 1px dashed #1e2433;
	}
	.common-group li:last-child {
		border-bottom: none;
	}
	.common-group li a {
		color: #60a5fa;
		text-decoration: none;
	}
	.common-group li a:hover {
		text-decoration: underline;
	}
	.prod {
		color: #64748b;
		font-size: 11px;
	}

	.share {
		margin-top: 20px;
		padding: 10px 14px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		font-size: 12px;
		color: #94a3b8;
		display: flex;
		gap: 10px;
		align-items: center;
		overflow-x: auto;
	}
	.share code {
		color: #60a5fa;
		font-family: monospace;
		white-space: nowrap;
	}

	.disclaimer {
		margin-top: 12px;
		font-size: 11px;
		color: #475569;
		line-height: 1.6;
	}

	@media (max-width: 768px) {
		.commons {
			grid-template-columns: 1fr;
		}
	}
</style>
