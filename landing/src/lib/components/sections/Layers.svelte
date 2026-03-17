<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { BarChart3, FileText, Link2 } from 'lucide-svelte';
</script>

<section id="features" class="py-24 px-6">
	<div class="mx-auto max-w-5xl">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Architecture</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">One Company, Four Namespaces</h2>
			<p class="text-dl-text-muted text-lg">The map stays the same. Only the source responsibility changes.</p>
		</div>

		<div class="grid md:grid-cols-2 xl:grid-cols-4 gap-6">
			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-dl-accent/10 flex items-center justify-center mb-4">
					<FileText class="w-5 h-5 text-dl-accent" />
				</div>
				<div class="text-xs font-mono text-dl-accent mb-2">docs</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">Structural Spine</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					Owns section boundaries, narrative payloads, retrieval blocks, and the raw evidence layer that keeps the company map grounded in the filings.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						`sections` as canonical spine
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						`retrievalBlocks` and `contextSlices`
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						Narrative and detail topics
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">Released</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-accent/40 hover:shadow-dl-accent/5">
				<div class="w-10 h-10 rounded-md bg-dl-primary/10 flex items-center justify-center mb-4">
					<BarChart3 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono text-dl-primary mb-2">finance</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">Authoritative Numbers</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					Owns balance sheet, income statement, cash flow, ratios, and comparable time series. When numbers are available here, they should win.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						Normalized statements
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						Quarterly comparable series
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						Source authority over numeric topics
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">Released</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-gradient-to-br from-dl-success/10 to-dl-success/20 flex items-center justify-center mb-4">
					<Link2 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono text-dl-success mb-2">report</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">Structured Disclosure</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					Owns structured disclosure APIs such as audit, dividend, employees, executives, and similar periodic report payloads where docs should not be the first authority.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-success"></span>
						Periodic report APIs
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-success"></span>
						Structured governance payloads
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-success"></span>
						Source authority over report topics
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">Released</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-gradient-to-br from-dl-primary/10 to-dl-accent/10 flex items-center justify-center mb-4">
					<Link2 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono bg-gradient-to-r from-dl-primary to-dl-accent bg-clip-text text-transparent mb-2">profile</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">Merged Company Layer</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					What the user sees by default: one company surface built on the same sections spine, ready for Python workflows now and AI interfaces next.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						`c.sections`
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						`c.show(...)`
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						`c.trace(...)`
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">Current Default</Badge>
				</div>
			</Card>
		</div>
	</div>
</section>
