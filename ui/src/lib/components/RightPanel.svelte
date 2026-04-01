<!--
	RightPanel — 오른쪽 컨텍스트 패널

	AI 생성물(artifact)과 데이터(data) 2모드.
-->
<script>
	import { X, ChevronLeft, ChevronRight } from "lucide-svelte";
	import { renderMarkdown } from "$lib/markdown.js";
	import ViewSpecRenderer from "$lib/ai/ViewSpecRenderer.svelte";

	let {
		mode = null,       // "data" | "artifact"
		data = null,       // data for "data"/"artifact" mode
		onClose,
		// Artifact navigation
		artifactHistory = [],
		artifactIndex = -1,
		onNavigateArtifact = null,
	} = $props();

	/** 텍스트에 마크다운 테이블이 포함되어 있는지 */
	function hasMarkdownContent(text) {
		if (!text) return false;
		return /^\|.+\|$/m.test(text) || /^#{1,3} /m.test(text) || /\*\*[^*]+\*\*/m.test(text) || /```/.test(text);
	}
</script>

<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark">
	<!-- Panel header -->
	<div class="relative z-30 flex items-center justify-between h-10 px-4 border-b border-dl-border/40 flex-shrink-0">
		<div class="flex items-center gap-2 min-w-0">
			{#if mode === "artifact"}
				<div class="flex items-center gap-1.5">
					{#if artifactHistory.length > 1}
						<button
							class="p-0.5 rounded text-dl-text-dim hover:text-dl-text disabled:opacity-30 transition-colors"
							onclick={() => onNavigateArtifact?.(artifactIndex - 1)}
							disabled={artifactIndex <= 0}
						>
							<ChevronLeft size={14} />
						</button>
						<span class="text-[10px] text-dl-text-dim font-mono">{artifactIndex + 1}/{artifactHistory.length}</span>
						<button
							class="p-0.5 rounded text-dl-text-dim hover:text-dl-text disabled:opacity-30 transition-colors"
							onclick={() => onNavigateArtifact?.(artifactIndex + 1)}
							disabled={artifactIndex >= artifactHistory.length - 1}
						>
							<ChevronRight size={14} />
						</button>
					{/if}
					<span class="text-[12px] font-semibold text-dl-text truncate">{data?.title || "Artifact"}</span>
				</div>
			{:else if mode === "data" && data?.label}
				<span class="text-[12px] font-semibold text-dl-text">{data.label}</span>
			{:else if mode === "data"}
				<span class="text-[12px] font-semibold text-dl-text">데이터</span>
			{/if}
		</div>
		<button
			class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
			onclick={() => onClose?.()}
		>
			<X size={15} />
		</button>
	</div>

	<!-- Panel content -->
	<div class="flex-1 overflow-auto min-h-0">
		{#if mode === "artifact" && data}
			<div class="p-4">
				<ViewSpecRenderer view={data} />
			</div>
		{:else if mode === "data" && data}
			<div class="p-4">
				{#if typeof data === "string"}
					{#if hasMarkdownContent(data)}
						<div class="prose-dartlab text-[13px] leading-[1.7]">
							{@html renderMarkdown(data)}
						</div>
					{:else}
						<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed">{data}</pre>
					{/if}
				{:else if data?.text}
					{#if data.module}
						<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2">{data.module}</div>
					{/if}
					{#if hasMarkdownContent(data.text)}
						<div class="prose-dartlab text-[13px] leading-[1.7]">
							{@html renderMarkdown(data.text)}
						</div>
					{:else}
						<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40">{data.text}</pre>
					{/if}
				{:else}
					<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40">{JSON.stringify(data, null, 2)}</pre>
				{/if}
			</div>
		{:else}
			<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">
				표시할 내용이 없습니다
			</div>
		{/if}
	</div>
</div>
