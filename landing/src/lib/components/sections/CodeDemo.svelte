<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="mx-auto max-w-3xl">
		<div class="text-center mb-12">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">간결한 API</h2>
			<p class="text-dl-text-muted text-lg">한 줄이면 분석이 시작된다</p>
		</div>

		<div class="rounded-2xl overflow-hidden border border-dl-border bg-dl-bg-card">
			<div class="flex items-center gap-2 px-4 py-3 bg-dl-bg-darker/80 border-b border-dl-border">
				<div class="flex gap-1.5">
					<div class="w-3 h-3 rounded-full bg-[#ff5f57]"></div>
					<div class="w-3 h-3 rounded-full bg-[#febc2e]"></div>
					<div class="w-3 h-3 rounded-full bg-[#28c840]"></div>
				</div>
				<span class="text-xs text-dl-text-dim ml-2 font-mono">analysis.py</span>
			</div>
			<div class="p-6 font-mono text-sm leading-relaxed overflow-x-auto">
				<div>
					<span class="text-[#c678dd]">from</span>
					<span class="text-dl-text"> dartlab.finance.summary </span>
					<span class="text-[#c678dd]">import</span>
					<span class="text-dl-text"> analyze</span>
				</div>
				<div class="mt-4">
					<span class="text-dl-text-dim"># 삼성전자 공시 데이터 분석</span>
				</div>
				<div>
					<span class="text-dl-text">result </span>
					<span class="text-[#c678dd]">= </span>
					<span class="text-[#61afef]">analyze</span>
					<span class="text-dl-text">(</span>
					<span class="text-[#98c379]">"data/docsData/005930.parquet"</span>
					<span class="text-dl-text">)</span>
				</div>
				<div class="mt-4">
					<span class="text-dl-text-dim"># 계정명 × 연도 시계열 DataFrame</span>
				</div>
				<div>
					<span class="text-[#61afef]">print</span>
					<span class="text-dl-text">(result.</span>
					<span class="text-[#e5c07b]">dataframe</span>
					<span class="text-dl-text">)</span>
				</div>
				<div class="mt-4">
					<span class="text-dl-text-dim"># 연도 간 계정 브릿지</span>
				</div>
				<div>
					<span class="text-[#c678dd]">for</span>
					<span class="text-dl-text"> bridge </span>
					<span class="text-[#c678dd]">in</span>
					<span class="text-dl-text"> result.</span>
					<span class="text-[#e5c07b]">bridges</span>
					<span class="text-dl-text">:</span>
				</div>
				<div class="pl-8">
					<span class="text-[#61afef]">print</span>
					<span class="text-dl-text">(</span>
					<span class="text-[#c678dd]">f</span>
					<span class="text-[#98c379]">"{'{'}bridge.fromPeriod{'}'} → {'{'}bridge.toPeriod{'}'}"</span>
					<span class="text-dl-text">)</span>
				</div>
			</div>
		</div>
	</div>
</section>
