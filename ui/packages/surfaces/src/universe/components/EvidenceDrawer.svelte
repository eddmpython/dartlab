<script lang="ts">
	import type { UniverseChangeMark, UniverseEvidenceResolution } from '@dartlab/ui-contracts';
	import AssertionTimeline from './AssertionTimeline.svelte';
	import EvidenceRibbon from './EvidenceRibbon.svelte';

	interface Props {
		change: UniverseChangeMark;
		resolution?: UniverseEvidenceResolution | null;
		loading?: boolean;
		onResolve: () => void;
		onClose: () => void;
	}

	let { change, resolution = null, loading = false, onResolve, onClose }: Props = $props();
	let pointer = $derived(resolution?.pointer ?? null);
	let gaps = $derived(resolution?.gaps ?? change.evidence.gaps);

	function deepLink(sourceRef: string): string | null {
		return /^https?:\/\//.test(sourceRef) ? sourceRef : null;
	}
</script>

<div class="drawer" role="dialog" aria-modal="false" aria-labelledby="evidence-title">
	<header><span>EVIDENCE DRAWER</span><button aria-label="근거 서랍 닫기" onclick={onClose}>×</button></header>
	<section class="plain">
		<span>RELATION</span><h2 id="evidence-title">{change.entityLabel}의 {change.metricId} 신호</h2><p>{change.summary}</p>
	</section>
	<section class="classRow">
		<div><span>STATUS</span><strong>{resolution?.receipt.status ?? 'missing'}</strong></div>
		<div><span>EVIDENCE CLASS</span><strong>{pointer ? pointer.locatorKind : 'candidate only'}</strong></div>
	</section>
	<section class="times">
		<div><span>VALID AT</span><strong>{resolution?.receipt.validAt ?? change.eventAt}</strong></div>
		<div><span>SOURCE PUBLISHED</span><strong>{pointer?.sourcePublishedAt ?? '결손'}</strong></div>
		<div><span>AVAILABLE AT</span><strong>{pointer?.availableAt ?? '결손'}</strong></div>
		<div><span>KNOWLEDGE AS OF</span><strong>{resolution?.receipt.knownAt ?? change.knownAt}</strong></div>
	</section>
	<AssertionTimeline {change} />
	<section class="source">
		<h3>FILING AND SECTION</h3>
		{#if pointer}
			<strong>{pointer.documentId}</strong><span>{pointer.sectionPath} · section {pointer.sectionOrder}</span>
			{#if deepLink(pointer.sourceRef)}<a href={deepLink(pointer.sourceRef) ?? ''} target="_blank" rel="noreferrer">원문 열기</a>{:else}<code>{pointer.sourceRef}</code>{/if}
		{:else}
			<p>검색 후보는 exact filing locator가 아닙니다. 원문 문단 또는 표 행이 결속되어야 supported로 바뀝니다.</p>
		{/if}
	</section>
	<section class="locator">
		<h3>EXACT LOCATOR</h3>
		{#if pointer?.textLocator}<code>chars {pointer.textLocator.charStart}:{pointer.textLocator.charEnd} · {pointer.textLocator.snippetHash}</code>
		{:else if pointer?.tableLocator}<code>row {pointer.tableLocator.rowIndex} · {pointer.tableLocator.rowHash}</code>
		{:else}<p>정확 텍스트 또는 표 locator가 없습니다.</p>{/if}
	</section>
	<section class="limits">
		<h3>METHOD AND LIMITATION</h3>
		<p>전역 공시 BM25 검색은 후보 문서를 찾는 데만 씁니다. 후보 점수는 사실 근거가 아니며 자동 승격되지 않습니다.</p>
	</section>
	<EvidenceRibbon before={change.evidence.before} after={change.evidence.after} gaps={change.evidence.gaps} />
	{#if resolution?.candidates.length}
		<section class="candidates"><h3>SEARCH CANDIDATES</h3><ol>{#each resolution.candidates as candidate (candidate.documentId)}<li><strong>{candidate.title || candidate.documentId}</strong><span>{candidate.entityId} · {candidate.publishedAt} · score {candidate.score.toFixed(2)}</span><p>{candidate.snippet}</p></li>{/each}</ol></section>
	{/if}
	{#if gaps.length}<section class="gaps"><h3>UNRESOLVED</h3>{#each gaps as gap (gap.gapId)}<p><b>{gap.reasonCode}</b><span>{gap.requestedField}</span></p>{/each}</section>{/if}
	<button class="resolve" onclick={onResolve} disabled={loading}>{loading ? '검색 중' : '공시 원문 후보 검색'}</button>
</div>

<style>
	.drawer { height: 100%; padding: 20px; overflow: auto; background: #0a0f17; }
	header { display: flex; justify-content: space-between; align-items: center; }
	header span, section > span, section h3, .classRow span, .times span { color: #53657d; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .1em; }
	header button { border: 0; color: #65758c; background: none; font-size: 20px; cursor: pointer; }
	.plain { margin: 30px 0 18px; }
	.plain h2 { margin: 8px 0 6px; color: #eef3f8; font-size: 21px; }
	.plain p, .source p, .locator p, .limits p { margin: 0; color: #718198; font-size: 10px; line-height: 1.55; }
	.classRow, .times { display: grid; gap: 5px; margin-bottom: 18px; }
	.classRow { grid-template-columns: 1fr 1fr; }
	.times { grid-template-columns: 1fr 1fr; }
	.classRow div, .times div { padding: 9px; border: 1px solid #182434; border-radius: 8px; background: #0d141f; }
	.classRow strong, .times strong { display: block; margin-top: 5px; color: #b9c5d5; font: 600 9px/1.2 ui-monospace, monospace; overflow-wrap: anywhere; }
	section { margin-bottom: 19px; }
	section h3 { margin: 0 0 8px; }
	.source strong, .source span { display: block; color: #aab8ca; font-size: 10px; }
	.source span { margin-top: 4px; color: #697a91; }
	.source a, .source code { display: block; margin-top: 7px; color: #68a8f5; font-size: 9px; overflow-wrap: anywhere; }
	.locator code { display: block; padding: 8px; border-radius: 6px; color: #8ca0b9; background: #0d141f; font-size: 8px; overflow-wrap: anywhere; }
	.candidates ol { margin: 0; padding: 0; list-style: none; }
	.candidates li { padding: 9px 0; border-top: 1px solid #182333; }
	.candidates strong, .candidates span { display: block; color: #acb9cb; font-size: 9px; }
	.candidates span { margin-top: 3px; color: #617188; }
	.candidates p { max-height: 3.1em; margin: 5px 0 0; overflow: hidden; color: #77889f; font-size: 9px; line-height: 1.55; }
	.gaps p { display: flex; justify-content: space-between; gap: 8px; margin: 5px 0; padding: 7px; border-radius: 6px; background: rgba(245,184,75,.06); }
	.gaps b { color: #d7a44c; font-size: 8px; }
	.gaps span { color: #75869c; font-size: 8px; text-align: right; }
	.resolve { width: 100%; margin-top: 19px; border: 1px solid #2a3a51; border-radius: 9px; padding: 10px; color: #b9c7d9; background: #111a27; cursor: pointer; }
	.resolve:disabled { opacity: .55; cursor: wait; }
</style>
