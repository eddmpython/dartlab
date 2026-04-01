<!--
	BlockToolbar — 블록 호버 시 표시되는 차트 토글, 복사, AI 분석 버튼 그룹.
	TopicRenderer에서 2회 중복 사용되던 코드를 단일 컴포넌트로 추출.
-->
<script>
	import { Copy, Check, Sparkles, BarChart3, Table2 } from "lucide-svelte";

	let {
		chartable = false,
		showChart = false,
		hasRows = false,
		isCopied = false,
		hasAskAI = false,
		onToggleChart,
		onCopy,
		onAnalyze,
	} = $props();
</script>

<div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
	{#if chartable}
		<button
			class="p-1 rounded transition-colors {showChart ? 'text-dl-accent-light bg-dl-accent/10' : 'text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5'}"
			onclick={onToggleChart}
			title={showChart ? '표로 보기' : '차트로 보기'}
		>
			{#if showChart}<Table2 size={12} />{:else}<BarChart3 size={12} />{/if}
		</button>
	{/if}
	{#if hasRows}
		<button
			class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors"
			onclick={onCopy}
			title="테이블 복사"
		>
			{#if isCopied}
				<Check size={12} class="text-dl-success" />
			{:else}
				<Copy size={12} />
			{/if}
		</button>
	{/if}
	{#if hasAskAI}
		<button
			class="p-1 rounded text-dl-text-dim/30 hover:text-[#a78bfa] hover:bg-white/5 transition-colors"
			onclick={onAnalyze}
			title="AI 분석"
		>
			<Sparkles size={12} />
		</button>
	{/if}
</div>
