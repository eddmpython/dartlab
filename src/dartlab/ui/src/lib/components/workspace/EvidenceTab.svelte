<script>
	import { cn } from "$lib/utils.js";
	import { Database, Wrench, Brain, Eye, CheckCircle2 } from "lucide-svelte";

	let {
		evidenceMessage = null,
		evidenceStats = [],
		evidenceContexts = [],
		evidenceTools = [],
		evidenceToolResults = [],
		onOpenDetailModal,
	} = $props();
</script>

{#if !evidenceMessage}
	<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center">
		<Database size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
		<div class="text-[13px] font-medium text-dl-text">아직 연결된 응답이 없습니다</div>
		<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
			채팅을 시작하면 이 패널에서 스냅샷, 사용한 모듈, 도구 호출, 시스템 프롬프트 요약을 함께 확인할 수 있습니다.
		</div>
	</div>
{:else}
	<div class="space-y-3">
		{#if evidenceStats.length > 0}
			<div class="grid grid-cols-2 gap-2">
				{#each evidenceStats as stat}
					<div class={cn(
						"rounded-2xl border px-3 py-3",
						stat.tone === "success"
							? "border-dl-success/20 bg-dl-success/[0.06]"
							: stat.tone === "accent"
								? "border-dl-accent/20 bg-dl-accent/[0.06]"
								: "border-dl-border/40 bg-dl-bg-darker/70"
					)}>
						<div class="text-[10px] text-dl-text-dim">{stat.label}</div>
						<div class="mt-1 text-[18px] font-semibold text-dl-text">{stat.value}</div>
					</div>
				{/each}
			</div>
		{/if}

		{#if evidenceMessage.meta?.company || evidenceMessage.meta?.dataYearRange}
			<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
				<div class="text-[12px] font-medium text-dl-text">현재 답변 컨텍스트</div>
				<div class="mt-2 flex flex-wrap gap-1.5">
					{#if evidenceMessage.meta?.company}
						<span class="rounded-full bg-dl-primary/10 px-2 py-1 text-[10px] text-dl-primary-light">{evidenceMessage.meta.company}</span>
					{/if}
					{#if evidenceMessage.meta?.dataYearRange}
						<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted">
							{typeof evidenceMessage.meta.dataYearRange === "string"
								? evidenceMessage.meta.dataYearRange
								: `${evidenceMessage.meta.dataYearRange.min_year}~${evidenceMessage.meta.dataYearRange.max_year}년`}
						</span>
					{/if}
					{#each evidenceMessage.meta?.includedModules || [] as moduleName}
						<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted">
							{moduleName}
						</span>
					{/each}
				</div>
			</div>
		{/if}

		{#if evidenceMessage.snapshot?.items?.length > 0}
			<button
				data-evidence-section="snapshot"
				class="block w-full rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4 text-left transition-colors hover:border-dl-primary/25 hover:bg-dl-bg-darker/85"
				onclick={() => onOpenDetailModal?.("snapshot", evidenceMessage.snapshot, "핵심 수치")}
			>
				<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
					<Database size={13} class="text-dl-success" />
					핵심 수치
				</div>
				<div class="grid grid-cols-2 gap-2">
					{#each evidenceMessage.snapshot.items as item}
						<div class="rounded-xl bg-dl-bg-card/60 p-2.5">
							<div class="text-[10px] text-dl-text-dim">{item.label}</div>
							<div class="mt-1 text-[12px] font-semibold text-dl-text">{item.value}</div>
						</div>
					{/each}
				</div>
			</button>
		{/if}

		<div data-evidence-section="contexts" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
				<Database size={13} class="text-dl-accent" />
				근거 모듈
			</div>
			{#if evidenceContexts.length > 0}
				<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">
					이 답변에 직접 투입된 원문/구조화 데이터입니다. 각 카드를 누르면 전문을 확인할 수 있습니다.
				</div>
				<div class="space-y-2">
					{#each evidenceContexts as ctx}
						<button
							class="w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"
							onclick={() => onOpenDetailModal?.("context", ctx, ctx.label || ctx.module || "컨텍스트")}
						>
							<div class="flex items-center justify-between gap-2">
								<div class="text-[11px] font-medium text-dl-text">{ctx.label || ctx.module}</div>
								<span class="inline-flex items-center gap-1 text-[10px] text-dl-primary-light">
									<Eye size={11} />
									상세
								</span>
							</div>
							<div class="mt-1 line-clamp-3 text-[10px] leading-relaxed text-dl-text-dim">{ctx.text}</div>
						</button>
					{/each}
				</div>
			{:else}
				<div class="text-[11px] text-dl-text-dim">표시할 컨텍스트 데이터가 없습니다.</div>
			{/if}
		</div>

		<div data-evidence-section="tool-calls" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
				<Wrench size={13} class="text-dl-primary-light" />
				도구 호출
			</div>
			{#if evidenceTools.length > 0}
				<div class="space-y-1.5">
					{#each evidenceTools as tool}
						<button
							class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"
							onclick={() => onOpenDetailModal?.("tool-call", tool, `${tool.name} 호출`)}
						>
							<span>
								{tool.name}
								{#if tool.arguments?.module} · {tool.arguments.module}{/if}
								{#if tool.arguments?.keyword} · {tool.arguments.keyword}{/if}
							</span>
							<span class="inline-flex items-center gap-1 text-dl-primary-light">
								<CheckCircle2 size={11} />
								JSON
							</span>
						</button>
					{/each}
				</div>
			{:else}
				<div class="text-[11px] text-dl-text-dim">도구 호출 기록이 없습니다.</div>
			{/if}
		</div>

		<div data-evidence-section="tool-results" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
			<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
				<CheckCircle2 size={13} class="text-dl-success" />
				도구 결과
			</div>
			{#if evidenceToolResults.length > 0}
				<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">
					LLM이 받은 실제 툴 결과입니다. 요약만 보지 말고 상세를 열어 반환 구조를 검증할 수 있습니다.
				</div>
				<div class="space-y-1.5">
					{#each evidenceToolResults as tool}
						<button
							class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"
							onclick={() => onOpenDetailModal?.("tool-result", tool, `${tool.name} 결과`)}
						>
							<span class="min-w-0 flex-1 truncate">
								{tool.name}
								{#if typeof tool.result === "string"} · {tool.result.slice(0, 80)}{/if}
							</span>
							<span class="inline-flex items-center gap-1 text-dl-success">
								<Eye size={11} />
								상세
							</span>
						</button>
					{/each}
				</div>
			{:else}
				<div class="text-[11px] text-dl-text-dim">도구 결과 기록이 없습니다.</div>
			{/if}
		</div>

		{#if evidenceMessage.systemPrompt || evidenceMessage.userContent}
			<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
				<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
					<Brain size={13} class="text-dl-accent-light" />
					프롬프트 투명성
				</div>
				{#if evidenceMessage.systemPrompt}
					<button
						data-evidence-section="system"
						class="mb-2 block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"
						onclick={() => onOpenDetailModal?.("system", evidenceMessage.systemPrompt, "System Prompt")}
					>
						<div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">System</div>
						<div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted">{evidenceMessage.systemPrompt}</div>
					</button>
				{/if}
				{#if evidenceMessage.userContent}
					<button
						data-evidence-section="input"
						class="block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"
						onclick={() => onOpenDetailModal?.("user", evidenceMessage.userContent, "LLM Input")}
					>
						<div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">LLM Input</div>
						<div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted">{evidenceMessage.userContent}</div>
					</button>
				{/if}
			</div>
		{/if}
	</div>
{/if}
