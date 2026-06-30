<script lang="ts">
	import Header from '$lib/components/sections/Header.svelte';
	import {
		probeHfRange,
		readParquetMetadata,
		readParquetRows,
		type ParquetMetadataSummary,
		type RangeRequestStat
	} from '@dartlab/ui-runtime/data/parquet/hfRange';

	const TARGETS = [
		{
			label: 'valuation',
			path: 'dart/scan/valuation.parquet',
			columns: ['stockCode', 'marketCap', 'per', 'pbr', 'dividendYield']
		},
		{
			label: 'finance-lite',
			path: 'dart/scan/finance-lite.parquet',
			columns: ['stockCode', 'bsns_year', 'account_id', 'thstrm_amount']
		},
		{
			label: 'krx raw current',
			path: `gov/prices/date/${new Date().getFullYear()}.parquet`,
			columns: ['BAS_DD', 'ISU_CD', 'ISU_NM', 'TDD_CLSPRC', 'MKTCAP']
		}
	];

	type Stage = 'idle' | 'running' | 'done' | 'error';

	let stage = $state<Stage>('idle');
	let errorMessage = $state('');
	let metadata = $state<ParquetMetadataSummary[]>([]);
	let rows = $state<Record<string, unknown>[]>([]);
	let requests = $state<RangeRequestStat[]>([]);
	let activePath = $state(TARGETS[0].path);

	async function runProbe() {
		stage = 'running';
		errorMessage = '';
		metadata = [];
		rows = [];
		requests = [];
		try {
			for (const target of TARGETS) {
				const probe = await probeHfRange(target.path);
				if (probe.status !== 206) {
					throw new Error(`${target.path} range probe 실패: ${probe.status}`);
				}
				const meta = await readParquetMetadata(target.path);
				metadata = [...metadata, meta];
				requests = [...requests, ...meta.requests];
			}
			const target = TARGETS.find((item) => item.path === activePath) ?? TARGETS[0];
			const sample = await readParquetRows(target.path, {
				columns: target.columns,
				rowStart: 0,
				rowEnd: 20
			});
			rows = sample.rows;
			requests = [...requests, ...sample.requests];
			stage = 'done';
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : String(err);
			stage = 'error';
		}
	}

	let totalBytes = $derived(requests.reduce((sum, req) => sum + req.bytes, 0));
</script>

<svelte:head>
	<title>HF Range Lab · dartlab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<Header context="landing" />

<main class="page">
	<section class="head">
		<div>
			<span class="eyebrow">lab · hf range runtime</span>
			<h1>HF Parquet Range Probe</h1>
		</div>
		<button type="button" onclick={runProbe} disabled={stage === 'running'}>
			{stage === 'running' ? '검증 중' : 'Range 검증'}
		</button>
	</section>

	<section class="targets">
		{#each TARGETS as target}
			<button
				type="button"
				class:active={activePath === target.path}
				onclick={() => (activePath = target.path)}
			>
				<strong>{target.label}</strong>
				<span>{target.path}</span>
			</button>
		{/each}
	</section>

	{#if errorMessage}
		<section class="panel error">{errorMessage}</section>
	{/if}

	<section class="summary">
		<div><span>stage</span><strong>{stage}</strong></div>
		<div><span>requests</span><strong>{requests.length}</strong></div>
		<div><span>transferred</span><strong>{totalBytes.toLocaleString('ko-KR')} bytes</strong></div>
		<div><span>sample rows</span><strong>{rows.length}</strong></div>
	</section>

	<section class="grid">
		<div class="panel">
			<h2>Metadata</h2>
			{#if metadata.length === 0}
				<p class="muted">아직 실행 전입니다.</p>
			{:else}
				{#each metadata as meta}
					<article>
						<strong>{meta.path}</strong>
						<p>{meta.rows.toLocaleString('ko-KR')} rows · {meta.rowGroups} row groups · {meta.size.toLocaleString('ko-KR')} bytes</p>
						<small>{meta.columns.join(', ')}</small>
					</article>
				{/each}
			{/if}
		</div>

		<div class="panel">
			<h2>Range Requests</h2>
			{#if requests.length === 0}
				<p class="muted">아직 range 요청이 없습니다.</p>
			{:else}
				<table>
					<thead><tr><th>status</th><th>range</th><th>bytes</th><th>ms</th></tr></thead>
					<tbody>
						{#each requests as req, i}
							<tr>
								<td>{req.status}</td>
								<td>{req.range ?? '·'}</td>
								<td>{req.bytes.toLocaleString('ko-KR')}</td>
								<td>{req.durationMs.toFixed(0)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}
		</div>
	</section>

	<section class="panel">
		<h2>Sample Rows</h2>
		<pre>{JSON.stringify(rows, null, 2)}</pre>
	</section>
</main>

<style>
	.page {
		min-height: 100vh;
		padding: 76px 20px 40px;
		background: #050811;
		color: #e5e7eb;
	}
	.head,
	.targets,
	.summary,
	.grid,
	.panel {
		max-width: 1180px;
		margin: 0 auto;
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 16px;
		padding-bottom: 18px;
		border-bottom: 1px solid #1e2433;
	}
	.eyebrow {
		color: var(--dl-accent);
		font-size: 11px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}
	h1 {
		margin: 6px 0 0;
		font-size: 36px;
		letter-spacing: 0;
	}
	button {
		border: 1px solid var(--dl-accent);
		border-radius: 5px;
		background: rgba(var(--dl-accent-rgb), 0.08);
		color: var(--dl-accent);
		padding: 8px 12px;
		font: inherit;
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.55;
		cursor: wait;
	}
	.targets {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 8px;
		padding: 14px 0;
	}
	.targets button {
		text-align: left;
		border-color: #263145;
		background: #080d17;
		color: #cbd5e1;
	}
	.targets button.active {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
	}
	.targets strong,
	.targets span {
		display: block;
	}
	.targets span {
		margin-top: 4px;
		color: #64748b;
		font-size: 11px;
		font-family: monospace;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.summary {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 8px;
		margin-bottom: 12px;
	}
	.summary div,
	.panel {
		border: 1px solid #1e2433;
		border-radius: 7px;
		background: #080d17;
	}
	.summary div {
		padding: 12px;
	}
	.summary span {
		display: block;
		color: #64748b;
		font-size: 11px;
		text-transform: uppercase;
	}
	.summary strong {
		display: block;
		margin-top: 6px;
	}
	.grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 12px;
		margin-bottom: 12px;
	}
	.panel {
		padding: 14px;
	}
	h2 {
		margin: 0 0 12px;
		font-size: 16px;
	}
	article {
		padding: 10px 0;
		border-top: 1px solid #172033;
	}
	article p,
	article small,
	.muted {
		color: #94a3b8;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 12px;
	}
	th,
	td {
		padding: 7px 8px;
		border-bottom: 1px solid #172033;
		text-align: left;
	}
	pre {
		overflow: auto;
		max-height: 420px;
		margin: 0;
		color: #cbd5e1;
		font-size: 12px;
	}
	.error {
		margin-bottom: 12px;
		border-color: rgba(239, 68, 68, 0.4);
		color: #fca5a5;
	}
	@media (max-width: 900px) {
		.targets,
		.summary,
		.grid {
			grid-template-columns: 1fr;
		}
		.head {
			align-items: stretch;
			flex-direction: column;
		}
	}
</style>
