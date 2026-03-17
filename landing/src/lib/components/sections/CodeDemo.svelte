<script lang="ts">
	import CodeWindow from './CodeWindow.svelte';
</script>

<section class="py-20 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Code Examples</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">One Company Surface</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			The public flow is small on purpose.
		</p>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-5 text-left">
			<CodeWindow title="sections.py">
				<span class="text-purple-400">from</span> <span class="text-dl-text">dartlab</span> <span class="text-purple-400">import</span> <span class="text-cyan-400">Company</span><br /><br />
				<span class="text-dl-text">samsung</span> <span class="text-dl-text-muted">=</span> <span class="text-cyan-400">Company</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"005930"</span><span class="text-dl-text-muted">)</span><br />
				<span class="text-dl-text">board</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">sections</span><br /><br />
				<span class="text-dl-text">board</span> <span class="text-dl-text-dim"># canonical company map</span><br />
				<span class="text-dl-text">board</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">columns</span> <span class="text-dl-text-dim"># periods</span><br />
				<span class="text-dl-text">board</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">shape</span> <span class="text-dl-text-dim"># topic rows x periods</span>
			</CodeWindow>

			<CodeWindow title="show-trace.py">
				<span class="text-dl-text">overview</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">show</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"companyOverview"</span><span class="text-dl-text-muted">)</span><br />
				<span class="text-dl-text">bs</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">show</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"BS"</span><span class="text-dl-text-muted">)</span><br /><br />
				<span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">trace</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"companyOverview"</span><span class="text-dl-text-muted">)</span><br />
				<span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">trace</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"BS"</span><span class="text-dl-text-muted">)</span><br /><br />
				<span class="text-dl-text-dim"># docs for narrative</span><br />
				<span class="text-dl-text-dim"># finance for numeric statements</span>
			</CodeWindow>

			<CodeWindow title="openapi-ai.py">
				<span class="text-purple-400">from</span> <span class="text-dl-text">dartlab</span> <span class="text-purple-400">import</span> <span class="text-cyan-400">OpenEdgar</span><br /><br />
				<span class="text-dl-text">e</span> <span class="text-dl-text-muted">=</span> <span class="text-cyan-400">OpenEdgar</span><span class="text-dl-text-muted">()</span><br />
				<span class="text-dl-text">facts</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">e</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">companyFactsJson</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"AAPL"</span><span class="text-dl-text-muted">)</span><br /><br />
				<span class="text-dl-text-dim"># same company map idea</span><br />
				<span class="text-dl-text-dim"># same saved parquet contract</span><br />
				<span class="text-dl-text-dim"># same AI-ready direction</span>
			</CodeWindow>
		</div>
	</div>
</section>
