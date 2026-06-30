<script lang="ts">
	import { base } from '$app/paths';
	import { FreshnessBadge } from '@dartlab/ui-surfaces/map';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	type CategoryKey =
		| 'profitImprove'
		| 'profitDecline'
		| 'revenueSpike'
		| 'revenueDrop'
		| 'debtStress'
		| 'extremeWarning';

	const CATEGORY_ORDER: CategoryKey[] = [
		'profitImprove',
		'profitDecline',
		'revenueSpike',
		'revenueDrop',
		'debtStress',
		'extremeWarning'
	];

	const CATEGORY_ICONS: Record<CategoryKey, string> = {
		profitImprove: '📈',
		profitDecline: '📉',
		revenueSpike: '🚀',
		revenueDrop: '⬇',
		debtStress: '⚠',
		extremeWarning: '🔬'
	};

	const CATEGORY_COLORS: Record<CategoryKey, string> = {
		profitImprove: '#34d399',
		profitDecline: '#f87171',
		revenueSpike: '#60a5fa',
		revenueDrop: '#fb923c',
		debtStress: '#fbbf24',
		extremeWarning: '#94a3b8'
	};

	let activeTab: CategoryKey = $state('profitImprove');

	function mdRow(e: any): string {
		const cells = [
			e.corpName,
			e.stockCode,
			e.industryName,
			(e.roe ?? '-') !== '-' ? `${e.roe}%` : '-',
			(e.roeDelta ?? '-') !== '-' ? `${e.roeDelta > 0 ? '+' : ''}${e.roeDelta}%p` : '-',
			(e.revenueYoyPct ?? '-') !== '-' ? `${e.revenueYoyPct > 0 ? '+' : ''}${e.revenueYoyPct}%` : '-',
			(e.signal || '').replace(/\|/g, '-')
		];
		return `| ${cells.join(' | ')} |`;
	}

	function copyMarkdown(entries: any[], title: string) {
		const header = `# ${title} · dartlab ${data.movers.asOf}\n\n`;
		const tableHead =
			'| 회사 | 종목코드 | 산업 | ROE | ROE YoY | 매출 YoY | 신호 |\n' +
			'|---|---|---|---|---|---|---|\n';
		const rows = entries.map(mdRow).join('\n');
		const footer = `\n\n> 출처: dartlab ${base || ''}/changes · ${data.movers.disclaimer}\n`;
		navigator.clipboard.writeText(header + tableHead + rows + footer);
	}
</script>

<svelte:head>
	<title>변화 감지 | dartlab 전자공시</title>
	<meta
		name="description"
		content="한국 상장사 이번 분기 급변 Top N. ROE 개선/악화, 매출 급증/급락, 부채 스트레스, 극단 이상치."
	/>
	<meta property="og:type" content="website" />
	<meta property="og:title" content="변화 감지 · dartlab" />
	<meta
		property="og:description"
		content="한국 상장사 이번 회계연도 급변 Top. ROE·매출·부채 6 카테고리 자동 감지."
	/>
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta name="twitter:card" content="summary_large_image" />
	<link rel="alternate" type="application/rss+xml" title="dartlab 변화 감지 RSS" href="{base}/feed/movers.xml" />
</svelte:head>

<div class="page">
	<header class="head">
		<div class="head-left">
			<a class="back" href="{base}/map">← 산업지도</a>
			<h1>변화 감지</h1>
			<p class="lead">
				한국 상장사 중 이번 회계연도에 <strong>유의미하게 변한</strong> 회사를 카테고리별로.
			</p>
		</div>
		{#if data.meta?.dataAsOf}
			<FreshnessBadge dataAsOf={data.meta.dataAsOf} variant="compact" />
		{/if}
	</header>

	<!-- 카테고리 탭 -->
	<nav class="tabs">
		{#each CATEGORY_ORDER as key (key)}
			{@const cat = data.movers.categories?.[key]}
			{#if cat}
				<button
					class="tab"
					class:active={activeTab === key}
					onclick={() => (activeTab = key)}
					style:border-bottom-color={activeTab === key ? CATEGORY_COLORS[key] : 'transparent'}
				>
					<span class="tab-icon">{CATEGORY_ICONS[key]}</span>
					<span class="tab-title">{cat.title}</span>
					<span class="tab-count">{cat.entries.length}</span>
				</button>
			{/if}
		{/each}
	</nav>

	<!-- 설명 + 액션 -->
	{#if data.movers.categories?.[activeTab]}
		{@const cat = data.movers.categories[activeTab]}
		<div class="cat-head">
			<p class="cat-desc">{cat.description}</p>
			<button class="copy-md" onclick={() => copyMarkdown(cat.entries, cat.title)}>
				📋 Markdown 복사 (기자용)
			</button>
		</div>

		<!-- 테이블 -->
		<div class="table-wrap">
			<table>
				<thead>
					<tr>
						<th>회사</th>
						<th>산업</th>
						<th class="num">ROE</th>
						<th class="num">ROE Δ</th>
						<th class="num">매출 YoY</th>
						<th class="num">부채 Δ</th>
						<th>신호</th>
						<th></th>
					</tr>
				</thead>
				<tbody>
					{#each cat.entries as e (e.stockCode)}
						<tr>
							<td>
								<div class="cell-main">
									<a href="{base}/map?focus={e.stockCode}" class="name">{e.corpName}</a>
									<span class="code">{e.stockCode}</span>
								</div>
							</td>
							<td>
								<a href="{base}/map?industry={e.industry}" class="ind">{e.industryName}</a>
							</td>
							<td class="num">{e.roe !== null && e.roe !== undefined ? `${e.roe}%` : '-'}</td>
							<td class="num" style:color={e.roeDelta > 0 ? '#34d399' : e.roeDelta < 0 ? '#f87171' : '#64748b'}>
								{e.roeDelta !== null && e.roeDelta !== undefined
									? `${e.roeDelta > 0 ? '+' : ''}${e.roeDelta}%p`
									: '-'}
							</td>
							<td class="num" style:color={e.revenueYoyPct > 0 ? '#34d399' : e.revenueYoyPct < 0 ? '#f87171' : '#64748b'}>
								{e.revenueYoyPct !== null && e.revenueYoyPct !== undefined
									? `${e.revenueYoyPct > 0 ? '+' : ''}${e.revenueYoyPct}%`
									: '-'}
							</td>
							<td class="num" style:color={e.debtRatioDelta > 20 ? '#f87171' : e.debtRatioDelta < 0 ? '#34d399' : '#64748b'}>
								{e.debtRatioDelta !== null && e.debtRatioDelta !== undefined
									? `${e.debtRatioDelta > 0 ? '+' : ''}${e.debtRatioDelta}%p`
									: '-'}
							</td>
							<td class="signal">{e.signal || ''}</td>
							<td>
								<a href="{base}/map?focus={e.stockCode}" class="open">→ 상세</a>
							</td>
						</tr>
						{#if e.note}
							<tr class="note-row">
								<td colspan="8" class="note-cell">
									<span class="note-label">해석 참고</span>
									{e.note}
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	<div class="disclaimer">
		{data.movers.disclaimer || ''}
	</div>
</div>

<style>
	.page {
		max-width: 1200px;
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
	.head-left {
		flex: 1;
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
		max-width: 720px;
	}
	.lead strong {
		color: #f1f5f9;
	}

	.tabs {
		display: flex;
		gap: 4px;
		margin-bottom: 18px;
		border-bottom: 1px solid #1e2433;
		overflow-x: auto;
	}
	.tab {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 10px 14px;
		background: transparent;
		border: none;
		border-bottom: 2px solid transparent;
		color: #94a3b8;
		cursor: pointer;
		font-size: 13px;
		white-space: nowrap;
	}
	.tab:hover:not(.active) {
		color: #cbd5e1;
		background: rgba(30, 36, 51, 0.4);
	}
	.tab.active {
		color: #f1f5f9;
		font-weight: 600;
	}
	.tab-icon {
		font-size: 16px;
	}
	.tab-count {
		font-size: 10px;
		font-family: monospace;
		color: #64748b;
		background: #050811;
		padding: 2px 6px;
		border-radius: 8px;
	}

	.cat-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 16px;
		margin-bottom: 12px;
	}
	.cat-desc {
		margin: 0;
		color: #94a3b8;
		font-size: 13px;
		line-height: 1.6;
	}
	.copy-md {
		padding: 8px 12px;
		background: #1e2433;
		border: 1px solid #334155;
		border-radius: 6px;
		color: #cbd5e1;
		font-size: 12px;
		cursor: pointer;
		white-space: nowrap;
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
		text-align: left;
		padding: 10px 12px;
		font-size: 11px;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid #1e2433;
		background: #050811;
		position: sticky;
		top: 0;
	}
	thead th.num {
		text-align: right;
	}
	tbody td {
		padding: 10px 12px;
		border-bottom: 1px solid #1e2433;
		vertical-align: top;
	}
	tbody td.num {
		text-align: right;
		font-family: monospace;
		font-weight: 600;
	}
	tbody tr:last-child td {
		border-bottom: none;
	}
	.cell-main {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.name {
		color: #f1f5f9;
		font-weight: 600;
		text-decoration: none;
	}
	.name:hover {
		color: #60a5fa;
	}
	.code {
		font-family: monospace;
		font-size: 10px;
		color: #64748b;
	}
	.ind {
		color: #a78bfa;
		text-decoration: none;
	}
	.ind:hover {
		text-decoration: underline;
	}
	.signal {
		color: #cbd5e1;
		font-size: 12px;
	}
	.open {
		color: #60a5fa;
		text-decoration: none;
		font-size: 12px;
		white-space: nowrap;
	}
	.open:hover {
		text-decoration: underline;
	}
	.note-row .note-cell {
		padding: 4px 12px 10px 12px;
		font-size: 11px;
		color: #64748b;
		background: rgba(30, 36, 51, 0.25);
		border-bottom: 1px solid #1e2433;
	}
	.note-label {
		color: #94a3b8;
		font-weight: 600;
		margin-right: 6px;
	}

	.disclaimer {
		margin-top: 24px;
		padding: 12px 16px;
		background: rgba(251, 191, 36, 0.08);
		border: 1px solid rgba(251, 191, 36, 0.25);
		border-radius: 6px;
		font-size: 12px;
		color: #fbbf24;
		line-height: 1.6;
	}
</style>
