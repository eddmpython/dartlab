<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import Section from '$lib/components/ui/Section.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Eyebrow from '$lib/components/ui/Eyebrow.svelte';
	import MonoNumber from '$lib/components/ui/MonoNumber.svelte';
	import Tag from '$lib/components/ui/Tag.svelte';
	import Bar from '$lib/components/ui/Bar.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { Sparkline } from '@dartlab/ui-surfaces/scan/viz';
	import { fmtKrwFromEok } from '@dartlab/ui-format/krw';
	import { fmtPct } from '@dartlab/ui-format/pct';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const allNodes = $derived((data.ecosystem as any)?.nodes ?? []);

	// URL ?codes=005930,000660,035420,000270 · 기본 4 큰 회사
	const codesParam = $derived(page.url?.searchParams?.get('codes') ?? '005930,000660,035420,000270');
	let codes = $state<string[]>([]);
	$effect(() => {
		codes = codesParam.split(',').filter(Boolean).slice(0, 4);
	});

	const selected = $derived(
		codes.map((c) => allNodes.find((n: any) => n.id === c)).filter(Boolean)
	);

	// 검색 (회사 추가)
	let searchQ = $state('');
	const searchResults = $derived.by(() => {
		const q = searchQ.trim().toLowerCase();
		if (!q) return [];
		return allNodes
			.filter((n: any) => !codes.includes(n.id))
			.filter((n: any) =>
				n.id?.toLowerCase().includes(q) ||
				n.label?.toLowerCase().includes(q) ||
				n.industryName?.toLowerCase().includes(q)
			)
			.slice(0, 6);
	});

	function addCode(code: string) {
		if (codes.length >= 4 || codes.includes(code)) return;
		codes = [...codes, code];
		searchQ = '';
	}
	function removeCode(code: string) {
		codes = codes.filter((c) => c !== code);
	}

	// ── 비교 metric 5축 (정규화) ──
	type Axis = { key: string; label: string; suffix: string; higher: boolean };
	const AXES: Axis[] = [
		{ key: 'roe', label: 'ROE', suffix: '%', higher: true },
		{ key: 'opMargin', label: '영업이익률', suffix: '%', higher: true },
		{ key: 'revCagr', label: '매출 CAGR', suffix: '%', higher: true },
		{ key: 'debtRatio', label: '부채비율', suffix: '%', higher: false },
		{ key: 'revenue', label: '매출 (조원)', suffix: '', higher: true }
	];

	// 색상 (4 회사 구분)
	const PALETTE = ['#ea4647', '#fb923c', '#34d399', '#60a5fa'];

	// radar
	const RADAR_SIZE = 360;
	const RADAR_R = 130;
	const RADAR_CX = RADAR_SIZE / 2;
	const RADAR_CY = RADAR_SIZE / 2;

	// 각 축의 min/max 로 정규화
	function axisRange(axis: Axis) {
		const vals = selected.map((n: any) => n[axis.key]).filter((v: any) => Number.isFinite(v));
		if (!vals.length) return { min: 0, max: 1 };
		return { min: Math.min(...vals), max: Math.max(...vals) };
	}

	function normalize(v: number, axis: Axis): number {
		const r = axisRange(axis);
		if (r.max === r.min) return 0.5;
		const t = (v - r.min) / (r.max - r.min);
		return axis.higher ? t : 1 - t;
	}

	function axisPoint(angleI: number, normVal: number) {
		const angle = -Math.PI / 2 + (angleI * 2 * Math.PI) / AXES.length;
		const r = normVal * RADAR_R;
		return [RADAR_CX + r * Math.cos(angle), RADAR_CY + r * Math.sin(angle)];
	}

	function polyPoints(node: any): string {
		return AXES.map((axis, i) => {
			const v = node[axis.key];
			const t = Number.isFinite(v) ? normalize(v, axis) : 0;
			const [x, y] = axisPoint(i, t);
			return `${x},${y}`;
		}).join(' ');
	}

	function ringPoints(t: number): string {
		return AXES.map((_, i) => {
			const [x, y] = axisPoint(i, t);
			return `${x},${y}`;
		}).join(' ');
	}
</script>

<svelte:head>
	<title>회사 비교 · /lab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<header class="lab-nav">
	<div class="nav-inner">
		<a href="{base}/lab" class="brand">
			<span class="brand-mark">dartlab</span>
			<span class="brand-slash">/</span>
			<span class="brand-ctx">lab · compare</span>
		</a>
		<div class="nav-actions">
			<Button variant="ghost" size="sm" href="{base}/lab/map">/map</Button>
			<Button variant="ghost" size="sm" href="{base}/terminal">/terminal</Button>
			<Button variant="ghost" size="sm" href="{base}/lab/duckdb">/duckdb</Button>
		</div>
	</div>
</header>

<section class="hero">
	<div class="hero-inner">
		<Eyebrow text="EXPLORE · 회사 비교" />
		<h1 class="hero-h1">최대 4사 5축 비교</h1>
		<p class="hero-sub">URL <span class="dl-mono">?codes=A,B,C,D</span> 또는 검색으로 회사 추가. 각 축은 4사 안에서 정규화 (relative scale).</p>
	</div>
</section>

<!-- 선택된 회사 칩 + 추가 입력 -->
<Section eyebrow="SELECTED · {selected.length}/4" title="비교 대상" container="max">
	<div class="chips-row">
		{#each selected as n, i}
			<div class="chip" style="--c: {PALETTE[i]}">
				<span class="chip-dot"></span>
				<span class="chip-code dl-mono">{n.id}</span>
				<span class="chip-name">{n.label}</span>
				<button class="chip-x" onclick={() => removeCode(n.id)} aria-label="제거">×</button>
			</div>
		{/each}
		{#if selected.length < 4}
			<div class="chip-add">
				<input
					type="text"
					placeholder="회사 추가 (이름/코드)"
					bind:value={searchQ}
				/>
				{#if searchResults.length > 0}
					<div class="chip-search">
						{#each searchResults as r}
							<button class="search-row" onclick={() => addCode(r.id)}>
								<span class="dl-mono">{r.id}</span>
								<span>{r.label}</span>
								<span class="r-ind">{r.industryName ?? ''}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</Section>

{#if selected.length >= 2}
	<!-- 레이더 + 비교 표 -->
	<Section eyebrow="RADAR · 5축" title="정규화된 비교" subtitle="각 축은 선택한 4사 안에서 0~1 로 정규화. 부채비율은 낮을수록 좋게 (반전).">
		<div class="cmp-grid">
			<Card padded>
				<svg viewBox="0 0 {RADAR_SIZE} {RADAR_SIZE}" width="100%" style="max-width: {RADAR_SIZE}px; display: block; margin: 0 auto;">
					<!-- rings -->
					{#each [0.25, 0.5, 0.75, 1.0] as t}
						<polygon points={ringPoints(t)} fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1" />
					{/each}
					<!-- axes -->
					{#each AXES as axis, i}
						{@const [x, y] = axisPoint(i, 1)}
						<line x1={RADAR_CX} y1={RADAR_CY} x2={x} y2={y} stroke="rgba(255,255,255,0.06)" stroke-width="1" />
					{/each}
					<!-- polygons -->
					{#each selected as n, i}
						<polygon
							points={polyPoints(n)}
							fill={PALETTE[i]}
							fill-opacity="0.12"
							stroke={PALETTE[i]}
							stroke-width="1.6"
						/>
					{/each}
					<!-- labels -->
					{#each AXES as axis, i}
						{@const [lx, ly] = axisPoint(i, 1.18)}
						<text
							x={lx}
							y={ly}
							text-anchor="middle"
							dominant-baseline="middle"
							font-size="11"
							fill="var(--dl-ink-mute)"
							font-family="var(--dl-font-ui)"
							font-weight="600"
						>{axis.label}</text>
					{/each}
				</svg>

				<!-- legend -->
				<div class="legend">
					{#each selected as n, i}
						<div class="leg-row">
							<span class="leg-sw" style="background: {PALETTE[i]}"></span>
							<span class="leg-name">{n.label}</span>
							<span class="leg-code dl-mono">{n.id}</span>
						</div>
					{/each}
				</div>
			</Card>

			<Card eyebrow="TABLE · 절대값" padded>
				<table class="cmp-table">
					<thead>
						<tr>
							<th class="dl-label">축</th>
							{#each selected as n, i}
								<th class="dl-label" style="color: {PALETTE[i]}; text-align: right;">{n.id}</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each AXES as axis}
							<tr>
								<td class="ax-label">{axis.label}</td>
								{#each selected as n, i}
									{@const v = n[axis.key]}
									<td style="text-align: right;">
										{#if axis.key === 'revenue'}
											<MonoNumber value={fmtKrwFromEok(v)} size="sm" tone="ink" align="right" />
										{:else}
											<MonoNumber value={fmtPct(v)} size="sm" tone="ink" align="right" />
										{/if}
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</Card>
		</div>
	</Section>

	<!-- 회사별 상세 카드 -->
	<Section eyebrow="DETAIL · 회사별" title="개별 카드" container="max">
		<div class="detail-grid">
			{#each selected as n, i}
				<Card eyebrow={n.id} accent={(['red', 'orange', 'good', 'info'] as any)[i]} padded>
					<h3 class="detail-name">{n.label}</h3>
					<div class="detail-meta">
						<Tag>{n.industryName ?? '·'}</Tag>
						{#if n.stageName}<Tag tone="info">{n.stageName}</Tag>{/if}
					</div>
					<div class="detail-rev">
						<span class="dl-label">매출</span>
						<MonoNumber value={fmtKrwFromEok(n.revenue)} size="lg" tone="ink" align="left" />
					</div>
					<dl class="detail-list">
						{#each AXES.filter((a) => a.key !== 'revenue') as axis}
							<div class="d-row">
								<dt class="dl-eyebrow">{axis.label}</dt>
								<dd><MonoNumber value={fmtPct(n[axis.key])} size="sm" tone="ink" align="right" /></dd>
							</div>
						{/each}
					</dl>
					<div style="margin-top: var(--dl-s-3); padding-top: var(--dl-s-3); border-top: 1px solid var(--dl-line);">
						<Button href="{base}/terminal?sym={n.id}" variant="ghost" size="sm" fullWidth>터미널 →</Button>
					</div>
				</Card>
			{/each}
		</div>
	</Section>
{:else}
	<Section container="article">
		<Card padded>
			<p class="dl-body" style="text-align: center; color: var(--dl-ink-mute)">
				최소 2 사 선택 (현재 {selected.length}). 위 입력에서 검색하여 추가.
			</p>
		</Card>
	</Section>
{/if}

<footer class="lab-foot">
	<Eyebrow text="END · /lab/compare · Phase 3 EXPLORE prototype" />
</footer>

<style>
	.lab-nav {
		position: sticky; top: 0; z-index: 30;
		border-bottom: 1px solid var(--dl-line);
		background: rgba(15, 15, 16, 0.85);
		backdrop-filter: blur(14px);
	}
	.nav-inner {
		max-width: var(--dl-w-max); margin-inline: auto;
		padding: var(--dl-s-3) var(--dl-s-6);
		display: flex; justify-content: space-between; align-items: center;
	}
	.brand { display: inline-flex; align-items: baseline; gap: var(--dl-s-2); text-decoration: none; color: var(--dl-ink); }
	.brand-mark { font-family: var(--dl-font-head); font-weight: 700; font-size: 18px; letter-spacing: -0.02em; }
	.brand-slash { color: var(--dl-ink-faint); font-weight: 300; }
	.brand-ctx { font-family: var(--dl-font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.16em; color: var(--dl-orange); }
	.nav-actions { display: flex; gap: var(--dl-s-1); }

	.hero { padding: var(--dl-s-7) var(--dl-s-6) var(--dl-s-5); }
	.hero-inner { max-width: var(--dl-w-max); margin-inline: auto; }
	.hero-h1 { font-family: var(--dl-font-ui); font-size: clamp(28px, 4vw, 42px); font-weight: 800; letter-spacing: -0.025em; line-height: 1.1; color: var(--dl-ink-print); margin: var(--dl-s-3) 0 var(--dl-s-3); }
	.hero-sub { font-size: 14px; color: var(--dl-ink-mute); line-height: 1.6; max-width: var(--dl-w-article); margin: 0; }

	/* chips */
	.chips-row { display: flex; flex-wrap: wrap; gap: var(--dl-s-3); align-items: center; }
	.chip {
		display: inline-flex; align-items: center; gap: var(--dl-s-2);
		padding: 6px 4px 6px 10px;
		border: 1px solid var(--c, var(--dl-line));
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-overlay);
		font-size: 13px;
	}
	.chip-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--c); }
	.chip-code { color: var(--dl-ink-mute); font-size: 11px; }
	.chip-name { color: var(--dl-ink-print); font-weight: 500; }
	.chip-x {
		width: 22px; height: 22px; border-radius: var(--dl-r-sm); border: none;
		background: transparent; color: var(--dl-ink-dim); cursor: pointer;
		font-size: 16px; line-height: 1; display: grid; place-items: center;
	}
	.chip-x:hover { background: var(--dl-bg-modal); color: var(--dl-ink); }

	.chip-add { position: relative; min-width: 240px; }
	.chip-add input {
		width: 100%;
		padding: 8px 12px;
		background: var(--dl-bg-base);
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		color: var(--dl-ink);
		font-family: var(--dl-font-ui);
		font-size: 13px;
	}
	.chip-add input:focus {
		outline: none;
		border-color: var(--dl-orange);
	}
	.chip-search {
		position: absolute; left: 0; right: 0; top: calc(100% + 4px);
		background: var(--dl-bg-modal);
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-md);
		overflow: hidden;
		z-index: 10;
		box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.6);
	}
	.search-row {
		display: grid; grid-template-columns: 56px 1fr auto;
		gap: var(--dl-s-2); align-items: center;
		width: 100%; padding: var(--dl-s-2) var(--dl-s-3);
		border: none; background: transparent; text-align: left; cursor: pointer;
		color: var(--dl-ink); font-size: 12px;
		transition: background var(--dl-dur-hover) var(--dl-ease);
	}
	.search-row:hover { background: var(--dl-bg-overlay); }
	.r-ind { color: var(--dl-ink-mute); font-size: 11px; }

	/* compare grid */
	.cmp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--dl-s-3); align-items: start; }
	.legend { display: flex; flex-direction: column; gap: var(--dl-s-2); margin-top: var(--dl-s-4); padding-top: var(--dl-s-3); border-top: 1px solid var(--dl-line); }
	.leg-row { display: grid; grid-template-columns: 12px 1fr auto; gap: var(--dl-s-2); align-items: center; font-size: 13px; }
	.leg-sw { width: 12px; height: 3px; border-radius: 2px; }
	.leg-name { color: var(--dl-ink-print); }
	.leg-code { color: var(--dl-ink-dim); font-size: 11px; }

	.cmp-table { width: 100%; border-collapse: collapse; font-size: 12px; }
	.cmp-table th, .cmp-table td { padding: var(--dl-s-2) var(--dl-s-3); border-bottom: 1px solid var(--dl-line); }
	.cmp-table th { text-align: left; font-size: 10px; }
	.cmp-table tr:last-child td { border-bottom: none; }
	.ax-label { color: var(--dl-ink); font-weight: 500; }

	/* detail */
	.detail-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--dl-s-3); }
	.detail-name { font-size: 18px; font-weight: 700; letter-spacing: -0.015em; color: var(--dl-ink-print); margin: var(--dl-s-2) 0 var(--dl-s-2); line-height: 1.2; }
	.detail-meta { display: flex; gap: var(--dl-s-1); flex-wrap: wrap; margin-bottom: var(--dl-s-3); }
	.detail-rev { display: flex; flex-direction: column; gap: var(--dl-s-1); padding-bottom: var(--dl-s-3); border-bottom: 1px solid var(--dl-line); margin-bottom: var(--dl-s-3); }
	.detail-list { margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--dl-s-2); }
	.d-row { display: flex; justify-content: space-between; align-items: baseline; }
	.d-row dt { margin: 0; }
	.d-row dd { margin: 0; }

	.lab-foot { padding: var(--dl-s-7) var(--dl-s-6); text-align: center; border-top: 1px solid var(--dl-line); }

	@media (max-width: 900px) {
		.cmp-grid { grid-template-columns: 1fr; }
		.detail-grid { grid-template-columns: repeat(2, 1fr); }
	}
	@media (max-width: 560px) {
		.detail-grid { grid-template-columns: 1fr; }
	}
</style>
