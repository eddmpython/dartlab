<script lang="ts">
	import { onMount } from 'svelte';
	import {
		applyRuntimeSetup,
		getAgentRuntimeStatus,
		planRuntimeSetup,
		selectDefaultRuntime,
		type AgentRuntimeInfo,
		type RuntimeSetupPlan,
		type RuntimeSetupResult
	} from '$lib/runtime/agentRuntimeApi';

	let { onChange = () => undefined }: { onChange?: () => void | Promise<void> } = $props();

	let runtimes = $state<AgentRuntimeInfo[]>([]);
	let loading = $state(true);
	let busy = $state<string | null>(null);
	let error = $state<string | null>(null);
	let plan = $state<RuntimeSetupPlan | null>(null);
	let setupResult = $state<RuntimeSetupResult | null>(null);
	let selected = $state('');

	onMount(() => void load(false));

	async function load(refresh: boolean): Promise<void> {
		loading = true;
		error = null;
		try {
			const status = await getAgentRuntimeStatus(refresh);
			runtimes = status.runtimes;
			selected = status.defaultRuntimeId ?? '';
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			loading = false;
		}
	}

	async function selectRuntime(runtimeId: string): Promise<void> {
		busy = `select:${runtimeId}`;
		error = null;
		try {
			const result = await selectDefaultRuntime(runtimeId);
			selected = result.defaultRuntimeId;
			await onChange();
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			busy = null;
		}
	}

	async function makeSetupPlan(runtimeId: string): Promise<void> {
		busy = `setup:${runtimeId}`;
		error = null;
		setupResult = null;
		try {
			plan = await planRuntimeSetup(runtimeId);
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			busy = null;
		}
	}

	async function approveSetup(): Promise<void> {
		if (!plan) return;
		busy = `setup:${plan.runtimeId}`;
		error = null;
		try {
			setupResult = await applyRuntimeSetup(plan.runtimeId);
			plan = null;
			await load(true);
			if (setupResult.investmentReady) await onChange();
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			busy = null;
		}
	}

</script>

<section class="runtimeCenter" data-qa="runtime-center">
	<header>
		<div>
			<h2>에이전트 런타임 센터</h2>
			<p>한 번 승인하면 설치, 공식 로그인, DartLab 연결과 기본 선택을 같은 흐름에서 끝냅니다.</p>
		</div>
		<button class="secondary" data-qa="runtime-refresh" onclick={() => load(true)} disabled={loading}>다시 확인</button>
	</header>

	{#if error}<div class="error" data-qa="runtime-error">{error}</div>{/if}
	{#if loading}
		<div class="empty" data-qa="runtime-loading" role="status" aria-label="설치된 에이전트를 확인하는 중">
			<span class="spinner" aria-hidden="true"></span>
		</div>
	{:else}
		<div class="grid">
			{#each runtimes as runtime (runtime.runtimeId)}
				<article data-qa={`runtime-card-${runtime.runtimeId}`} class:active={selected === runtime.runtimeId} class:readyCard={runtime.investmentReady}>
					<div class="title">
						<div>
							<strong>{runtime.displayName}</strong>
							<span>{runtime.protocol}</span>
						</div>
						<span class:ready={runtime.investmentReady} class="state">
							{runtime.investmentReady ? '투자 분석 준비 완료' : runtime.state === 'ready' && !runtime.embeddedGrounding ? '현재 미지원' : '준비 필요'}
						</span>
					</div>
					<p class="plainState">
						{runtime.investmentReady
							? '지금 바로 회사명이나 종목코드로 투자 브리프를 만들 수 있습니다.'
							: runtime.blockingReason ?? '필요한 준비 단계를 자동으로 확인합니다.'}
					</p>
					<ol class="rail" aria-label="런타임 준비 단계">
						<li class:done={runtime.readiness.install === 'ready'}>1 설치</li>
						<li class:done={runtime.auth.state === 'authenticated' || runtime.auth.state === 'unsupported'}>2 로그인</li>
						<li class:done={runtime.readiness.grounding === 'connected'}>3 DartLab 연결</li>
						<li class:done={runtime.investmentReady}>4 투자 분석</li>
					</ol>
					<div class="actions">
						{#if runtime.investmentReady}
							<button data-qa={`runtime-select-${runtime.runtimeId}`} onclick={() => void selectRuntime(runtime.runtimeId)} disabled={!runtime.groundedReady || selected === runtime.runtimeId || busy !== null}>
								{selected === runtime.runtimeId ? '사용 중' : '이 런타임 사용'}
							</button>
						{:else if runtime.embeddedGrounding}
							<button data-qa={`runtime-setup-${runtime.runtimeId}`} onclick={() => makeSetupPlan(runtime.runtimeId)} disabled={busy !== null}>
								{busy === `setup:${runtime.runtimeId}` ? '준비 상태 확인 중…' : '분석 엔진 준비'}
							</button>
						{/if}
						<a href={runtime.officialUrl} target="_blank" rel="noreferrer">공식 문서</a>
					</div>
					<details class="advanced">
						<summary>기술 상세</summary>
						<dl>
							<div><dt>버전</dt><dd>{runtime.version ?? '미설치'}</dd></div>
							<div><dt>DartLab 연결</dt><dd>{runtime.mcp?.connected ? '연결됨' : '미연결'}</dd></div>
							<div><dt>투자 계약</dt><dd>{runtime.investmentContractReady ? '확인됨' : '미확인'}</dd></div>
							<div><dt>인증</dt><dd>{runtime.auth.state === 'authenticated' ? '로그인됨' : runtime.auth.state === 'unsupported' ? 'CLI 직접 관리' : '로그인 필요'}</dd></div>
						</dl>
					</details>
				</article>
			{/each}
		</div>
	{/if}

	{#if plan}
		<div class="plan" data-qa="runtime-setup-plan">
			<h3>{plan.displayName} 준비 계획</h3>
			<p>다음 단계를 한 번 승인합니다. 공급자 로그인 화면의 동의는 공식 절차로 별도 표시됩니다.</p>
			<ul>
				{#each plan.changes as change}<li>{change}</li>{/each}
			</ul>
			{#if plan.prerequisitePlan}<code>{plan.prerequisitePlan.argv.join(' ')}</code>{/if}
			{#if plan.installPlan}<code>{plan.installPlan.argv.join(' ')}</code>{/if}
			{#if plan.mcpPlan}<code>{plan.mcpPlan.argv.join(' ')}</code>{/if}
			<div class="actions">
				<button data-qa="runtime-setup-approve" onclick={approveSetup} disabled={busy !== null}>
					{busy ? '공식 로그인 또는 연결 진행 중…' : '한 번 승인하고 준비 완료'}
				</button>
				<button class="secondary" data-qa="runtime-setup-cancel" onclick={() => (plan = null)} disabled={busy !== null}>취소</button>
			</div>
		</div>
	{/if}

	{#if setupResult}
		<div class:success={setupResult.investmentReady} class="result" data-qa="runtime-setup-result" aria-live="polite">
			<strong>{setupResult.investmentReady ? '투자 분석 준비 완료' : `준비 상태: ${setupResult.state}`}</strong>
			{#if setupResult.investmentReady}
				<span>채팅에서 회사명 또는 종목코드와 “투자 분석”을 입력하면 첫 브리프가 시작됩니다.</span>
			{:else if setupResult.nextAction}<span>{setupResult.nextAction}</span>{/if}
		</div>
	{/if}
</section>

<style>
	.runtimeCenter { display: grid; gap: 1rem; color: var(--dl-ink, #e7e7ea); }
	header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
	h2 { margin: 0; font-size: 1.1rem; }
	p { margin: .35rem 0 0; color: var(--dl-ink-dim, #9aa0aa); font-size: .84rem; line-height: 1.5; }
	.grid { display: grid; gap: .75rem; }
	article { border: 1px solid var(--dl-line, #2a2c33); border-radius: 12px; padding: 1rem; background: var(--dl-bg-raised, #16171a); }
	article.active { border-color: var(--dl-accent, #ff5a36); box-shadow: inset 3px 0 var(--dl-accent, #ff5a36); }
	article.readyCard { background: color-mix(in srgb, #70d6a5 4%, var(--dl-bg-raised, #16171a)); }
	.title, .actions, dl div { display: flex; align-items: center; gap: .6rem; }
	.title { justify-content: space-between; }
	.title div { display: grid; gap: .2rem; }
	.title span, dt { color: var(--dl-ink-mute, #6b7280); font-size: .72rem; }
	.state { padding: .18rem .5rem; border-radius: 999px; background: #2a2c33; }
	.state.ready { color: #70d6a5; background: color-mix(in srgb, #70d6a5 12%, transparent); }
	dl { display: grid; gap: .35rem; margin: .8rem 0; }
	.plainState { min-height: 2.5rem; }
	.rail { display: grid; grid-template-columns: repeat(4, 1fr); gap: .35rem; margin: .8rem 0; padding: 0; list-style: none; }
	.rail li { min-height: 2.2rem; display: grid; place-items: center; border: 1px solid var(--dl-line, #2a2c33); border-radius: 7px; color: var(--dl-ink-mute, #6b7280); font-size: .68rem; text-align: center; }
	.rail li.done { color: #70d6a5; border-color: color-mix(in srgb, #70d6a5 40%, var(--dl-line, #2a2c33)); background: color-mix(in srgb, #70d6a5 8%, transparent); }
	dt { width: 6.5rem; }
	dd { margin: 0; font-size: .8rem; overflow-wrap: anywhere; }
	.actions { flex-wrap: wrap; }
	button, a { min-height: 2.75rem; display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: 8px; padding: .55rem .8rem; background: var(--dl-accent, #ff5a36); color: white; font-size: .78rem; cursor: pointer; text-decoration: none; text-align: center; }
	button.secondary { background: transparent; border: 1px solid var(--dl-line, #2a2c33); color: var(--dl-ink-dim, #9aa0aa); }
	button:disabled { opacity: .45; cursor: default; }
	.plan { display: grid; gap: .65rem; padding: 1rem; border: 1px solid var(--dl-accent, #ff5a36); border-radius: 12px; }
	.plan h3 { margin: 0; font-size: .95rem; }
	.plan ul { margin: 0; padding-left: 1.15rem; color: var(--dl-ink-dim, #9aa0aa); font-size: .8rem; line-height: 1.7; }
	code { display: block; padding: .75rem; border-radius: 8px; background: #090a0c; overflow-x: auto; white-space: pre; font-size: .75rem; }
	.error { color: #ff8c8c; padding: .65rem; border: 1px solid #713b3b; border-radius: 8px; }
	.advanced { margin-top: .75rem; color: var(--dl-ink-mute, #6b7280); font-size: .75rem; }
	.advanced summary { cursor: pointer; min-height: 2.25rem; display: flex; align-items: center; }
	.result { display: grid; gap: .3rem; padding: .85rem 1rem; border: 1px solid #713b3b; border-radius: 10px; color: #ffb4b4; font-size: .8rem; }
	.result.success { border-color: color-mix(in srgb, #70d6a5 45%, transparent); color: #8be0b7; }
	.result span { color: var(--dl-ink-dim, #9aa0aa); line-height: 1.5; }
	.empty { color: var(--dl-ink-dim, #9aa0aa); padding: 1rem 0; }
	.spinner { display: block; width: 1.4rem; height: 1.4rem; border: 2px solid var(--dl-line, #2a2c33); border-top-color: var(--dl-accent, #ff5a36); border-radius: 50%; animation: spin .8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
	@media (max-width: 520px) {
		header { flex-wrap: wrap; }
		header > button { width: 100%; }
		article { padding: .85rem; }
		.title { align-items: flex-start; gap: .45rem; }
		.state { max-width: 45%; text-align: center; overflow-wrap: anywhere; }
		dl div { display: grid; grid-template-columns: 5.25rem minmax(0, 1fr); align-items: baseline; }
		dt { width: auto; }
		.actions { display: grid; grid-template-columns: 1fr; }
		.actions > button, .actions > a { width: 100%; }
		.plan { min-width: 0; padding: .8rem; }
		code { max-width: 100%; }
	}
</style>
