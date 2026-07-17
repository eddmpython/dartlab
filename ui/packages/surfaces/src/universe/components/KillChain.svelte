<script lang="ts">
	import type { UniverseWorkflowCompilation, UniverseWorkflowId, UniverseWorkflowRecipe } from '@dartlab/ui-contracts';
	import ClaimLedger from './ClaimLedger.svelte';

	interface Props {
		workflows: readonly UniverseWorkflowRecipe[];
		selectedWorkflowId: UniverseWorkflowId;
		compilation: UniverseWorkflowCompilation | null;
		loading?: boolean;
		error?: string | null;
		onSelectWorkflow: (workflowId: UniverseWorkflowId) => void;
		onCompile: () => void;
	}

	let { workflows, selectedWorkflowId, compilation, loading = false, error = null, onSelectWorkflow, onCompile }: Props = $props();
</script>

<section class="killChain" aria-label="Thesis Kill-Chain">
	<header><div><span>SCENE 03</span><h2>Thesis Kill-Chain</h2><p>근거를 모아 결론을 강화하는 대신, 반증이 열려 있는지를 먼저 확인합니다.</p></div><b class:ready={compilation?.conclusionReady}>{compilation?.conclusionReady ? 'CONCLUSION READY' : 'CONCLUSION OPEN'}</b></header>
	<nav aria-label="검증 워크플로">{#each workflows as workflow (workflow.workflowId)}<button class:active={workflow.workflowId === selectedWorkflowId} onclick={() => onSelectWorkflow(workflow.workflowId)}><span>{workflow.version}</span><strong>{workflow.label}</strong></button>{/each}</nav>
	{#if compilation}
		<div class="beats" aria-label="Flight Plan">{#each compilation.flightPlan.beats as beat, index (beat.beatId)}<div><b>{String(index + 1).padStart(2, '0')}</b><span>{beat.intent}</span>{#if index < compilation.flightPlan.beats.length - 1}<i></i>{/if}</div>{/each}</div>
		<div class="body"><ClaimLedger claims={compilation.claims} /><aside><span>FLIGHT RECEIPT</span><code>{compilation.flightReceipt.outputHash}</code><span>COMPILE HASH</span><code>{compilation.compileHash}</code><p>필수 근거가 하나라도 없으면 gap lane에 남고 결론은 닫히지 않습니다. 시나리오는 사실 lane으로 승격되지 않습니다.</p></aside></div>
	{:else}
		<div class="empty"><h3>선택한 산업을 seed로 검증 비행을 컴파일합니다.</h3><p>recipe별 전용 화면은 만들지 않습니다. 동일한 flight, claim, receipt 계약으로 세 워크플로를 실행합니다.</p>{#if error}<b role="alert">{error}</b>{/if}<button onclick={onCompile} disabled={loading}>{loading ? '컴파일 중' : error ? '워크플로 다시 컴파일' : '워크플로 컴파일'}</button></div>
	{/if}
	<footer><strong>교차시장 게이트</strong><span>고정 질문 20개 compiler 준비. exact corpCode, CIK, sourceRef, dataAsOf, unit 없이는 paired result를 열지 않습니다.</span></footer>
</section>

<style>
	.killChain { min-height: 610px; }
	.killChain > header { display: flex; justify-content: space-between; gap: 20px; align-items: start; margin: 0 2px 16px; }
	header span, aside span { color: #53657d; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .1em; }
	header h2 { margin: 6px 0 0; color: #e2e9f2; font-size: 18px; }
	header p { margin: 6px 0 0; color: #708198; font-size: 10px; }
	header > b { padding: 6px 8px; border: 1px solid rgba(245,184,75,.28); border-radius: 999px; color: #dba94f; font: 600 8px/1 ui-monospace, monospace; }
	header > b.ready { border-color: rgba(61,196,132,.3); color: #63c493; }
	nav { display: grid; grid-template-columns: repeat(3, 1fr); gap: 7px; margin-bottom: 15px; }
	nav button { display: flex; justify-content: space-between; align-items: center; border: 1px solid #1d2a3d; border-radius: 9px; padding: 10px; color: #8293a9; background: #0d141f; cursor: pointer; }
	nav button.active { border-color: #416187; color: #d1dbe7; background: #111c2a; }
	nav span { font: 500 7px/1 ui-monospace, monospace; }
	nav strong { font-size: 10px; }
	.beats { display: flex; align-items: center; justify-content: center; gap: 0; padding: 13px; border: 1px solid #172333; border-radius: 10px; background: #090f18; }
	.beats div { display: flex; align-items: center; }
	.beats b { display: grid; place-items: center; width: 25px; height: 25px; border: 1px solid #2b3b51; border-radius: 50%; color: #75aef1; font: 600 7px/1 ui-monospace, monospace; }
	.beats span { margin-left: 5px; color: #8a9aaf; font-size: 8px; }
	.beats i { width: clamp(12px, 4vw, 55px); margin: 0 7px; border-top: 1px solid #26364b; }
	.body { display: grid; grid-template-columns: minmax(0, 1fr) 230px; gap: 12px; margin-top: 14px; }
	aside { padding: 12px; border: 1px solid #182434; border-radius: 9px; background: #0b111a; }
	aside span { display: block; margin: 3px 0 6px; }
	aside code { display: block; margin-bottom: 15px; color: #5d7089; font-size: 7px; overflow-wrap: anywhere; }
	aside p { color: #718198; font-size: 9px; line-height: 1.55; }
	.empty { max-width: 480px; margin: 110px auto; text-align: center; }
	.empty h3 { color: #dfe7f1; font-size: 18px; }
	.empty p { color: #708198; font-size: 11px; line-height: 1.6; }
	.empty > b { display: block; margin: 10px 0; color: #e58a8a; font-size: 9px; }
	.empty button { margin-top: 12px; border: 1px solid #2a3a51; border-radius: 9px; padding: 10px 15px; color: #b9c7d9; background: #111a27; cursor: pointer; }
	footer { display: flex; gap: 9px; margin-top: 15px; padding: 10px; border: 1px dashed #25344a; border-radius: 9px; color: #6b7c92; font-size: 8px; }
	footer strong { flex: 0 0 auto; color: #88a0bd; }
	@media (max-width: 720px) { nav { grid-template-columns: 1fr; } .beats { overflow-x: auto; justify-content: start; } .body { grid-template-columns: 1fr; } }
</style>
