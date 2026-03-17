<script lang="ts">
	import { Download, Code2, LineChart } from 'lucide-svelte';

	const steps = [
		{
			icon: Download,
			step: '01',
			title: 'Install',
			desc: 'One line — uv add dartlab. No separate data preparation needed.',
			code: '$ uv add dartlab',
			color: 'text-dl-primary bg-dl-primary/10 border-dl-primary/20'
		},
		{
			icon: Code2,
			step: '02',
			title: 'Create Company',
			desc: 'Start from the public entrypoint. Missing data is auto-downloaded from GitHub Releases.',
			code: 'c = dartlab.Company("005930")',
			color: 'text-dl-accent bg-dl-accent/10 border-dl-accent/20'
		},
		{
			icon: LineChart,
			step: '03',
			title: 'Read the Map',
			desc: 'Start from sections, then open a topic and trace the source that won.',
			code: 'c.sections  # then c.show("BS")',
			color: 'text-dl-success bg-dl-success/10 border-dl-success/20'
		}
	];
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="max-w-5xl mx-auto">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">How it works</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">From Stock Code to Company Map</h2>
			<p class="text-dl-text-muted text-lg">No parser inventory first. Start from the company board.</p>
		</div>

		<div class="grid md:grid-cols-3 gap-6">
			{#each steps as s, i}
				<div class="relative">
					{#if i < steps.length - 1}
						<div class="hidden md:block absolute top-12 -right-3 w-6 h-px bg-dl-border z-10"></div>
						<div class="hidden md:block absolute top-[46px] -right-1.5 w-0 h-0 border-t-[4px] border-t-transparent border-b-[4px] border-b-transparent border-l-[6px] border-l-dl-border z-10"></div>
					{/if}

					<div class="rounded-lg border border-dl-border bg-dl-bg-card p-6 hover:border-dl-primary/30 transition-colors h-full">
						<div class="flex items-center gap-3 mb-4">
							<div class="w-10 h-10 rounded-md border flex items-center justify-center {s.color}">
								<s.icon class="w-5 h-5" />
							</div>
							<span class="text-xs font-mono text-dl-text-dim">{s.step}</span>
						</div>

						<h3 class="text-lg font-bold text-dl-text mb-2">{s.title}</h3>
						<p class="text-sm text-dl-text-muted leading-relaxed mb-4">{s.desc}</p>

						<div class="rounded-lg bg-dl-bg-darker px-3 py-2 font-mono text-xs text-dl-text-muted">
							<span class="text-dl-text-dim select-none">› </span>{s.code}
						</div>
					</div>
				</div>
			{/each}
		</div>
	</div>
</section>
