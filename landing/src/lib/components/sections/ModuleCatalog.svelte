<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';

	const modules = [
		{ name: 'BS / IS / CF', desc: 'Balance Sheet, Income Statement, Cash Flow', category: 'statements' },
		{ name: 'fsSummary', desc: 'Summary financials with Bridge Matching', category: 'statements' },
		{ name: 'timeseries', desc: 'Cross-company quarterly time series', category: 'statements' },
		{ name: 'ratios', desc: 'ROE, margins, debt ratio, FCF, valuation', category: 'statements' },
		{ name: 'segments', desc: 'Revenue by business segment', category: 'finance' },
		{ name: 'costByNature', desc: 'Cost breakdown by nature', category: 'finance' },
		{ name: 'tangibleAsset', desc: 'PPE movement schedule', category: 'finance' },
		{ name: 'bond', desc: 'Debt securities issuance', category: 'finance' },
		{ name: 'rnd', desc: 'R&D expenses', category: 'finance' },
		{ name: 'otherFinance', desc: 'Bad debt allowance, etc.', category: 'finance' },
		{ name: 'productService', desc: 'Major products/services', category: 'finance' },
		{ name: 'salesOrder', desc: 'Sales performance, order backlog', category: 'finance' },
		{ name: 'dividend', desc: 'DPS, payout ratio, dividend yield', category: 'report' },
		{ name: 'majorHolder', desc: 'Largest shareholder + related parties', category: 'report' },
		{ name: 'employee', desc: 'Headcount, avg salary, tenure', category: 'report' },
		{ name: 'executive', desc: 'Registered, inside/outside directors', category: 'report' },
		{ name: 'executivePay', desc: 'Compensation by category', category: 'report' },
		{ name: 'audit', desc: 'Auditor, opinion, key audit matters', category: 'report' },
		{ name: 'shareCapital', desc: 'Total shares outstanding', category: 'report' },
		{ name: 'subsidiary', desc: 'Investments in other entities', category: 'report' },
		{ name: 'boardOfDirectors', desc: 'Board composition, attendance', category: 'governance' },
		{ name: 'shareholderMeeting', desc: 'Shareholder meeting agendas', category: 'governance' },
		{ name: 'auditSystem', desc: 'Audit committee activities', category: 'governance' },
		{ name: 'internalControl', desc: 'Internal control assessment', category: 'governance' },
		{ name: 'contingentLiability', desc: 'Guarantees, lawsuits', category: 'governance' },
		{ name: 'relatedPartyTx', desc: 'Related party transactions', category: 'governance' },
		{ name: 'sanction', desc: 'Sanctions, penalties', category: 'governance' },
		{ name: 'riskDerivative', desc: 'FX sensitivity, derivatives', category: 'governance' },
		{ name: 'capitalChange', desc: 'Capital changes', category: 'other' },
		{ name: 'fundraising', desc: 'Capital increases/decreases', category: 'other' },
		{ name: 'affiliateGroup', desc: 'Affiliate group companies', category: 'other' },
		{ name: 'investmentInOther', desc: 'Investee ownership, book value', category: 'other' },
		{ name: 'companyHistory', desc: 'Corporate history timeline', category: 'other' },
		{ name: 'companyOverviewDetail', desc: 'Founded, listed, CEO, address', category: 'other' },
		{ name: 'articlesOfIncorporation', desc: 'Articles amendments', category: 'other' },
		{ name: 'notes (12 items)', desc: 'Inventory, borrowings, lease, EPS, etc.', category: 'notes' },
		{ name: 'business', desc: 'Business description + change detection', category: 'disclosure' },
		{ name: 'overview', desc: 'Company overview (address, credit)', category: 'disclosure' },
		{ name: 'mdna', desc: "Management Discussion & Analysis", category: 'disclosure' },
		{ name: 'rawMaterial', desc: 'Raw materials, tangible assets, CAPEX', category: 'disclosure' },
	];

	const statementsModules = modules.filter(m => m.category === 'statements');
	const financeModules = modules.filter(m => m.category === 'finance');
	const reportModules = modules.filter(m => m.category === 'report');
	const governanceModules = modules.filter(m => m.category === 'governance');
	const otherModules = modules.filter(m => m.category === 'other');
	const notesModules = modules.filter(m => m.category === 'notes');
	const disclosureModules = modules.filter(m => m.category === 'disclosure');
</script>

<section class="py-24 px-6">
	<div class="max-w-5xl mx-auto">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Module Catalog</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">{modules.length} Analysis Modules</h2>
			<p class="text-dl-text-muted text-lg">One stock code. Every module returns a structured DataFrame.</p>
		</div>

		<div class="space-y-8">
			<div>
				<div class="flex items-center gap-3 mb-4">
					<h3 class="text-sm font-semibold text-dl-text uppercase tracking-wider">Financial Statements</h3>
					<span class="text-xs text-dl-text-dim font-mono">{statementsModules.length}</span>
					<div class="flex-1 h-px bg-dl-border"></div>
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each statementsModules as m}
						<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-primary/30 hover:bg-dl-bg-card transition-all">
							<div class="shrink-0 mt-0.5">
								<span class="w-1.5 h-1.5 rounded-full bg-dl-primary block"></span>
							</div>
							<div class="min-w-0">
								<span class="text-sm font-mono text-dl-text group-hover:text-dl-primary transition-colors">.{m.name}</span>
								<p class="text-xs text-dl-text-dim mt-0.5 truncate">{m.desc}</p>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div>
				<div class="flex items-center gap-3 mb-4">
					<h3 class="text-sm font-semibold text-dl-text uppercase tracking-wider">Financial Details</h3>
					<span class="text-xs text-dl-text-dim font-mono">{financeModules.length}</span>
					<div class="flex-1 h-px bg-dl-border"></div>
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each financeModules as m}
						<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-primary/30 hover:bg-dl-bg-card transition-all">
							<div class="shrink-0 mt-0.5">
								<span class="w-1.5 h-1.5 rounded-full bg-dl-primary block"></span>
							</div>
							<div class="min-w-0">
								<span class="text-sm font-mono text-dl-text group-hover:text-dl-primary transition-colors">.{m.name}</span>
								<p class="text-xs text-dl-text-dim mt-0.5 truncate">{m.desc}</p>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div>
				<div class="flex items-center gap-3 mb-4">
					<h3 class="text-sm font-semibold text-dl-text uppercase tracking-wider">Periodic Report</h3>
					<span class="text-xs text-dl-text-dim font-mono">{reportModules.length}</span>
					<div class="flex-1 h-px bg-dl-border"></div>
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each reportModules as m}
						<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-primary/30 hover:bg-dl-bg-card transition-all">
							<div class="shrink-0 mt-0.5">
								<span class="w-1.5 h-1.5 rounded-full bg-dl-primary block"></span>
							</div>
							<div class="min-w-0">
								<span class="text-sm font-mono text-dl-text group-hover:text-dl-primary transition-colors">.{m.name}</span>
								<p class="text-xs text-dl-text-dim mt-0.5 truncate">{m.desc}</p>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div>
				<div class="flex items-center gap-3 mb-4">
					<h3 class="text-sm font-semibold text-dl-text uppercase tracking-wider">Governance & Risk</h3>
					<span class="text-xs text-dl-text-dim font-mono">{governanceModules.length}</span>
					<div class="flex-1 h-px bg-dl-border"></div>
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each governanceModules as m}
						<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-accent/30 hover:bg-dl-bg-card transition-all">
							<div class="shrink-0 mt-0.5">
								<span class="w-1.5 h-1.5 rounded-full bg-dl-accent block"></span>
							</div>
							<div class="min-w-0">
								<span class="text-sm font-mono text-dl-text group-hover:text-dl-accent transition-colors">.{m.name}</span>
								<p class="text-xs text-dl-text-dim mt-0.5 truncate">{m.desc}</p>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div>
				<div class="flex items-center gap-3 mb-4">
					<h3 class="text-sm font-semibold text-dl-text uppercase tracking-wider">Corporate Info</h3>
					<span class="text-xs text-dl-text-dim font-mono">{otherModules.length}</span>
					<div class="flex-1 h-px bg-dl-border"></div>
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each otherModules as m}
						<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-accent/30 hover:bg-dl-bg-card transition-all">
							<div class="shrink-0 mt-0.5">
								<span class="w-1.5 h-1.5 rounded-full bg-dl-accent block"></span>
							</div>
							<div class="min-w-0">
								<span class="text-sm font-mono text-dl-text group-hover:text-dl-accent transition-colors">.{m.name}</span>
								<p class="text-xs text-dl-text-dim mt-0.5 truncate">{m.desc}</p>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
				<div>
					<div class="flex items-center gap-3 mb-4">
						<h3 class="text-sm font-semibold text-dl-text uppercase tracking-wider">K-IFRS Notes</h3>
						<span class="text-xs text-dl-text-dim font-mono">{notesModules.length}</span>
						<div class="flex-1 h-px bg-dl-border"></div>
					</div>
					<div class="grid grid-cols-1 gap-3">
						{#each notesModules as m}
							<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-primary/30 hover:bg-dl-bg-card transition-all">
								<div class="shrink-0 mt-0.5">
									<span class="w-1.5 h-1.5 rounded-full bg-dl-primary block"></span>
								</div>
								<div class="min-w-0">
									<span class="text-sm font-mono text-dl-text group-hover:text-dl-primary transition-colors">.{m.name}</span>
									<p class="text-xs text-dl-text-dim mt-0.5 truncate">{m.desc}</p>
								</div>
							</div>
						{/each}
					</div>
				</div>

				<div>
					<div class="flex items-center gap-3 mb-4">
						<h3 class="text-sm font-semibold text-dl-text uppercase tracking-wider">Disclosure Text</h3>
						<span class="text-xs text-dl-text-dim font-mono">{disclosureModules.length}</span>
						<div class="flex-1 h-px bg-dl-border"></div>
					</div>
					<div class="grid grid-cols-1 gap-3">
						{#each disclosureModules as m}
							<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border bg-dl-bg-card/50 hover:border-dl-accent/30 hover:bg-dl-bg-card transition-all">
								<div class="shrink-0 mt-0.5">
									<span class="w-1.5 h-1.5 rounded-full bg-dl-accent block"></span>
								</div>
								<div class="min-w-0">
									<span class="text-sm font-mono text-dl-text group-hover:text-dl-accent transition-colors">.{m.name}</span>
									<p class="text-xs text-dl-text-dim mt-0.5 truncate">{m.desc}</p>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<div class="mt-10 text-center">
			<Badge variant="success">
				<span class="w-1.5 h-1.5 rounded-full bg-dl-success animate-pulse"></span>
				All Modules Released
			</Badge>
		</div>
	</div>
</section>
