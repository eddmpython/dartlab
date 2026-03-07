<script lang="ts">
	let activeTab = $state(0);
	let copied = $state(false);

	const tabs = [
		{
			label: '재무제표',
			filename: 'financial.py',
			code: `from dartlab import Company

samsung = Company("005930")
result = samsung.analyze()

result.FS          # 재무제표 시계열 DataFrame
result.allRate     # 매칭률 (예: 0.97)
result.breakpoints # 변경점 목록`
		},
		{
			label: '주주·배당',
			filename: 'holder.py',
			code: `result = samsung.majorHolder()

result.majorHolder  # "이재용"
result.majorRatio   # 20.76
result.timeSeries   # 지분율 시계열

div = samsung.dividend()
div.timeSeries      # dps, payoutRatio, yield`
		},
		{
			label: '경영진단의견',
			filename: 'mdna.py',
			code: `result = samsung.mdna()

for section in result.sections:
    print(f"[{section.category}] {section.title}")
    print(section.text[:200])

result.overview     # 사업 개요 텍스트`
		}
	];

	async function copyCode() {
		await navigator.clipboard.writeText(tabs[activeTab].code);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	function colorize(line: string): string {
		return line
			.replace(/^(from|import|for|in)\b/g, '<span style="color:#c678dd">$1</span>')
			.replace(/\b(from|import|for|in)\b/g, ' <span style="color:#c678dd">$1</span>')
			.replace(/\b(Company|print)\b/g, '<span style="color:#61afef">$1</span>')
			.replace(/\.(analyze|majorHolder|dividend|mdna|sections)\b/g, '.<span style="color:#61afef">$1</span>')
			.replace(/\.(FS|allRate|breakpoints|majorRatio|timeSeries|overview|category|title|text)\b/g, '.<span style="color:#e5c07b">$1</span>')
			.replace(/"([^"]+)"/g, '<span style="color:#98c379">"$1"</span>')
			.replace(/(#.+)$/, '<span class="text-dl-text-dim">$1</span>')
			.replace(/\bf"/, '<span style="color:#c678dd">f</span>"');
	}
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="mx-auto max-w-3xl">
		<div class="text-center mb-12">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">간결한 API</h2>
			<p class="text-dl-text-muted text-lg">종목코드 하나면 분석이 시작된다</p>
		</div>

		<div
			class="rounded-2xl overflow-hidden border border-dl-border bg-dl-bg-card shadow-2xl shadow-black/30"
		>
			<div
				class="flex items-center justify-between px-4 py-3 bg-dl-bg-darker/80 border-b border-dl-border"
			>
				<div class="flex items-center gap-3">
					<div class="flex gap-1.5">
						<div class="w-3 h-3 rounded-full bg-[#ff5f57]"></div>
						<div class="w-3 h-3 rounded-full bg-[#febc2e]"></div>
						<div class="w-3 h-3 rounded-full bg-[#28c840]"></div>
					</div>
					<span class="text-xs text-dl-text-dim ml-1 font-mono"
						>{tabs[activeTab].filename}</span
					>
				</div>
				<button
					onclick={copyCode}
					class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-all"
				>
					{#if copied}
						<svg class="w-3.5 h-3.5 text-dl-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
						복사됨
					{:else}
						<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
						복사
					{/if}
				</button>
			</div>

			<div class="flex border-b border-dl-border">
				{#each tabs as tab, i}
					<button
						onclick={() => { activeTab = i; copied = false; }}
						class="px-4 py-2.5 text-xs font-medium transition-all {i === activeTab
							? 'text-dl-primary border-b-2 border-dl-primary bg-dl-primary/5'
							: 'text-dl-text-dim hover:text-dl-text-muted'}"
					>
						{tab.label}
					</button>
				{/each}
			</div>

			<div class="p-6 font-mono text-sm leading-7 overflow-x-auto">
				{#each tabs[activeTab].code.split('\n') as line}
					<div class="min-h-[1.75rem]">
						{#if line.trim() === ''}
							&nbsp;
						{:else}
							{@html colorize(line)}
						{/if}
					</div>
				{/each}
			</div>
		</div>
	</div>
</section>
