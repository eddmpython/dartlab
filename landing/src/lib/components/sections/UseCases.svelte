<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { BarChart3, Shield, TrendingUp, GraduationCap, Search, Bell } from 'lucide-svelte';

	const cases = [
		{ icon: BarChart3, color: 'text-dl-primary bg-dl-primary/10', title: 'Company Reading', desc: 'Start from `sections`, then open only the topics you need. The company structure stays visible while you inspect one payload at a time.' },
		{ icon: Shield, color: 'text-dl-accent bg-dl-accent/10', title: 'Source Audit', desc: 'Use `trace(...)` to understand whether a value came from docs, finance, or report. This makes review and debugging much faster.' },
		{ icon: TrendingUp, color: 'text-dl-success bg-dl-success/10', title: 'Time-Series Comparison', desc: 'Because the board is horizontalized first, narrative topics and numeric topics can both be compared across periods with less glue code.' },
		{ icon: GraduationCap, color: 'text-dl-primary bg-dl-primary/10', title: 'Research Datasets', desc: 'Build data pipelines on top of a stable company map rather than chaining together dozens of unrelated parser outputs.' },
		{ icon: Search, color: 'text-dl-accent bg-dl-accent/10', title: 'OpenAPI + Runtime', desc: 'Use `OpenDart` or `OpenEdgar` for raw public APIs, then save into parquet that the same runtime can consume immediately.' },
		{ icon: Bell, color: 'text-dl-warning bg-dl-warning/10', title: 'AI GUI', desc: 'The next interface layer is not a new schema. It is the same company map, consumed through a GUI and source-aware AI workflow.' }
	];
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Use Cases</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">Built Around the Same Map</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			Analysis, review, data pipelines, and AI workflows can all start from the same company structure.
		</p>

		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
			{#each cases as c}
				<Card class="text-left">
					<div class="w-10 h-10 rounded-md flex items-center justify-center mb-4 {c.color}">
						<c.icon class="w-6 h-6" />
					</div>
					<h4 class="text-base font-semibold text-dl-text mb-2">{c.title}</h4>
					<p class="text-sm text-dl-text-muted leading-relaxed">{c.desc}</p>
				</Card>
			{/each}
		</div>
	</div>
</section>
