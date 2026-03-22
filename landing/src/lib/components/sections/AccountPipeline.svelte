<script lang="ts">
	import { Card } from '$lib/components/ui/card';

	const steps = [
		{
			step: 1,
			label: 'Strip Prefixes',
			detail: 'ifrs-full_, dart_, ifrs_, ifrs-smes_',
			example: ['ifrs-full_Revenue', 'Revenue'],
			count: '4 prefixes'
		},
		{
			step: 2,
			label: 'ID Synonyms',
			detail: 'English account ID normalization',
			example: ['NetIncome', 'ProfitLoss'],
			count: '59 rules'
		},
		{
			step: 3,
			label: 'Name Synonyms',
			detail: 'Korean account name unification',
			example: ['영업수익', '매출액'],
			count: '104 rules'
		},
		{
			step: 4,
			label: 'Learned Map',
			detail: 'Accumulated mapping table',
			example: ['ProfitLoss', 'net_income'],
			count: '34,249'
		}
	];
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-5xl">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block"
				>Standardization</span
			>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">
				34,249 Account Mappings. Zero Manual Work.
			</h2>
			<p class="text-dl-text-muted text-lg max-w-2xl mx-auto">
				Every company files with different XBRL account IDs. DartLab normalizes them through a
				4-step pipeline so cross-company comparison works automatically.
			</p>
		</div>

		<!-- Pipeline flow -->
		<div class="grid md:grid-cols-4 gap-4 mb-10">
			{#each steps as s}
				<Card>
					<div class="flex items-center gap-2 mb-3">
						<div
							class="w-7 h-7 rounded-full bg-dl-primary/10 flex items-center justify-center text-dl-primary text-xs font-bold"
						>
							{s.step}
						</div>
						<span class="text-xs font-semibold text-dl-text">{s.label}</span>
					</div>
					<div class="text-[10px] text-dl-text-dim mb-3">{s.detail}</div>
					<div class="font-mono text-xs space-y-1">
						<div class="flex items-center gap-2">
							<span class="text-dl-text-dim">{s.example[0]}</span>
						</div>
						<div class="flex items-center gap-2">
							<span class="text-dl-primary text-[10px]">--></span>
							<span class="text-dl-text">{s.example[1]}</span>
						</div>
					</div>
					<div
						class="mt-3 pt-3 border-t border-dl-border text-center text-xs font-bold text-dl-primary tabular-nums"
					>
						{s.count}
					</div>
				</Card>
			{/each}
		</div>

		<!-- Result -->
		<Card hover={false} class="border-dl-primary/20 bg-dl-bg-card">
			<div class="flex flex-wrap items-center justify-center gap-6 text-center">
				<div>
					<div class="text-2xl font-black text-dl-primary tabular-nums">~97%</div>
					<div class="text-xs text-dl-text-dim">mapping rate</div>
				</div>
				<div class="hidden md:block w-px h-10 bg-dl-border"></div>
				<div>
					<div class="text-2xl font-black text-dl-text tabular-nums">3,143</div>
					<div class="text-xs text-dl-text-dim">standard accounts</div>
				</div>
				<div class="hidden md:block w-px h-10 bg-dl-border"></div>
				<div>
					<div class="text-sm text-dl-text-muted max-w-xs">
						Samsung's <code class="text-dl-primary">revenue</code> and SK Hynix's
						<code class="text-dl-primary">revenue</code> resolve to the same snakeId
					</div>
				</div>
			</div>
		</Card>
	</div>
</section>
