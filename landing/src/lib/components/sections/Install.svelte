<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Check, Copy } from 'lucide-svelte';

	let copiedIdx = $state(-1);

	const commands = [
		{ label: 'uv', cmd: 'uv add dartlab', highlight: true },
		{ label: 'AI 기업분석', cmd: 'uv add dartlab[ai] && uv run dartlab ai', highlight: false }
	];

	async function copy(idx: number) {
		await navigator.clipboard.writeText(commands[idx].cmd);
		copiedIdx = idx;
		setTimeout(() => (copiedIdx = -1), 2000);
	}
</script>

<section id="install" class="py-24 px-6">
	<div class="mx-auto max-w-2xl">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Get Started</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">Installation</h2>
			<p class="text-dl-text-muted text-lg">Start analyzing right after install</p>
		</div>

		<div class="space-y-4">
			{#each commands as item, i}
				<div
					class="rounded-xl overflow-hidden border bg-dl-bg-card transition-all hover:-translate-y-0.5 {item.highlight
						? 'border-dl-primary/30 ring-1 ring-dl-primary/10 shadow-lg shadow-dl-primary/5'
						: 'border-dl-border'}"
				>
					<div
						class="flex items-center justify-between px-4 py-2.5 bg-dl-bg-darker/80 border-b border-dl-border"
					>
						<span
							class="text-xs font-mono {item.highlight ? 'text-dl-primary' : 'text-dl-text-dim'}"
							>{item.label}</span
						>
						<button
							onclick={() => copy(i)}
							class="flex items-center gap-1 px-2 py-0.5 rounded text-xs text-dl-text-dim hover:text-dl-text transition-colors cursor-pointer"
						>
							{#if copiedIdx === i}
								<Check class="w-3.5 h-3.5 text-dl-success" />
							{:else}
								<Copy class="w-3.5 h-3.5" />
							{/if}
						</button>
					</div>
					<div class="p-4 font-mono text-sm">
						<span class="text-dl-text-dim select-none">$ </span>
						<span class="text-dl-text">{item.cmd}</span>
					</div>
				</div>
			{/each}
		</div>

		<Card class="mt-8">
			<div class="text-xs font-mono text-dl-primary mb-3">Auto Download</div>
			<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
				No separate data preparation needed. Pass a stock code and missing data is
				<span class="text-dl-text">automatically downloaded from GitHub Releases</span>.
			</p>
			<div class="font-mono text-sm leading-7">
				<div>
					<span class="text-purple-400">from</span>
					<span class="text-dl-text"> dartlab </span>
					<span class="text-purple-400">import</span>
					<span class="text-cyan-400"> Company</span>
				</div>
				<div class="mt-1">
					<span class="text-dl-text">c = </span>
					<span class="text-cyan-400">Company</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"005930"</span><span class="text-dl-text-muted">)</span>
					<span class="text-dl-text-dim">&nbsp;&nbsp;# auto-downloads</span>
				</div>
			</div>
		</Card>
	</div>
</section>
