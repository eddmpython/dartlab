<!--
	[최우선 UX 원칙] 데이터 투명성 — 절대 제거 금지

	LLM이 보는 모든 데이터는 UI에서 실시간으로 뱃지/태그로 표시해야 한다.
	시스템이 LLM에 제공하는 데이터(컨텍스트, 모듈, 시스템프롬프트)는 반드시 사용자에게 보여야 한다.

	SSE 이벤트 흐름과 UI 표시:
	  meta          → 회사 뱃지, 연도 범위 뱃지, includedModules
	  snapshot      → 핵심 수치 카드 (클릭 시 원본 JSON)
	  context       → 모듈별 데이터 뱃지 (클릭 시 원문/렌더링 모달)
	  system_prompt → "시스템 프롬프트" 버튼 (클릭 시 전문 확인)
	  tool_call     → 도구 호출 뱃지
	  tool_result   → 도구 결과 (toolEvents에 누적)
	  chunk         → 응답 텍스트 스트리밍
	  done          → 완료 (duration, 토큰 추정, 재생성 버튼)

	하단 메타: 응답 시간, 추정 토큰(입력↑/출력↓), 시스템 프롬프트, LLM 입력 전문
-->
<script>
	import { cn } from "$lib/utils.js";
	import {
		Database, Eye, Wrench, Loader2, Brain, FileText,
		RefreshCw, CheckCircle2, Clock,
	} from "lucide-svelte";
	import { renderMarkdown } from "$lib/markdown.js";
	import { estimateTokens, formatTokens } from "$lib/chat/tokenEstimator.js";
	import { createStreamSplitter } from "$lib/chat/contentSplitter.js";
	import { createIncrementalRenderer } from "$lib/markdown.js";
	import ViewSpecRenderer from "$lib/ai/ViewSpecRenderer.svelte";
	import TransparencyBadges from "./TransparencyBadges.svelte";
	import EvidenceModal from "./EvidenceModal.svelte";

	let { message, onRegenerate, onOpenEvidence } = $props();
	let openModal = $state(null);
	let modalType = $state("context");

	let loadingPhase = $derived.by(() => {
		if (!message.loading) return "";
		if (message.text) return "응답 작성 중";
		if (message.toolEvents?.length > 0) {
			const lastCall = [...message.toolEvents].reverse().find(e => e.type === "call");
			const detail = lastCall?.arguments?.module || lastCall?.arguments?.keyword || "";
			return `도구 실행 중 — ${lastCall?.name || ""}${detail ? ` (${detail})` : ""}`;
		}
		if (message.contexts?.length > 0) {
			const last = message.contexts[message.contexts.length - 1];
			return `데이터 분석 중 — ${last?.label || last?.module || ""}`;
		}
		if (message.snapshot) return "핵심 수치 확인 완료, 데이터 검색 중";
		if (message.meta?.company) return `${message.meta.company} 데이터 검색 중`;
		if (message.meta?.includedModules) return "분석 모듈 선택 완료";
		return "생각 중";
	});

	let companyName = $derived(message.company || message.meta?.company || null);
	const DIALOGUE_MODE_LABELS = {
		capability: "기능 탐색", coding: "코딩 작업", company_explore: "회사 탐색",
		company_analysis: "회사 분석", follow_up: "후속 질문", general_chat: "일반 대화",
	};
	let dialogueModeLabel = $derived(
		message.meta?.dialogueMode ? DIALOGUE_MODE_LABELS[message.meta.dialogueMode] || message.meta.dialogueMode : null
	);

	let hasTransparencyData = $derived(
		message.systemPrompt || message.userContent ||
		message.contexts?.length > 0 || message.meta?.includedModules ||
		message.toolEvents?.length > 0
	);

	let dataYearRange = $derived.by(() => {
		const raw = message.meta?.dataYearRange;
		if (!raw) return null;
		if (typeof raw === "string") return raw;
		if (raw.min_year && raw.max_year) return `${raw.min_year}~${raw.max_year}년`;
		return null;
	});

	let inputTokens = $derived.by(() => {
		let total = 0;
		if (message.systemPrompt) total += estimateTokens(message.systemPrompt);
		if (message.userContent) total += estimateTokens(message.userContent);
		else if (message.contexts?.length > 0) {
			for (const ctx of message.contexts) total += estimateTokens(ctx.text);
		}
		return total;
	});
	let outputTokens = $derived(estimateTokens(message.text));

	let contentEl = $state();
	const ICON_COPY = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
	const ICON_CHECK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

	function handleContentClick(e) {
		const btn = e.target.closest('.code-copy-btn');
		if (!btn) return;
		const wrap = btn.closest('.code-block-wrap');
		const code = wrap?.querySelector('code')?.textContent || "";
		navigator.clipboard.writeText(code).then(() => {
			btn.innerHTML = ICON_CHECK;
			setTimeout(() => { btn.innerHTML = ICON_COPY; }, 2000);
		});
	}

	function openContextModal(idx) {
		if (onOpenEvidence) { onOpenEvidence("contexts", idx); return; }
		openModal = idx; modalType = "context";
	}
	function openSystemPromptModal() {
		if (onOpenEvidence) { onOpenEvidence("system"); return; }
		openModal = 0; modalType = "system";
	}
	function openSnapshotModal() {
		if (onOpenEvidence) { onOpenEvidence("snapshot"); return; }
		openModal = 0; modalType = "snapshot";
	}
	function openToolEventModal(idx) {
		if (onOpenEvidence) {
			const event = message.toolEvents?.[idx];
			onOpenEvidence(event?.type === "result" ? "tool-results" : "tool-calls", idx);
			return;
		}
		openModal = idx; modalType = "tool";
	}
	function openUserContentModal() {
		if (onOpenEvidence) { onOpenEvidence("input"); return; }
		openModal = 0; modalType = "userContent";
	}

	let toolCallEvents = $derived((message.toolEvents || []).filter(e => e.type === "call"));
	let toolResultEvents = $derived((message.toolEvents || []).filter(e => e.type === "result"));
	const splitter = createStreamSplitter();
	const incRenderer = createIncrementalRenderer();
	let streamingContent = $derived.by(() => splitter.split(message.text || "", message.loading));
	let activityBadges = $derived.by(() => {
		const badges = [];
		if (message.meta?.includedModules?.length > 0) badges.push({ label: `모듈 ${message.meta.includedModules.length}개`, icon: Database });
		if (message.contexts?.length > 0) badges.push({ label: `컨텍스트 ${message.contexts.length}건`, icon: Eye });
		if (toolCallEvents.length > 0) badges.push({ label: `툴 호출 ${toolCallEvents.length}건`, icon: Wrench });
		if (toolResultEvents.length > 0) badges.push({ label: `툴 결과 ${toolResultEvents.length}건`, icon: CheckCircle2 });
		if (message.systemPrompt) badges.push({ label: "시스템 프롬프트", icon: Brain });
		if (message.userContent) badges.push({ label: "LLM 입력", icon: FileText });
		return badges;
	});

	// elapsed time for loading state
	let elapsed = $state(0);
	let elapsedTimer = null;
	$effect(() => {
		if (message.loading && message.startedAt) {
			elapsed = Math.round((Date.now() - message.startedAt) / 1000);
			elapsedTimer = setInterval(() => { elapsed = Math.round((Date.now() - message.startedAt) / 1000); }, 1000);
		} else {
			if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null; }
		}
		return () => { if (elapsedTimer) clearInterval(elapsedTimer); };
	});

	let loadingSteps = $derived.by(() => {
		if (!message.loading) return [];
		const steps = [];
		if (message.meta?.company) steps.push({ label: `${message.meta.company} 인식`, done: true });
		if (message.snapshot) steps.push({ label: "핵심 수치 확인", done: true });
		if (message.meta?.includedModules) steps.push({ label: `모듈 ${message.meta.includedModules.length}개 선택`, done: true });
		if (message.contexts?.length > 0) steps.push({ label: `데이터 ${message.contexts.length}건 로드`, done: true });
		if (message.systemPrompt) steps.push({ label: "프롬프트 조립", done: true });
		if (message.text) steps.push({ label: "응답 작성 중", done: false });
		else steps.push({ label: loadingPhase || "준비 중", done: false });
		return steps;
	});
</script>

{#if message.role === "user"}
	<div class="flex items-start gap-3 animate-fadeIn">
		<div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">
			You
		</div>
		<div class="flex-1 pt-0.5">
			<p class="text-[15px] text-dl-text leading-relaxed">{message.text}</p>
		</div>
	</div>
{:else}
	<div class="flex items-start gap-3 animate-fadeIn">
		<img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5" />
		<div class="message-shell flex-1 pt-0.5 min-w-0">

			<TransparencyBadges
				{message}
				{companyName}
				{dataYearRange}
				{dialogueModeLabel}
				{activityBadges}
				onOpenContextModal={openContextModal}
				onOpenSnapshotModal={openSnapshotModal}
				onOpenToolEventModal={openToolEventModal}
				onOpenSystemPromptModal={openSystemPromptModal}
				onOpenUserContentModal={openUserContentModal}
				{onOpenEvidence}
			/>

			<!-- ── 로딩: 진행 단계 표시 ── -->
			{#if message.loading && !message.text}
				<div class="animate-fadeIn">
					<div class="space-y-1 mb-3">
						{#each loadingSteps as step}
							<div class="flex items-center gap-2 text-[11px]">
								{#if step.done}
									<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0">
										<svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
									</span>
									<span class="text-dl-text-muted">{step.label}</span>
								{:else}
									<Loader2 size={14} class="animate-spin flex-shrink-0 text-dl-text-dim" />
									<span class="text-dl-text-dim animate-pulse">{step.label}</span>
								{/if}
							</div>
						{/each}
						{#if elapsed > 0}
							<div class="text-[10px] text-dl-text-dim/60 mt-1 font-mono">{elapsed}초 경과</div>
						{/if}
					</div>
					<div class="space-y-2.5">
						<div class="skeleton-line w-full"></div>
						<div class="skeleton-line w-[85%]"></div>
						<div class="skeleton-line w-[70%]"></div>
					</div>
				</div>
			{:else}
				{#if message.loading}
					<div class="message-section-slot flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim">
						<Loader2 size={12} class="animate-spin flex-shrink-0" />
						<span>{loadingPhase}</span>
					</div>
				{/if}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class={cn("prose-dartlab message-body text-[15px] leading-[1.75]", message.error && "text-dl-primary")}
					bind:this={contentEl}
					onclick={handleContentClick}
				>
					{#if streamingContent.committed}
						<div class="message-committed">
							{@html message.loading ? incRenderer.render(streamingContent.committed) : renderMarkdown(streamingContent.committed)}
						</div>
					{/if}
					{#if streamingContent.draft}
						<div class={cn(
							"message-live-tail",
							streamingContent.draftType === "table" && "message-draft-table",
							streamingContent.draftType === "code" && "message-draft-code"
						)}>
							<div class="message-live-label">
								{streamingContent.draftType === "table" ? "표 구성 중" : streamingContent.draftType === "code" ? "코드 블록 생성 중" : "응답 작성 중"}
							</div>
							<pre>{streamingContent.draft}</pre>
						</div>
					{/if}
				</div>

				<!-- ── Canonical ViewSpec 렌더 ── -->
				{#if message.renderViews?.length}
					<div class="mt-3 space-y-3">
						{#each message.renderViews as view}
							<ViewSpecRenderer {view} />
						{/each}
					</div>
				{/if}

				<!-- ── 하단 메타 (응답 완료 후) ── -->
				{#if !message.loading && (message.duration || hasTransparencyData || onRegenerate)}
					<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20">
						{#if message.duration}
							<span class="flex items-center gap-1 text-[10px] text-dl-text-dim">
								<Clock size={10} />
								{message.duration}초
							</span>
						{/if}

						{#if inputTokens > 0 || outputTokens > 0}
							<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)">
								{#if inputTokens > 0}
									<span class="text-dl-accent/60">↑{formatTokens(inputTokens)}</span>
								{/if}
								{#if outputTokens > 0}
									<span class="text-dl-success/60">↓{formatTokens(outputTokens)}</span>
								{/if}
							</span>
						{/if}

						{#if onRegenerate}
							<button
								class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"
								onclick={() => onRegenerate?.()}
							>
								<RefreshCw size={10} />
								재생성
							</button>
						{/if}

						{#if message.systemPrompt}
							<button
								class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"
								onclick={openSystemPromptModal}
							>
								<Brain size={10} />
								시스템 프롬프트
							</button>
						{/if}

						{#if message.userContent}
							<button
								class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"
								onclick={openUserContentModal}
							>
								<FileText size={10} />
								LLM 입력 ({message.userContent.length.toLocaleString()}자 · ~{formatTokens(estimateTokens(message.userContent))}tok)
							</button>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	</div>
{/if}

<EvidenceModal {message} bind:openModal bind:modalType />
