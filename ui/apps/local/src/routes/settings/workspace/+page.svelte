<script lang="ts">
	import { base } from '$app/paths';
	import { getLocalRuntime } from '$lib/runtime/localRuntime';
	import { listAgentRuntimes } from '$lib/runtime/agentRuntimeApi';

	// Workspace 상태 — 발명 기능이 아니라 *기존 상태*를 표면화한다(덕지덕지 회피): 로컬 서버(/api) 연결 상태,
	// 설치형 agent runtime과 로컬 앱 환경을 한 화면에서 확인한다.

	const env = getLocalRuntime().env;

	let conn = $state<'checking' | 'ok' | 'down'>('checking');
	let active = $state<{ key: string; label: string; model: string } | null>(null);
	let runtimeCount = $state(0);

	async function probe(): Promise<void> {
		conn = 'checking';
		try {
			const runtimes = await listAgentRuntimes(false);
			const ready = runtimes.filter((item) => item.state === 'ready');
			runtimeCount = ready.length;
			const preferred = localStorage.getItem('dartlab-agent-runtime');
			const selected = ready.find((item) => item.runtimeId === preferred) ?? ready[0] ?? null;
			active = selected
				? { key: selected.runtimeId, label: selected.displayName, model: selected.version || 'CLI 관리' }
				: null;
			conn = 'ok';
		} catch {
			conn = 'down';
			active = null;
			runtimeCount = 0;
		}
	}

	$effect(() => {
		void probe();
	});

	const rows = $derived([
		{ k: '시장 기본', v: env.marketDefault },
		{ k: '로케일', v: env.locale },
		{ k: '빌드', v: env.buildVersion },
		{ k: '런타임', v: env.kind },
		{ k: '읽기전용', v: env.readonly ? 'yes' : 'no' }
	]);
</script>

<svelte:head>
	<title>Settings · Workspace — dartlab local</title>
</svelte:head>

<section>
	<a class="back" href={base || '/'}>← local</a>
	<h1>Workspace</h1>
	<p>로컬 서버와 설치형 agent 상태. 선택·설치·MCP 연결은 <a href={`${base}/settings/runtimes`}>Runtime Center</a>.</p>

	<div class="block">
		<div class="row">
			<span class="k">서버(/api)</span>
			<span class="v">
				{#if conn === 'checking'}<span class="dot checking"></span>확인 중…
				{:else if conn === 'ok'}<span class="dot ok"></span>연결됨
				{:else}<span class="dot down"></span>연결 안 됨 — dartlab 로컬 서버를 실행하세요{/if}
			</span>
		</div>
		<div class="row">
			<span class="k">활성 agent</span>
			<span class="v">
				{#if conn !== 'ok'}—
				{:else if active}{active.label} · <code>{active.model}</code>
				{:else}미설치 — <a href={`${base}/settings/runtimes`}>Runtime Center에서 설치</a>{/if}
			</span>
		</div>
		{#if conn === 'ok'}
			<div class="row"><span class="k">가용 runtime</span><span class="v">{runtimeCount}개</span></div>
		{/if}
	</div>

	<div class="block">
		{#each rows as r (r.k)}
			<div class="row"><span class="k">{r.k}</span><span class="v"><code>{r.v}</code></span></div>
		{/each}
	</div>

	<button class="btn" onclick={() => probe()}>새로고침</button>
</section>

<style>
	section {
		max-width: 720px;
		margin: 0 auto;
		padding: 3rem 1.5rem;
	}
	.back {
		color: var(--dl-ink-dim, #9aa0aa);
		text-decoration: none;
		font-size: 0.85rem;
	}
	h1 {
		font-size: 1.5rem;
		margin: 1rem 0 0.4rem;
	}
	p {
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.9rem;
		margin: 0 0 1.5rem;
	}
	p a,
	.v a {
		color: var(--dl-accent, #ff5a36);
	}
	.block {
		border: 1px solid var(--dl-border, #2a2c31);
		border-radius: 8px;
		padding: 0.4rem 0.9rem;
		margin-bottom: 1rem;
	}
	.row {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.55rem 0;
		border-bottom: 1px solid color-mix(in srgb, var(--dl-border, #2a2c31) 50%, transparent);
		font-size: 0.88rem;
	}
	.row:last-child {
		border-bottom: none;
	}
	.k {
		color: var(--dl-ink-dim, #9aa0aa);
		min-width: 110px;
	}
	.v {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}
	code {
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 12px;
		color: var(--dl-info, #6ab0ff);
	}
	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		display: inline-block;
	}
	.dot.ok {
		background: #34d399;
	}
	.dot.down {
		background: #f87171;
	}
	.dot.checking {
		background: #d1a054;
	}
	.btn {
		height: 32px;
		padding: 0 0.9rem;
		border: 1px solid var(--dl-border, #2a2c31);
		border-radius: 6px;
		background: transparent;
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.82rem;
		cursor: pointer;
	}
</style>
