<section id="install" class="py-24 px-6">
	<div class="mx-auto max-w-2xl">
		<div class="text-center mb-12">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">설치</h2>
		</div>

		<div class="space-y-4">
			<div class="rounded-xl overflow-hidden border border-dl-border bg-dl-bg-card">
				<div class="flex items-center justify-between px-4 py-2.5 bg-dl-bg-darker/80 border-b border-dl-border">
					<span class="text-xs text-dl-text-dim font-mono">pip</span>
				</div>
				<div class="p-4 font-mono text-sm">
					<span class="text-dl-text-dim select-none">$ </span>
					<span class="text-dl-text">pip install dartlab</span>
				</div>
			</div>

			<div class="rounded-xl overflow-hidden border border-dl-primary/30 bg-dl-bg-card ring-1 ring-dl-primary/10">
				<div class="flex items-center justify-between px-4 py-2.5 bg-dl-bg-darker/80 border-b border-dl-border">
					<span class="text-xs text-dl-primary font-mono">uv (권장)</span>
				</div>
				<div class="p-4 font-mono text-sm">
					<span class="text-dl-text-dim select-none">$ </span>
					<span class="text-dl-text">uv add dartlab</span>
				</div>
			</div>
		</div>

		<div class="mt-8 p-6 rounded-xl bg-dl-bg-card border border-dl-border">
			<div class="text-xs font-mono text-dl-text-dim mb-3">데이터 준비</div>
			<div class="font-mono text-sm space-y-1">
				<div>
					<span class="text-dl-text-dim select-none">$ </span>
					<span class="text-dl-text">mkdir -p data/docsData</span>
				</div>
				<div>
					<span class="text-dl-text-dim select-none">$ </span>
					<span class="text-dl-text">curl -L -o data/docsData/005930.parquet \</span>
				</div>
				<div class="pl-4">
					<span class="text-[#98c379]">"https://github.com/eddmpython/dartlab/releases/download/data-v1/005930.parquet"</span>
				</div>
			</div>
		</div>
	</div>
</section>
