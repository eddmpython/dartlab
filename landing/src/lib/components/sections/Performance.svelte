<script lang="ts">
	import { Card } from '$lib/components/ui/card';

	const benchmarks = [
		{
			label: 'Company creation',
			time: '~2s',
			bar: 25,
			detail: 'Data load + sections build'
		},
		{
			label: 'sections query',
			time: '<100ms',
			bar: 5,
			detail: '329 topics × 106 periods instant'
		},
		{
			label: 'show(topic)',
			time: '<50ms',
			bar: 3,
			detail: 'Single topic block extraction'
		},
		{
			label: 'BS / IS / CF',
			time: '<100ms',
			bar: 5,
			detail: 'Normalized financial statements'
		},
		{
			label: 'ratios series',
			time: '<200ms',
			bar: 10,
			detail: 'TTM-based trailing calculation'
		},
		{
			label: 'diff(topic)',
			time: '<300ms',
			bar: 15,
			detail: 'Period-over-period text comparison'
		}
	];

	const techSpecs = [
		{ label: 'Runtime', value: 'Polars (not Pandas)' },
		{ label: 'Data format', value: 'Parquet (columnar)' },
		{ label: 'Auto download', value: 'HuggingFace Datasets' },
		{ label: 'Incremental', value: 'mtime-based delta sync' },
		{ label: 'Cache', value: 'Company object reuse' },
		{ label: 'Python', value: '3.12+ required' }
	];
</script>

<section class="py-24 px-6">
	<div class="max-w-5xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Performance</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-3">Fast Because It's Simple</h2>
			<p class="text-dl-text-muted text-lg">Polars + Parquet + one structure = no unnecessary conversion</p>
		</div>

		<div class="grid lg:grid-cols-5 gap-6">
			<!-- Benchmark Bars -->
			<div class="lg:col-span-3">
				<div class="rounded-lg border border-dl-border bg-dl-bg-card/50 p-6">
					<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">Response Time (Samsung Electronics)</div>
					<div class="space-y-4">
						{#each benchmarks as b}
							<div>
								<div class="flex items-center justify-between mb-1.5">
									<span class="text-sm text-dl-text">{b.label}</span>
									<span class="text-sm font-mono font-bold text-dl-primary">{b.time}</span>
								</div>
								<div class="h-2 rounded-full bg-dl-bg-darker overflow-hidden">
									<div
										class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-accent transition-all duration-700"
										style="width: {b.bar}%"
									></div>
								</div>
								<div class="text-[10px] text-dl-text-dim mt-1">{b.detail}</div>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<!-- Tech Specs -->
			<div class="lg:col-span-2">
				<Card hover={false}>
					<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">Tech Stack</div>
					<div class="space-y-3">
						{#each techSpecs as spec}
							<div class="flex items-start justify-between gap-3">
								<span class="text-sm text-dl-text-dim shrink-0">{spec.label}</span>
								<span class="text-sm text-dl-text font-mono text-right">{spec.value}</span>
							</div>
						{/each}
					</div>
				</Card>

				<Card hover={false} class="mt-4">
					<div class="text-xs font-mono text-dl-text-dim mb-3 uppercase tracking-wider">Why It's Fast</div>
					<div class="space-y-2 text-sm text-dl-text-muted leading-relaxed">
						<p><span class="text-dl-text font-medium">One structure.</span> All queries run on sections — no data conversion needed.</p>
						<p><span class="text-dl-text font-medium">Polars.</span> 5-10x faster DataFrame operations than Pandas.</p>
						<p><span class="text-dl-text font-medium">Parquet.</span> Columnar format reads only the columns you need.</p>
					</div>
				</Card>
			</div>
		</div>
	</div>
</section>
