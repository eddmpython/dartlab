<script lang="ts">
	import CodeWindow from './CodeWindow.svelte';

	let activeDemo = $state(0);

	const demos = [
		{
			title: 'sections.py',
			result: [
				{ col: 'chapter', values: ['I', 'II', 'II', 'III', 'V'] },
				{ col: 'topic', values: ['companyOverview', 'businessOverview', 'businessOverview', 'riskManagement', 'auditOpinion'] },
				{ col: 'blockType', values: ['text', 'text', 'table', 'text', 'text'] },
				{ col: '2024', values: ['Founded in 1969…', 'Semiconductors…', 'Revenue (5×3)', 'FX risk…', 'Unqualified'] },
				{ col: '2023', values: ['Founded in 1969…', 'Semiconductors…', 'Revenue (5×3)', 'FX risk…', 'Unqualified'] }
			],
			shape: 'shape: (329, 106)'
		},
		{
			title: 'show-trace.py',
			result: [
				{ col: 'block', values: ['0', '1', '2'] },
				{ col: 'type', values: ['text', 'table', 'table'] },
				{ col: 'source', values: ['docs', 'docs', 'docs'] },
				{ col: 'preview', values: ['Founded in 1969…', 'Name: Samsung Electronics', 'Est: 1969-01-13'] }
			],
			shape: 'show("companyOverview") → 3 blocks'
		},
		{
			title: 'diff-finance.py',
			result: [
				{ col: 'account', values: ['total_assets', 'total_equity', 'revenue', 'operating_income', 'net_income'] },
				{ col: '2024Q4', values: ['476.1T', '361.2T', '300.9T', '42.4T', '32.7T'] },
				{ col: '2024Q3', values: ['472.8T', '358.7T', '285.1T', '38.5T', '30.1T'] },
				{ col: '2023Q4', values: ['455.3T', '345.8T', '258.9T', '6.6T', '5.3T'] }
			],
			shape: 'source: finance (authoritative)'
		}
	];
</script>

<section class="py-20 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Code → Result</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">sections is the whole company</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			One DataFrame. Every topic. Every period. Here's what you actually get.
		</p>

		<!-- Tab Selector -->
		<div class="flex justify-center gap-2 mb-8">
			{#each demos as demo, i}
				<button
					onclick={() => activeDemo = i}
					class="px-3 py-1.5 rounded-md text-xs font-mono transition-all cursor-pointer {activeDemo === i
						? 'bg-dl-primary/15 text-dl-primary border border-dl-primary/30'
						: 'text-dl-text-dim border border-transparent hover:text-dl-text'}"
				>
					{demo.title}
				</button>
			{/each}
		</div>

		<!-- Code + Result Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-4 text-left">
			<!-- Code Panel -->
			{#if activeDemo === 0}
				<CodeWindow title="sections.py">
					<span class="text-purple-400">from</span> <span class="text-dl-text">dartlab</span> <span class="text-purple-400">import</span> <span class="text-cyan-400">Company</span><br /><br />
					<span class="text-dl-text">samsung</span> <span class="text-dl-text-muted">=</span> <span class="text-cyan-400">Company</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"005930"</span><span class="text-dl-text-muted">)</span><br />
					<span class="text-dl-text">board</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">sections</span><br /><br />
					<span class="text-dl-text">board</span> <span class="text-dl-text-dim"># canonical company map</span><br />
					<span class="text-dl-text">board</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">shape</span> <span class="text-dl-text-dim"># (329, 106)</span>
				</CodeWindow>
			{:else if activeDemo === 1}
				<CodeWindow title="show-trace.py">
					<span class="text-dl-text">overview</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">show</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"companyOverview"</span><span class="text-dl-text-muted">)</span><br /><br />
					<span class="text-dl-text-dim"># block index first</span><br />
					<span class="text-dl-text">overview</span> <span class="text-dl-text-dim"># text, table blocks</span><br /><br />
					<span class="text-dl-text-dim"># source tracking</span><br />
					<span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">trace</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"companyOverview"</span><span class="text-dl-text-muted">)</span>
				</CodeWindow>
			{:else}
				<CodeWindow title="diff-finance.py">
					<span class="text-dl-text-dim"># finance shortcuts</span><br />
					<span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">BS</span> <span class="text-dl-text-dim"># balance sheet</span><br />
					<span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">IS</span> <span class="text-dl-text-dim"># income statement</span><br />
					<span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">ratios</span> <span class="text-dl-text-dim"># financial ratios</span><br /><br />
					<span class="text-dl-text-dim"># text change detection</span><br />
					<span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">diff</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"businessOverview"</span><span class="text-dl-text-muted">)</span>
				</CodeWindow>
			{/if}

			<!-- Result Panel -->
			<div class="rounded-lg overflow-hidden bg-dl-bg-card border border-dl-border shadow-lg shadow-black/20">
				<div class="flex items-center justify-between px-4 py-2.5 bg-white/[0.03] border-b border-dl-border">
					<div class="flex items-center gap-2">
						<span class="w-2 h-2 rounded-full bg-dl-success"></span>
						<span class="text-xs text-dl-text-dim font-mono">Output</span>
					</div>
					<span class="text-[10px] text-dl-text-dim font-mono">{demos[activeDemo].shape}</span>
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-left font-mono text-xs">
						<thead>
							<tr class="border-b border-dl-border/50">
								{#each demos[activeDemo].result as col}
									<th class="px-3 py-2 text-dl-text-dim font-semibold whitespace-nowrap">{col.col}</th>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each demos[activeDemo].result[0].values as _, rowIdx}
								<tr class="border-b border-dl-border/30 {rowIdx % 2 === 1 ? 'bg-white/[0.01]' : ''}">
									{#each demos[activeDemo].result as col, colIdx}
										<td class="px-3 py-1.5 whitespace-nowrap max-w-[160px] truncate {colIdx === 0 ? 'text-dl-accent' : 'text-dl-text-muted'}">{col.values[rowIdx]}</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</section>
