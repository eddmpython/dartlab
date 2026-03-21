<!--
	대화 삭제 확인 다이얼로그.
-->
<script>
	const { ui, onConfirm } = $props();

	let dialogEl = $state(null);

	$effect(() => {
		if (!ui.deleteConfirmId || !dialogEl) return;
		requestAnimationFrame(() => dialogEl?.focus());
	});
</script>

{#if ui.deleteConfirmId}
	<div
		class="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) ui.deleteConfirmId = null; }}
		role="presentation"
	>
		<div
			bind:this={dialogEl}
			class="w-full max-w-xs bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl p-5"
			role="dialog"
			aria-modal="true"
			aria-labelledby="delete-dialog-title"
			tabindex="-1"
		>
			<div id="delete-dialog-title" class="text-[14px] font-medium text-dl-text mb-1.5">대화 삭제</div>
			<div class="text-[12px] text-dl-text-muted mb-4">이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다.</div>
			<div class="flex items-center justify-end gap-2">
				<button
					class="px-3.5 py-1.5 rounded-lg text-[12px] text-dl-text-muted hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={() => ui.deleteConfirmId = null}
				>
					취소
				</button>
				<button
					class="px-3.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors"
					onclick={onConfirm}
				>
					삭제
				</button>
			</div>
		</div>
	</div>
{/if}
