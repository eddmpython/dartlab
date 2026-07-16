<script lang="ts">
	import type { UniverseChangeKind, UniverseChangeMark, UniverseChangeSet } from '@dartlab/ui-contracts';
	import EvidenceRibbon from './EvidenceRibbon.svelte';

	interface Props {
		data: UniverseChangeSet | null;
		loading?: boolean;
		error?: string | null;
		onLoad: () => void;
		onSelect: (mark: UniverseChangeMark) => void;
	}

	let { data, loading = false, error = null, onLoad, onSelect }: Props = $props();
	let mode = $state<'orbit' | 'table'>('orbit');
	const GLYPHS: Readonly<Record<UniverseChangeKind, string>> = {
		created: '+', corrected: '△', retracted: '×', newlyKnown: '●', stale: '○'
	};
	const LABELS: Readonly<Record<UniverseChangeKind, string>> = {
		created: '생성', corrected: '정정', retracted: '철회', newlyKnown: '새로 인지', stale: '오래됨'
	};
	let visibleAggregates = $derived(data?.aggregates.filter((item) => item.changeCount > 0).slice(0, 12) ?? []);

	function marksFor(industryId: string): readonly UniverseChangeMark[] {
		return data?.marks.filter((mark) => mark.industryId === industryId).slice(0, 8) ?? [];
	}

	function percent(value: number): string {
		return `${Math.round(value * 100)}%`;
	}
</script>

<section class="changeShell" aria-label="변화 우주">
	<header>
		<div><span>SCENE 02</span><h2>변화 우주</h2></div>
		<div class="controls">
			<button class:active={mode === 'orbit'} onclick={() => (mode = 'orbit')}>궤도</button>
			<button class:active={mode === 'table'} onclick={() => (mode = 'table')}>표</button>
		</div>
	</header>
	{#if !data}
		<div class="loadState">
			<span>LAZY SOURCE</span><h3>타임라인과 변화 신호는 요청 전까지 읽지 않습니다.</h3>
			<p>현재 원천에는 exact historical assertion 묶음이 없습니다. 로드 후에도 사실 변화가 아닌 현재 신호 데모로 표시됩니다.</p>
			<button onclick={onLoad} disabled={loading}>{loading ? '불러오는 중' : '변화 원천 불러오기'}</button>
			{#if error}<b role="alert">{error}</b>{/if}
		</div>
	{:else}
		<div class="modeBanner" class:exact={data.mode === 'exactReplay'}>
			<strong>{data.mode === 'exactReplay' ? 'EXACT HISTORICAL REPLAY' : 'CURRENT SIGNAL DEMO'}</strong>
			<span>{data.fromPeriod ?? '이력 없음'} → {data.toPeriod}</span>
			<p>{data.mode === 'exactReplay' ? '두 불변 snapshot 사이의 assertion 차이입니다.' : '재무 급변 신호를 배치한 데모입니다. 기업 관계 또는 공시 문구의 역사적 변화를 주장하지 않습니다.'}</p>
		</div>
		<div class="glyphLegend" aria-label="변화 표식 범례">
			{#each Object.entries(GLYPHS) as [kind, glyph]}<span class={kind}><b>{glyph}</b>{LABELS[kind as UniverseChangeKind]}</span>{/each}
		</div>
		{#if mode === 'orbit'}
			<div class="orbitGrid">
				{#each visibleAggregates as aggregate (aggregate.industryId)}
					<article>
						<div class="industryHead"><div><span>{aggregate.industryId}</span><h3>{aggregate.industryLabel}</h3></div><b>{aggregate.changeCount}</b></div>
						<div class="coverage"><i style:width={`${Math.round(aggregate.coverage * 100)}%`}></i></div>
						<p>coverage {percent(aggregate.coverage)} · unknown {aggregate.unknownCount} · omitted {aggregate.omittedCount}</p>
						<div class="marks">
							{#each marksFor(aggregate.industryId) as mark (mark.changeId)}
								<button class={mark.kind} onclick={() => onSelect(mark)} title={`${mark.entityLabel}: ${mark.summary}`} aria-label={`${mark.entityLabel}, ${LABELS[mark.kind]}, ${mark.summary}`}>
									<b>{GLYPHS[mark.kind]}</b><span>{mark.entityLabel}</span>
								</button>
							{/each}
						</div>
					</article>
				{/each}
			</div>
		{:else}
			<div class="changeTable"><table>
				<thead><tr><th>종류</th><th>기업과 신호</th><th>산업</th><th>전후 근거</th></tr></thead>
				<tbody>{#each data.marks as mark (mark.changeId)}<tr>
					<td><button class="kindButton" onclick={() => onSelect(mark)}><b>{GLYPHS[mark.kind]}</b>{LABELS[mark.kind]}</button></td>
					<td><strong>{mark.entityLabel}</strong><span>{mark.summary}</span></td>
					<td><code>{mark.industryId}</code></td>
					<td><EvidenceRibbon before={mark.evidence.before} after={mark.evidence.after} gaps={mark.evidence.gaps} /></td>
				</tr>{/each}</tbody>
			</table></div>
		{/if}
		<footer><span>DIFF HASH</span><code>{data.diffHash}</code><b>{data.gaps.length} global gap</b></footer>
	{/if}
</section>

<style>
	.changeShell { min-height: 610px; }
	header { display: flex; align-items: end; justify-content: space-between; margin: 0 2px 13px; }
	header > div > span, .loadState > span { color: #53657d; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .12em; }
	header h2 { margin: 6px 0 0; font-size: 15px; font-weight: 600; }
	.controls { display: flex; padding: 3px; border: 1px solid #202c3f; border-radius: 8px; }
	.controls button { border: 0; border-radius: 5px; padding: 6px 10px; color: #66778e; background: transparent; cursor: pointer; }
	.controls button.active { color: #dce5f2; background: #1a2637; }
	.loadState { max-width: 510px; margin: 110px auto; text-align: center; }
	.loadState h3 { margin: 14px 0 8px; color: #dfe7f1; font-size: 20px; }
	.loadState p { color: #708198; font-size: 12px; line-height: 1.65; }
	.loadState button { margin-top: 15px; border: 1px solid #2a3a51; border-radius: 9px; padding: 10px 15px; color: #b9c7d9; background: #111a27; cursor: pointer; }
	.loadState b { display: block; margin-top: 10px; color: #e47777; font-size: 10px; }
	.modeBanner { display: grid; grid-template-columns: auto auto 1fr; gap: 12px; align-items: center; padding: 11px 13px; border: 1px dashed rgba(245,184,75,.3); border-radius: 10px; background: rgba(245,184,75,.05); }
	.modeBanner.exact { border-style: solid; border-color: rgba(61,196,132,.3); background: rgba(61,196,132,.05); }
	.modeBanner strong { color: #e4b661; font: 700 9px/1 ui-monospace, monospace; }
	.modeBanner span { color: #8c9bb0; font: 500 9px/1 ui-monospace, monospace; }
	.modeBanner p { margin: 0; color: #7a8aa0; font-size: 10px; line-height: 1.4; text-align: right; }
	.glyphLegend { display: flex; flex-wrap: wrap; gap: 14px; margin: 13px 2px; }
	.glyphLegend span { display: flex; align-items: center; gap: 5px; color: #708198; font-size: 9px; }
	.glyphLegend b { color: #aebbd0; font: 700 12px/1 ui-monospace, monospace; }
	.glyphLegend .retracted b { color: #e46b6b; }
	.glyphLegend .newlyKnown b { color: #64a8ff; }
	.glyphLegend .stale b { color: #687a91; }
	.orbitGrid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }
	.orbitGrid article { min-height: 160px; padding: 12px; border: 1px solid #182536; border-radius: 12px; background: radial-gradient(circle at 90% 10%, rgba(100,168,255,.08), transparent 34%), #0b111a; }
	.industryHead { display: flex; justify-content: space-between; align-items: center; }
	.industryHead span { color: #53657d; font: 600 7px/1 ui-monospace, monospace; text-transform: uppercase; }
	.industryHead h3 { margin: 4px 0 0; color: #cdd7e4; font-size: 12px; }
	.industryHead > b { display: grid; place-items: center; width: 27px; height: 27px; border: 1px solid #2a3a51; border-radius: 50%; color: #73adf4; font: 600 10px/1 ui-monospace, monospace; }
	.coverage { height: 2px; margin: 10px 0 5px; background: #162131; }
	.coverage i { display: block; height: 100%; background: #4e7fb8; }
	article > p { margin: 0 0 10px; color: #53657d; font: 500 7px/1 ui-monospace, monospace; }
	.marks { display: flex; flex-wrap: wrap; gap: 5px; }
	.marks button { display: flex; align-items: center; gap: 4px; max-width: 100%; border: 1px solid #223149; border-radius: 999px; padding: 4px 7px; color: #91a1b7; background: #111926; cursor: pointer; }
	.marks button:hover, .marks button:focus-visible { border-color: #5075a3; outline: none; }
	.marks button b { color: #65a8fa; }
	.marks button span { overflow: hidden; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
	.changeTable { overflow: auto; border: 1px solid #172333; border-radius: 10px; }
	table { width: 100%; border-collapse: collapse; font-size: 10px; }
	th { padding: 9px 10px; color: #5e6e84; background: #0c121c; text-align: left; font: 600 8px/1 ui-monospace, monospace; }
	td { padding: 9px 10px; border-top: 1px solid #172333; color: #8f9fb4; vertical-align: middle; }
	td > strong, td > span { display: block; }
	td > span { max-width: 260px; margin-top: 3px; color: #617188; }
	.kindButton { display: flex; gap: 6px; align-items: center; border: 0; color: #9aabc0; background: none; cursor: pointer; }
	.kindButton b { color: #65a8fa; }
	td code { color: #71829a; font-size: 8px; }
	footer { display: flex; align-items: center; gap: 9px; margin-top: 11px; color: #52637a; }
	footer span { font: 600 7px/1 ui-monospace, monospace; }
	footer code { max-width: 50%; overflow: hidden; font-size: 7px; text-overflow: ellipsis; }
	footer b { margin-left: auto; color: #b0874b; font-size: 8px; }
	@media (max-width: 900px) { .orbitGrid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .modeBanner { grid-template-columns: 1fr auto; } .modeBanner p { grid-column: 1 / -1; text-align: left; } }
	@media (max-width: 560px) { .orbitGrid { grid-template-columns: 1fr; } .modeBanner { grid-template-columns: 1fr; } .changeTable { max-height: 560px; } }
</style>
