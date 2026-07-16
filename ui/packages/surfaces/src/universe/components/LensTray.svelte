<script lang="ts">
	import type { UniverseLensCard, UniverseLensTray } from '@dartlab/ui-contracts';

	interface Props { tray: UniverseLensTray | null; }
	let { tray }: Props = $props();

	function displayValue(card: UniverseLensCard): string {
		if (card.ref.value === null) return '결손';
		return `${String(card.ref.value)}${card.ref.unit ? ` ${card.ref.unit}` : ''}`;
	}
</script>

<section class="lensTray" aria-label="엔진 렌즈">
	<header><span>LENS TRAY</span><p>primary 1개와 comparison 1개까지만 표시합니다.</p></header>
	{#if tray}
		<div class="cards">
			{#each [tray.primary, ...(tray.comparison ? [tray.comparison] : [])] as card (card.lensId)}
				<article>
					<div><span>{card.role.toUpperCase()} · {card.ref.engine}.{card.ref.axis}</span><b class:missing={card.gaps.length}>{card.ref.status}</b></div>
					<h3>{card.ref.label}</h3>
					{#if card.ref.kind === 'tableRef' && card.ref.rows.length}
						<table><thead><tr>{#each card.ref.columns as column}<th>{column}</th>{/each}</tr></thead><tbody>{#each card.ref.rows.slice(0, 3) as row}<tr>{#each row as cell}<td>{cell ?? '결손'}</td>{/each}</tr>{/each}</tbody></table>
					{:else}<strong class="value">{displayValue(card)}</strong>{/if}
					<p>{card.ref.limitation}</p><code>{card.ref.sourceRef || 'sourceRef 결손'}</code>
				</article>
			{/each}
		</div>
	{:else}<p class="empty">산업을 선택하면 generic Ref 렌즈가 열립니다. 결손값은 0으로 바꾸지 않습니다.</p>{/if}
</section>

<style>
	.lensTray { margin-top: 22px; }
	header { display: flex; justify-content: space-between; align-items: center; }
	header span, article > div span { color: #53657d; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .1em; }
	header p { margin: 0; color: #596a81; font-size: 8px; }
	.cards { display: grid; gap: 7px; margin-top: 9px; }
	article { padding: 10px; border: 1px solid #182434; border-radius: 9px; background: #0d141f; }
	article > div { display: flex; justify-content: space-between; }
	article b { color: #63c493; font-size: 8px; }
	article b.missing { color: #d5a14a; }
	article h3 { margin: 8px 0; color: #cbd6e4; font-size: 11px; }
	.value { display: block; color: #e5ebf3; font: 600 16px/1 ui-monospace, monospace; }
	article p { margin: 8px 0 5px; color: #687990; font-size: 8px; line-height: 1.45; }
	article code { color: #53657c; font-size: 7px; overflow-wrap: anywhere; }
	table { width: 100%; border-collapse: collapse; font-size: 8px; }
	th, td { padding: 4px; border: 1px solid #1c293a; color: #8495aa; text-align: left; }
	.empty { color: #68798f; font-size: 9px; line-height: 1.5; }
</style>
