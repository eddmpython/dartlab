<script lang="ts">
	import type { LensEngine, LensProduct, LensProductBundle } from '@dartlab/ui-contracts';
	import type { Lang } from '../lib/types';
	import Panel from '../ui/Panel.svelte';

	interface Props {
		bundle: LensProductBundle | null;
		state: 'loading' | 'ready' | 'empty';
		lang: Lang;
	}
	let { bundle, state, lang }: Props = $props();
	const order: LensEngine[] = ['analysis', 'credit', 'industry', 'quant', 'macro'];
	const names: Record<LensEngine, { kr: string; en: string }> = {
		analysis: { kr: '재무 인과', en: 'ANALYSIS' },
		credit: { kr: '신용 하방', en: 'CREDIT' },
		industry: { kr: '산업 위치', en: 'INDUSTRY' },
		quant: { kr: '기대 괴리', en: 'QUANT' },
		macro: { kr: '거시 전파', en: 'MACRO' }
	};
	const statusLabel = (status: LensProduct['status']): string => {
		if (lang === 'en') return status;
		return ({ usable: '사용 가능', partial: '부분 근거', blocked: '판단 차단', notApplicable: '해당 없음' })[status];
	};
	const timeLabel = (product: LensProduct): string => {
		const data = product.time.dataAsOf;
		if (typeof data === 'string') return data;
		if (data) {
			for (const key of ['sourceDataAsOf', 'date', 'dataAsOf', 'retrievedAt']) {
				const value = data[key];
				if (typeof value === 'string' && value) return value;
			}
		}
		return product.time.period || product.time.asOf || (lang === 'en' ? 'unknown' : '시점 미상');
	};
	const rowRecord = (row: unknown): Record<string, unknown> => row && typeof row === 'object' ? row as Record<string, unknown> : {};
	const textValue = (value: unknown): string => {
		if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
		return '';
	};
	const rowLabel = (row: unknown): string => {
		const value = rowRecord(row);
		return textValue(value.label) || textValue(value.id) || textValue(value.kind) || (lang === 'en' ? 'item' : '항목');
	};
	const rowDetail = (row: unknown): string => {
		const value = rowRecord(row);
		for (const key of ['detail', 'reason', 'condition', 'summary', 'direction', 'status', 'value']) {
			const text = textValue(value[key]);
			if (text) return text;
		}
		return '';
	};
	const rowSource = (row: unknown): string => textValue(rowRecord(row).sourceRef);
	const products = $derived(bundle?.products ?? {});
</script>

<Panel {lang} className="eAnalysis" prov="derived"
	title={{ kr: '다섯 분석 렌즈', en: 'FIVE ANALYSIS LENSES' }}
	sub={{ kr: '독립 판단 · 통합점수 없음', en: 'independent views · no composite score' }} flush>
	{#if state === 'loading'}
		<div class="lensMessage">{lang === 'en' ? 'Loading engine products …' : '엔진 제품 결과 불러오는 중 …'}</div>
	{:else if state === 'empty' || !bundle}
		<div class="lensMessage">
			<b>{lang === 'en' ? 'Product artifact unavailable' : '대표 렌즈 제품 미발행'}</b>
			<span>{lang === 'en' ? 'No browser-side score was substituted.' : '브라우저에서 임의 점수나 판단으로 대체하지 않았습니다.'}</span>
		</div>
	{:else}
		<div class="lensGrid">
			{#each order as engine (engine)}
				{@const product = products[engine]}
				{#if product}
					<div class="lensRow" data-status={product.status}>
						<div class="lensIdentity">
							<b>{lang === 'en' ? names[engine].en : names[engine].kr}</b>
							<span class="lensState">{statusLabel(product.status)}</span>
						</div>
						<div class="lensJudgement" title={product.conclusion.summary}>
							<strong>{product.conclusion.label}</strong>
							<span>{product.conclusion.summary}</span>
						</div>
						<div class="lensEvidence">
							<span title={product.confidence.method}>{lang === 'en' ? 'evidence state' : '근거 상태'} {product.confidence.level}</span>
							<span>E {product.evidence.length}</span>
							<span>G {product.gaps.length}</span>
							<time>{timeLabel(product)}</time>
						</div>
						<details class="lensDetail">
							<summary>{lang === 'en' ? 'inspect evidence' : '근거 세부 보기'}</summary>
							<div class="lensDetailGroups">
								{#if product.drivers.length}
									<section><b>{lang === 'en' ? 'DRIVERS' : '주요 동인'}</b>{#each product.drivers as row}<span><strong>{rowLabel(row)}</strong><i>{rowDetail(row)}</i>{#if rowSource(row)}<code>{rowSource(row)}</code>{/if}</span>{/each}</section>
								{/if}
								{#if product.claims?.length}
									<section><b>{lang === 'en' ? 'TYPED CLAIMS' : '비교 주장'}</b>{#each product.claims as row}<span><strong>{rowLabel(row)}</strong><i>{row.direction} · {row.period ?? row.horizon}</i><code>{row.sourceRef}</code></span>{/each}</section>
								{/if}
								{#if product.evidence.length}
									<section><b>{lang === 'en' ? 'EVIDENCE' : '근거'}</b>{#each product.evidence as row}<span><strong>{rowLabel(row)}</strong><i>{rowDetail(row)}</i><code>{row.sourceRef}</code></span>{/each}</section>
								{/if}
								{#if product.gaps.length}
									<section><b>{lang === 'en' ? 'LIMITS' : '결손과 한계'}</b>{#each product.gaps as row}<span><strong>{rowLabel(row)}</strong><i>{row.reason}</i>{#if row.sourceRef}<code>{row.sourceRef}</code>{/if}</span>{/each}</section>
								{/if}
								{#if product.falsifiers.length}
									<section><b>{lang === 'en' ? 'FALSIFIERS' : '반증 조건'}</b>{#each product.falsifiers as row}<span><strong>{rowLabel(row)}</strong><i>{rowDetail(row)}</i>{#if rowSource(row)}<code>{rowSource(row)}</code>{/if}</span>{/each}</section>
								{/if}
							</div>
						</details>
					</div>
				{:else}
					<div class="lensRow missing">
						<div class="lensIdentity"><b>{lang === 'en' ? names[engine].en : names[engine].kr}</b><span class="lensState">missing</span></div>
						<div class="lensJudgement"><strong>{lang === 'en' ? 'No product' : '대표 제품 없음'}</strong></div>
					</div>
				{/if}
			{/each}
		</div>
		{#if bundle.gaps.length}
			<div class="bundleGap">{lang === 'en' ? 'Collection gaps' : '수집 결손'} {bundle.gaps.length}</div>
		{/if}
	{/if}
</Panel>

<style>
	.lensMessage { min-height: 74px; display: flex; flex-direction: column; justify-content: center; gap: 4px; padding: 10px 12px; color: var(--dim); font-size: 10px; }
	.lensMessage b { color: var(--text); font-family: var(--cond); font-size: 11px; }
	.lensGrid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); }
	.lensRow { grid-column: span 2; min-width: 0; padding: 7px 8px 6px; border-right: 1px solid var(--bd); border-bottom: 1px solid var(--bd); border-top: 2px solid var(--good); background: rgba(148, 163, 184, 0.025); }
	.lensRow:nth-child(n + 4) { grid-column: span 3; }
	.lensRow:nth-child(3), .lensRow:nth-child(5) { border-right: 0; }
	.lensRow[data-status='partial'] { border-top-color: var(--warn); }
	.lensRow[data-status='blocked'], .lensRow.missing { border-top-color: var(--dn); }
	.lensRow[data-status='notApplicable'] { border-top-color: var(--dim); }
	.lensIdentity { display: flex; align-items: center; justify-content: space-between; gap: 4px; margin-bottom: 5px; }
	.lensIdentity b { font-family: var(--cond); font-size: 10px; letter-spacing: .35px; color: var(--text); white-space: nowrap; }
	.lensState { font-family: var(--mono); font-size: 8.5px; color: var(--dimmer); white-space: nowrap; }
	.lensJudgement { min-height: 45px; min-width: 0; }
	.lensJudgement strong, .lensJudgement span { display: block; overflow: hidden; text-overflow: ellipsis; }
	.lensJudgement strong { color: var(--text); font-size: 10px; line-height: 1.25; white-space: nowrap; }
	.lensJudgement span { display: -webkit-box; margin-top: 2px; color: var(--dim); font-size: 9px; line-height: 1.4; white-space: normal; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
	.lensEvidence { display: grid; grid-template-columns: minmax(72px, 1fr) auto auto auto; align-items: center; gap: 4px; margin-top: 5px; font-family: var(--mono); font-size: 8.5px; color: var(--dimmer); }
	.lensEvidence time { text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.lensDetail { margin-top: 6px; border-top: 1px solid var(--bd); }
	.lensDetail summary { padding-top: 5px; color: var(--amber); font-family: var(--mono); font-size: 8.5px; cursor: pointer; }
	.lensDetailGroups { display: grid; gap: 6px; margin-top: 6px; }
	.lensDetailGroups section { min-width: 0; display: grid; gap: 4px; }
	.lensDetailGroups section > b { color: var(--dimmer); font-family: var(--mono); font-size: 8px; letter-spacing: .06em; }
	.lensDetailGroups section > span { min-width: 0; display: grid; grid-template-columns: minmax(90px, .7fr) minmax(120px, 1.3fr); gap: 2px 6px; padding: 4px 5px; border: 1px solid var(--bd); }
	.lensDetailGroups strong, .lensDetailGroups i, .lensDetailGroups code { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.lensDetailGroups strong { color: var(--text); font-size: 9px; }
	.lensDetailGroups i { color: var(--dim); font-size: 8.5px; font-style: normal; }
	.lensDetailGroups code { grid-column: 1 / -1; color: var(--dimmer); font-family: var(--mono); font-size: 7.5px; }
	.bundleGap { border-top: 1px solid var(--bd); padding: 4px 8px; color: var(--warn); font-family: var(--mono); font-size: 8.5px; }
	@media (max-width: 980px) { .lensGrid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .lensRow, .lensRow:nth-child(n + 4) { grid-column: span 1; } .lensRow:nth-child(odd) { border-right: 1px solid var(--bd); } .lensRow:nth-child(even) { border-right: 0; } }
</style>
