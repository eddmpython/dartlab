<!--
	Toast 알림 컴포넌트 — ui store의 toast 상태를 렌더링.
-->
<script>
	import { X } from "lucide-svelte";
	import { cn } from "$lib/utils.js";

	const { ui } = $props();
</script>

{#if ui.toastVisible}
	<div class="fixed bottom-6 right-6 z-[300] animate-fadeIn" aria-live="polite" aria-atomic="true">
		<div class={cn(
			"surface-overlay flex items-start gap-3 px-4 py-3 rounded-2xl border text-[13px] shadow-2xl max-w-sm",
			ui.toastType === "error" ? "bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light" :
			ui.toastType === "success" ? "bg-dl-success/10 border-dl-success/30 text-dl-success" :
			"bg-dl-bg-card border-dl-border text-dl-text"
		)}>
			<div class="min-w-0 flex-1">{ui.toastMessage}</div>
			<button
				class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current"
				onclick={() => ui.dismissToast()}
				aria-label="알림 닫기"
			>
				<X size={14} />
			</button>
		</div>
	</div>
{/if}
