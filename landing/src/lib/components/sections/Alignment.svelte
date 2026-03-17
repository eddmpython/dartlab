<script lang="ts">
	import { Card } from '$lib/components/ui/card';
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Sections</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">From Vertical Filings to One Horizontal Map</h2>
			<p class="text-dl-text-muted text-lg">The real product is not a parser list. It is the map.</p>
		</div>

		<div class="grid md:grid-cols-2 gap-6">
			<Card>
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					Section Alignment
				</div>

				<div class="space-y-3">
					{#each [
						{ label: '2023', width: 'w-full', text: 'companyOverview | business | risk', color: 'from-dl-primary/50 to-dl-primary/20', textColor: 'text-dl-primary-light' },
						{ label: '2024Q1', width: 'w-3/4', text: 'companyOverview | business', color: 'from-dl-primary/50 to-dl-primary/20', textColor: 'text-dl-primary-light' },
						{ label: '2024Q2', width: 'w-3/4', text: 'companyOverview | business', color: 'from-dl-primary/50 to-dl-primary/20', textColor: 'text-dl-primary-light' },
						{ label: '2024', width: 'w-full', text: 'companyOverview | business | risk', color: 'from-dl-accent/50 to-dl-accent/20', textColor: 'text-dl-accent-light' }
					] as bar}
						<div class="grid grid-cols-[5rem_1fr] items-center gap-3">
							<span class="text-dl-text-muted text-xs text-right font-mono">{bar.label}</span>
							<div class="h-8 rounded-md bg-dl-bg-darker overflow-hidden">
								<div
									class="h-full {bar.width} bg-gradient-to-r {bar.color} rounded-lg flex items-center justify-center"
								>
									<span class="text-[10px] {bar.textColor} font-semibold">{bar.text}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>

				<div class="flex items-center gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg class="w-4 h-4 text-dl-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
					<span class="text-dl-text text-xs">Same topic row, different period coverage. Missing periods stay empty instead of breaking the map.</span>
				</div>
			</Card>

			<Card>
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					Source-Aware Merge
				</div>

				<div class="space-y-4 font-mono text-sm">
					<div class="grid grid-cols-3 gap-3 text-center">
						<div class="text-xs text-dl-text-dim">docs</div>
						<div class="text-xs text-dl-text-dim">finance</div>
						<div class="text-xs text-dl-text-dim">report</div>
					</div>

					{#each [
						{ a: 'companyOverview', b: 'BS', c: 'audit', changed: false },
						{ a: 'risk text', b: 'IS', c: 'dividend', changed: false },
						{ a: 'retrievalBlocks', b: 'ratios', c: 'employee', changed: true }
					] as row}
						<div class="grid grid-cols-3 gap-3 items-center">
							<div class="px-2 py-2 rounded-lg bg-dl-bg-darker text-xs text-dl-text text-center truncate">
								{row.a}
							</div>
							<div class="px-2 py-2 rounded-lg bg-dl-bg-darker text-xs text-dl-text text-center truncate">
								{row.b}
							</div>
							<div
								class="px-2 py-2 rounded-lg text-xs text-center truncate {row.changed
									? 'bg-dl-primary/10 text-dl-primary border border-dl-primary/30'
									: 'bg-dl-bg-darker text-dl-text'}"
							>
								{row.c}
							</div>
						</div>
						{#if row.changed}
							<div class="grid grid-cols-3 gap-3 -mt-2">
								<div></div>
								<div class="flex justify-center">
									<span class="text-[10px] text-dl-primary">──→</span>
								</div>
								<div class="flex justify-center">
									<span class="text-[9px] text-dl-primary font-medium">merged on same spine</span>
								</div>
							</div>
						{/if}
					{/each}
				</div>

				<div class="flex items-center gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg class="w-4 h-4 text-dl-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
					<span class="text-dl-text text-xs">`show(...)` and `trace(...)` sit on top of the same company spine instead of inventing a second structure.</span>
				</div>
			</Card>
		</div>
	</div>
</section>
