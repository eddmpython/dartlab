<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';

	let activeCategory = $state(0);

	const categories = [
		{
			id: 'docs',
			label: 'docs',
			color: 'text-dl-accent',
			bgColor: 'bg-dl-accent/10',
			borderColor: 'border-dl-accent/30',
			desc: 'Narrative structure, section boundaries, retrieval blocks',
			modules: [
				{ name: 'sections', desc: 'topic × period horizontalization — the company map' },
				{ name: 'retrievalBlocks', desc: 'RAG-ready text blocks' },
				{ name: 'contextSlices', desc: 'Evidence layer slices' },
				{ name: 'companyOverview', desc: 'Company overview' },
				{ name: 'businessOverview', desc: 'Business description' },
				{ name: 'riskManagement', desc: 'Risk management' },
				{ name: 'auditOpinion', desc: 'Audit opinion' },
				{ name: 'segments', desc: 'Segment information' },
				{ name: 'salesOrder', desc: 'Sales performance' },
				{ name: 'notes', desc: 'K-IFRS notes wrapper' }
			]
		},
		{
			id: 'finance',
			label: 'finance',
			color: 'text-dl-primary',
			bgColor: 'bg-dl-primary/10',
			borderColor: 'border-dl-primary/30',
			desc: 'Normalized statements, ratios, time series',
			modules: [
				{ name: 'BS', desc: 'Balance Sheet' },
				{ name: 'IS', desc: 'Income Statement' },
				{ name: 'CF', desc: 'Cash Flow Statement' },
				{ name: 'CIS', desc: 'Comprehensive Income Statement' },
				{ name: 'ratios', desc: 'Financial ratios time series' },
				{ name: 'ratioSeries', desc: 'Individual ratio extraction' },
				{ name: 'timeseries', desc: 'Single account time series' },
				{ name: 'statements', desc: 'All statements unified view' }
			]
		},
		{
			id: 'report',
			label: 'report',
			color: 'text-dl-success',
			bgColor: 'bg-dl-success/10',
			borderColor: 'border-dl-success/30',
			desc: 'Structured disclosure APIs — DART only',
			modules: [
				{ name: 'audit', desc: 'Auditor and audit opinion' },
				{ name: 'dividend', desc: 'Dividend information' },
				{ name: 'employee', desc: 'Employee statistics' },
				{ name: 'executive', desc: 'Executive roster' },
				{ name: 'compensation', desc: 'Executive compensation' },
				{ name: 'treasury', desc: 'Treasury shares' },
				{ name: 'minority', desc: 'Minority shareholders' },
				{ name: 'largestShareholder', desc: 'Largest shareholder' },
				{ name: 'majorShareholder', desc: '5%+ shareholders' },
				{ name: 'capital', desc: 'Capital increase/decrease' }
			]
		},
		{
			id: 'analysis',
			label: 'analysis',
			color: 'text-dl-warning',
			bgColor: 'bg-dl-warning/10',
			borderColor: 'border-dl-warning/30',
			desc: 'Cross-source analysis engines',
			modules: [
				{ name: 'show(topic)', desc: 'Block index + data per topic' },
				{ name: 'trace(topic)', desc: 'Source tracking (docs/finance/report)' },
				{ name: 'diff(topic)', desc: 'Text change detection across periods' },
				{ name: 'insights', desc: '7-area grading + outlier detection' },
				{ name: 'market', desc: 'Market cap ranking' },
				{ name: 'sector', desc: 'WICS sector classification' },
				{ name: 'profile', desc: 'Merged company layer' },
				{ name: 'index', desc: 'Full topic index' }
			]
		},
		{
			id: 'ai',
			label: 'AI + tools',
			color: 'text-purple-400',
			bgColor: 'bg-purple-500/10',
			borderColor: 'border-purple-500/30',
			desc: 'LLM analysis, export, CLI, server',
			modules: [
				{ name: 'AI Analysis', desc: '7 providers (GPT, Claude, Ollama…)' },
				{ name: 'Excel export', desc: 'Export all modules to Excel' },
				{ name: 'Server API', desc: 'FastAPI 40+ endpoints' },
				{ name: 'CLI', desc: 'ask · status · ai · excel' },
				{ name: 'Desktop', desc: 'Windows GUI app' },
				{ name: 'search', desc: 'Stock search (fuzzy match)' }
			]
		}
	];
</script>

<section class="py-24 px-6">
	<div class="max-w-5xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Module Catalog</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-3">42 Modules, One Structure</h2>
			<p class="text-dl-text-muted text-lg">All modules sit on the same sections spine. No separate schemas.</p>
		</div>

		<!-- Category Tabs -->
		<div class="flex flex-wrap justify-center gap-2 mb-8">
			{#each categories as cat, i}
				<button
					onclick={() => activeCategory = i}
					class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono transition-all cursor-pointer border
						{activeCategory === i
							? `${cat.bgColor} ${cat.color} ${cat.borderColor}`
							: 'bg-dl-bg-card/50 text-dl-text-dim border-dl-border hover:text-dl-text hover:border-dl-border'
						}"
				>
					<span class="w-2 h-2 rounded-full {activeCategory === i ? cat.bgColor.replace('/10', '') : 'bg-dl-text-dim/30'}"></span>
					{cat.label}
					<span class="text-[10px] opacity-60">{cat.modules.length}</span>
				</button>
			{/each}
		</div>

		<!-- Category Description -->
		<div class="text-center mb-6">
			<p class="text-sm text-dl-text-muted">{categories[activeCategory].desc}</p>
		</div>

		<!-- Module Grid -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
			{#each categories[activeCategory].modules as mod, i}
				<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border/50 bg-dl-bg-card/30 hover:border-dl-primary/20 hover:bg-dl-bg-card/60 transition-all duration-200">
					<div class="shrink-0 mt-0.5">
						<span class="flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold {categories[activeCategory].bgColor} {categories[activeCategory].color}">
							{i + 1}
						</span>
					</div>
					<div class="min-w-0">
						<div class="text-sm font-mono font-semibold text-dl-text group-hover:text-dl-primary-light transition-colors">{mod.name}</div>
						<div class="text-xs text-dl-text-dim mt-0.5">{mod.desc}</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Total Count -->
		<div class="mt-8 text-center">
			<Badge variant="success">
				<span class="w-1.5 h-1.5 rounded-full bg-dl-success animate-pulse"></span>
				{categories.reduce((sum, c) => sum + c.modules.length, 0)} modules on one sections spine
			</Badge>
		</div>
	</div>
</section>
