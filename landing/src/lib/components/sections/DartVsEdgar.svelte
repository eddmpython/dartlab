<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';

	const features = [
		{ feature: 'sections horizontalization', dart: true, edgar: true },
		{ feature: 'show(topic)', dart: true, edgar: true },
		{ feature: 'trace(topic)', dart: true, edgar: true },
		{ feature: 'diff(topic)', dart: true, edgar: true },
		{ feature: 'BS · IS · CF normalization', dart: true, edgar: true },
		{ feature: 'ratios time series', dart: true, edgar: true },
		{ feature: 'timeseries', dart: true, edgar: true },
		{ feature: 'report API (28 types)', dart: true, edgar: false },
		{ feature: 'insights (7-area grading)', dart: true, edgar: false },
		{ feature: 'sector classification', dart: true, edgar: false },
		{ feature: 'market ranking', dart: true, edgar: false },
		{ feature: 'AI company analysis', dart: true, edgar: true },
		{ feature: 'Excel export', dart: true, edgar: true },
		{ feature: 'Desktop GUI', dart: true, edgar: true }
	];

	const dartCount = features.filter(f => f.dart).length;
	const edgarCount = features.filter(f => f.edgar).length;
</script>

<section class="py-24 px-6">
	<div class="max-w-4xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Coverage</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-3">DART + EDGAR — Same Interface</h2>
			<p class="text-dl-text-muted text-lg">Korean DART and US SEC EDGAR through one Company interface</p>
		</div>

		<div class="grid md:grid-cols-2 gap-6 mb-8">
			<!-- DART Card -->
			<Card hover={false} class="border-dl-primary/20">
				<div class="flex items-center gap-3 mb-4">
					<div class="w-10 h-10 rounded-lg bg-dl-primary/10 flex items-center justify-center">
						<span class="text-lg font-black text-dl-primary">D</span>
					</div>
					<div>
						<div class="text-lg font-bold text-dl-text">DART</div>
						<div class="text-xs text-dl-text-dim">Korean Electronic Disclosure</div>
					</div>
					<Badge variant="success" class="ml-auto">Stable</Badge>
				</div>
				<div class="space-y-2 text-sm">
					<div class="flex justify-between text-dl-text-muted">
						<span>Sections mapping</span><span class="text-dl-text font-mono">99.95%</span>
					</div>
					<div class="flex justify-between text-dl-text-muted">
						<span>Finance mapping</span><span class="text-dl-text font-mono">97.07%</span>
					</div>
					<div class="flex justify-between text-dl-text-muted">
						<span>Verified companies</span><span class="text-dl-text font-mono">283</span>
					</div>
					<div class="flex justify-between text-dl-text-muted">
						<span>Feature coverage</span><span class="text-dl-text font-mono">{dartCount}/{features.length}</span>
					</div>
				</div>
			</Card>

			<!-- EDGAR Card -->
			<Card hover={false} class="border-dl-accent/20">
				<div class="flex items-center gap-3 mb-4">
					<div class="w-10 h-10 rounded-lg bg-dl-accent/10 flex items-center justify-center">
						<span class="text-lg font-black text-dl-accent">E</span>
					</div>
					<div>
						<div class="text-lg font-bold text-dl-text">EDGAR</div>
						<div class="text-xs text-dl-text-dim">SEC Filing (10-K, 10-Q)</div>
					</div>
					<Badge variant="accent" class="ml-auto">Beta</Badge>
				</div>
				<div class="space-y-2 text-sm">
					<div class="flex justify-between text-dl-text-muted">
						<span>Sections mapping</span><span class="text-dl-text font-mono">100.00%</span>
					</div>
					<div class="flex justify-between text-dl-text-muted">
						<span>Verified companies</span><span class="text-dl-text font-mono">974</span>
					</div>
					<div class="flex justify-between text-dl-text-muted">
						<span>10-K / 10-Q pairs</span><span class="text-dl-text font-mono">6</span>
					</div>
					<div class="flex justify-between text-dl-text-muted">
						<span>Feature coverage</span><span class="text-dl-text font-mono">{edgarCount}/{features.length}</span>
					</div>
				</div>
			</Card>
		</div>

		<!-- Feature Comparison Table -->
		<div class="rounded-lg overflow-hidden border border-dl-border bg-dl-bg-card/50">
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-dl-border">
							<th class="text-left px-4 py-3 text-dl-text-dim font-semibold">Feature</th>
							<th class="px-4 py-3 text-center text-dl-primary font-semibold w-24">DART</th>
							<th class="px-4 py-3 text-center text-dl-accent font-semibold w-24">EDGAR</th>
						</tr>
					</thead>
					<tbody>
						{#each features as f, i}
							<tr class="border-b border-dl-border/30 {i % 2 === 0 ? '' : 'bg-white/[0.01]'}">
								<td class="px-4 py-2 text-dl-text-muted">{f.feature}</td>
								<td class="px-4 py-2 text-center">
									{#if f.dart}
										<span class="text-dl-success">&#10003;</span>
									{:else}
										<span class="text-dl-text-dim">—</span>
									{/if}
								</td>
								<td class="px-4 py-2 text-center">
									{#if f.edgar}
										<span class="text-dl-success">&#10003;</span>
									{:else}
										<span class="text-dl-text-dim">—</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<div class="mt-4 text-center">
			<p class="text-xs text-dl-text-dim">Company("005930") for DART · Company("AAPL") for EDGAR — same interface, same methods</p>
		</div>
	</div>
</section>
