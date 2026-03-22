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

		<!-- Code before/after -->
		<div class="grid md:grid-cols-2 gap-4 mt-8">
			<div class="rounded-lg overflow-hidden border border-dl-border bg-dl-bg-card/50">
				<div class="px-4 py-2 bg-white/[0.03] border-b border-dl-border">
					<span class="text-[10px] font-mono text-dl-warning uppercase tracking-wider">Without DartLab</span>
				</div>
				<pre class="p-4 font-mono text-xs text-dl-text-dim leading-relaxed overflow-x-auto"><code><span class="text-dl-text-dim"># 1. Download PDF from DART</span>
pdf = download_report("005930", "2024")
<span class="text-dl-text-dim"># 2. Extract tables from PDF</span>
tables = parse_pdf_tables(pdf)
<span class="text-dl-text-dim"># 3. Manual account mapping</span>
mapped = manual_map(tables, my_schema)
<span class="text-dl-text-dim"># 4. Repeat for each quarter...</span>
<span class="text-dl-text-dim"># 5. Repeat for each company...</span>
<span class="text-dl-text-dim"># 6. Hope the formats match</span></code></pre>
			</div>

			<div class="rounded-lg overflow-hidden border border-dl-primary/30 bg-dl-bg-card">
				<div class="px-4 py-2 bg-dl-primary/5 border-b border-dl-primary/20">
					<span class="text-[10px] font-mono text-dl-primary uppercase tracking-wider">With DartLab</span>
				</div>
				<pre class="p-4 font-mono text-xs text-dl-text leading-relaxed overflow-x-auto"><code><span class="text-cyan-400">import</span> dartlab

c = dartlab.Company(<span class="text-dl-primary">"005930"</span>)
c.BS       <span class="text-dl-text-dim"># standardized balance sheet</span>
c.ratios   <span class="text-dl-text-dim"># 47 financial ratios</span>
c.diff()   <span class="text-dl-text-dim"># 5 years of changes</span></code></pre>
			</div>
		</div>
	</div>
</section>
