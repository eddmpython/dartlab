<script lang="ts">
	import { base } from '$app/paths';
	import { Button } from '$lib/components/ui/button';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-2xl text-center">
		<div
			class="p-8 md:p-12 rounded-2xl bg-gradient-to-b from-dl-bg-card to-dl-bg-darker border border-dl-border relative overflow-hidden"
		>
			<div
				class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(234,70,71,0.05)_0%,_transparent_70%)]"
			></div>
			<div class="relative">
				<div class="mb-6 flex justify-center">
					<img
						src="{base}/avatar-discover.png"
						alt="DartLab mascot"
						width="80"
						height="80"
						class="rounded-full drop-shadow-[0_0_16px_rgba(234,70,71,0.3)] animate-float"
					/>
				</div>
				<h2 class="text-2xl md:text-3xl font-bold text-dl-text mb-4">Start Analyzing DART Disclosures</h2>
				<p class="text-dl-text-muted mb-8">Read the story beyond the numbers.</p>

				<div class="flex flex-wrap items-center justify-center gap-4">
					<Button href="#install">Install</Button>
					<Button variant="secondary" href="{base}/docs/">Documentation →</Button>
				</div>
			</div>
		</div>
	</div>
</section>
