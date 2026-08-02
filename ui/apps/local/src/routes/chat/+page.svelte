<script lang="ts">
	// 로컬 챗. 옛 React ui/web 챗 GUI(ChatGPT 양식: 사이드바 대화이력 + 아바타 + 마크다운 + 둥근 composer)를
	// Svelte 로 옮긴 것. AiPort.streamAsk(mode:'chat') 한 포트로 대화(터미널 모드와 같은 Ask engine 계약).
	import { onMount, tick } from 'svelte';
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { isKrStockCode, normalizeKrCode } from '@dartlab/ui-contracts';
	import { getLocalRuntime } from '$lib/runtime/localRuntime';
	import { ChatStore, type ChatMessage } from '$lib/chat/chatStore.svelte';
	import Sidebar from '$lib/chat/Sidebar.svelte';
	import Composer from '$lib/chat/Composer.svelte';
	import Markdown from '$lib/chat/Markdown.svelte';
	import ToolCard from '$lib/chat/ToolCard.svelte';
	import Evidence from '$lib/chat/Evidence.svelte';
	import RuntimeCenter from '$lib/chat/RuntimeCenter.svelte';
	import '@dartlab/ui-surfaces/terminal/terminal.css';
	import { BrandSocial, DARTLAB_BRAND_LINKS, LAST_SYM_KEY } from '@dartlab/ui-surfaces/terminal';

	const runtime = getLocalRuntime();
	const store = new ChatStore(runtime.ai);

	let draft = $state('');
	let scroller: HTMLDivElement | null = $state(null);
	let sidebarOpen = $state(true);
	let runtimeOpen = $state(false);
	let runtimeTrigger: HTMLButtonElement | null = $state(null);
	let runtimeDialog: HTMLDivElement | null = $state(null);
	let focusReturnTarget: HTMLElement | null = null;
	type EvidenceHandle = { openRef: (refId: string) => Promise<void> };
	let evidencePanels: Record<string, EvidenceHandle | undefined> = {};

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
		const contextCode = normalizeKrCode(page.url.searchParams.get('code') ?? '');
		if (isKrStockCode(contextCode)) store.setContextCode(contextCode);
		if (window.matchMedia('(max-width: 720px)').matches) sidebarOpen = false;
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

	function openRuntimeCenter(): void {
		focusReturnTarget = document.activeElement instanceof HTMLElement ? document.activeElement : runtimeTrigger;
		runtimeOpen = true;
		void tick().then(() => {
			const first = runtimeDialog?.querySelector<HTMLElement>(
				'button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'
			);
			(first ?? runtimeDialog)?.focus();
		});
	}

	function closeRuntimeCenter(): void {
		if (!runtimeOpen) return;
		runtimeOpen = false;
		void tick().then(() => focusReturnTarget?.focus());
	}

	function trapRuntimeFocus(event: KeyboardEvent): void {
		if (event.key === 'Escape') {
			event.preventDefault();
			closeRuntimeCenter();
			return;
		}
		if (event.key !== 'Tab' || !runtimeDialog) return;
		const focusable = Array.from(
			runtimeDialog.querySelectorAll<HTMLElement>(
				'button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'
			)
		);
		if (!focusable.length) {
			event.preventDefault();
			runtimeDialog.focus();
			return;
		}
		const first = focusable[0];
		const last = focusable.at(-1) as HTMLElement;
		const activeElement = document.activeElement;
		if (event.shiftKey && (activeElement === first || !runtimeDialog.contains(activeElement))) {
			event.preventDefault();
			last.focus();
		} else if (!event.shiftKey && activeElement === last) {
			event.preventDefault();
			first.focus();
		}
	}

	function markEvidenceVerified(message: ChatMessage, refId: string): void {
		if (!message.verifiedRefIds.includes(refId)) message.verifiedRefIds.push(refId);
	}

	const ISSUE_LABELS: Record<string, string> = {
		runtime_not_completed: '런타임 완료 실패',
		read_skill_missing: 'Skill OS 계약 미확인',
		read_skill_repeated: 'Skill OS 반복 조회',
		empty_answer: '최종 답변 없음',
		source_ref_missing: '표·문서 출처 누락',
		document_ref_missing: '공시 원문 누락',
		date_ref_missing: '기준시점 누락',
		value_ref_missing: '수치 근거 누락',
		value_binding_mismatch: '답변 수치와 근거 불일치',
		date_binding_mismatch: '답변 시점과 근거 불일치',
		period_coverage_incomplete: '요구 기간 일부 누락',
		comparison_target_incomplete: '비교 대상 일부 누락',
		target_evidence_mismatch: '질문 대상과 근거 불일치',
		metric_evidence_mismatch: '질문 지표와 근거 불일치',
		evidence_payload_empty: '근거 내용 비어 있음',
		table_evidence_empty: '표 내용 비어 있음',
		value_evidence_unavailable: '값을 확인할 수 없음',
		date_evidence_unavailable: '기준일을 확인할 수 없음'
	};

	const EVIDENCE_LABELS: Record<string, string> = {
		tableRef: '표',
		docRef: '문서',
		valueRef: '값',
		dateRef: '기준시점',
		skillRef: 'Skill OS',
		executionRef: '실행 기록',
		sourceRef: '원천 출처'
	};

	function issueLabel(issue: string): string {
		return ISSUE_LABELS[issue] ?? issue;
	}

	function evidenceLabel(kind: string): string {
		return EVIDENCE_LABELS[kind] ?? kind;
	}

	function viewSpecSummary(spec: unknown): string {
		if (!spec || typeof spec !== 'object') return '시각 결과 준비됨';
		const value = spec as Record<string, unknown>;
		const widgets = Array.isArray(value.widgets) ? value.widgets.length : 0;
		const charts = Array.isArray(value.charts) ? value.charts.length : 0;
		if (widgets || charts) return `위젯 ${widgets} · 차트 ${charts}`;
		return typeof value.component === 'string' ? value.component : '시각 결과 준비됨';
	}

	function artifactTitle(data: Record<string, unknown>): string {
		for (const key of ['title', 'name', 'filename', 'label', 'kind']) {
			if (typeof data[key] === 'string' && data[key]) return String(data[key]);
		}
		return '분석 산출물';
	}

	function artifactHref(data: Record<string, unknown>): string | null {
		for (const key of ['url', 'href', 'downloadUrl']) {
			const value = data[key];
			if (typeof value !== 'string' || !value) continue;
			if (value.startsWith('/')) return value;
			try {
				const url = new URL(value);
				if (url.protocol === 'http:' || url.protocol === 'https:') return url.href;
			} catch {
				// 공개 URL이 아니면 채팅에서 링크하지 않는다.
			}
		}
		return null;
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

<div class="shell" inert={runtimeOpen}>
	{#if sidebarOpen}
		<button class="sideveil" aria-label="사이드바 닫기" onclick={() => (sidebarOpen = false)}></button>
		<Sidebar {store} />
	{/if}

	<main class="main">
		<div class="topstrip">
			<button class="ghost" onclick={() => (sidebarOpen = !sidebarOpen)} aria-label="사이드바 토글" aria-expanded={sidebarOpen} title="사이드바">
				<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /></svg>
			</button>
			<div class="spacer"></div>
			{#if cap?.providerLabel}<span class="runtimeBadge">{cap.providerLabel} · 근거 게이트</span>{/if}
			<a class="ghost" href={`${base}/terminal/${recent}`} title="터미널로" aria-label="터미널로">
				<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17l6-6-6-6M12 19h8" /></svg>
			</a>
			<button
				class="ghost"
				bind:this={runtimeTrigger}
				onclick={openRuntimeCenter}
				title="Agent Runtime Center"
				aria-label="Agent Runtime Center"
				aria-haspopup="dialog"
				aria-expanded={runtimeOpen}
				aria-controls="runtime-center-dialog"
			>
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
									{#if m.streaming && !m.text}
										<div class="runstate" role="status" aria-label="근거를 확인하는 중"><span></span></div>
									{/if}
									{#if m.activities.length}
										<details class="activityLog" open={m.streaming}>
											<summary>
												{m.streaming ? `분석 진행 · 최근 ${m.activities.length}개` : `명령어 ${m.activityCount}개 실행`}
											</summary>
											<div class="activityItems" aria-live={m.streaming ? 'polite' : 'off'}>
												{#each m.activities as activity (activity.id)}
													<div class="activityItem" class:error={activity.status === 'error'}>
														<span class:running={activity.status === 'running'}></span>
														<strong>{activity.passLabel ?? '실행'}</strong>
														<p>{activity.summary}</p>
													</div>
												{/each}
											</div>
										</details>
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
										<Markdown text={m.text} onrefclick={(refId) => evidencePanels[m.id]?.openRef(refId)} />
										{#if m.streaming}<span class="caret"></span>{/if}
									{/if}

									{#if m.error}
										<div class="err">⚠ 응답 오류: {m.error}</div>
									{/if}

									{#if m.refs.length}
										<Evidence
											bind:this={evidencePanels[m.id]}
											refs={m.refs}
											citedRefIds={m.quality?.citedRefIds ?? null}
											verifiedRefIds={m.verifiedRefIds}
											onverified={(refId) => markEvidenceVerified(m, refId)}
										/>
									{/if}
									{#if m.quality}
										<div class="qualityPanel" class:passed={m.quality.passed} role="status">
											<header>
												<strong>자동 답변 품질 검증</strong>
												<span>{m.quality.passed ? '통과' : '차단'} · {m.quality.contract === 'quantitative' ? '정량' : '문서'} · {m.quality.score}점</span>
											</header>
											<div class="coverageSummary">
												<span>답변 인용 {m.quality.citedRefIds.length}개</span>
												<span>Skill OS 조회 {m.runtimeCoverage?.readSkillCalls ?? m.quality.readSkillCalls ?? 0}회</span>
												{#if m.quality.contractIds.length}<span title={m.quality.contractIds.join('\n')}>적용 계약 {m.quality.contractIds.length}개</span>{/if}
											</div>
											{#if m.quality.requiredEvidence.length}
												<div class="requirements" aria-label="요구 근거">
													{#each m.quality.requiredEvidence as requirement (requirement)}
														<span>{evidenceLabel(requirement)}</span>
													{/each}
												</div>
											{/if}
											{#if m.quality.issues.length}
												<ul class="qualityIssues">
													{#each m.quality.issues as issue (issue)}<li>{issueLabel(issue)}</li>{/each}
												</ul>
											{/if}
										</div>
									{/if}

									{#if m.viewSpecs.length || m.artifacts.length}
										<div class="outputs" aria-label="분석 결과와 산출물">
											{#each m.viewSpecs as view (view.id)}
												<article class="outputCard">
													<span class="outputKind">시각 결과</span>
													<strong>{view.title}</strong>
													<small>{viewSpecSummary(view.spec)}{view.source ? ` · ${view.source}` : ''}</small>
												</article>
											{/each}
											{#each m.artifacts as artifact (artifact.id)}
												<article class="outputCard">
													<span class="outputKind">산출물</span>
													<strong>{artifactTitle(artifact.data)}</strong>
													{#if artifactHref(artifact.data)}
														<a href={artifactHref(artifact.data) ?? undefined} target="_blank" rel="noopener">열기</a>
													{:else}<small>런타임 세션에 보존됨</small>{/if}
												</article>
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
					onstop={() => store.cancel()}
				/>
			</div>
		</div>
	</main>
</div>

{#if runtimeOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="povl" role="presentation" onclick={closeRuntimeCenter}>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			id="runtime-center-dialog"
			class="pmodal"
			bind:this={runtimeDialog}
			role="dialog"
			aria-modal="true"
			aria-labelledby="runtime-center-title"
			tabindex="-1"
			onkeydown={trapRuntimeFocus}
			onclick={(e) => e.stopPropagation()}
		>
			<header class="pmhead">
				<h2 id="runtime-center-title">Agent Runtime Center</h2>
				<button class="pmx" onclick={closeRuntimeCenter} aria-label="닫기">✕</button>
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
	.runtimeBadge {
		display: inline-flex;
		align-items: center;
		border: 1px solid color-mix(in srgb, #70d6a5 35%, transparent);
		border-radius: 999px;
		padding: .24rem .55rem;
		color: #8de2b9;
		background: color-mix(in srgb, #70d6a5 8%, transparent);
		font-size: .68rem;
		white-space: nowrap;
	}
	.ghost {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.75rem;
		height: 2.75rem;
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
	.activityLog { border: 1px solid var(--dl-line, #2a2c33); border-radius: 9px; overflow: hidden; background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 45%, transparent); }
	.activityLog summary { min-height: 2.75rem; display: flex; align-items: center; padding: .45rem .65rem; color: var(--dl-ink-dim, #9aa0aa); font-size: .75rem; cursor: pointer; }
	.activityItems { display: grid; gap: .3rem; padding: .15rem .65rem .65rem; border-top: 1px solid var(--dl-line, #2a2c33); }
	.activityItem { display: grid; grid-template-columns: auto auto minmax(0, 1fr); gap: .4rem; align-items: baseline; padding-top: .4rem; color: var(--dl-ink-dim, #9aa0aa); font-size: .72rem; }
	.activityItem > span { width: .45rem; height: .45rem; border-radius: 50%; background: #70d6a5; }
	.activityItem > span.running { background: var(--dl-info, #6ab0ff); animation: pulse 1s ease-in-out infinite; }
	.activityItem.error > span { background: var(--dl-bad, #ff6b6b); }
	.activityItem strong { color: var(--dl-ink-mute, #6b7280); font-size: .65rem; }
	.activityItem p { margin: 0; min-width: 0; overflow-wrap: anywhere; }
	@keyframes pulse { 50% { opacity: .3; } }
	.runstate { min-height: 1.25rem; display: flex; align-items: center; }
	.runstate span { width: .9rem; height: .9rem; border: 2px solid var(--dl-line, #2a2c33); border-top-color: var(--dl-accent, #ff5a36); border-radius: 50%; animation: spin .8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
	.sideveil { display: none; }
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
	.qualityPanel { display: grid; gap: .55rem; padding: .7rem .8rem; border: 1px solid color-mix(in srgb, var(--dl-bad, #ff6b6b) 45%, var(--dl-line, #2a2c33)); border-radius: 9px; background: color-mix(in srgb, var(--dl-bad, #ff6b6b) 6%, transparent); }
	.qualityPanel.passed { border-color: color-mix(in srgb, #70d6a5 35%, var(--dl-line, #2a2c33)); background: color-mix(in srgb, #70d6a5 6%, transparent); }
	.qualityPanel header { display: flex; flex-wrap: wrap; align-items: center; gap: .45rem .75rem; }
	.qualityPanel header strong { color: var(--dl-ink, #e7e7ea); font-size: .78rem; }
	.qualityPanel header span { color: var(--dl-bad, #ff8c8c); font-size: .72rem; }
	.qualityPanel.passed header span { color: #70d6a5; }
	.coverageSummary, .requirements { display: flex; flex-wrap: wrap; gap: .35rem; }
	.coverageSummary span, .requirements span { padding: .18rem .42rem; border-radius: 5px; background: var(--dl-bg-raised, #16171a); color: var(--dl-ink-dim, #9aa0aa); font-size: .66rem; }
	.requirements span { border: 1px solid var(--dl-line, #2a2c33); }
	.qualityIssues { margin: 0; padding-left: 1.1rem; color: var(--dl-bad, #ff8c8c); font-size: .72rem; line-height: 1.5; }
	.outputs { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: .45rem; }
	.outputCard { min-width: 0; display: grid; gap: .25rem; padding: .7rem; border: 1px solid var(--dl-line, #2a2c33); border-radius: 9px; background: var(--dl-bg-raised, #16171a); }
	.outputCard .outputKind { width: fit-content; padding: .1rem .35rem; border-radius: 4px; background: color-mix(in srgb, var(--dl-info, #6ab0ff) 12%, transparent); color: var(--dl-info, #6ab0ff); font-size: .64rem; }
	.outputCard strong { color: var(--dl-ink, #e7e7ea); font-size: .78rem; overflow-wrap: anywhere; }
	.outputCard small { color: var(--dl-ink-mute, #6b7280); font-size: .68rem; overflow-wrap: anywhere; }
	.outputCard a { width: fit-content; min-height: 2.75rem; display: inline-flex; align-items: center; color: var(--dl-info, #6ab0ff); font-size: .72rem; }
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
		width: 2.75rem;
		height: 2.75rem;
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
	@media (max-width: 720px) {
		.runtimeBadge { display: none; }
		.shell :global(.sidebar) {
			position: fixed;
			inset: 0 auto 0 0;
			z-index: 70;
			box-shadow: 18px 0 45px rgba(0, 0, 0, 0.45);
		}
		.sideveil {
			display: block;
			position: fixed;
			inset: 0;
			z-index: 60;
			border: 0;
			background: rgba(0, 0, 0, 0.55);
		}
		.col { padding-inline: 0.85rem; }
		.user .bubble { max-width: 88%; }
		.chatSns { display: none !important; }
		.povl { padding: 0; align-items: stretch; }
		.pmodal { max-width: none; max-height: 100dvh; border-radius: 0; border-block: 0; }
		.pmhead { padding: .75rem .85rem .35rem; }
		.pmsub { padding: 0 .85rem .65rem; }
		.pmbody { padding: 0 .85rem .85rem; }
		.outputs { grid-template-columns: 1fr; }
	}
</style>
