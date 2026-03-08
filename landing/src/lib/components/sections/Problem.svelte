<script lang="ts">
	import { base } from '$app/paths';
	import { Card } from '$lib/components/ui/card';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">99% of Disclosures Go Unread</h2>
			<p class="text-dl-text-muted text-lg">Most tools only extract a few numbers. What about the rest?</p>
		</div>

		<div class="grid md:grid-cols-2 gap-6">
			<Card hover={false}>
				<div class="text-xs font-mono text-dl-text-dim mb-4 uppercase tracking-wider">Existing Tools</div>
				<div class="space-y-3 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text-muted">
						<span class="text-dl-success">✓</span> Revenue
					</div>
					<div class="flex items-center gap-3 text-dl-text-muted">
						<span class="text-dl-success">✓</span> Operating Income
					</div>
					<div class="flex items-center gap-3 text-dl-text-muted">
						<span class="text-dl-success">✓</span> Net Income
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Business Description
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Risk Factors
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Audit Opinion
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Litigation / Governance
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Text Change Tracking
					</div>
				</div>
			</Card>

			<Card hover={false} class="border-dl-primary/30 ring-1 ring-dl-primary/10 bg-gradient-to-br from-dl-bg-card to-dl-bg-card">
				<div class="flex items-center gap-2 mb-4">
					<img src="{base}/avatar-analyze.png" alt="" width="24" height="24" class="rounded-full" />
					<span class="text-xs font-mono text-dl-primary uppercase tracking-wider">DartLab</span>
				</div>
				<div class="space-y-3 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-success">✓</span> Revenue
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-success">✓</span> Operating Income
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-success">✓</span> Net Income
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Business Description
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Risk Factors
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Audit Opinion
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Litigation / Governance
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Text Change Tracking
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-accent">✓</span> Quantitative × Qualitative Cross-check
					</div>
				</div>
			</Card>
		</div>
	</div>
</section>
