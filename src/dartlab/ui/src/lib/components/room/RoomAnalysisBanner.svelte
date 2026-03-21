<!--
	AI 분석 브로드캐스트 배너 — 다른 멤버가 질문하면 스트리밍 응답을 보여줌.
-->
<script>
	import { Loader2, Sparkles } from "lucide-svelte";
	import { renderMarkdown } from "$lib/markdown.js";

	const { stream, analyzing = false } = $props();
</script>

{#if stream}
	<div class="mx-3 my-2 rounded-lg border border-dl-accent/30 bg-dl-accent/5 overflow-hidden">
		<!-- 헤더 -->
		<div class="flex items-center gap-2 px-3 py-1.5 bg-dl-accent/10 text-xs">
			{#if analyzing}
				<Loader2 size={12} class="animate-spin text-dl-accent" />
			{:else}
				<Sparkles size={12} class="text-dl-accent" />
			{/if}
			<span class="text-dl-accent font-medium">{stream.memberName || "멤버"}</span>
			<span class="text-dl-text-muted">asked:</span>
			<span class="text-dl-text truncate flex-1">{stream.question}</span>
			{#if stream.company}
				<span class="text-dl-text-dim font-mono text-[10px]">{stream.company}</span>
			{/if}
		</div>

		<!-- 스트리밍 응답 -->
		{#if stream.chunks}
			<div class="px-3 py-2 text-sm text-dl-text max-h-48 overflow-y-auto prose-sm">
				{@html renderMarkdown(stream.chunks)}
			</div>
		{:else if analyzing}
			<div class="px-3 py-3 text-sm text-dl-text-muted">분석 중...</div>
		{/if}

		<!-- 완료 메타 -->
		{#if stream.done && stream.responseMeta}
			<div class="px-3 py-1 border-t border-dl-border/20 text-[10px] text-dl-text-dim">
				{#if stream.responseMeta.duration}
					{(stream.responseMeta.duration / 1000).toFixed(1)}s
				{/if}
				{#if stream.responseMeta.tokens}
					· {stream.responseMeta.tokens} tokens
				{/if}
			</div>
		{/if}
	</div>
{/if}
