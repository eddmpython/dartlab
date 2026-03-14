<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { BarChart3, FileText, Link2 } from 'lucide-svelte';
</script>

<section id="features" class="py-24 px-6">
	<div class="mx-auto max-w-5xl">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Architecture</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">Three Layers of Disclosure Analysis</h2>
			<p class="text-dl-text-muted text-lg">From numbers to text, from text to insights</p>
		</div>

		<div class="grid md:grid-cols-3 gap-6">
			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-dl-primary/10 flex items-center justify-center mb-4">
					<BarChart3 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono text-dl-primary mb-2">Layer 1</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">Quantitative Analysis</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					34,000+ learned synonyms map 98.7% of XBRL accounts to a unified schema. 40 modules, 2,700+ listed companies cross-comparable.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						7-stage account standardization pipeline
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						Quarter reverse-calculation (Q1–Q4)
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						Bridge Matching across K-IFRS revisions
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">Released</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-accent/40 hover:shadow-dl-accent/5">
				<div class="w-10 h-10 rounded-md bg-dl-accent/10 flex items-center justify-center mb-4">
					<FileText class="w-5 h-5 text-dl-accent" />
				</div>
				<div class="text-xs font-mono text-dl-accent mb-2">Layer 2</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">Qualitative Analysis</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					Specialized text analysis modules developed separately will be integrated into DartLab as batch releases.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						Section-level text diff
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						Risk factor tracking
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						Audit opinion change detection
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge>Planned</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-gradient-to-br from-dl-primary/10 to-dl-accent/10 flex items-center justify-center mb-4">
					<Link2 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono bg-gradient-to-r from-dl-primary to-dl-accent bg-clip-text text-transparent mb-2">Layer 3</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">Cross-validation</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					Links quantitative changes with qualitative shifts to automatically detect risk signals.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						Earnings change ↔ text explanation
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						Leading risk signal analysis
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						Audit opinion ↔ reliability assessment
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge>In Development</Badge>
				</div>
			</Card>
		</div>
	</div>
</section>
