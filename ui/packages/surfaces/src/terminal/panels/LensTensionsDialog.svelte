<script lang="ts">
	import type { LensEngine, LensEvidence, LensProductBundle, LensTensionEvaluation, LensTensionItem, LensTensionSide } from '@dartlab/ui-contracts';
	import type { Lang } from '../lib/types';
	import LensProductsPanel from './LensProductsPanel.svelte';

	interface Props {
		bundle: LensProductBundle | null;
		loadState: 'loading' | 'ready' | 'empty';
		lang: Lang;
		onClose: () => void;
	}
	let { bundle, loadState, lang, onClose }: Props = $props();
	let tab = $state<'tensions' | 'lenses'>('tensions');
	const engineName: Record<LensEngine, { kr: string; en: string }> = {
		analysis: { kr: '재무 인과', en: 'ANALYSIS' },
		credit: { kr: '신용 하방', en: 'CREDIT' },
		industry: { kr: '산업 위치', en: 'INDUSTRY' },
		quant: { kr: '시장 기대', en: 'QUANT' },
		macro: { kr: '거시 전파', en: 'MACRO' }
	};
	const kindLabel: Record<LensTensionItem['kind'], { kr: string; en: string }> = {
		divergence: { kr: '괴리', en: 'DIVERGENCE' },
		tradeoff: { kr: '상충', en: 'TRADEOFF' },
		counterforce: { kr: '반대힘', en: 'COUNTERFORCE' }
	};
	const patternName: Record<string, { kr: string; en: string }> = {
		fundamentalPriceDivergence: { kr: '펀더멘털과 가격', en: 'Fundamental vs price' },
		earningsCashDivergence: { kr: '이익과 현금', en: 'Earnings vs cash' },
		growthCreditTradeoff: { kr: '성장과 신용', en: 'Growth vs credit' },
		industryExecutionCounterforce: { kr: '산업과 실행', en: 'Industry vs execution' },
		macroCompanyCounterforce: { kr: '거시와 회사', en: 'Macro vs company' }
	};
	const reasonName: Record<string, { kr: string; en: string }> = {
		aligned: { kr: '반대 방향 미관찰', en: 'no opposite direction observed' },
		missingProduct: { kr: '렌즈 제품 없음', en: 'lens product missing' },
		productNotUsable: { kr: '렌즈 근거 불충분', en: 'lens evidence insufficient' },
		identityMismatch: { kr: '회사 식별 불일치', en: 'company identity mismatch' },
		timeMismatch: { kr: '판단 시점 불일치', en: 'decision time mismatch' },
		missingTypedClaims: { kr: '비교 주장 없음', en: 'typed claims missing' },
		missingTypedClaim: { kr: '필요한 비교 주장 없음', en: 'required typed claim missing' },
		claimConflict: { kr: '관계 주장과 방향 불일치', en: 'relation and direction conflict' }
	};
	const directionLabel = (value: string): string => {
		if (lang === 'en') return ({ supportive: 'positive direction', adverse: 'negative direction', neutral: 'neutral', unknown: 'unknown' } as Record<string, string>)[value] ?? value;
		return ({ supportive: '긍정 방향', adverse: '부정 방향', neutral: '중립', unknown: '방향 미상' } as Record<string, string>)[value] ?? value;
	};
	const evaluationLabel = (row: LensTensionEvaluation): string => {
		if (row.status === 'active') return lang === 'en' ? 'mismatch observed' : '불일치 관찰';
		const reason = reasonName[row.reason];
		const text = reason ? reason[lang] : row.reason;
		if (row.status === 'clear') return text;
		return lang === 'en' ? `blocked: ${text}` : `차단: ${text}`;
	};
	const evidenceFor = (side: LensTensionSide): LensEvidence[] => {
		const refs = new Set(side.evidenceRefs);
		return bundle?.products[side.engine]?.evidence.filter((row) => refs.has(row.id)) ?? [];
	};

	$effect(() => {
		const onKey = (event: KeyboardEvent) => {
			if (event.key === 'Escape') onClose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<div class="scrimWrap" role="presentation" onclick={onClose}>
	<div class="scrModal lensDialog" role="dialog" aria-modal="true" tabindex="-1" aria-label={lang === 'en' ? 'Lens tensions' : '렌즈 틈 상세'} onclick={(event) => event.stopPropagation()} onkeydown={(event) => event.stopPropagation()}>
		<div class="scrHead">
			<span class="scrTitle">{lang === 'en' ? 'LENS GAPS' : '렌즈 간극'}</span>
			<span class="lensDialogTarget">{bundle?.target ?? ''} · {bundle?.market ?? ''}</span>
			<div class="lensTabs" role="tablist">
				<button class:active={tab === 'tensions'} onclick={() => (tab = 'tensions')} role="tab" aria-selected={tab === 'tensions'}>{lang === 'en' ? 'Tensions' : '틈'}</button>
				<button class:active={tab === 'lenses'} onclick={() => (tab = 'lenses')} role="tab" aria-selected={tab === 'lenses'}>{lang === 'en' ? 'Lenses' : '렌즈'}</button>
			</div>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>

		{#if tab === 'tensions'}
			<div class="tensionDialogBody">
				<div class="tensionRuleNote">
					<b>{lang === 'en' ? 'Five fixed comparison rules' : '고정된 다섯 비교 규칙'}</b>
					<span>{lang === 'en' ? 'Grounded typed claims can raise a mismatch hypothesis. This is not proof, a composite score, or a buy or sell verdict.' : '근거가 연결된 비교 주장이 불일치 가설을 제기합니다. 확정적 증명, 종합점수, 매수 또는 매도 판정이 아닙니다.'}</span>
				</div>
				{#if loadState === 'loading'}
					<div class="dialogEmpty">{lang === 'en' ? 'Reading engine evidence...' : '엔진 근거를 읽는 중입니다.'}</div>
				{:else if !bundle}
					<div class="dialogEmpty">{lang === 'en' ? 'Tension artifact unavailable.' : '틈 결과가 발행되지 않았습니다.'}</div>
				{:else if bundle.tensions.items.length}
					<div class="tensionCards">
						{#each bundle.tensions.items as item (item.id)}
							<article class="tensionCard">
								<header>
									<span class="kindBadge">{lang === 'en' ? kindLabel[item.kind].en : kindLabel[item.kind].kr}</span>
									<h3>{lang === 'en' ? item.headline.en : item.headline.kr}</h3>
									<time>{item.asOf}</time>
								</header>
								<p class="mechanism">{lang === 'en' ? item.mechanism.en : item.mechanism.kr}</p>
								<div class="sideGrid">
									{#each item.sides as side (side.engine + side.claimId)}
										<div class="sideCard">
											<span class="sideEngine">{engineName[side.engine][lang]}</span>
											<b>{side.label}</b>
											<span>{directionLabel(side.direction)} · {side.period ?? side.horizon}</span>
											{#each evidenceFor(side) as evidence (evidence.id)}
												<span class="sideEvidence"><b>{evidence.kind}</b>{evidence.detail ?? evidence.sourceRef}</span>
											{/each}
										</div>
									{/each}
								</div>
								<div class="nextQuestion"><b>{lang === 'en' ? 'NEXT QUESTION' : '다음 질문'}</b><span>{lang === 'en' ? item.question.en : item.question.kr}</span></div>
								{#if item.falsifiers.length}
									<div class="falsifierList">
										<b>{lang === 'en' ? 'WHAT WOULD BREAK THIS' : '이 틈을 깨는 관측'}</b>
										{#each item.falsifiers as row (row.id)}<span>{row.condition}</span>{/each}
									</div>
								{/if}
								{#if item.gaps.length}
									<div class="gapList">
										<b>{lang === 'en' ? 'LIMITS' : '남은 한계'}</b>
										{#each item.gaps as row (row.id)}<span>{row.reason}</span>{/each}
									</div>
								{/if}
							</article>
						{/each}
					</div>
				{:else}
					<div class="dialogEmpty"><b>{lang === 'en' ? 'No mismatch captured now' : '현재 포착된 간극이 없습니다.'}</b><span>{lang === 'en' ? 'Blocked rules remain visible below and are not treated as no mismatch.' : '근거 부족으로 차단된 규칙은 불일치 없음으로 간주하지 않고 아래에 남깁니다.'}</span></div>
				{/if}

				{#if bundle}
					<div class="evaluationGrid">
						{#each bundle.tensions.evaluations as row (row.patternId)}
							<div data-status={row.status}><b>{patternName[row.patternId]?.[lang] ?? row.patternId}</b><span>{evaluationLabel(row)}</span></div>
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<div class="lensDialogBody"><LensProductsPanel {bundle} state={loadState} {lang} /></div>
		{/if}
	</div>
</div>

<style>
	.lensDialog { width: min(940px, 96vw); }
	.lensDialogTarget { color: var(--dim); font-family: var(--mono); font-size: 9px; }
	.lensTabs { display: flex; gap: 2px; margin-left: auto; }
	.lensTabs button { min-width: 54px; padding: 4px 9px; border: 1px solid var(--bd); background: transparent; color: var(--dim); font-size: 9px; cursor: pointer; }
	.lensTabs button.active { border-color: rgba(245, 158, 11, .55); background: rgba(245, 158, 11, .08); color: var(--amber); }
	.lensDialog .scrClose { margin-left: 0; }
	.tensionDialogBody, .lensDialogBody { min-height: 0; overflow-y: auto; padding: 12px; }
	.lensDialogBody { padding: 0; }
	.tensionRuleNote { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px; padding: 8px 10px; border: 1px solid var(--bd); background: rgba(255, 255, 255, .015); }
	.tensionRuleNote b { color: var(--text); font-size: 10.5px; white-space: nowrap; }
	.tensionRuleNote span { color: var(--dim); font-size: 9.5px; line-height: 1.45; }
	.tensionCards { display: grid; gap: 9px; }
	.tensionCard { border: 1px solid var(--bd); background: rgba(148, 163, 184, .018); }
	.tensionCard > header { display: grid; grid-template-columns: 72px minmax(0, 1fr) auto; gap: 8px; align-items: center; padding: 8px 10px; border-bottom: 1px solid var(--bd); }
	.kindBadge { padding: 2px 4px; border: 1px solid rgba(245, 158, 11, .38); color: var(--amber); font-family: var(--mono); font-size: 8px; text-align: center; }
	.tensionCard h3 { margin: 0; color: var(--text); font-size: 12px; }
	.tensionCard time { color: var(--dimmer); font-family: var(--mono); font-size: 8.5px; }
	.mechanism { margin: 0; padding: 8px 10px; color: var(--dim); font-size: 10px; line-height: 1.45; }
	.sideGrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; padding: 0 10px 9px; }
	.sideCard { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 3px 7px; padding: 7px 8px; border: 1px solid var(--bd); }
	.sideEngine { grid-row: span 2; align-self: start; color: var(--amber); font-family: var(--mono); font-size: 8px; }
	.sideCard b { overflow: hidden; color: var(--text); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
	.sideCard span:not(.sideEngine) { color: var(--dim); font-size: 9px; }
	.sideEvidence { grid-column: 1 / -1; min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 5px; overflow: hidden; color: var(--dimmer); font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
	.sideEvidence b { color: var(--dim); font-family: var(--mono); font-size: 7.5px; }
	.nextQuestion, .falsifierList, .gapList { display: grid; grid-template-columns: 126px minmax(0, 1fr); gap: 7px; padding: 7px 10px; border-top: 1px solid var(--bd); }
	.nextQuestion b, .falsifierList > b, .gapList > b { color: var(--amber); font-family: var(--mono); font-size: 8px; letter-spacing: .05em; }
	.nextQuestion span, .falsifierList span, .gapList span { color: var(--dim); font-size: 9.5px; line-height: 1.4; }
	.falsifierList span + span, .gapList span + span { grid-column: 2; }
	.dialogEmpty { min-height: 100px; display: flex; flex-direction: column; justify-content: center; gap: 4px; color: var(--dim); font-size: 10px; text-align: center; }
	.dialogEmpty b { color: var(--text); font-size: 11px; }
	.evaluationGrid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); margin-top: 10px; border: 1px solid var(--bd); }
	.evaluationGrid div { min-width: 0; padding: 6px 7px; border-right: 1px solid var(--bd); border-top: 2px solid var(--good); }
	.evaluationGrid div:last-child { border-right: 0; }
	.evaluationGrid div[data-status='active'] { border-top-color: var(--amber); }
	.evaluationGrid div[data-status='blocked'] { border-top-color: var(--dimmer); }
	.evaluationGrid b, .evaluationGrid span { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.evaluationGrid b { color: var(--text); font-family: var(--mono); font-size: 7.5px; }
	.evaluationGrid span { margin-top: 2px; color: var(--dim); font-size: 8.5px; }
	@media (max-width: 720px) {
		.scrimWrap { padding: 8px; }
		.lensDialog { width: 100%; max-height: 94vh; }
		.lensDialogTarget { display: none; }
		.tensionRuleNote { align-items: flex-start; flex-direction: column; gap: 3px; }
		.sideGrid, .evaluationGrid { grid-template-columns: 1fr; }
		.evaluationGrid div { border-right: 0; border-bottom: 1px solid var(--bd); }
		.tensionCard > header { grid-template-columns: 62px minmax(0, 1fr); }
		.tensionCard time { grid-column: 2; }
	}
</style>
