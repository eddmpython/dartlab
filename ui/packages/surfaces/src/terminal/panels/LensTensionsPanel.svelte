<script lang="ts">
	import type { LensEngine, LensProduct, LensProductBundle, LensTensionItem } from '@dartlab/ui-contracts';
	import type { Lang } from '../lib/types';
	import Panel from '../ui/Panel.svelte';

	interface Props {
		bundle: LensProductBundle | null;
		loadState: 'loading' | 'ready' | 'empty';
		lang: Lang;
	}
	let { bundle, loadState, lang }: Props = $props();
	let dialogOpen = $state(false);
	let dialogTarget = $state<string | null>(null);
	const order: LensEngine[] = ['analysis', 'credit', 'industry', 'quant', 'macro'];
	const shortName: Record<LensEngine, { kr: string; en: string }> = {
		analysis: { kr: '재무', en: 'A' },
		credit: { kr: '신용', en: 'C' },
		industry: { kr: '산업', en: 'I' },
		quant: { kr: '시장', en: 'Q' },
		macro: { kr: '거시', en: 'M' }
	};
	const kindLabel: Record<LensTensionItem['kind'], { kr: string; en: string }> = {
		divergence: { kr: '괴리', en: 'DIVERGENCE' },
		tradeoff: { kr: '상충', en: 'TRADEOFF' },
		counterforce: { kr: '반대힘', en: 'COUNTERFORCE' }
	};
	const directionLabel = (value: string): string => {
		if (lang === 'en') return ({ supportive: 'positive direction', adverse: 'negative direction', neutral: 'neutral', unknown: 'unknown' } as Record<string, string>)[value] ?? value;
		return ({ supportive: '긍정 방향', adverse: '부정 방향', neutral: '중립', unknown: '미상' } as Record<string, string>)[value] ?? value;
	};
	const active = $derived(bundle?.tensions?.items ?? []);
	const blocked = $derived(bundle?.tensions?.evaluations.filter((row) => row.status === 'blocked').length ?? 0);
	const statusText = (product: LensProduct | undefined): string => {
		if (!product) return lang === 'en' ? 'missing' : '없음';
		if (lang === 'en') return product.status;
		return ({ usable: '사용', partial: '부분', blocked: '차단', notApplicable: '제외' })[product.status];
	};
	const openDialog = (): void => {
		dialogTarget = bundle?.target ?? null;
		dialogOpen = true;
	};
	$effect(() => {
		const currentTarget = bundle?.target ?? null;
		if (dialogOpen && dialogTarget !== currentTarget) dialogOpen = false;
	});
</script>

<Panel
	{lang}
	className="eAnalysis lensTensionPanel"
	prov="derived"
	title={{ kr: '렌즈 간극', en: 'LENS GAPS' }}
	sub={{ kr: '고정 규칙이 포착한 불일치 가설', en: 'mismatch hypotheses from fixed rules' }}
	flush
>
	{#snippet right()}
		{#if loadState === 'ready'}<span class="tensionCount">{active.length} {lang === 'en' ? 'observed' : '포착'}</span>{/if}
		<button class="finFullBtn" onclick={openDialog} disabled={loadState === 'loading'}>{lang === 'en' ? 'detail' : '상세보기'}</button>
	{/snippet}
	{#if loadState === 'loading'}
		<div class="tensionMessage">{lang === 'en' ? 'Reading engine evidence...' : '엔진 근거를 읽는 중입니다.'}</div>
	{:else if loadState === 'empty' || !bundle}
		<div class="tensionMessage">
			<b>{lang === 'en' ? 'Tension artifact unavailable' : '틈 결과 미발행'}</b>
			<span>{lang === 'en' ? 'No browser inference was substituted.' : '브라우저 추론으로 대체하지 않았습니다.'}</span>
		</div>
	{:else}
		<div class="lensStateRail" aria-label={lang === 'en' ? 'lens evidence states' : '렌즈 근거 상태'}>
			{#each order as engine (engine)}
				{@const product = bundle.products[engine]}
				<span class="lensStateChip" data-status={product?.status ?? 'missing'} title={`${shortName[engine].kr}: ${statusText(product)}`}>
					<b>{lang === 'en' ? shortName[engine].en : shortName[engine].kr}</b><i>{statusText(product)}</i>
				</span>
			{/each}
		</div>
		{#if active.length}
			<div class="tensionList">
				{#each active.slice(0, 2) as item (item.id)}
					<button class="tensionRow" onclick={openDialog} title={lang === 'en' ? item.question.en : item.question.kr}>
						<span class="tensionKind">{lang === 'en' ? kindLabel[item.kind].en : kindLabel[item.kind].kr}</span>
						<strong>{lang === 'en' ? item.headline.en : item.headline.kr}</strong>
						<span class="tensionSides">
							{#each item.sides as side, index (side.engine + side.claimId)}
								{#if index > 0}<i>×</i>{/if}<b>{shortName[side.engine][lang]}</b> {directionLabel(side.direction)}
							{/each}
							<time>{item.asOf}</time>
						</span>
					</button>
				{/each}
			</div>
			{#if active.length > 2}<div class="tensionMore">+{active.length - 2} {lang === 'en' ? 'more in detail' : '상세에서 더 보기'}</div>{/if}
		{:else}
			<div class="tensionClear">
				<b>{lang === 'en' ? 'No mismatch captured now' : '현재 포착된 간극 없음'}</b>
				<span>{blocked ? `${blocked} ${lang === 'en' ? 'rules blocked by evidence gaps' : '개 규칙은 근거 부족으로 차단'}` : (lang === 'en' ? 'No opposite direction was observed in the five rules.' : '다섯 규칙에서 반대 방향이 관찰되지 않았습니다.')}</span>
			</div>
		{/if}
	{/if}
</Panel>

{#if dialogOpen && dialogTarget === bundle?.target}
	{#await import('./LensTensionsDialog.svelte') then { default: LensTensionsDialog }}
		<LensTensionsDialog {bundle} {loadState} {lang} onClose={() => (dialogOpen = false)} />
	{/await}
{/if}

<style>
	.tensionCount { color: var(--amber); font-family: var(--mono); font-size: 9px; }
	.tensionMessage, .tensionClear { min-height: 78px; display: flex; flex-direction: column; justify-content: center; gap: 3px; padding: 9px 11px; color: var(--dim); font-size: 10px; line-height: 1.35; }
	.tensionMessage b, .tensionClear b { color: var(--text); font-size: 10.5px; }
	.lensStateRail { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border-bottom: 1px solid var(--bd); }
	.lensStateChip { min-width: 0; padding: 5px 2px 4px; text-align: center; border-right: 1px solid var(--bd); border-top: 2px solid var(--good); }
	.lensStateChip:last-child { border-right: 0; }
	.lensStateChip[data-status='partial'] { border-top-color: var(--warn); }
	.lensStateChip[data-status='blocked'], .lensStateChip[data-status='missing'] { border-top-color: var(--dimmer); }
	.lensStateChip[data-status='notApplicable'] { border-top-color: var(--dim); }
	.lensStateChip b, .lensStateChip i { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.lensStateChip b { color: var(--text); font-size: 9px; }
	.lensStateChip i { margin-top: 1px; color: var(--dimmer); font-family: var(--mono); font-size: 8px; font-style: normal; }
	.tensionList { display: flex; flex-direction: column; }
	.tensionRow { display: grid; grid-template-columns: 42px minmax(0, 1fr); gap: 2px 7px; padding: 7px 9px; border: 0; border-bottom: 1px solid var(--bd); background: transparent; color: inherit; text-align: left; cursor: pointer; }
	.tensionRow:hover { background: rgba(245, 158, 11, .045); }
	.tensionKind { grid-row: span 2; align-self: start; margin-top: 1px; padding: 2px 3px; border: 1px solid rgba(245, 158, 11, .34); color: var(--amber); font-family: var(--mono); font-size: 8px; text-align: center; }
	.tensionRow strong { min-width: 0; overflow: hidden; color: var(--text); font-size: 10px; line-height: 1.3; text-overflow: ellipsis; white-space: nowrap; }
	.tensionSides { min-width: 0; overflow: hidden; color: var(--dim); font-family: var(--mono); font-size: 8.5px; text-overflow: ellipsis; white-space: nowrap; }
	.tensionSides b { color: var(--text); font-weight: 600; }
	.tensionSides i { margin: 0 4px; color: var(--dimmer); font-style: normal; }
	.tensionSides time { margin-left: 7px; color: var(--dimmer); }
	.tensionMore { padding: 3px 9px; color: var(--dimmer); font-family: var(--mono); font-size: 8px; text-align: right; }
</style>
