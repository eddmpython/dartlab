<script>
	import AutocompleteInput from "./AutocompleteInput.svelte";
	import { Database, Search } from "lucide-svelte";

	let { onSend, inputText = $bindable(""), onOpenExplorer, selectedCompany = null } = $props();

	const starterPrompts = [
		"표준화된 계정 기준으로 최근 실적 변화를 비교해줘",
		"사업보고서와 공시 텍스트에서 핵심 리스크를 정리해줘",
		"재무 수치와 원문 근거를 같이 보여주면서 설명해줘",
	];
</script>

<div class="flex-1 flex flex-col items-center justify-center px-5">
	<div class="w-full max-w-[720px] flex flex-col items-center">
		<div class="relative mb-6">
			<div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div>
			<img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full" />
		</div>
		<h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1>
		<p class="text-sm text-dl-text-muted mb-4">재무 수치와 서술 텍스트를 함께 읽고, 필요하면 원문 근거까지 바로 확인할 수 있습니다</p>

		{#if selectedCompany}
			<div class="mb-6 inline-flex items-center gap-2 rounded-full border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-1.5 text-[12px] text-dl-text">
				<Database size={13} class="text-dl-primary-light" />
				<span>{selectedCompany.corpName || selectedCompany.company || "선택된 회사"} · {selectedCompany.stockCode}</span>
			</div>
		{/if}

		<div class="w-full">
			<AutocompleteInput
				bind:inputText
				large={true}
				placeholder="삼성전자 재무 건전성을 분석해줘..."
				{onSend}
			/>
		</div>

		<div class="mt-5 grid w-full gap-3 md:grid-cols-3">
			<div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3">
				<div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Coverage</div>
				<div class="mt-1 text-[18px] font-semibold text-dl-text">40개 모듈</div>
				<div class="mt-1 text-[11px] text-dl-text-dim">재무, 주석, 사업, 리스크, 지배구조까지 연결</div>
			</div>
			<div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3">
				<div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Schema</div>
				<div class="mt-1 text-[18px] font-semibold text-dl-text">표준화 계정</div>
				<div class="mt-1 text-[11px] text-dl-text-dim">회사마다 다른 XBRL 계정을 비교 가능한 구조로 정리</div>
			</div>
			<div class="surface-panel rounded-2xl border border-dl-border/60 px-4 py-3">
				<div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Evidence</div>
				<div class="mt-1 text-[18px] font-semibold text-dl-text">원문 근거 보존</div>
				<div class="mt-1 text-[11px] text-dl-text-dim">숫자와 서술 텍스트를 함께 보고 근거까지 바로 열람</div>
			</div>
		</div>

		<div class="mt-5 grid w-full gap-3 md:grid-cols-3">
			<button
				class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"
				onclick={() => onOpenExplorer?.("explore")}
			>
				<Search size={14} />
				검색 탐색
			</button>
			<button
				class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"
				onclick={() => onOpenExplorer?.("overview")}
			>
				<Database size={14} />
				Overview
			</button>
			<button
				class="surface-panel flex items-center justify-center gap-2 rounded-2xl border border-dl-border/60 px-4 py-3 text-[13px] text-dl-text-dim transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:text-dl-text-muted"
				onclick={() => onOpenExplorer?.("evidence")}
			>
				<Database size={14} />
				근거 패널
			</button>
		</div>

		<div class="surface-panel mt-5 w-full rounded-[24px] border border-dl-border/60 p-4">
			<div class="mb-3 flex items-center justify-between gap-3">
				<div>
					<div class="text-[12px] font-medium text-dl-text">바로 시작할 질문</div>
					<div class="mt-1 text-[11px] text-dl-text-dim">표준화된 계정, 40개 모듈, 원문 근거 보존이라는 DartLab의 강점을 바로 써먹는 질문입니다.</div>
				</div>
				<span class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[9px] uppercase tracking-[0.16em] text-dl-primary-light">Evidence First</span>
			</div>
			<div class="grid gap-2 md:grid-cols-3">
				{#each starterPrompts as prompt}
					<button
						class="rounded-2xl border border-dl-border/50 bg-dl-bg-card/40 px-3 py-3 text-left text-[12px] text-dl-text-muted transition-all duration-200 hover:-translate-y-0.5 hover:border-dl-primary/30 hover:bg-dl-bg-card/65 hover:text-dl-text"
						onclick={() => { inputText = selectedCompany ? `${selectedCompany.corpName || selectedCompany.company || selectedCompany.stockCode} ${prompt}` : prompt; }}
					>
						{prompt}
					</button>
				{/each}
			</div>
		</div>
	</div>
</div>
