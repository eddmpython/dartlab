<script lang="ts">
	import { base } from '$app/paths';
	import { Card } from '$lib/components/ui/card';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">Most Filing Tools Still Think in Outputs</h2>
			<p class="text-dl-text-muted text-lg">DartLab now thinks in company structure first.</p>
		</div>

		<div class="grid md:grid-cols-2 gap-5">
			<Card hover={false}>
				<div class="text-[11px] font-mono text-dl-text-dim mb-4 uppercase tracking-wider">Before</div>
				<div class="space-y-2.5 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> One parser per topic
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Docs and numbers split apart
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Weak year-over-year structure
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Hard to explain source selection
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Hard to feed into AI consistently
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Company object becomes a property zoo
					</div>
				</div>
			</Card>

			<Card hover={false} class="border-dl-primary/20 bg-dl-bg-card">
				<div class="flex items-center gap-2 mb-4">
					<picture>
						<source srcset="{base}/avatar-analyze.webp" type="image/webp" />
						<img src="{base}/avatar-analyze.png" alt="" width="20" height="20" loading="lazy" decoding="async" class="rounded-full" />
					</picture>
					<span class="text-[11px] font-mono text-dl-primary uppercase tracking-wider">DartLab</span>
				</div>
				<div class="space-y-2.5 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> One `sections` map first
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Docs become the spine
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> `finance` and `report` override where they should
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Topic-by-topic `show(...)`
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Source-aware `trace(...)`
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> One shared structure for AI GUI
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-accent">✓</span> Better performance from a simpler structure
					</div>
				</div>
			</Card>
		</div>
	</div>
</section>
