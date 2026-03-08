<script lang="ts">
	import CodeWindow from './CodeWindow.svelte';
</script>

<section class="py-20 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Code Examples</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">Clean API</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			One stock code starts the analysis.
		</p>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-5 text-left">
			<CodeWindow title="financial.py">
				<span class="text-purple-400">from</span> <span class="text-dl-text">dartlab</span> <span class="text-purple-400">import</span> <span class="text-cyan-400">Company</span><br /><br />
				<span class="text-dl-text">samsung</span> <span class="text-dl-text-muted">=</span> <span class="text-cyan-400">Company</span><span class="text-dl-text-muted">(</span><span class="text-emerald-400">"005930"</span><span class="text-dl-text-muted">)</span><br />
				<span class="text-dl-text">result</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">analyze</span><span class="text-dl-text-muted">()</span><br /><br />
				<span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">FS</span> <span class="text-dl-text-dim">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# time series</span><br />
				<span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">allRate</span> <span class="text-dl-text-dim">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# match rate</span><br />
				<span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">breakpoints</span> <span class="text-dl-text-dim">&nbsp;# breakpoints</span>
			</CodeWindow>

			<CodeWindow title="holder.py">
				<span class="text-dl-text">result</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">majorHolder</span><span class="text-dl-text-muted">()</span><br /><br />
				<span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">majorHolder</span> <span class="text-dl-text-dim">&nbsp;# name</span><br />
				<span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">majorRatio</span> <span class="text-dl-text-dim">&nbsp;&nbsp;# 20.76</span><br />
				<span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">timeSeries</span> <span class="text-dl-text-dim">&nbsp;&nbsp;# stake history</span><br /><br />
				<span class="text-dl-text">div</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">dividend</span><span class="text-dl-text-muted">()</span><br />
				<span class="text-dl-text">div</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">timeSeries</span> <span class="text-dl-text-dim">&nbsp;&nbsp;&nbsp;&nbsp;# DPS, yield</span>
			</CodeWindow>

			<CodeWindow title="mdna.py">
				<span class="text-dl-text">result</span> <span class="text-dl-text-muted">=</span> <span class="text-dl-text">samsung</span><span class="text-dl-text-muted">.</span><span class="text-cyan-400">mdna</span><span class="text-dl-text-muted">()</span><br /><br />
				<span class="text-purple-400">for</span> <span class="text-dl-text">section</span> <span class="text-purple-400">in</span> <span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">sections</span><span class="text-dl-text-muted">:</span><br />
				<span class="text-dl-text">&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="text-cyan-400">print</span><span class="text-dl-text-muted">(</span><span class="text-dl-text">section</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">category</span><span class="text-dl-text-muted">)</span><br />
				<span class="text-dl-text">&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="text-cyan-400">print</span><span class="text-dl-text-muted">(</span><span class="text-dl-text">section</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">text</span><span class="text-dl-text-muted">[:</span><span class="text-orange-400">200</span><span class="text-dl-text-muted">])</span><br /><br />
				<span class="text-dl-text">result</span><span class="text-dl-text-muted">.</span><span class="text-rose-300">overview</span> <span class="text-dl-text-dim">&nbsp;&nbsp;&nbsp;# biz overview</span>
			</CodeWindow>
		</div>
	</div>
</section>
