<script lang="ts">
	import { base } from '$app/paths';
	import { Card } from '$lib/components/ui/card';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">You Shouldn't Need a Week to Read One Company</h2>
			<p class="text-dl-text-muted text-lg max-w-2xl mx-auto">Annual reports are 200+ pages. Quarterly filings pile up. The data you need is buried across documents, formats, and years.</p>
		</div>

		<div class="grid md:grid-cols-2 gap-5">
			<Card hover={false}>
				<div class="text-[11px] font-mono text-dl-text-dim mb-4 uppercase tracking-wider">The reality today</div>
				<div class="space-y-2.5 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Scroll through 200-page PDFs to find one section
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Financial numbers in one tool, text in another
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Comparing last year's risk factors? Manual copy-paste
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> DART tools don't work on EDGAR (and vice versa)
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Feeding filings to AI? Hours of prompt engineering
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> Screening 2,700 companies? Build it yourself
					</div>
				</div>
			</Card>

			<Card hover={false} class="border-dl-primary/20 bg-dl-bg-card">
				<div class="flex items-center gap-2 mb-4">
					<picture>
						<source srcset="{base}/avatar-analyze.webp" type="image/webp" />
						<img src="{base}/avatar-analyze.png" alt="" width="20" height="20" loading="lazy" decoding="async" class="rounded-full" />
					</picture>
					<span class="text-[11px] font-mono text-dl-primary uppercase tracking-wider">With DartLab</span>
				</div>
				<div class="space-y-2.5 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Every section of every filing, already structured
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Text + numbers + reports in one company object
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 5 years side-by-side with `diff()` — one line
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Same `Company` interface for DART and EDGAR
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> Structured sections go straight into LLM context
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-accent">✓</span> Market-wide scans across all listed companies
					</div>
				</div>
			</Card>
		</div>
	</div>
</section>
