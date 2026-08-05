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

	// 상태 조회는 아는 것을 즉시 주고 느린 CLI 실측은 뒤따라온다. 화면은 첫 응답으로
	// 카드를 바로 그리고, 남은 단계는 probing 표시가 사라질 때까지 같은 조회를 반복한다.
	const POLL_INTERVAL_MS = 600;
	const POLL_BUDGET_MS = 60_000;

	type StepState = 'done' | 'probing' | 'todo';

	let runtimes = $state<AgentRuntimeInfo[]>([]);
	let firstLoad = $state(true);
	let probing = $state(false);
	let rechecking = $state(false);
	let busy = $state<string | null>(null);
	let error = $state<string | null>(null);
	let plan = $state<RuntimeSetupPlan | null>(null);
	let setupResult = $state<RuntimeSetupResult | null>(null);
	let selected = $state('');
	let pollTimer: ReturnType<typeof setTimeout> | null = null;
	let pollDeadline = 0;

	onMount(() => {
		void load(false);
		return () => stopPolling();
	});

	function stopPolling(): void {
		if (pollTimer !== null) {
			clearTimeout(pollTimer);
			pollTimer = null;
		}
	}

	function schedulePoll(): void {
		stopPolling();
		if (!probing || Date.now() > pollDeadline) return;
		pollTimer = setTimeout(() => void load(false, true), POLL_INTERVAL_MS);
	}

	async function load(refresh: boolean, isPoll = false): Promise<void> {
		if (isPoll && rechecking) return;
		if (!isPoll) {
			error = null;
			pollDeadline = Date.now() + POLL_BUDGET_MS;
		}
		if (refresh) rechecking = true;
		try {
			const status = await getAgentRuntimeStatus(refresh);
			runtimes = status.runtimes;
			selected = status.defaultRuntimeId ?? '';
			probing = status.probing === true;
			schedulePoll();
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
			probing = false;
			stopPolling();
		} finally {
			firstLoad = false;
			if (refresh) rechecking = false;
		}
	}

	function stageOf(runtime: AgentRuntimeInfo, key: keyof AgentRuntimeInfo['probing']): boolean {
		return runtime.probing?.[key] === true;
	}

	/** 4 단계 레일의 각 칸이 끝났는지, 확인 중인지, 아직 남았는지 판정한다. */
	function railSteps(runtime: AgentRuntimeInfo): Array<{ label: string; state: StepState }> {
		const authDone = runtime.auth.state === 'authenticated' || runtime.auth.state === 'unsupported';
		return [
			{
				label: '설치',
				state: stageOf(runtime, 'install') ? 'probing' : runtime.readiness.install === 'ready' ? 'done' : 'todo'
			},
			{
				label: '로그인',
				state: stageOf(runtime, 'auth') ? 'probing' : authDone ? 'done' : 'todo'
			},
			{
				label: 'DartLab 연결',
				state: stageOf(runtime, 'grounding')
					? 'probing'
					: runtime.readiness.grounding === 'connected'
						? 'done'
						: 'todo'
			},
			{
				label: '투자 분석',
				state: stageOf(runtime, 'contract') ? 'probing' : runtime.investmentReady ? 'done' : 'todo'
			}
		];
	}

	/** 카드 우측 상태 칩. 측정 중이거나 판정하지 못했으면 결론을 쓰지 않는다. */
	function stateChip(runtime: AgentRuntimeInfo): string {
		if (runtime.investmentReady) return '투자 분석 준비 완료';
		if (runtime.pending) return '확인 중';
		if (runtime.undetermined) return '확인 실패';
		if (runtime.state === 'ready' && !runtime.embeddedGrounding) return '현재 미지원';
		return '준비 필요';
	}

	/** 카드 본문 한 줄. 지금 무엇을 기다리는지 또는 무엇이 막혔는지를 그대로 쓴다. */
	function plainState(runtime: AgentRuntimeInfo): string {
		if (runtime.investmentReady) return '지금 바로 회사명이나 종목코드로 투자 브리프를 만들 수 있습니다.';
		return runtime.blockingReason ?? '필요한 준비 단계를 자동으로 확인합니다.';
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
	<!-- 제목은 모달 헤더가 소유한다. 여기는 도구줄 한 줄만. -->
	<div class="toolbar">
		{#if probing}
			<p class="probingNote" data-qa="runtime-probing" role="status">
				<span class="pulse" aria-hidden="true"></span>설치된 CLI 를 확인하는 중입니다. 끝난 항목부터 차례로 채워집니다.
			</p>
		{/if}
		<button class="secondary" data-qa="runtime-refresh" onclick={() => load(true)} disabled={rechecking}>
			{rechecking ? '다시 확인 중' : '다시 확인'}
		</button>
	</div>

	{#if error}<div class="error" data-qa="runtime-error">{error}</div>{/if}
	{#if firstLoad && runtimes.length === 0}
		<div class="empty" data-qa="runtime-loading" role="status">
			<span class="pulse" aria-hidden="true"></span>설치된 에이전트 목록을 불러오는 중입니다.
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
						<span class:ready={runtime.investmentReady} class:probing={runtime.pending} class:undetermined={!runtime.pending && runtime.undetermined} class="state">
							{stateChip(runtime)}
						</span>
					</div>
					<p class="plainState">{plainState(runtime)}</p>
					<ol class="rail" aria-label="런타임 준비 단계">
						{#each railSteps(runtime) as step, index (step.label)}
							<li class:done={step.state === 'done'} class:probing={step.state === 'probing'}>
								{#if step.state === 'probing'}<span class="pulse" aria-hidden="true"></span>{:else}{index + 1}{' '}{/if}{step.label}
							</li>
						{/each}
					</ol>
					<div class="actions">
						{#if runtime.investmentReady}
							<button data-qa={`runtime-select-${runtime.runtimeId}`} onclick={() => void selectRuntime(runtime.runtimeId)} disabled={!runtime.groundedReady || selected === runtime.runtimeId || busy !== null}>
								{selected === runtime.runtimeId ? '사용 중' : '이 런타임 사용'}
							</button>
						{:else if runtime.undetermined}
							<button class="secondary" data-qa={`runtime-recheck-${runtime.runtimeId}`} onclick={() => load(true)} disabled={rechecking}>
								{rechecking ? '다시 확인 중' : '다시 확인'}
							</button>
						{:else if runtime.embeddedGrounding}
							<button data-qa={`runtime-setup-${runtime.runtimeId}`} onclick={() => makeSetupPlan(runtime.runtimeId)} disabled={busy !== null || runtime.pending}>
								{#if runtime.pending}준비 상태 확인 중{:else if busy === `setup:${runtime.runtimeId}`}준비 계획 만드는 중{:else}분석 엔진 준비{/if}
							</button>
						{/if}
						<a href={runtime.officialUrl} target="_blank" rel="noreferrer">공식 문서</a>
					</div>
					<details class="advanced">
						<summary>기술 상세</summary>
						<dl>
							<div><dt>실행 파일</dt><dd>{runtime.installed ? '찾음' : '없음'}</dd></div>
							<div><dt>버전</dt><dd>{stageOf(runtime, 'install') ? '확인 중' : (runtime.version ?? (runtime.detail ?? '미설치'))}</dd></div>
							<div><dt>DartLab 연결</dt><dd>{stageOf(runtime, 'grounding') ? '확인 중' : runtime.mcp?.connected ? '연결됨' : '미연결'}</dd></div>
							<div><dt>투자 계약</dt><dd>{stageOf(runtime, 'contract') ? '확인 중' : runtime.investmentContractReady ? '확인됨' : '미확인'}</dd></div>
							<div><dt>인증</dt><dd>{stageOf(runtime, 'auth') ? '확인 중' : runtime.auth.state === 'authenticated' ? '로그인됨' : runtime.auth.state === 'unsupported' ? 'CLI 직접 관리' : '로그인 필요'}</dd></div>
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
	.runtimeCenter { display: grid; gap: .6rem; color: var(--dl-ink, #e7e7ea); }
	.toolbar { display: flex; align-items: center; justify-content: space-between; gap: .5rem; }
	.toolbar > button { margin-left: auto; }
	.probingNote { display: flex; align-items: center; gap: .4rem; font-size: .74rem; }
	p { margin: 0; color: var(--dl-ink-dim, #9aa0aa); font-size: .78rem; line-height: 1.45; }
	.grid { display: grid; gap: .5rem; }
	article { border: 1px solid var(--dl-line, #2a2c33); border-radius: 10px; padding: .65rem .8rem; background: var(--dl-bg-raised, #16171a); display: grid; gap: .45rem; }
	article.active { border-color: var(--dl-accent, #ff5a36); box-shadow: inset 3px 0 var(--dl-accent, #ff5a36); }
	article.readyCard { background: color-mix(in srgb, var(--dl-good, #34d399) 4%, var(--dl-bg-raised, #16171a)); }
	.title, .actions, dl div { display: flex; align-items: center; gap: .5rem; }
	.title { justify-content: space-between; }
	.title div { display: flex; align-items: baseline; gap: .45rem; }
	.title strong { font-size: .86rem; }
	.title span, dt { color: var(--dl-ink-mute, #6b7280); font-size: .68rem; }
	.state { padding: .12rem .45rem; border-radius: 999px; background: #2a2c33; white-space: nowrap; }
	.state.ready { color: var(--dl-good, #34d399); background: color-mix(in srgb, var(--dl-good, #34d399) 12%, transparent); }
	.state.probing { color: var(--dl-ink-dim, #9aa0aa); background: color-mix(in srgb, #9aa0aa 12%, transparent); }
	.state.undetermined { color: #e0c07a; background: color-mix(in srgb, #e0c07a 12%, transparent); }
	dl { display: grid; gap: .2rem; margin: .1rem 0 0; }
	.plainState { font-size: .76rem; }
	.rail { display: grid; grid-template-columns: repeat(4, 1fr); gap: .3rem; margin: 0; padding: 0; list-style: none; }
	.rail li { min-height: 1.5rem; display: flex; align-items: center; justify-content: center; gap: .22rem; padding: 0 .2rem; border: 1px solid var(--dl-line, #2a2c33); border-radius: 6px; color: var(--dl-ink-mute, #6b7280); font-size: .64rem; text-align: center; }
	.rail li.done { color: var(--dl-good, #34d399); border-color: color-mix(in srgb, var(--dl-good, #34d399) 40%, var(--dl-line, #2a2c33)); background: color-mix(in srgb, var(--dl-good, #34d399) 8%, transparent); }
	.rail li.probing { color: var(--dl-ink-dim, #9aa0aa); border-style: dashed; }
	dt { width: 5.5rem; }
	dd { margin: 0; font-size: .74rem; overflow-wrap: anywhere; }
	.actions { flex-wrap: wrap; }
	button { min-height: 1.9rem; display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: 7px; padding: .3rem .7rem; background: var(--dl-accent, #ff5a36); color: white; font-size: .74rem; cursor: pointer; text-align: center; }
	a { color: var(--dl-ink-dim, #9aa0aa); font-size: .72rem; text-decoration: underline; text-underline-offset: 2px; }
	button.secondary { background: transparent; border: 1px solid var(--dl-line, #2a2c33); color: var(--dl-ink-dim, #9aa0aa); }
	button:disabled { opacity: .45; cursor: default; }
	.plan { display: grid; gap: .5rem; padding: .75rem .85rem; border: 1px solid var(--dl-accent, #ff5a36); border-radius: 10px; }
	.plan h3 { margin: 0; font-size: .88rem; }
	.plan ul { margin: 0; padding-left: 1.1rem; color: var(--dl-ink-dim, #9aa0aa); font-size: .76rem; line-height: 1.55; }
	code { display: block; padding: .5rem .6rem; border-radius: 7px; background: #090a0c; overflow-x: auto; white-space: pre; font-size: .72rem; }
	.error { color: var(--dl-bad, #ef4444); padding: .5rem .6rem; border: 1px solid color-mix(in srgb, var(--dl-bad, #ef4444) 45%, transparent); border-radius: 7px; font-size: .76rem; }
	.advanced { color: var(--dl-ink-mute, #6b7280); font-size: .72rem; }
	.advanced summary { cursor: pointer; min-height: 1.5rem; display: flex; align-items: center; }
	.result { display: grid; gap: .25rem; padding: .55rem .7rem; border: 1px solid color-mix(in srgb, var(--dl-bad, #ef4444) 45%, transparent); border-radius: 8px; color: #ffb4b4; font-size: .76rem; }
	.result.success { border-color: color-mix(in srgb, var(--dl-good, #34d399) 45%, transparent); color: var(--dl-good, #34d399); }
	.result span { color: var(--dl-ink-dim, #9aa0aa); line-height: 1.5; }
	.empty { display: flex; align-items: center; gap: .4rem; color: var(--dl-ink-dim, #9aa0aa); padding: .8rem 0; font-size: .76rem; }
	.pulse { flex: none; width: .42rem; height: .42rem; border-radius: 50%; background: var(--dl-accent, #ff5a36); animation: pulse 1.1s ease-in-out infinite; }
	@keyframes pulse { 0%, 100% { opacity: .25; } 50% { opacity: 1; } }
	@media (prefers-reduced-motion: reduce) { .pulse { animation: none; opacity: .8; } }
	@media (max-width: 520px) {
		article { padding: .6rem .7rem; }
		.title { align-items: flex-start; gap: .4rem; }
		.state { max-width: 45%; text-align: center; overflow-wrap: anywhere; }
		dl div { display: grid; grid-template-columns: 5.25rem minmax(0, 1fr); align-items: baseline; }
		dt { width: auto; }
		.actions { display: grid; grid-template-columns: 1fr; }
		.actions > button { width: 100%; }
		.plan { min-width: 0; padding: .7rem; }
		code { max-width: 100%; }
	}
</style>
