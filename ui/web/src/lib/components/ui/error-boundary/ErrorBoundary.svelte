<!--
	에러 바운더리 — 자식 컴포넌트 crash 방지 + 사용자 친화적 에러 UI + 재시도.
	Svelte 5 <svelte:boundary> 기반.
-->
<script>
	import { AlertTriangle, RefreshCw } from "lucide-svelte";
	import { cn } from "$lib/utils.js";

	let { children, title = "오류가 발생했습니다", class: className } = $props();

	let error = $state(null);

	function reset() {
		error = null;
	}
</script>

<svelte:boundary onerror={(e) => { error = e; }}>
	{#if error}
		<div class={cn(
			"flex flex-col items-center justify-center gap-3 py-8 px-4 rounded-xl border border-dl-border/40 bg-dl-bg-card/30 text-center animate-fadeIn",
			className
		)}>
			<div class="w-10 h-10 rounded-full bg-dl-primary/10 flex items-center justify-center">
				<AlertTriangle size={20} class="text-dl-primary" />
			</div>
			<div>
				<h4 class="text-sm font-medium text-dl-text mb-1">{title}</h4>
				<p class="text-[12px] text-dl-text-dim max-w-xs">
					{error.message || "알 수 없는 오류"}
				</p>
			</div>
			<button
				class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium text-dl-text-muted bg-dl-bg-card border border-dl-border/60 hover:text-dl-text hover:border-dl-primary/40 transition-all active:scale-95"
				onclick={reset}
			>
				<RefreshCw size={12} />
				다시 시도
			</button>
		</div>
	{:else}
		{@render children()}
	{/if}
</svelte:boundary>
