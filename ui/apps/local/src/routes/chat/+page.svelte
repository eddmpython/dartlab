<script lang="ts">
	// 로컬 챗. 옛 React ui/web 챗 GUI(ChatGPT 양식: 사이드바 대화이력 + 아바타 + 마크다운 + 둥근 composer)를
	// Svelte 로 옮긴 것. AiPort.streamAsk(mode:'chat') 한 포트로 대화(터미널 모드와 같은 Ask engine 계약).
	import { onMount, tick } from 'svelte';
	import { base } from '$app/paths';
	import { getLocalRuntime } from '$lib/runtime/localRuntime';
	import { ChatStore } from '$lib/chat/chatStore.svelte';
	import { theme } from '$lib/chat/theme.svelte';
	import Sidebar from '$lib/chat/Sidebar.svelte';
	import Composer from '$lib/chat/Composer.svelte';
	import Markdown from '$lib/chat/Markdown.svelte';
	import SnsLinks from '$lib/chat/SnsLinks.svelte';

	const runtime = getLocalRuntime();
	const store = new ChatStore(runtime.ai);

	let draft = $state('');
	let scroller: HTMLDivElement | null = $state(null);
	let sidebarOpen = $state(true);

	const suggestions = [
		'삼성전자 005930 최근 5년 매출과 영업이익 추이',
		'코스피에서 ROE 높고 부채비율 낮은 종목 찾아줘',
		'테슬라 최근 분기 실적 정리',
		'한국 매크로 지표 (환율 · 금리 · CPI)'
	];

	onMount(() => {
		theme.apply();
		void store.loadCapabilities();
	});

	const active = $derived(store.active);
	const messages = $derived(active?.messages ?? []);
	const hasMessages = $derived(messages.length > 0);
	const cap = $derived(store.capabilities);
	const code = $derived(active?.code?.trim() ?? '');
	const hasCode = $derived(/^\d{6}$/.test(code));

	// 스트리밍·새 메시지마다 하단 고정. 사용자가 위로 스크롤했으면(200px 밖) 건드리지 않는다.
	$effect(() => {
		messages.length;
		messages.at(-1)?.text;
		messages.at(-1)?.activities.length;
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

	function onCode(e: Event): void {
		const v = (e.target as HTMLInputElement).value;
		if (!store.active) store.newConversation();
		const a = store.active;
		if (a) a.code = v;
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
			<SnsLinks />
		</div>

		{#if cap?.upgradeHint}
			<div class="hint">{cap.upgradeHint}</div>
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
									{#if m.activities.length}
										<div class="acts">
											{#each m.activities as a (a.id)}
												<span class="act" class:running={a.status === 'running'}>
													{a.status === 'running' ? '⋯' : '✓'} {a.summary}
												</span>
											{/each}
										</div>
									{/if}

									{#if m.text}
										<Markdown text={m.text} />
										{#if m.streaming}<span class="caret"></span>{/if}
									{:else if m.streaming && !m.error}
										<div class="thinking"><span class="dot"></span><span class="dot"></span><span class="dot"></span> 분석 준비 중</div>
									{/if}

									{#if m.error}
										<div class="err">⚠ 응답 오류: {m.error}</div>
									{/if}

									{#if m.refs.length}
										<div class="refs">
											{#each m.refs as r (r.id)}
												<span class="ref" title={`${r.kind} · ${r.source}`}>{r.title || r.kind}</span>
											{/each}
										</div>
									{/if}

									{#if m.suggested.length}
										<div class="suggest">
											{#each m.suggested as s (s)}
												<button class="sug" onclick={() => ask(s)} disabled={store.busy}>{s}</button>
											{/each}
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
				<div class="ctxrow">
					<input
						class="codein"
						value={active?.code ?? ''}
						oninput={onCode}
						placeholder="종목 컨텍스트 (선택, 6자리)"
						inputmode="numeric"
						maxlength="6"
						aria-label="종목 컨텍스트 코드"
					/>
					{#if hasCode}
						<a class="goterm" href={`${base}/terminal/${code}`}>터미널 →</a>
					{/if}
				</div>
				<Composer
					bind:value={draft}
					busy={store.busy}
					placeholder={hasCode ? `${code} 에 대해 질문…` : '질문을 입력하세요…  (Enter 전송 · Shift+Enter 줄바꿈)'}
					onsend={submit}
				/>
			</div>
		</div>
	</main>
</div>

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
	.ctxrow {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}
	.codein {
		width: 11rem;
		padding: 0.35rem 0.6rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 7px;
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 0.78rem;
		outline: none;
	}
	.codein:focus {
		border-color: var(--dl-accent, #ff5a36);
	}
	.goterm {
		font-size: 0.78rem;
		color: var(--dl-info, #6ab0ff);
		text-decoration: none;
		white-space: nowrap;
	}
	.hint {
		font-size: 0.78rem;
		color: var(--dl-ink-mute, #6b7280);
		padding: 0.5rem 1rem;
		border-bottom: 1px solid var(--dl-line, #2a2c33);
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
	.acts {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
	}
	.act {
		font-size: 0.7rem;
		padding: 0.15rem 0.5rem;
		border-radius: 6px;
		background: var(--dl-bg-raised, #16171a);
		border: 1px solid var(--dl-line, #2a2c33);
		color: var(--dl-ink-mute, #6b7280);
		font-family: var(--dl-font-mono, ui-monospace, monospace);
	}
	.act.running {
		color: var(--dl-info, #6ab0ff);
		border-color: color-mix(in srgb, var(--dl-info, #6ab0ff) 40%, var(--dl-line, #2a2c33));
	}
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
	.thinking {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.85rem;
		color: var(--dl-ink-mute, #6b7280);
	}
	.thinking .dot {
		width: 0.35rem;
		height: 0.35rem;
		border-radius: 50%;
		background: currentColor;
		animation: bob 1.2s infinite ease-in-out;
	}
	.thinking .dot:nth-child(2) {
		animation-delay: 0.15s;
	}
	.thinking .dot:nth-child(3) {
		animation-delay: 0.3s;
	}
	@keyframes bob {
		0%, 60%, 100% {
			opacity: 0.3;
		}
		30% {
			opacity: 1;
		}
	}
	.err {
		font-size: 0.85rem;
		color: var(--dl-bad, #ff6b6b);
	}
	.refs {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
	}
	.ref {
		font-size: 0.7rem;
		padding: 0.15rem 0.5rem;
		border-radius: 6px;
		border: 1px solid var(--dl-line, #2a2c33);
		color: var(--dl-ink-dim, #9aa0aa);
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
		border: 1px dashed var(--dl-line, #2a2c33);
		background: none;
		color: var(--dl-info, #6ab0ff);
		cursor: pointer;
	}
	.sug:hover:not(:disabled) {
		border-style: solid;
	}
	.sug:disabled {
		opacity: 0.5;
		cursor: default;
	}

	/* 하단 입력 도크 */
	.dock {
		border-top: 1px solid var(--dl-line, #2a2c33);
		padding: 0.75rem 0 1rem;
	}
</style>
