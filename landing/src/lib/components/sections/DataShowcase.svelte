<script lang="ts">
	let activeTab = $state(0);

	const tabs = [
		{
			label: 'sections',
			code: 'samsung.sections',
			desc: 'The entire company map — 329 topics horizontalized across periods',
			headers: ['chapter', 'topic', 'blockType', '2024', '2023', '2022'],
			rows: [
				['I', 'companyOverview', 'text', 'Founded in 1969…', 'Founded in 1969…', 'Founded in 1969…'],
				['II', 'businessOverview', 'text', 'Semiconductors, display…', 'Semiconductors, display…', 'Semiconductors, display…'],
				['II', 'businessOverview', 'table', 'Revenue mix (5×3)', 'Revenue mix (5×3)', 'Revenue mix (5×3)'],
				['III', 'riskManagement', 'text', 'FX risk exposure…', 'FX risk exposure…', '—'],
				['V', 'auditOpinion', 'text', 'Unqualified', 'Unqualified', 'Unqualified']
			],
			footer: 'shape: (329, 106) — 329 topics × 106 periods'
		},
		{
			label: 'show("BS")',
			code: 'samsung.show("BS")',
			desc: 'Balance Sheet — normalized numbers from the finance namespace',
			headers: ['account', '2024Q4', '2024Q3', '2024Q2', '2024Q1', '2023Q4'],
			rows: [
				['total_assets', '476.1T', '472.8T', '465.2T', '455.9T', '455.3T'],
				['total_equity', '361.2T', '358.7T', '353.1T', '346.3T', '345.8T'],
				['total_liabilities', '114.9T', '114.1T', '112.1T', '109.6T', '109.5T'],
				['current_assets', '230.5T', '226.3T', '222.8T', '218.7T', '218.2T'],
				['retained_earnings', '315.4T', '311.8T', '308.2T', '302.6T', '302.0T']
			],
			footer: 'source: finance (authoritative) — quarterly standalone normalization'
		},
		{
			label: 'ratios',
			code: 'samsung.ratios',
			desc: 'Financial ratios time series — profitability, stability, valuation',
			headers: ['ratio', '2024Q4', '2024Q3', '2024Q2', '2024Q1', '2023Q4'],
			rows: [
				['roe', '10.2%', '9.8%', '7.5%', '2.1%', '1.6%'],
				['operating_margin', '14.1%', '12.8%', '10.5%', '4.2%', '2.8%'],
				['debt_ratio', '31.8%', '31.8%', '31.7%', '31.7%', '31.7%'],
				['current_ratio', '258.6%', '252.1%', '248.3%', '246.8%', '254.3%'],
				['per', '18.7', '20.3', '25.1', '42.8', '46.2']
			],
			footer: 'TTM basis — trailing four quarters cumulative'
		},
		{
			label: 'diff',
			code: 'samsung.diff("businessOverview")',
			desc: 'Text change detection — compare narrative across periods',
			headers: ['segment', 'period', 'changeType', 'detail'],
			rows: [
				['Revenue mix', '2024→2023', 'modified', 'Semiconductor share 31%→35%'],
				['Key products', '2024→2023', 'added', 'HBM paragraph added'],
				['Market outlook', '2024→2023', 'modified', 'AI chip demand forecast revised'],
				['Competition', '2024→2023', 'unchanged', '—'],
				['New business', '2024→2023', 'added', 'On-device AI description added']
			],
			footer: 'segment-level comparison — added / modified / removed / unchanged'
		}
	];

	$effect(() => {
		const interval = setInterval(() => {
			activeTab = (activeTab + 1) % tabs.length;
		}, 6000);
		return () => clearInterval(interval);
	});
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Real Data</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-3">Samsung Electronics — Actual Output</h2>
			<p class="text-dl-text-muted text-lg">What you get from Company("005930") out of the box</p>
		</div>

		<!-- Tabs -->
		<div class="flex flex-wrap justify-center gap-2 mb-6">
			{#each tabs as tab, i}
				<button
					onclick={() => activeTab = i}
					class="px-4 py-2 rounded-md text-sm font-mono transition-all duration-200 cursor-pointer {activeTab === i
						? 'bg-dl-primary/15 text-dl-primary border border-dl-primary/30'
						: 'bg-dl-bg-card/50 text-dl-text-dim border border-dl-border hover:text-dl-text hover:border-dl-border'
					}"
				>
					{tab.label}
				</button>
			{/each}
		</div>

		<!-- Terminal Window -->
		<div class="rounded-lg overflow-hidden border border-dl-border bg-dl-bg-card shadow-2xl shadow-black/30">
			<!-- Title Bar -->
			<div class="flex items-center justify-between px-4 py-2.5 bg-white/[0.03] border-b border-dl-border">
				<div class="flex items-center gap-1.5">
					<span class="w-2.5 h-2.5 rounded-full bg-red-500"></span>
					<span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
					<span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
					<span class="ml-2 text-xs text-dl-text-dim font-mono">python</span>
				</div>
				<span class="text-[10px] text-dl-text-dim font-mono">{tabs[activeTab].desc}</span>
			</div>

			<!-- Code Input -->
			<div class="px-5 pt-4 pb-2 font-mono text-sm border-b border-dl-border/50">
				<span class="text-dl-text-dim select-none">>>> </span>
				<span class="text-cyan-400">{tabs[activeTab].code}</span>
			</div>

			<!-- Data Table -->
			<div class="overflow-x-auto">
				<table class="w-full text-left font-mono text-xs">
					<thead>
						<tr class="border-b border-dl-border/50">
							{#each tabs[activeTab].headers as header}
								<th class="px-4 py-2.5 text-dl-text-dim font-semibold whitespace-nowrap">{header}</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each tabs[activeTab].rows as row, rowIdx}
							<tr class="border-b border-dl-border/30 hover:bg-white/[0.02] transition-colors {rowIdx % 2 === 0 ? '' : 'bg-white/[0.01]'}">
								{#each row as cell, colIdx}
									<td class="px-4 py-2 whitespace-nowrap max-w-[200px] truncate {colIdx === 0 ? 'text-dl-accent' : colIdx <= 1 ? 'text-dl-text' : 'text-dl-text-muted'}">
										{#if cell === 'added'}
											<span class="text-dl-success">{cell}</span>
										{:else if cell === 'modified'}
											<span class="text-dl-warning">{cell}</span>
										{:else if cell === 'removed'}
											<span class="text-dl-primary">{cell}</span>
										{:else}
											{cell}
										{/if}
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Footer -->
			<div class="px-5 py-3 bg-white/[0.02] border-t border-dl-border/50 flex items-center justify-between">
				<span class="text-[11px] text-dl-text-dim font-mono">{tabs[activeTab].footer}</span>
				<div class="flex gap-1">
					{#each tabs as _, i}
						<div class="w-1.5 h-1.5 rounded-full transition-colors {activeTab === i ? 'bg-dl-primary' : 'bg-dl-border'}"></div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</section>
