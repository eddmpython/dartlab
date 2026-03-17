<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';

	const principles = [
		{
			title: 'Sections replace parser sprawl',
			desc: 'The public surface starts from one company board instead of making you learn a long list of outputs first.'
		},
		{
			title: 'Raw docs are not discarded',
			desc: '`docs.sections`, retrieval blocks, and context slices preserve the evidence layer underneath the merged company view.'
		},
		{
			title: 'Source authority is explicit',
			desc: 'Numeric statements come from finance, structured disclosure comes from report, and narrative structure stays with docs.'
		},
		{
			title: 'Same map feeds AI',
			desc: 'The upcoming AI GUI is built to consume the same company map, not a separate AI-only schema.'
		}
	];
</script>

<section class="py-24 px-6">
	<div class="max-w-5xl mx-auto">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Why This Feels Simpler</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">The Advantage of a Single Map</h2>
			<p class="text-dl-text-muted text-lg">Recent performance and quality gains came from simplifying the structure, not from adding more surfaces.</p>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			{#each principles as item}
				<div class="group flex items-start gap-3 px-5 py-4 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-primary/30 hover:bg-dl-bg-card transition-colors">
					<div class="shrink-0 mt-1">
						<span class="w-1.5 h-1.5 rounded-full bg-dl-primary block"></span>
					</div>
					<div class="min-w-0">
						<div class="text-sm font-semibold text-dl-text group-hover:text-dl-primary transition-colors">{item.title}</div>
						<p class="text-sm text-dl-text-dim mt-1 leading-relaxed">{item.desc}</p>
					</div>
				</div>
			{/each}
		</div>

		<div class="mt-10 text-center">
			<Badge variant="success">
				<span class="w-1.5 h-1.5 rounded-full bg-dl-success animate-pulse"></span>
				Sections-Centric Public Contract
			</Badge>
		</div>
	</div>
</section>
