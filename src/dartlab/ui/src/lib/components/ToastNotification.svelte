<!--
	Toast 알림 큐 — 최대 5개 스택, slide-in 등장 + progress bar 자동닫힘 시각화.
-->
<script>
	import { X, CheckCircle2, AlertCircle, Info } from "lucide-svelte";
	import { cn } from "$lib/utils.js";

	const { ui } = $props();

	const icons = {
		error: AlertCircle,
		success: CheckCircle2,
		info: Info,
	};

	const styles = {
		error: "bg-dl-primary/10 border-dl-primary/30 text-dl-primary-light",
		success: "bg-dl-success/10 border-dl-success/30 text-dl-success",
		info: "bg-dl-bg-card border-dl-border text-dl-text",
	};

	const progressColors = {
		error: "bg-dl-primary/60",
		success: "bg-dl-success/60",
		info: "bg-dl-text-dim/40",
	};
</script>

{#if ui.toastQueue?.length > 0}
	<div
		class="fixed bottom-6 right-6 z-[300] flex flex-col-reverse gap-2"
		aria-live="polite"
		aria-atomic="true"
	>
		{#each ui.toastQueue as toast, i (toast.id)}
			{@const Icon = icons[toast.type] || icons.info}
			<div class="toast-slide-in">
				<div class={cn(
					"surface-overlay flex flex-col rounded-2xl border text-[13px] shadow-2xl max-w-sm overflow-hidden",
					styles[toast.type] || styles.info
				)}>
					<div class="flex items-start gap-2.5 px-4 py-3">
						<Icon size={16} class="shrink-0 mt-0.5" />
						<div class="min-w-0 flex-1">{toast.message}</div>
						<button
							class="rounded-lg p-1 text-current/80 transition-colors hover:bg-white/5 hover:text-current"
							onclick={() => ui.dismissToast(toast.id)}
							aria-label="알림 닫기"
						>
							<X size={14} />
						</button>
					</div>
					<div class="h-[2px] w-full bg-white/5">
						<div
							class={cn("h-full rounded-full toast-progress", progressColors[toast.type] || progressColors.info)}
							style="animation-duration: {toast.duration}ms"
						></div>
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	@keyframes toast-slide-in {
		from {
			opacity: 0;
			transform: translateX(100%) translateY(0);
		}
		to {
			opacity: 1;
			transform: translateX(0) translateY(0);
		}
	}
	.toast-slide-in {
		animation: toast-slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1);
	}
	@keyframes toast-progress-shrink {
		from { width: 100%; }
		to { width: 0%; }
	}
	.toast-progress {
		animation: toast-progress-shrink linear forwards;
	}
	@media (prefers-reduced-motion: reduce) {
		.toast-slide-in {
			animation: none;
		}
		.toast-progress {
			animation: none;
		}
	}
</style>
