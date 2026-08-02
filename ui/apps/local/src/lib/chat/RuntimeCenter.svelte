<script lang="ts">
	import { onMount } from 'svelte';
	import {
		applyRuntimePlan,
		listAgentRuntimes,
		planRuntimeInstall,
		planRuntimeMcp,
		type AgentRuntimeInfo,
		type RuntimePlan
	} from '$lib/runtime/agentRuntimeApi';

	let { onChange = () => undefined }: { onChange?: () => void | Promise<void> } = $props();

	let runtimes = $state<AgentRuntimeInfo[]>([]);
	let loading = $state(true);
	let busy = $state<string | null>(null);
	let error = $state<string | null>(null);
	let plan = $state<{ kind: 'install' | 'mcp'; value: RuntimePlan } | null>(null);
	let selected = $state('');

	onMount(() => void load(false));

	async function load(refresh: boolean): Promise<void> {
		loading = true;
		error = null;
		try {
			runtimes = await listAgentRuntimes(refresh);
			const stored = localStorage.getItem('dartlab-agent-runtime');
			selected = runtimes.some((item) => item.runtimeId === stored && item.groundedReady)
				? (stored ?? '')
				: (runtimes.find((item) => item.groundedReady)?.runtimeId ?? '');
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			loading = false;
		}
	}

	function selectRuntime(runtimeId: string): void {
		selected = runtimeId;
		localStorage.setItem('dartlab-agent-runtime', runtimeId);
		void onChange();
	}

	async function makePlan(kind: 'install' | 'mcp', runtimeId: string): Promise<void> {
		busy = `${kind}:${runtimeId}`;
		error = null;
		try {
			const value = kind === 'install' ? await planRuntimeInstall(runtimeId) : await planRuntimeMcp(runtimeId);
			plan = { kind, value };
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			busy = null;
		}
	}

	async function approvePlan(): Promise<void> {
		if (!plan) return;
		busy = `${plan.kind}:${plan.value.runtimeId}`;
		error = null;
		try {
			await applyRuntimePlan(plan.kind, plan.value);
			plan = null;
			await load(true);
			await onChange();
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			busy = null;
		}
	}
</script>

<section class="runtimeCenter">
	<header>
		<div>
			<h2>Agent Runtime Center</h2>
			<p>로그인과 모델은 설치된 CLI가 소유하고, DartLab은 재무 도구와 근거를 연결합니다.</p>
		</div>
		<button class="secondary" onclick={() => load(true)} disabled={loading}>다시 확인</button>
	</header>

	{#if error}<div class="error">{error}</div>{/if}
	{#if loading}
		<div class="empty">설치된 에이전트를 확인하는 중입니다.</div>
	{:else}
		<div class="grid">
			{#each runtimes as runtime (runtime.runtimeId)}
				<article class:active={selected === runtime.runtimeId}>
					<div class="title">
						<div>
							<strong>{runtime.displayName}</strong>
							<span>{runtime.protocol}</span>
						</div>
						<span class:ready={runtime.groundedReady} class="state">{runtime.groundedReady ? '사용 가능' : runtime.state}</span>
					</div>
					<dl>
						<div><dt>버전</dt><dd>{runtime.version ?? '미설치'}</dd></div>
						<div><dt>DartLab MCP</dt><dd>{runtime.mcp?.connected ? '연결됨' : '미연결'}</dd></div>
						<div><dt>인증</dt><dd>CLI가 직접 관리</dd></div>
					</dl>
					<div class="actions">
						{#if runtime.state === 'ready'}
							<button onclick={() => selectRuntime(runtime.runtimeId)} disabled={!runtime.groundedReady || selected === runtime.runtimeId}>
								{selected === runtime.runtimeId ? '사용 중' : '이 런타임 사용'}
							</button>
							{#if !runtime.mcp?.connected}
								<button class="secondary" onclick={() => makePlan('mcp', runtime.runtimeId)} disabled={busy !== null}>MCP 연결</button>
							{/if}
						{:else}
							<button onclick={() => makePlan('install', runtime.runtimeId)} disabled={busy !== null}>설치 계획</button>
						{/if}
						<a href={runtime.officialUrl} target="_blank" rel="noreferrer">공식 문서</a>
					</div>
				</article>
			{/each}
		</div>
	{/if}

	{#if plan}
		<div class="plan">
			<h3>{plan.kind === 'install' ? '설치' : 'MCP 연결'} 실행 전 확인</h3>
			<p>아래 명령만 실행합니다. 구성 파일을 직접 수정하거나 인증 정보를 읽지 않습니다.</p>
			<code>{plan.value.argv.join(' ')}</code>
			<small>SHA-256 {plan.value.digest}</small>
			<div class="actions">
				<button onclick={approvePlan} disabled={busy !== null}>이 계획 승인하고 실행</button>
				<button class="secondary" onclick={() => (plan = null)} disabled={busy !== null}>취소</button>
			</div>
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
	.title, .actions, dl div { display: flex; align-items: center; gap: .6rem; }
	.title { justify-content: space-between; }
	.title div { display: grid; gap: .2rem; }
	.title span, dt, small { color: var(--dl-ink-mute, #6b7280); font-size: .72rem; }
	.state { padding: .18rem .5rem; border-radius: 999px; background: #2a2c33; }
	.state.ready { color: #70d6a5; background: color-mix(in srgb, #70d6a5 12%, transparent); }
	dl { display: grid; gap: .35rem; margin: .8rem 0; }
	dt { width: 6.5rem; }
	dd { margin: 0; font-size: .8rem; overflow-wrap: anywhere; }
	.actions { flex-wrap: wrap; }
	button, a { border: 0; border-radius: 8px; padding: .45rem .7rem; background: var(--dl-accent, #ff5a36); color: white; font-size: .76rem; cursor: pointer; text-decoration: none; }
	button.secondary { background: transparent; border: 1px solid var(--dl-line, #2a2c33); color: var(--dl-ink-dim, #9aa0aa); }
	button:disabled { opacity: .45; cursor: default; }
	.plan { display: grid; gap: .65rem; padding: 1rem; border: 1px solid var(--dl-accent, #ff5a36); border-radius: 12px; }
	.plan h3 { margin: 0; font-size: .95rem; }
	code { display: block; padding: .75rem; border-radius: 8px; background: #090a0c; overflow-x: auto; white-space: pre; font-size: .75rem; }
	.error { color: #ff8c8c; padding: .65rem; border: 1px solid #713b3b; border-radius: 8px; }
	.empty { color: var(--dl-ink-dim, #9aa0aa); padding: 1rem 0; }
</style>
