<script lang="ts">
	const stats = [
		{ value: '329', label: 'topics per company', sub: 'Samsung Electronics' },
		{ value: '106', label: 'periods horizontalized', sub: 'annual + quarterly' },
		{ value: '97%', label: 'account mapping rate', sub: '34,249 accounts' },
		{ value: '100%', label: 'EDGAR sections mapped', sub: '974 companies verified' },
		{ value: '283', label: 'DART companies verified', sub: 'zero errors' },
		{ value: '42', label: 'data modules', sub: 'docs · finance · report' }
	];
</script>

<section class="py-20 px-6 relative overflow-hidden">
	<div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(234,70,71,0.04)_0%,_transparent_60%)]"></div>

	<div class="relative max-w-5xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">By the Numbers</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text">Built on Real Data, Not Promises</h2>
		</div>

		<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 stagger">
			{#each stats as stat, i}
				<div class="group relative text-center px-4 py-6 rounded-lg border border-dl-border/50 bg-dl-bg-card/30 hover:border-dl-primary/30 hover:bg-dl-bg-card/60 transition-all duration-300">
					<div class="text-3xl md:text-4xl font-black bg-gradient-to-b from-dl-primary to-dl-accent bg-clip-text text-transparent mb-1 tabular-nums">
						{stat.value}
					</div>
					<div class="text-xs font-semibold text-dl-text mb-1">{stat.label}</div>
					<div class="text-[10px] text-dl-text-dim">{stat.sub}</div>
				</div>
			{/each}
		</div>
	</div>
</section>
