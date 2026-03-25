<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Download, Globe } from 'lucide-svelte';
</script>

<section class="relative pt-32 pb-20 px-6 overflow-hidden">
	<div
		class="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(234,70,71,0.06)_0%,_transparent_60%)]"
	></div>

	<div class="relative mx-auto max-w-4xl text-center">
		<div class="mb-6 flex justify-center">
			<picture>
				<source srcset="{base}/avatar.webp" type="image/webp" />
				<img
					src="{base}/avatar.png"
					alt="DartLab mascot"
					width="180"
					height="180"
					fetchpriority="high"
					class="drop-shadow-[0_0_32px_rgba(234,70,71,0.25)] animate-float"
				/>
			</picture>
		</div>

		<Badge variant="success" class="mb-8">
			<span class="w-1.5 h-1.5 rounded-full bg-dl-success animate-pulse"></span>
			v{brand.version} — Sections-First Company Map
		</Badge>

		<h1 class="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6">
			<span class="text-dl-text">The Complete Picture</span><br />
			<span class="text-dl-text">of Any </span><span
				class="bg-gradient-to-r from-dl-primary via-dl-primary-light to-dl-primary bg-clip-text text-transparent"
				>Company</span
			>
		</h1>

		<p class="text-lg md:text-xl text-dl-text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
			Stop digging through PDFs. DartLab turns DART and EDGAR filings into<br />
			one structured map — text, financials, and reports aligned across every period.
		</p>

		<div class="flex flex-wrap items-center justify-center gap-3 mb-16">
			<Button href={brand.spaces}>
				<Globe class="w-4 h-4" />
				Try Online
			</Button>
			<Button variant="secondary" href={brand.desktop}>
				<Download class="w-4 h-4" />
				Windows Download
			</Button>
			<Button variant="secondary" href="#install">pip / uv Install</Button>
			<Button variant="secondary" href="{base}/docs/">Docs</Button>
		</div>

		<div class="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-3xl mx-auto">
			{#each [
				{ value: '2,700+', unit: '', label: 'Korean companies ready' },
				{ value: '970+', unit: '', label: 'US companies (EDGAR)' },
				{ value: '329', unit: '', label: 'topics per company' },
				{ value: '1 line', unit: '', label: 'of Python to start' }
			] as stat}
				<div
					class="px-4 py-3 rounded-lg bg-dl-bg-card/50 border border-dl-border/50 hover:border-dl-primary/20 transition-colors"
				>
					<div
						class="text-2xl font-extrabold bg-gradient-to-r from-dl-primary to-dl-accent bg-clip-text text-transparent"
					>
						{stat.value}<span class="text-sm">{stat.unit}</span>
					</div>
					<div class="text-xs text-dl-text-dim mt-1">{stat.label}</div>
				</div>
			{/each}
		</div>
	</div>
</section>
