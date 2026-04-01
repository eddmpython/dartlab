<!--
	근거 모달 — Context / System Prompt / User Content / Snapshot / Tool Event 상세 보기.
-->
<script>
	import { cn } from "$lib/utils.js";
	import { formatEvidenceLabel, formatToolLabel } from "$lib/ai/evidenceLabels.js";
	import { X, Database, Brain, FileText, Code } from "lucide-svelte";
	import { renderMarkdown } from "$lib/markdown.js";

	let { message, openModal = $bindable(null), modalType = $bindable("context") } = $props();

	let contextTab = $state("rendered");

	let isSystemPrompt = $derived(modalType === "system");
	let isUserContent = $derived(modalType === "userContent");
	let isContext = $derived(modalType === "context");
	let isSnapshot = $derived(modalType === "snapshot");
	let isTool = $derived(modalType === "tool");

	let ctx = $derived(isContext ? message.contexts?.[openModal] : null);
	let toolEvent = $derived(isTool ? message.toolEvents?.[openModal] : null);

	let modalTitle = $derived(
		isSnapshot ? "핵심 수치 (원본 데이터)" :
		isSystemPrompt ? "시스템 프롬프트" :
		isUserContent ? "LLM에 전달된 입력" :
		isTool ? (toolEvent?.type === "call" ? `${formatToolLabel(toolEvent?.name)} 호출` : `${formatToolLabel(toolEvent?.name)} 결과`) :
		formatEvidenceLabel(ctx?.label || ctx?.module, ctx?.label || "")
	);

	let modalText = $derived(
		isSnapshot ? JSON.stringify(message.snapshot, null, 2) :
		isSystemPrompt ? message.systemPrompt :
		isUserContent ? message.userContent :
		isTool ? JSON.stringify(toolEvent, null, 2) :
		ctx?.text
	);

	function summarizeToolEvent(ev) {
		if (!ev) return "";
		if (ev.type === "call") {
			if (ev.arguments?.module) return formatEvidenceLabel(ev.arguments.module, "관련 데이터");
			return ev.arguments?.keyword || ev.arguments?.engine || ev.arguments?.name || "";
		}
		if (typeof ev.result === "string") return ev.result.slice(0, 120);
		if (ev.result && typeof ev.result === "object") {
			if (ev.result.module) return formatEvidenceLabel(ev.result.module, "관련 데이터");
			return ev.result.status || ev.result.name || "";
		}
		return "";
	}

	function close() { openModal = null; }
</script>

{#if openModal !== null}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) close(); }}
		onkeydown={(e) => { if (e.key === "Escape") close(); }}
	>
		<div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col">
			<div class="flex-shrink-0 border-b border-dl-border/50">
				<div class="flex items-center justify-between px-5 pt-4 pb-3">
					<div class="flex items-center gap-2 text-[14px] font-medium text-dl-text">
						{#if isSnapshot}
							<Database size={15} class="text-dl-success flex-shrink-0" />
						{:else if isSystemPrompt}
							<Brain size={15} class="text-dl-primary-light flex-shrink-0" />
						{:else if isUserContent}
							<FileText size={15} class="text-dl-accent flex-shrink-0" />
						{:else}
							<Database size={15} class="flex-shrink-0" />
						{/if}
						<span>{modalTitle}</span>
						{#if isSystemPrompt}
							<span class="text-[10px] text-dl-text-dim">({modalText?.length?.toLocaleString()}자)</span>
						{/if}
					</div>
					<div class="flex items-center gap-2">
						{#if isContext}
							<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5">
								<button
									class={cn(
										"flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",
										contextTab === "rendered"
											? "bg-dl-bg-card text-dl-text shadow-sm"
											: "text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => contextTab = "rendered"}
								>
									<FileText size={11} />
									렌더링
								</button>
								<button
									class={cn(
										"flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",
										contextTab === "raw"
											? "bg-dl-bg-card text-dl-text shadow-sm"
											: "text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => contextTab = "raw"}
								>
									<Code size={11} />
									원문
								</button>
							</div>
						{/if}
						<button
							class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
							onclick={close}
						>
							<X size={18} />
						</button>
					</div>
				</div>

				{#if isContext && message.contexts?.length > 1}
					<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide">
						<div class="flex items-center gap-1.5">
							{#each message.contexts as _, idx}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",
										idx === openModal
											? "bg-dl-primary/20 text-dl-primary-light font-medium"
											: "bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"
									)}
									onclick={() => { openModal = idx; }}
								>
									{formatEvidenceLabel(message.contexts[idx].label || message.contexts[idx].module, message.contexts[idx].label || "컨텍스트")}
								</button>
							{/each}
						</div>
					</div>
				{/if}

				{#if !isContext && !isSnapshot && !isTool}
					<div class="px-5 pb-2.5">
						<div class="flex items-center gap-1.5">
							{#if message.systemPrompt}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",
										isSystemPrompt
											? "bg-dl-primary/20 text-dl-primary-light font-medium"
											: "bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => { modalType = "system"; }}
								>
									시스템 프롬프트
								</button>
							{/if}
							{#if message.userContent}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",
										isUserContent
											? "bg-dl-accent/20 text-dl-accent font-medium"
											: "bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => { modalType = "userContent"; }}
								>
									LLM 입력
								</button>
							{/if}
						</div>
					</div>
				{/if}
			</div>

			<div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0">
				{#if isContext && contextTab === "rendered"}
					<div class="prose-dartlab text-[13px] leading-[1.7] pt-3">
						{@html renderMarkdown(ctx?.text)}
					</div>
				{:else if isTool}
					<div class="mt-3 space-y-3">
						<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker p-3">
							<div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">요약</div>
							<div class="text-[11px] text-dl-text-muted">
								{toolEvent?.type === "call" ? "LLM이 도구를 호출한 이벤트입니다." : "도구 실행 결과가 반환된 이벤트입니다."}
								{#if summarizeToolEvent(toolEvent)}
									<span class="text-dl-text"> {summarizeToolEvent(toolEvent)}</span>
								{/if}
							</div>
						</div>
						<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words">{modalText}</pre>
					</div>
				{:else}
					<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words">{modalText}</pre>
				{/if}
			</div>
		</div>
	</div>
{/if}
