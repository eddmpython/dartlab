<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { Button } from '$lib/components/ui/button';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-2xl text-center">
		<div
			class="p-8 md:p-12 rounded-lg bg-dl-bg-card border border-dl-border relative overflow-hidden"
		>
			<div
				class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(234,70,71,0.05)_0%,_transparent_70%)]"
			></div>
			<div class="relative">
				<div class="mb-6 flex justify-center">
					<picture>
						<source srcset="{base}/avatar-discover.webp" type="image/webp" />
						<img
							src="{base}/avatar-discover.png"
							alt="DartLab mascot"
							width="120"
							height="120"
							loading="lazy"
							decoding="async"
							class="drop-shadow-[0_0_24px_rgba(234,70,71,0.35)] animate-float"
						/>
					</picture>
				</div>
				<h2 class="text-2xl md:text-3xl font-bold text-dl-text mb-3">Start Reading Companies, Not PDFs</h2>
				<p class="text-dl-text-muted mb-3 text-lg">
					One stock code. Every filing structured. Every period comparable.
				</p>
				<p class="text-sm text-dl-text-dim mb-8">One line of Python gives you what used to take days of PDF reading.</p>

				<div class="flex flex-wrap items-center justify-center gap-4">
					<Button href="#install">Install</Button>
					<Button variant="secondary" href="{base}/docs/">Documentation →</Button>
					<Button variant="secondary" href={brand.spaces}>Live Demo →</Button>
				</div>
			</div>
		</div>
	</div>
</section>
