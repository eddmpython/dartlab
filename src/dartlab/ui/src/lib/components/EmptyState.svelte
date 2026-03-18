<script>
	import AutocompleteInput from "./AutocompleteInput.svelte";

	let { onSend, inputText = $bindable(""), onCompanySelect } = $props();

	const STARTERS = [
		"지금 dartlab에서 할 수 있는 기능을 먼저 정리해줘",
		"EDGAR에서 추가로 받을 수 있는 데이터와 방법을 알려줘",
		"OpenDart와 OpenEdgar로 가능한 일을 비교해줘",
		"GPT 연결 시 현재 UI에서 가능한 코딩 작업 범위를 알려줘",
	];
</script>

<div class="flex-1 flex flex-col items-center justify-center px-5">
	<div class="w-full max-w-[580px] flex flex-col items-center">
		<div class="relative mb-8">
			<div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div>
			<img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full" />
		</div>
		<h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1>
		<p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p>
		<div class="mb-6 max-w-[520px] rounded-2xl border border-dl-border/50 bg-dl-bg-card/50 px-4 py-3 text-left">
			<div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-dl-text-dim">Evidence First</div>
			<div class="mt-2 text-[13px] leading-relaxed text-dl-text-muted">
				DartLab은 재무 수치와 서술 텍스트를 함께 읽고, 표준화된 계정과 원문 근거를 같은 흐름에서 확인하도록 설계되어 있습니다.
				DART와 EDGAR를 포함한 40개 모듈 이상의 기능 범위를 먼저 물어본 뒤 바로 탐색을 시작할 수 있습니다.
			</div>
		</div>
		<div class="w-full">
			<AutocompleteInput
				bind:inputText
				large={true}
				placeholder="삼성전자 재무 건전성을 분석해줘..."
				{onSend}
				{onCompanySelect}
			/>
		</div>
		<div class="mt-5 flex w-full flex-wrap justify-center gap-2">
			{#each STARTERS as starter}
				<button
					class="rounded-full border border-dl-border/60 bg-dl-bg-card/40 px-3 py-1.5 text-[12px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-primary-light"
					onclick={() => onSend?.(starter)}
				>
					{starter}
				</button>
			{/each}
		</div>
	</div>
</div>
