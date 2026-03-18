<script>
	import AutocompleteInput from "./AutocompleteInput.svelte";

	let { onSend, inputText = $bindable(""), onCompanySelect } = $props();
</script>

<div class="flex-1 flex flex-col items-center justify-center px-5">
	<div class="w-full max-w-[580px] flex flex-col items-center">
		<div class="relative mb-8">
			<div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div>
			<img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full" />
		</div>
		<h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1>
		<p class="text-sm text-dl-text-muted mb-6">종목명, 질문, 무엇이든 입력하세요</p>
		<div class="w-full">
			<AutocompleteInput
				bind:inputText
				large={true}
				placeholder="삼성전자 재무 건전성을 분석해줘..."
				{onSend}
				{onCompanySelect}
			/>
		</div>
	</div>
</div>
