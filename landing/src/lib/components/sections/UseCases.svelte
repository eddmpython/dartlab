<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { BarChart3, Shield, TrendingUp, GraduationCap, Search, Bell } from 'lucide-svelte';

	const cases = [
		{ icon: BarChart3, color: 'text-dl-primary bg-dl-primary/10', title: 'Financial Analysis', desc: 'Align revenue, operating income, and net income as quarterly time series. Reverse-calculate individual quarters from cumulative statements, with auto-tracking of renamed accounts.' },
		{ icon: Shield, color: 'text-dl-accent bg-dl-accent/10', title: 'Risk Monitoring', desc: 'Cross-validate qualitative and quantitative risk signals — audit opinion changes, litigation status, sudden debt ratio spikes.' },
		{ icon: TrendingUp, color: 'text-dl-success bg-dl-success/10', title: 'Investment Research', desc: 'Track largest shareholder stake changes, dividend trends, and treasury stock over time. Understand the context behind valuation shifts.' },
		{ icon: GraduationCap, color: 'text-dl-primary bg-dl-primary/10', title: 'Academic Research', desc: 'Build panel datasets from standardized financials of 260+ listed companies for event studies, regression analysis, and more.' },
		{ icon: Search, color: 'text-dl-accent bg-dl-accent/10', title: 'Due Diligence', desc: 'Query executive compensation, employee stats, and governance data in one call. 13 periodic report modules replace your DD checklist.' },
		{ icon: Bell, color: 'text-dl-warning bg-dl-warning/10', title: 'Disclosure Monitoring', desc: 'Detect changes in annual reports via text diff. Automatically flag added risk factors, business structure changes, and more.' }
	];
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Use Cases</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">Built For These</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			From financial analysis to due diligence — every domain that needs DART disclosure data.
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
