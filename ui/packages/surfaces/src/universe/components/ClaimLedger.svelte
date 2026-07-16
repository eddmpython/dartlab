<script lang="ts">
	import type { UniverseClaimReceipt } from '@dartlab/ui-contracts';
	interface Props { claims: readonly UniverseClaimReceipt[]; }
	let { claims }: Props = $props();
</script>

<section class="ledger" aria-label="주장 원장">
	<header><span>CLAIM LEDGER</span><b>{claims.filter((claim) => claim.conclusionReady).length}/{claims.length} READY</b></header>
	<div>{#each claims as claim, index (claim.claimId)}<article class={claim.lane}>
		<span>{String(index + 1).padStart(2, '0')}</span><div><h3>{claim.label}</h3><p>{claim.falsifier}</p><small>{claim.evidence.evidenceRefs.length} evidence · {claim.gaps.length} gap</small></div><b>{claim.lane}</b>
	</article>{/each}</div>
</section>

<style>
	.ledger header { display: flex; justify-content: space-between; margin-bottom: 9px; }
	.ledger header span { color: #53657d; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.ledger header b { color: #7590b1; font: 600 8px/1 ui-monospace, monospace; }
	.ledger > div { display: grid; gap: 6px; }
	article { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: start; padding: 11px; border: 1px solid #1a2637; border-radius: 9px; background: #0d141f; }
	article > span { color: #53657d; font: 600 8px/1 ui-monospace, monospace; }
	article h3 { margin: 0; color: #c7d2e0; font-size: 11px; }
	article p { margin: 5px 0; color: #6e7f95; font-size: 9px; line-height: 1.45; }
	article small { color: #53657d; font: 500 7px/1 ui-monospace, monospace; }
	article > b { padding: 4px 6px; border-radius: 5px; color: #d7a64e; background: rgba(215,166,78,.08); font: 600 7px/1 ui-monospace, monospace; }
	article.fact > b { color: #62c493; }
	article.derived > b { color: #69aaf6; }
	article.scenario > b { color: #b891e5; }
</style>
