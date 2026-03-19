<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { BarChart3, Shield, TrendingUp, GraduationCap, Search, Bell } from 'lucide-svelte';

	const cases = [
		{ icon: BarChart3, color: 'text-dl-primary bg-dl-primary/10', title: '"How did their story change?"', desc: 'Compare business descriptions, risk factors, or any disclosure section across 5+ years. One line: diff("businessOverview"). See exactly what was added, removed, or reworded.' },
		{ icon: TrendingUp, color: 'text-dl-success bg-dl-success/10', title: '"Show me the numbers in context"', desc: 'Financial statements alone miss half the story. DartLab puts BS/IS/CF next to the narrative that explains them — same company, same timeline, same object.' },
		{ icon: Shield, color: 'text-dl-accent bg-dl-accent/10', title: '"Screen the entire market"', desc: 'Scan all 2,700 listed companies by governance quality, workforce trends, capital returns, or debt risk. One call: dartlab.governance("all"). Filter, rank, compare.' },
		{ icon: GraduationCap, color: 'text-dl-primary bg-dl-primary/10', title: '"Build a research dataset"', desc: 'Standardized text + financial data across hundreds of companies. Ready for NLP, ML training, or academic research. No cleaning, no alignment — already done.' },
		{ icon: Bell, color: 'text-dl-warning bg-dl-warning/10', title: '"Let AI analyze with real evidence"', desc: 'Feed structured company context to any LLM — not raw PDFs. 7 providers supported. The AI reasons over actual disclosure data, not hallucinated summaries.' },
		{ icon: Search, color: 'text-dl-accent bg-dl-accent/10', title: '"One tool for Korea and US"', desc: 'Same Company interface for Korean DART and US EDGAR. Learn it once, apply it to both markets. Compare Samsung and Apple with the same API.' }
	];
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">What You Can Do</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">Questions DartLab Answers</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			Every question starts from the same company map. No glue code, no context switching.
		</p>

		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
			{#each cases as c}
				<Card class="text-left">
					<div class="w-10 h-10 rounded-md flex items-center justify-center mb-4 {c.color}">
						<c.icon class="w-6 h-6" />
					</div>
					<h4 class="text-base font-semibold text-dl-text mb-2">{c.title}</h4>
					<p class="text-sm text-dl-text-muted leading-relaxed">{c.desc}</p>
				</Card>
			{/each}
		</div>
	</div>
</section>
