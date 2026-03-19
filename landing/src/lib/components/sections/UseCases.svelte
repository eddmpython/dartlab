<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { BarChart3, Shield, TrendingUp, GraduationCap, Search, Bell } from 'lucide-svelte';

	const cases = [
		{ icon: BarChart3, color: 'text-dl-primary bg-dl-primary/10', title: 'Company Analysis', desc: 'Start from `sections` to see the full structure, then open specific topics with `show(topic)`. Text and numbers side by side.' },
		{ icon: Shield, color: 'text-dl-accent bg-dl-accent/10', title: 'Source Audit', desc: 'Use `trace(topic)` to instantly verify whether a value came from docs, finance, or report. Makes review and debugging faster.' },
		{ icon: TrendingUp, color: 'text-dl-success bg-dl-success/10', title: 'Change Tracking', desc: 'Run `diff(topic)` on horizontalized sections to detect text changes across periods. Automatically catch risk wording updates.' },
		{ icon: GraduationCap, color: 'text-dl-primary bg-dl-primary/10', title: 'Research Datasets', desc: 'Build structured datasets from 283 companies with standardized sections. Combine narrative and financial data for papers or ML training.' },
		{ icon: Search, color: 'text-dl-accent bg-dl-accent/10', title: 'API Pipelines', desc: 'Call raw APIs via `OpenDart` → save to parquet → consume in the same Company runtime. End-to-end data pipeline in one tool.' },
		{ icon: Bell, color: 'text-dl-warning bg-dl-warning/10', title: 'AI Company Analysis', desc: '7 LLM providers supported. Feed the same sections map to AI — switch providers without losing analysis consistency.' }
	];
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Use Cases</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">Built Around the Same Map</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			Analysis, audit, data pipelines, and AI workflows all start from the same company structure.
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
