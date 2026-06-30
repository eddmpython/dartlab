<script lang="ts">
	import { Check, Minus, X } from 'lucide-svelte';

	interface RuntimeEntry {
		status?: string;
		notes?: string[];
		limitations?: string[];
		dataSources?: string[];
	}

	let {
		runtimeCompatibility = {}
	}: {
		runtimeCompatibility?: Record<string, RuntimeEntry>;
	} = $props();

	const order = [
		{ key: 'localPython', label: 'Local Python' },
		{ key: 'server', label: 'Server' },
		{ key: 'mcp', label: 'MCP' },
		{ key: 'webAi', label: 'Web AI' },
		{ key: 'pyodide', label: 'Pyodide' }
	];

	function statusOf(key: string): string {
		return runtimeCompatibility?.[key]?.status ?? 'unknown';
	}

	const hasAny = $derived(
		order.some((o) => Object.prototype.hasOwnProperty.call(runtimeCompatibility ?? {}, o.key))
	);
</script>

{#if hasAny}
	<section class="matrix" aria-label="실행 환경 호환성">
		<header class="head">
			<p class="kicker">런타임</p>
			<h2>실행 환경별 호환성</h2>
		</header>
		<table>
			<thead>
				<tr>
					<th class="col-env">환경</th>
					<th class="col-status">상태</th>
					<th class="col-notes">비고 / 제한</th>
				</tr>
			</thead>
			<tbody>
				{#each order as row}
					{@const status = statusOf(row.key)}
					{@const entry = runtimeCompatibility?.[row.key] ?? {}}
					<tr class="row st-{status}">
						<td class="col-env">{row.label}</td>
						<td class="col-status">
							{#if status === 'supported'}
								<span class="badge ok"><Check size={12} /> supported</span>
							{:else if status === 'limited'}
								<span class="badge limited"><Minus size={12} /> limited</span>
							{:else if status === 'unsupported'}
								<span class="badge no"><X size={12} /> unsupported</span>
							{:else}
								<span class="badge unk">unknown</span>
							{/if}
						</td>
						<td class="col-notes">
							{#if entry.notes?.length || entry.limitations?.length}
								<ul>
									{#each entry.notes ?? [] as n}<li>{n}</li>{/each}
									{#each entry.limitations ?? [] as l}<li class="lim">{l}</li>{/each}
								</ul>
							{:else}
								<span class="dim">·</span>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
{/if}

<style>
	.matrix {
		margin: 1.25rem 0;
		padding: 1.1rem 1.25rem;
		border: 1px solid var(--dl-line);
		border-left: 3px solid var(--dl-cat-runtime);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-raised);
	}

	.head {
		margin-bottom: 0.85rem;
	}

	.kicker {
		margin: 0 0 0.2rem;
		color: var(--dl-cat-runtime);
		font-size: 0.64rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		font-weight: 700;
	}

	.head h2 {
		margin: 0;
		font-size: 1rem;
		color: var(--dl-ink-print);
		font-weight: 600;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.84rem;
	}

	th, td {
		padding: 0.55rem 0.6rem;
		border-bottom: 1px solid var(--dl-line);
		text-align: left;
		vertical-align: top;
	}

	thead th {
		font-size: 0.7rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
		font-weight: 600;
	}

	.col-env {
		width: 30%;
		color: var(--dl-ink);
		font-family: var(--dl-font-mono);
		font-size: 0.82rem;
	}

	.col-status {
		width: 22%;
	}

	.col-notes {
		color: var(--dl-ink-mute);
	}

	.badge {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.1rem 0.5rem;
		border-radius: var(--dl-r-sm);
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
		font-weight: 600;
	}

	.badge.ok { background: rgba(52, 211, 153, 0.12); color: var(--dl-good); }
	.badge.limited { background: rgba(251, 191, 36, 0.12); color: var(--dl-warn); }
	.badge.no { background: rgba(239, 68, 68, 0.12); color: var(--dl-bad); }
	.badge.unk { background: var(--dl-bg-modal); color: var(--dl-ink-dim); }

	.col-notes ul {
		list-style: disc;
		margin: 0;
		padding-left: 1.1rem;
		font-size: 0.82rem;
	}

	.col-notes li.lim {
		color: var(--dl-warn);
	}

	.dim {
		color: var(--dl-ink-faint);
		font-family: var(--dl-font-mono);
	}
</style>
