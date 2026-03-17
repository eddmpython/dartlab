<script lang="ts">
	import { base } from '$app/paths';
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
				<h2 class="text-2xl md:text-3xl font-bold text-dl-text mb-4">Start from the Company Map</h2>
				<p class="text-dl-text-muted mb-8">Use the same `sections -> show -> trace` structure in Python today and in the upcoming AI GUI next.</p>

				<div class="flex flex-wrap items-center justify-center gap-4">
					<Button href="#install">Install</Button>
					<Button variant="secondary" href="{base}/docs/">Documentation →</Button>
				</div>
			</div>
		</div>
	</div>
</section>
