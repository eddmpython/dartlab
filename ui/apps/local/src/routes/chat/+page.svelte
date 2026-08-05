<script lang="ts">
	// 로컬 챗. 옛 React ui/web 챗 GUI(ChatGPT 양식: 사이드바 대화이력 + 아바타 + 마크다운 + 둥근 composer)를
	// Svelte 로 옮긴 것. AiPort.streamAsk(mode:'chat') 한 포트로 대화(터미널 모드와 같은 Ask engine 계약).
	import { onMount, tick } from 'svelte';
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { isKrStockCode, normalizeKrCode } from '@dartlab/ui-contracts';
	import { getLocalRuntime } from '$lib/runtime/localRuntime';
	import { ChatStore, messageText, type ChatMessage, type MessagePart } from '$lib/chat/chatStore.svelte';
	import { toolLabel } from '$lib/chat/toolLabels';
	import Sidebar from '$lib/chat/Sidebar.svelte';
	import Composer from '$lib/chat/Composer.svelte';
	import Markdown from '$lib/chat/Markdown.svelte';
	import ToolCard from '$lib/chat/ToolCard.svelte';
	import ThinkingPanel from '$lib/chat/ThinkingPanel.svelte';
	import Evidence from '$lib/chat/Evidence.svelte';
	import VerificationBadge from '$lib/chat/VerificationBadge.svelte';
	import Settings from '$lib/chat/Settings.svelte';
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
		'삼성전자 005930, 현재 투자 논지와 가장 강한 반대논지를 같이 분석해줘',
		'삼성전자와 SK하이닉스 중 어느 쪽이 나은지 성장·가치·리스크로 비교해줘',
		'삼성전자 최근 5년 실적 변화가 일시적인지 구조적인지 검증해줘',
		'코스피에서 ROE가 높고 부채가 낮은 후보를 찾고 함정까지 걸러줘'
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
	const activeRuntimeLabel = $derived(
		active?.runtimeId
			? active.runtimeId === cap?.runtimeId
				? cap.providerLabel ?? active.runtimeId
				: active.runtimeId
			: cap?.providerLabel
	);
	// 연결 = 설치형 agent CLI가 실제 사용 가능. 아니면 Runtime Center 안내.
	const connected = $derived(cap?.tier === 'advanced' || cap?.tier === 'onDevice');

	// 스트리밍·새 메시지마다 하단 고정. 사용자가 위로 스크롤했으면(200px 밖) 건드리지 않는다.
	// 시간축이라 마지막 part 의 길이·상태가 바뀔 때도 따라가야 한다.
	$effect(() => {
		messages.length;
		const lastMessage = messages.at(-1);
		lastMessage?.parts.length;
		const tail = lastMessage?.parts.at(-1);
		if (tail?.kind === 'text' || tail?.kind === 'thinking') tail.text.length;
		else if (tail?.kind === 'tool') tail.status;
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
		date_evidence_unavailable: '기준일을 확인할 수 없음',
		claim_cell_coverage_incomplete: '대상·지표·기간 조합 근거 일부 누락',
		derived_evidence_lineage_missing: '계산 결과의 원본 근거 계보 누락'
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

	// 과정은 전부 보인다. 예전에는 7개 도구만 통과시켜 ReadSkill·EngineCall 같은 실제
	// 분석 경로가 화면에서 통째로 빠졌다. 도구는 접힌 한 줄로 놓이므로 노출해도
	// 소음이 되지 않는다. 내부 전용 도구만 감춘다.
	const HIDDEN_TOOL_CARDS = new Set(['RequestUserInput', 'LookAheadGuard', 'EvidenceGate']);

	function showToolCard(name: string): boolean {
		return !HIDDEN_TOOL_CARDS.has(name);
	}

	/** 화면에 놓을 시간축. 내부 전용 도구만 빼고 도착 순서는 그대로 둔다. */
	function timeline(message: ChatMessage): MessagePart[] {
		return message.parts.filter((part) => part.kind !== 'tool' || showToolCard(part.name));
	}

	/** 검수 제어면이 잡을 이름. 마지막 답변에만 붙여 qa id 중복을 만들지 않는다. */
	function partQaId(message: ChatMessage, part: MessagePart, index: number): string | null {
		if (message.id !== messages.at(-1)?.id) return null;
		return `chat-part-${index}-${part.kind}`;
	}

	/**
	 * 진행 표시는 화면에 하나뿐이다. 도구가 돌고 있으면 그 카드가 진행을 말하고,
	 * 사고가 흐르고 있으면 사고 줄이 말하고, 본문을 쓰는 중이면 캐럿이 말한다.
	 * 셋 다 아닐 때만 꼬리에 스피너 한 줄을 둔다.
	 */
	function showLiveRow(message: ChatMessage): boolean {
		if (!message.streaming) return false;
		if (message.parts.some((part) => part.kind === 'tool' && part.status === 'running')) return false;
		const tail = message.parts.at(-1);
		if (tail?.kind === 'thinking' && tail.endedAt === null) return false;
		if (tail?.kind === 'text' && tail.text.trim()) return false;
		return true;
	}

	/** 진행 표시를 맡은 도구 하나. 병렬 실행이면 먼저 시작한 것이 맡는다. */
	function liveToolId(message: ChatMessage): string | null {
		const running = message.parts.find((part) => part.kind === 'tool' && part.status === 'running');
		return running?.id ?? null;
	}

	/** 진행 줄 문구. 마지막 상태 줄을 쓰고, 없으면 마지막 도구 이름을 쓴다. */
	function liveLabel(message: ChatMessage): string {
		for (let index = message.parts.length - 1; index >= 0; index -= 1) {
			const part = message.parts[index];
			if (part.kind === 'activity') return part.summary;
			if (part.kind === 'tool') return toolLabel(part.name);
		}
		return '분석을 시작합니다';
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

<div class="shell" data-qa="chat-shell" inert={runtimeOpen}>
	{#if sidebarOpen}
		<button class="sideveil" data-qa="sidebar-veil" aria-label="사이드바 닫기" onclick={() => (sidebarOpen = false)}></button>
		<Sidebar {store} />
	{/if}

	<main class="main">
		<div class="topstrip">
			<button class="ghost" data-qa="sidebar-toggle" onclick={() => (sidebarOpen = !sidebarOpen)} aria-label="사이드바 토글" aria-expanded={sidebarOpen} title="사이드바">
				<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /></svg>
			</button>
			<div class="spacer"></div>
			<a class="ghost" data-qa="terminal-link" href={`${base}/terminal/${recent}`} title="터미널로" aria-label="터미널로">
				<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17l6-6-6-6M12 19h8" /></svg>
			</a>
			<button
				class="ghost runtimeGear"
				class:linked={connected}
				data-qa="runtime-center-open"
				bind:this={runtimeTrigger}
				onclick={openRuntimeCenter}
				title={activeRuntimeLabel ? `${activeRuntimeLabel} 연결됨` : '런타임 설정'}
				aria-label={activeRuntimeLabel ? `${activeRuntimeLabel} 연결됨. 런타임 설정 열기` : '런타임 설정'}
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
				<span>투자 분석 런타임을 한 번 연결하면 이 대화에서 계속 사용할 수 있습니다.</span>
				<button onclick={openRuntimeCenter}>설치·연결 시작</button>
			</div>
		{/if}

		<div class="stream" data-qa="chat-stream" bind:this={scroller}>
			<div class="col">
				{#if !hasMessages}
					<div class="welcome" data-qa="chat-welcome">
						<img class="ava" src="{base}/avatar.png" alt="DartLab" width="56" height="56" />
						<h1>투자 판단에 필요한 질문을 해보세요</h1>
						<p>결론만 단정하지 않습니다. 핵심 논지와 반대 근거, 가격에 반영된 기대, 판단이 바뀌는 조건까지 같은 근거로 연결합니다.</p>
						<div class="chips">
							{#each suggestions as s, index (s)}
								<button class="chip" data-qa={`chat-suggestion-${index}`} onclick={() => ask(s)}>{s}</button>
							{/each}
						</div>
					</div>
				{:else}
					{#each messages as m (m.id)}
						{#if m.role === 'user'}
							<div class="turn user">
								<div class="bubble">{messageText(m)}</div>
							</div>
						{:else}
							<!--
								시간축 본문. 이벤트가 도착한 순서 그대로 렌더한다. 도구 요약을 본문 위에
								몰아 두면 도구가 언제 불렸는지가 사라지므로 한 줄로 끼워 넣는다.
							-->
							{@const parts = timeline(m)}
							{@const liveTool = liveToolId(m)}
							<div class="turn assistant">
								<img class="msgava" src="{base}/avatar.png" alt="DartLab" width="30" height="30" />
								<div class="body">
									{#if m.conversationGuide}
										<div
											class="analysisFrame"
											class:running={m.streaming}
											data-qa={m.id === messages.at(-1)?.id ? 'analysis-conversation-frame' : undefined}
										>
											<span>{m.conversationGuide.label}</span>
											<strong>{m.conversationGuide.decisionGoal}</strong>
											{#if m.streaming}
												<div class="analysisStages" aria-label="예정된 분석 단계">
													{#each m.conversationGuide.stages as stage (stage)}<small>{stage}</small>{/each}
												</div>
											{/if}
										</div>
									{/if}
									{#each parts as part, partIndex (part.id)}
										{#if part.kind === 'text'}
											<div class="textpart" data-qa={partQaId(m, part, partIndex) ?? undefined}>
												<Markdown text={part.text} onrefclick={(refId) => evidencePanels[m.id]?.openRef(refId)} />
												{#if m.streaming && partIndex === parts.length - 1}<span class="caret"></span>{/if}
											</div>
										{:else if part.kind === 'tool'}
											<ToolCard tool={part} qaId={partQaId(m, part, partIndex)} live={part.id === liveTool} />
										{:else if part.kind === 'thinking'}
											<ThinkingPanel {part} qaId={partQaId(m, part, partIndex)} />
										{:else}
											<div
												class="actline"
												class:err={part.status === 'error'}
												data-qa={partQaId(m, part, partIndex) ?? undefined}
											>
												{part.summary}
											</div>
										{/if}
									{/each}

									{#if showLiveRow(m)}
										<div
											class="runstate"
											role="status"
											data-qa={m.id === messages.at(-1)?.id ? 'chat-live-status' : undefined}
										>
											<span class="spin" aria-hidden="true"></span>
											<span class="now">{liveLabel(m)}</span>
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

									<!-- 실패는 위 오류 블록이 이미 말한다. 뱃지가 같은 말을 반복하면 빨간 벽이 둘이 된다. -->
								{#if !m.streaming && m.verificationStatus && m.verificationStatus !== 'failed' && !m.error}
										<VerificationBadge
											status={m.verificationStatus}
											evidenceCount={m.evidenceCount}
											notes={m.verificationNotes}
										/>
									{/if}

									{#if m.error}
										<div class="err" role="alert">
											<div class="errText">
												<strong>분석을 완료하지 못했습니다</strong>
												<span>{m.error}</span>
											</div>
											<button onclick={() => store.retry(m.id)} disabled={store.busy}>다시 시도</button>
										</div>
									{/if}

									{#if m.refs.length}
										<Evidence
											bind:this={evidencePanels[m.id]}
											refs={m.refs}
											citedRefIds={m.quality?.citedRefIds ?? null}
											candidateRefIds={m.candidateRefIds}
											verifiedRefIds={m.verifiedRefIds}
											onverified={(refId) => markEvidenceVerified(m, refId)}
										/>
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
											<strong>다음 분석</strong>
											{#each m.suggested as s (s)}
												<button class="sug" onclick={() => ask(s)} disabled={store.busy}>{s}</button>
											{/each}
										</div>
									{/if}

									{#if !m.streaming && messageText(m)}
										<div class="msgacts">
											<button class="msgact" onclick={() => copyMsg(m.id, messageText(m))} title="복사">
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
	<div class="povl" data-qa="runtime-center-overlay" role="presentation" onclick={closeRuntimeCenter}>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			id="runtime-center-dialog"
			class="pmodal"
			data-qa="runtime-center-dialog"
			bind:this={runtimeDialog}
			role="dialog"
			aria-modal="true"
			aria-labelledby="runtime-center-title"
			tabindex="-1"
			onkeydown={trapRuntimeFocus}
			onclick={(e) => e.stopPropagation()}
		>
			<header class="pmhead">
				<h2 id="runtime-center-title">설정</h2>
				<button class="pmx" data-qa="runtime-center-close" onclick={closeRuntimeCenter} aria-label="닫기">
					<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12" /></svg>
				</button>
			</header>
			<div class="pmbody">
				<Settings onChange={() => store.loadCapabilities()} />
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
	/* 상단 크롬은 조용하다. 런타임 상태는 전문용어 칩 대신 설정 아이콘의 점 하나로
	   말한다(운영자 지적: "근거 게이트가 뭐지"). 상세는 Runtime Center 가 소유한다. */
	.ghost {
		position: relative;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.25rem;
		height: 2.25rem;
		border: none;
		border-radius: 8px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		cursor: pointer;
		transition: color .12s ease, background .12s ease;
	}
	.runtimeGear.linked::after {
		content: '';
		position: absolute;
		right: .34rem;
		top: .34rem;
		width: .34rem;
		height: .34rem;
		border-radius: 50%;
		background: #70d6a5;
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
	.notice button {
		min-height: 2.25rem;
		border: 1px solid color-mix(in srgb, var(--dl-warn, #f4b740) 55%, transparent);
		border-radius: 7px;
		background: color-mix(in srgb, var(--dl-warn, #f4b740) 12%, transparent);
		color: var(--dl-accent, #ff5a36);
		font-weight: 600;
		white-space: nowrap;
		cursor: pointer;
	}
	.notice button:hover {
		background: color-mix(in srgb, var(--dl-warn, #f4b740) 20%, transparent);
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
		max-width: 34rem;
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
		max-width: 21rem;
		padding: 0.6rem 0.8rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 10px;
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.8rem;
		line-height: 1.35;
		text-align: left;
		cursor: pointer;
	}
	.chip:hover {
		border-color: var(--dl-accent, #ff5a36);
		color: var(--dl-ink, #e7e7ea);
	}

	/* 메시지 */
	/* 읽기 리듬은 데스크탑 챗 앱 규범을 따른다. 질문은 오른쪽 말풍선, 답변은 말풍선
	   없이 열 전체를 쓰고 행간을 넉넉히 준다. 답변이 주인공이고 나머지는 배경이다. */
	.turn {
		display: flex;
		margin: 1.6rem 0;
	}
	.turn.user {
		justify-content: flex-end;
	}
	.user .bubble {
		max-width: 78%;
		padding: 0.65rem 0.95rem;
		border-radius: 1.15rem;
		background: var(--dl-bg-raised, #16171a);
		border: 1px solid var(--dl-line, #2a2c33);
		font-size: 0.94rem;
		line-height: 1.6;
		white-space: pre-wrap;
		word-break: break-word;
	}
	.turn.assistant {
		gap: 0.75rem;
		align-items: flex-start;
	}
	.msgava {
		flex-shrink: 0;
		border-radius: 9px;
		margin-top: 0.15rem;
	}
	.body {
		min-width: 0;
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		font-size: 0.95rem;
		line-height: 1.72;
	}
	.analysisFrame {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		align-items: baseline;
		gap: .35rem .65rem;
		padding: .55rem .7rem;
		border-left: 2px solid #70d6a5;
		background: color-mix(in srgb, #70d6a5 5%, transparent);
	}
	.analysisFrame > span {
		padding: .15rem .38rem;
		border-radius: 999px;
		background: color-mix(in srgb, #70d6a5 12%, transparent);
		color: #8de2b9;
		font-size: .65rem;
		white-space: nowrap;
	}
	.analysisFrame > strong { color: var(--dl-ink, #e7e7ea); font-size: .76rem; line-height: 1.45; }
	.analysisStages { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: .3rem; }
	.analysisStages small { color: var(--dl-ink-mute, #6b7280); font-size: .64rem; }
	.analysisStages small:not(:last-child)::after { content: '→'; margin-left: .3rem; color: var(--dl-line-strong, #3b3e46); }
	@keyframes pulse { 50% { opacity: .3; } }
	/* 화면에 도는 스피너는 이 줄 하나뿐이다. 도구가 돌면 도구 카드가 대신 말하고
	   이 줄은 그리지 않는다(showLiveRow). 높이를 한 줄로 고정해 사라질 때 덜 흔들린다. */
	.runstate { min-height: 1.25rem; display: flex; align-items: center; gap: .45rem; font-size: .78rem; }
	.runstate .spin { flex: none; width: .8rem; height: .8rem; border: 2px solid var(--dl-line, #2a2c33); border-top-color: var(--dl-accent, #ff5a36); border-radius: 50%; animation: spin .8s linear infinite; }
	.runstate .now { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--dl-ink-dim, #9aa0aa); }
	@keyframes spin { to { transform: rotate(360deg); } }
	/* 상태 한 줄. 도구 카드보다 가벼운 배경 정보라 들여쓰기 없이 흐린 글씨만 쓴다. */
	.actline { font-size: .74rem; line-height: 1.6; color: var(--dl-ink-mute, #6b7280); overflow-wrap: anywhere; }
	.actline.err { color: #ff8c8c; }
	.textpart { min-width: 0; }
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
	/* 오류는 벽이 아니라 상태다. 데스크탑 앱은 실패를 붉은 판때기로 덮지 않고
	   한 줄 제목 + 사유 + 행동 하나로 조용히 말한다(운영자 지적: 빨간 벽 2개). */
	.err {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: .9rem;
		padding: .7rem .85rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-left: 2px solid color-mix(in srgb, var(--dl-bad, #ff6b6b) 65%, transparent);
		border-radius: 9px;
		background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 60%, transparent);
		font-size: 0.8rem;
		color: var(--dl-ink-dim, #9aa0aa);
	}
	.errText { display: grid; gap: .15rem; min-width: 0; }
	.errText strong { color: var(--dl-ink, #e7e7ea); font-size: .82rem; font-weight: 600; }
	.errText span { overflow-wrap: anywhere; }
	.err button {
		min-height: 2rem;
		flex-shrink: 0;
		padding: 0 .8rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 7px;
		background: transparent;
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: .76rem;
		cursor: pointer;
	}
	.err button:hover:not(:disabled) { border-color: var(--dl-ink-mute, #6b7280); color: var(--dl-ink, #e7e7ea); }
	.err button:disabled { opacity: .5; cursor: default; }
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
	/* 설정 창. 데스크탑 앱 규범: 넓은 폭, 흐린 배경, 부드러운 깊이. */
	.povl {
		position: fixed;
		inset: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.55);
		backdrop-filter: blur(3px);
		padding: 1.25rem;
	}
	.pmodal {
		width: 100%;
		max-width: 46rem;
		max-height: 86vh;
		display: flex;
		flex-direction: column;
		background: var(--dl-bg-base, #0f0f10);
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 14px;
		box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
		overflow: hidden;
	}
	.pmhead {
		display: flex;
		align-items: center;
		gap: .5rem;
		padding: .85rem 1rem .85rem 1.25rem;
		border-bottom: 1px solid var(--dl-line, #2a2c33);
	}
	.pmhead h2 {
		font-size: .95rem;
		font-weight: 600;
		margin: 0;
		letter-spacing: -0.01em;
	}
	.pmx {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.9rem;
		height: 1.9rem;
		border: none;
		border-radius: 7px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		cursor: pointer;
	}
	.pmx:hover {
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
	}
	.pmbody {
		overflow: hidden;
		padding: 1rem 1.25rem 1.25rem;
	}
	.suggest > strong { width: 100%; color: var(--dl-ink-mute, #6b7280); font-size: .68rem; font-weight: 600; }
	@media (max-width: 720px) {
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
		.analysisFrame { grid-template-columns: 1fr; }
		.analysisStages { display: none; }
		.err { align-items: stretch; flex-direction: column; }
		.user .bubble { max-width: 88%; }
		.chatSns { display: none !important; }
		.povl { padding: 0; align-items: stretch; }
		.pmodal { max-width: none; max-height: 100dvh; border-radius: 0; border-block: 0; }
		.pmhead { padding: .75rem .85rem .35rem; }
		.pmbody { padding: 0 .85rem .85rem; }
		.outputs { grid-template-columns: 1fr; }
	}
</style>
