<script>
	import AutocompleteInput from "./AutocompleteInput.svelte";
	import { Database } from "lucide-svelte";

	let { onSend, inputText = $bindable(""), onOpenExplorer } = $props();
</script>

<div class="flex-1 flex flex-col items-center justify-center px-5">
	<div class="w-full max-w-[720px] flex flex-col items-center">
		<div class="relative mb-6">
			<div class="absolute inset-0 rounded-full blur-2xl opacity-40" style="background: radial-gradient(circle, rgba(234,70,71,0.6) 0%, rgba(251,146,60,0.3) 50%, transparent 70%); transform: scale(2.5);"></div>
			<img src="/avatar.png" alt="DartLab" class="relative w-16 h-16 rounded-full" />
		</div>
		<h1 class="text-2xl font-bold text-dl-text mb-1.5">무엇을 분석할까요?</h1>
		<p class="text-sm text-dl-text-muted mb-8">종목명과 질문을 입력하거나, 자유롭게 대화하세요</p>

		<div class="w-full">
			<AutocompleteInput
				bind:inputText
				large={true}
				placeholder="삼성전자 재무 건전성을 분석해줘..."
				{onSend}
			/>
		</div>

		<div class="mt-5 w-full">
			<button
				class="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl border border-dl-border bg-dl-bg-card/30 text-[13px] text-dl-text-dim hover:text-dl-text-muted hover:border-dl-primary/30 hover:bg-dl-bg-card/50 transition-all duration-200"
				onclick={() => onOpenExplorer?.()}
			>
				<Database size={14} />
				데이터 탐색
			</button>
		</div>
	</div>
</div>
