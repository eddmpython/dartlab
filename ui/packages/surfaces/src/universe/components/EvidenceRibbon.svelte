<script lang="ts">
	import type { EvidenceReceipt, GapReceipt } from '@dartlab/ui-contracts';

	interface Props {
		before: EvidenceReceipt;
		after: EvidenceReceipt;
		gaps?: readonly GapReceipt[];
	}

	let { before, after, gaps = [] }: Props = $props();

	function label(receipt: EvidenceReceipt): string {
		return receipt.status === 'supported' ? `${receipt.evidenceRefs.length}개 근거` : '정확 근거 없음';
	}
</script>

<div class="ribbon" aria-label="변화 전후 근거 상태">
	<div class:supported={before.status === 'supported'}><span>BEFORE</span><strong>{label(before)}</strong></div>
	<i aria-hidden="true">→</i>
	<div class:supported={after.status === 'supported'}><span>AFTER</span><strong>{label(after)}</strong></div>
	{#if gaps.length}<b title={gaps.map((gap) => gap.reasonCode).join(', ')}>{gaps.length} GAP</b>{/if}
</div>

<style>
	.ribbon { display: flex; align-items: center; gap: 8px; min-width: 280px; }
	.ribbon div { min-width: 86px; padding: 7px 9px; border: 1px dashed rgba(245,184,75,.3); border-radius: 8px; background: rgba(245,184,75,.05); }
	.ribbon div.supported { border-style: solid; border-color: rgba(61,196,132,.36); background: rgba(61,196,132,.07); }
	.ribbon span { display: block; color: #5d6e85; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .11em; }
	.ribbon strong { display: block; margin-top: 4px; color: #c7a75f; font-size: 9px; font-weight: 600; }
	.ribbon .supported strong { color: #68c99a; }
	.ribbon i { color: #405068; font-style: normal; }
	.ribbon b { padding: 4px 6px; border-radius: 5px; color: #d89d47; background: rgba(216,157,71,.1); font: 600 8px/1 ui-monospace, monospace; }
</style>
