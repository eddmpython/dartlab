<script lang="ts">
	// 로컬 챗. 옛 React ui/web 챗 GUI(ChatGPT 양식: 사이드바 대화이력 + 아바타 + 마크다운 + 둥근 composer)를
	// Svelte 로 옮긴 것. AiPort.streamAsk(mode:'chat') 한 포트로 대화(터미널 모드와 같은 Ask engine 계약).
	import { onMount, tick } from 'svelte';
	import { base } from '$app/paths';
	import { getLocalRuntime } from '$lib/runtime/localRuntime';
	import { ChatStore } from '$lib/chat/chatStore.svelte';
	import Sidebar from '$lib/chat/Sidebar.svelte';
	import Composer from '$lib/chat/Composer.svelte';
	import Markdown from '$lib/chat/Markdown.svelte';
	import ToolCard from '$lib/chat/ToolCard.svelte';
	import Evidence from '$lib/chat/Evidence.svelte';
	import ThinkingPanel from '$lib/chat/ThinkingPanel.svelte';
	import RuntimeCenter from '$lib/chat/RuntimeCenter.svelte';
	import '@dartlab/ui-surfaces/terminal/terminal.css';
	import { BrandSocial, DARTLAB_BRAND_LINKS, LAST_SYM_KEY } from '@dartlab/ui-surfaces/terminal';

	const runtime = getLocalRuntime();
	const store = new ChatStore(runtime.ai);

	let draft = $state('');
	let scroller: HTMLDivElement | null = $state(null);
	let sidebarOpen = $state(true);
	let runtimeOpen = $state(false);

	const suggestions = [
		'삼성전자 005930 최근 5년 매출과 영업이익 추이',
		'코스피에서 ROE 높고 부채비율 낮은 종목 찾아줘',
		'테슬라 최근 분기 실적 정리',
		'한국 매크로 지표 (환율 · 금리 · CPI)'
	];

	// 터미널 토글 목적지 · surface 가 관리하는 최근 종목(LAST_SYM_KEY), 없으면 005930.
	const recent =
		(typeof localStorage !== 'undefined' && localStorage.getItem(LAST_SYM_KEY)) || '005930';

	onMount(() => {
		// 챗은 터미널과 같은 다크 계기판 · 라이트 잔상 제거(공용 SNS 아이콘 가시성 보장).
		if (typeof document !== 'undefined') document.documentElement.removeAttribute('data-theme');
		void store.loadCapabilities();
	});

	const active = $derived(store.active);
	const messages = $derived(active?.messages ?? []);
	const hasMessages = $derived(messages.length > 0);
	const cap = $derived(store.capabilities);
	// 연결 = 설치형 agent CLI가 실제 사용 가능. 아니면 Runtime Center 안내.
	const connected = $derived(cap?.tier === 'advanced' || cap?.tier === 'onDevice');

	// 스트리밍·새 메시지마다 하단 고정. 사용자가 위로 스크롤했으면(200px 밖) 건드리지 않는다.
	$effect(() => {
		messages.length;
		messages.at(-1)?.text;
		messages.at(-1)?.thinking;
		messages.at(-1)?.tools.length;
		if (!scroller) return;
		const el = scroller;
		const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
		if (dist < 220) {
			void tick().then(() => {
				el.scrollTop = el.scrollHeight;
			});
		}
	});

	async function submit(): Promise<void> {
		const text = draft.trim();
		if (!text || store.busy) return;
		draft = '';
		await store.send(text);
	}

	function ask(prompt: string): void {
		draft = prompt;
		void submit();
	}

	function openSupport(): void {
		window.open(DARTLAB_BRAND_LINKS.coffee, '_blank', 'noopener');
	}

	let copiedId = $state<string | null>(null);
	async function copyMsg(id: string, text: string): Promise<void> {
		try {
			await navigator.clipboard.writeText(text);
			copiedId = id;
			setTimeout(() => {
				if (copiedId === id) copiedId = null;
			}, 1400);
		} catch {
			// 클립보드 미지원 환경은 무시.
		}
	}
</script>

<svelte:head>
	<title>챗 · dartlab local</title>
</svelte:head>

<div class="shell">
	{#if sidebarOpen}
		<Sidebar {store} />
	{/if}

	<main class="main">
		<div class="topstrip">
			<button class="ghost" onclick={() => (sidebarOpen = !sidebarOpen)} aria-label="사이드바 토글" title="사이드바">
				<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /></svg>
			</button>
			<div class="spacer"></div>
			<a class="ghost" href={`${base}/terminal/${recent}`} title="터미널로" aria-label="터미널로">
				<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17l6-6-6-6M12 19h8" /></svg>
			</a>
			<button class="ghost" onclick={() => (runtimeOpen = true)} title="Agent Runtime Center" aria-label="Agent Runtime Center">
				<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
			</button>
			<div class="dlTerm chatSns" style="display:contents">
				<BrandSocial links={DARTLAB_BRAND_LINKS} ghStars={null} onSupport={openSupport} />
			</div>
		</div>

		{#if store.capabilitiesLoaded && !connected}
			<div class="notice">
				<span>사용 가능한 agent CLI가 없습니다. 설치 전에는 답변하지 않습니다.</span>
				<a href={`${base}/settings/runtimes`}>Runtime Center →</a>
			</div>
		{/if}

		<div class="stream" bind:this={scroller}>
			<div class="col">
				{#if !hasMessages}
					<div class="welcome">
						<img class="ava" src="{base}/avatar.png" alt="DartLab" width="56" height="56" />
						<h1>무엇을 도와드릴까요?</h1>
						<p>회사·재무·공시·시장·거시 지표. 무엇이든 물어보세요. 근거 기반 Ask 엔진이 답합니다.</p>
						<div class="chips">
							{#each suggestions as s (s)}
								<button class="chip" onclick={() => ask(s)}>{s}</button>
							{/each}
						</div>
					</div>
				{:else}
					{#each messages as m (m.id)}
						{#if m.role === 'user'}
							<div class="turn user">
								<div class="bubble">{m.text}</div>
							</div>
						{:else}
							<div class="turn assistant">
								<img class="msgava" src="{base}/avatar.png" alt="DartLab" width="30" height="30" />
								<div class="body">
									{#if m.thinking || (m.streaming && !m.text)}
										<ThinkingPanel thinking={m.thinking} active={m.streaming && !m.text} />
									{/if}

									{#if m.tools.length}
										<div class="workbench">
											{#each m.tools as t (t.id)}
												<ToolCard tool={t} />
											{/each}
										</div>
									{/if}

									{#if m.approvals.length}
										<div class="approvals">
											{#each m.approvals as approval (approval.id)}
												<div class="approval">
													<span>{approval.summary}</span>
													{#if approval.status === 'pending'}
														<button onclick={() => store.resolveApproval(m, approval.id, true)}>허용</button>
														<button class="deny" onclick={() => store.resolveApproval(m, approval.id, false)}>거부</button>
													{:else}<small>{approval.status}</small>{/if}
												</div>
											{/each}
										</div>
									{/if}

									{#if m.text}
										<Markdown text={m.text} />
										{#if m.streaming}<span class="caret"></span>{/if}
									{/if}

									{#if m.error}
										<div class="err">⚠ 응답 오류: {m.error}</div>
									{/if}

									{#if m.refs.length}
										<Evidence refs={m.refs} />
									{/if}

									{#if m.suggested.length}
										<div class="suggest">
											{#each m.suggested as s (s)}
												<button class="sug" onclick={() => ask(s)} disabled={store.busy}>{s}</button>
											{/each}
										</div>
									{/if}

									{#if m.text && !m.streaming}
										<div class="msgacts">
											<button class="msgact" onclick={() => copyMsg(m.id, m.text)} title="복사">
												{#if copiedId === m.id}
													<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5" /></svg>
													복사됨
												{:else}
													<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>
													복사
												{/if}
											</button>
										</div>
									{/if}
								</div>
							</div>
						{/if}
					{/each}
				{/if}
			</div>
		</div>

		<div class="dock">
			<div class="col">
				<Composer
					bind:value={draft}
					busy={store.busy}
					placeholder="질문을 입력하세요…  (Enter 전송 · Shift+Enter 줄바꿈)"
					onsend={submit}
				/>
			</div>
		</div>
	</main>
</div>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape' && runtimeOpen) runtimeOpen = false; }} />

{#if runtimeOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="povl" role="presentation" onclick={() => (runtimeOpen = false)}>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="pmodal" role="dialog" aria-modal="true" aria-label="Agent Runtime Center" tabindex="-1" onclick={(e) => e.stopPropagation()}>
			<header class="pmhead">
				<h2>Agent Runtime Center</h2>
				<button class="pmx" onclick={() => (runtimeOpen = false)} aria-label="닫기">✕</button>
			</header>
			<p class="pmsub">설치된 CLI를 선택하고 DartLab MCP 연결을 확인하세요.</p>
			<div class="pmbody">
				<RuntimeCenter onChange={() => store.loadCapabilities()} />
			</div>
		</div>
	</div>
{/if}

<style>
	.shell {
		display: flex;
		height: 100vh;
		background: var(--dl-bg-base, #0f0f10);
		color: var(--dl-ink, #e7e7ea);
	}
	.main {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 0;
		height: 100vh;
	}
	.topstrip {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
	}
	.spacer {
		flex: 1;
	}
	.ghost {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		border: none;
		border-radius: 7px;
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		cursor: pointer;
	}
	.ghost:hover {
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
	}
	.notice {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		flex-wrap: wrap;
		font-size: 0.8rem;
		color: var(--dl-warn, #f4b740);
		background: color-mix(in srgb, var(--dl-warn, #f4b740) 10%, transparent);
		padding: 0.55rem 1rem;
		border-bottom: 1px solid color-mix(in srgb, var(--dl-warn, #f4b740) 30%, var(--dl-line, #2a2c33));
	}
	.notice a {
		color: var(--dl-accent, #ff5a36);
		text-decoration: none;
		font-weight: 600;
		white-space: nowrap;
	}
	.notice a:hover {
		text-decoration: underline;
	}
	.stream {
		flex: 1;
		overflow-y: auto;
		scrollbar-width: thin;
	}
	.col {
		width: 100%;
		max-width: 46rem;
		margin: 0 auto;
		padding: 0 1.25rem;
	}
	.stream .col {
		padding-top: 1.5rem;
		padding-bottom: 2rem;
	}

	/* 빈 상태 웰컴 */
	.welcome {
		min-height: 60vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		gap: 0.4rem;
	}
	.welcome .ava {
		border-radius: 14px;
		margin-bottom: 0.6rem;
	}
	.welcome h1 {
		font-size: 1.5rem;
		font-weight: 600;
		letter-spacing: -0.02em;
		margin: 0;
	}
	.welcome p {
		max-width: 30rem;
		font-size: 0.88rem;
		color: var(--dl-ink-dim, #9aa0aa);
		margin: 0 0 1rem;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 0.5rem;
	}
	.chip {
		padding: 0.5rem 0.9rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 999px;
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.8rem;
		cursor: pointer;
	}
	.chip:hover {
		border-color: var(--dl-accent, #ff5a36);
		color: var(--dl-ink, #e7e7ea);
	}

	/* 메시지 */
	.turn {
		display: flex;
		margin: 1.25rem 0;
	}
	.turn.user {
		justify-content: flex-end;
	}
	.user .bubble {
		max-width: 78%;
		padding: 0.6rem 0.9rem;
		border-radius: 1.1rem;
		background: var(--dl-bg-raised, #16171a);
		border: 1px solid var(--dl-line, #2a2c33);
		font-size: 0.92rem;
		line-height: 1.55;
		white-space: pre-wrap;
		word-break: break-word;
	}
	.turn.assistant {
		gap: 0.7rem;
		align-items: flex-start;
	}
	.msgava {
		flex-shrink: 0;
		border-radius: 9px;
		margin-top: 0.1rem;
	}
	.body {
		min-width: 0;
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.workbench {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	.approvals { display: grid; gap: .4rem; }
	.approval { display: flex; align-items: center; gap: .5rem; padding: .65rem; border: 1px solid var(--dl-warn, #f4b740); border-radius: 8px; font-size: .78rem; }
	.approval span { flex: 1; }
	.approval button { border: 0; border-radius: 6px; padding: .3rem .55rem; background: var(--dl-accent, #ff5a36); color: white; cursor: pointer; }
	.approval button.deny { background: transparent; border: 1px solid var(--dl-line, #2a2c33); color: var(--dl-ink-dim, #9aa0aa); }
	.caret {
		display: inline-block;
		width: 0.5rem;
		height: 1rem;
		margin-left: 2px;
		vertical-align: text-bottom;
		background: var(--dl-accent, #ff5a36);
		animation: blink 1s step-start infinite;
	}
	@keyframes blink {
		50% {
			opacity: 0;
		}
	}
	.err {
		font-size: 0.85rem;
		color: var(--dl-bad, #ff6b6b);
	}
	.suggest {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin-top: 0.2rem;
	}
	.sug {
		font-size: 0.78rem;
		padding: 0.3rem 0.7rem;
		border-radius: 999px;
		border: 1px solid var(--dl-line, #2a2c33);
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		cursor: pointer;
	}
	.sug:hover:not(:disabled) {
		border-color: var(--dl-accent, #ff5a36);
		color: var(--dl-ink, #e7e7ea);
	}
	.sug:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.msgacts {
		margin-top: 0.15rem;
		opacity: 0;
		transition: opacity 0.15s ease;
	}
	.turn.assistant:hover .msgacts {
		opacity: 1;
	}
	.msgact {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.25rem 0.5rem;
		border: none;
		border-radius: 6px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		font-size: 0.72rem;
		cursor: pointer;
	}
	.msgact:hover {
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
	}

	/* 하단 입력 도크 */
	.dock {
		border-top: 1px solid var(--dl-line, #2a2c33);
		padding: 0.75rem 0 1rem;
	}
	.povl {
		position: fixed;
		inset: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.6);
		padding: 1rem;
	}
	.pmodal {
		width: 100%;
		max-width: 34rem;
		max-height: 85vh;
		display: flex;
		flex-direction: column;
		background: var(--dl-bg-base, #0f0f10);
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 14px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
		overflow: hidden;
	}
	.pmhead {
		display: flex;
		align-items: center;
		padding: 1rem 1.25rem 0.4rem;
	}
	.pmhead h2 {
		font-size: 1.05rem;
		font-weight: 600;
		margin: 0;
	}
	.pmx {
		margin-left: auto;
		width: 1.9rem;
		height: 1.9rem;
		border: none;
		border-radius: 7px;
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.95rem;
		cursor: pointer;
	}
	.pmx:hover {
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
	}
	.pmsub {
		font-size: 0.82rem;
		color: var(--dl-ink-dim, #9aa0aa);
		margin: 0;
		padding: 0 1.25rem 0.75rem;
	}
	.pmbody {
		overflow-y: auto;
		padding: 0 1.25rem 1.25rem;
		scrollbar-width: thin;
	}
</style>
