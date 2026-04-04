<script>
	import { X } from "lucide-svelte";

	let {
		detailModal = null,
		onClose,
	} = $props();

	let detailDialog = $state(null);

	$effect(() => {
		if (!detailModal || !detailDialog) return;
		requestAnimationFrame(() => detailDialog?.focus());
	});
</script>

{#if detailModal}
	<div
		class="fixed inset-0 z-[320] flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm"
		onclick={(event) => { if (event.target === event.currentTarget) onClose?.(); }}
		role="presentation"
	>
		<div
			bind:this={detailDialog}
			class="max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-2xl border border-dl-border bg-dl-bg-card shadow-2xl shadow-black/30"
			role="dialog"
			aria-modal="true"
			aria-labelledby="workspace-detail-title"
			tabindex="-1"
			onkeydown={(event) => { if (event.key === "Escape") onClose?.(); }}
		>
			<div class="flex items-center justify-between border-b border-dl-border/50 px-5 py-4">
				<div>
					<div id="workspace-detail-title" class="text-[14px] font-semibold text-dl-text">{detailModal.title}</div>
					<div class="mt-1 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">
						{detailModal.type === "context"
							? "Context Detail"
							: detailModal.type === "tool" || detailModal.type === "tool-call" || detailModal.type === "tool-result"
								? "Tool Event"
								: detailModal.type === "snapshot"
									? "Snapshot"
									: "Prompt Detail"}
					</div>
				</div>
				<button
					class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text"
					onclick={() => onClose?.()}
					aria-label="상세 데이터 닫기"
				>
					<X size={16} />
				</button>
			</div>
			<div class="max-h-[calc(80vh-76px)] overflow-y-auto p-5">
				{#if detailModal.type === "context"}
					<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4">
						<pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted">{detailModal.payload?.text || "-"}</pre>
					</div>
				{:else if detailModal.type === "tool" || detailModal.type === "tool-call" || detailModal.type === "tool-result"}
					<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted">{JSON.stringify(detailModal.payload, null, 2)}</pre>
				{:else if detailModal.type === "snapshot"}
					<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted">{JSON.stringify(detailModal.payload, null, 2)}</pre>
				{:else}
					<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4">
						<pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted">{detailModal.payload || "-"}</pre>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
