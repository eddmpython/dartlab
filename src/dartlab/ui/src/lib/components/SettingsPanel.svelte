<!--
	AI Provider 설정 모달 — 탭 기반 2-panel 레이아웃.
	탭: AI 모델 / 공시 API / 채널
	ui store에서 모든 상태를 읽고 메서드를 호출한다.
-->
<script>
	import { cn } from "$lib/utils.js";
	import {
		X, Loader2, Check, ExternalLink,
		Key, AlertCircle, CheckCircle2, Terminal, LogOut,
		Download, MessageSquare, Radio
	} from "lucide-svelte";

	const { ui } = $props();

	let dialogEl = $state(null);

	$effect(() => {
		if (!ui.settingsOpen || !dialogEl) return;
		requestAnimationFrame(() => dialogEl?.focus());
	});

	$effect(() => {
		return () => ui.cleanupProfileEvents();
	});

	const OPEN_DART_SOURCE_LABELS = {
		env: "시스템 환경변수",
		dotenv: "프로젝트 .env",
		none: "미설정",
	};

	function openDartSourceLabel(source) {
		return OPEN_DART_SOURCE_LABELS[source] || source || "미설정";
	}

	const TABS = [
		{ id: "providers", label: "AI 모델", icon: Radio },
		{ id: "openDart", label: "공시 API", icon: Key },
		{ id: "channels", label: "채널", icon: MessageSquare },
	];

	function activeChannelCount() {
		if (!ui.channels) return 0;
		return Object.values(ui.channels).filter(c => c.running).length;
	}
</script>

{#if ui.settingsOpen}
	<div
		class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) ui.settingsOpen = false; }}
		role="presentation"
	>
		<div
			bind:this={dialogEl}
			class="surface-overlay w-full max-w-2xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden"
			role="dialog"
			aria-modal="true"
			aria-labelledby="settings-dialog-title"
			tabindex="-1"
		>
			<!-- Modal Header -->
			<div class="border-b border-dl-border/40 px-6 pt-5 pb-3">
				<div class="flex items-center justify-between">
					<div>
						<div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">설정</div>
						<div class="mt-1 text-[11px] text-dl-text-dim">AI provider, 공시 API, 외부 채널을 관리합니다.</div>
					</div>
					<button
						class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
						onclick={() => ui.settingsOpen = false}
						aria-label="설정 닫기"
					>
						<X size={18} />
					</button>
				</div>
			</div>

			<!-- 2-Panel: Tabs + Content -->
			<div class="flex" style="min-height: 420px; max-height: 70vh;">
				<!-- Left Tab Navigation -->
				<div class="w-[140px] flex-shrink-0 border-r border-dl-border/40 bg-dl-bg-darker/50 py-3 px-2 flex flex-col gap-1">
					{#each TABS as tab}
						{@const isActive = ui.settingsSection === tab.id}
						{@const channelCount = tab.id === "channels" ? activeChannelCount() : 0}
						<button
							class={cn(
								"flex items-center gap-2.5 w-full px-3 py-2.5 rounded-xl text-left text-[12px] transition-all",
								isActive
									? "bg-dl-primary/10 text-dl-primary-light font-medium border border-dl-primary/20"
									: "text-dl-text-dim hover:text-dl-text hover:bg-white/5 border border-transparent"
							)}
							onclick={() => ui.settingsSection = tab.id}
						>
							<tab.icon size={14} class={isActive ? "text-dl-primary-light" : "text-dl-text-dim"} />
							<span class="flex-1">{tab.label}</span>
							{#if channelCount > 0}
								<span class="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-dl-success/20 text-dl-success min-w-[18px] text-center">{channelCount}</span>
							{/if}
							{#if tab.id === "openDart" && ui.openDart.configured}
								<span class="w-1.5 h-1.5 rounded-full bg-dl-success flex-shrink-0"></span>
							{/if}
						</button>
					{/each}
				</div>

				<!-- Right Content Panel -->
				<div class="flex-1 overflow-y-auto px-5 py-4">

					<!-- ━━━ TAB: AI 모델 ━━━ -->
					{#if ui.settingsSection === "providers"}
						<div class="space-y-2.5">
							{#each Object.entries(ui.providers) as [name, info]}
								{@const isActive = name === ui.activeProvider}
								{@const isExpanded = ui.expandedProvider === name}
								{@const needsKey = info.auth === "api_key"}
								{@const needsCli = info.auth === "cli"}
								{@const needsOAuth = info.auth === "oauth"}
								{@const models = ui.providerModels[name] || []}
								{@const isModelsLoading = ui.modelsLoading[name]}
								<div class={cn(
									"rounded-xl border transition-all",
									isActive ? "border-dl-primary/40 bg-dl-primary/[0.03]" : "border-dl-border"
								)}>
									<!-- Provider header -->
									<button
										class="flex items-center gap-3 w-full px-4 py-3 text-left"
										onclick={() => {
											if (info.available) {
												if (name === ui.activeProvider) ui.toggleExpandProvider(name);
												else ui.selectProvider(name);
											} else if (needsKey || needsOAuth) {
												if (name === ui.activeProvider) ui.toggleExpandProvider(name);
												else ui.selectProvider(name);
											} else if (!info.checked) {
												ui.selectProvider(name);
											} else {
												ui.toggleExpandProvider(name);
											}
										}}
									>
										<span class={cn(
											"w-2.5 h-2.5 rounded-full flex-shrink-0",
											info.available ? "bg-dl-success" : needsKey ? "bg-amber-400" : "bg-dl-text-dim"
										)}></span>
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2">
												<span class="text-[13px] font-medium text-dl-text">{info.label || name}</span>
												{#if isActive}
													<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-primary/20 text-dl-primary-light">사용 중</span>
												{/if}
											</div>
											<div class="text-[11px] text-dl-text-dim mt-0.5">{info.desc || ""}</div>
											{#if info.credentialSource && info.auth !== "none"}
												<div class="text-[10px] text-dl-text-dim mt-1">credential: {info.credentialSource}</div>
											{/if}
										</div>
										<div class="flex items-center gap-2 flex-shrink-0">
											{#if info.available}
												<CheckCircle2 size={16} class="text-dl-success" />
											{:else if needsKey}
												<Key size={14} class="text-amber-400" />
												<span class="text-[10px] text-amber-400">인증 필요</span>
											{:else if needsOAuth}
												<Key size={14} class="text-amber-400" />
												<span class="text-[10px] text-amber-400">로그인 필요</span>
											{:else if needsCli && name === "codex" && ui.codexDetail.installed}
												<AlertCircle size={14} class="text-amber-400" />
												<span class="text-[10px] text-amber-400">인증 필요</span>
											{:else if needsCli && info.checked && !info.available}
												<Terminal size={14} class="text-dl-text-dim" />
												<span class="text-[10px] text-dl-text-dim">미설치</span>
											{/if}
										</div>
									</button>

									<!-- Expanded content -->
									{#if isExpanded || isActive}

										<!-- API Key input (not available) -->
										{#if needsKey && !info.available}
											<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
												<div class="text-[11px] text-dl-text-muted mb-2">
													{info.envKey ? `환경변수 ${info.envKey}로도 설정 가능합니다` : "API 키를 입력하세요"}
												</div>
												<div class="flex items-center gap-2">
													<input
														type="password"
														bind:value={ui.apiKeyInput}
														placeholder={name === "openai" ? "sk-..." : "API Key"}
														class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
														onkeydown={(e) => { if (e.key === 'Enter') ui.submitApiKey(); }}
													/>
													<button
														class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"
														onclick={() => ui.submitApiKey()}
														disabled={!ui.apiKeyInput.trim() || ui.apiKeyVerifying}
													>
														{#if ui.apiKeyVerifying}
															<Loader2 size={12} class="animate-spin" />
														{:else}
															<Key size={12} />
														{/if}
														인증
													</button>
												</div>
												{#if ui.apiKeyResult === "error"}
													<div class="flex items-center gap-1.5 mt-2 text-[11px] text-dl-primary-light">
														<AlertCircle size={12} />
														API 키가 유효하지 않습니다. 다시 확인해주세요.
													</div>
												{/if}
											</div>
										{/if}

										{#if needsOAuth && name !== "gemini" && !info.available}
											<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
												<div class="text-[12px] text-dl-text mb-2.5">ChatGPT OAuth 로그인이 필요합니다</div>
												<div class="text-[10px] text-dl-text-dim mb-2.5">
													Codex CLI 없이 브라우저 로그인으로 GPT 구독 모델을 `ask`/서버 공용 경로에서 사용합니다.
												</div>
												<button
													class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"
													onclick={() => ui.handleOauthCodexLogin()}
													disabled={ui.oauthLoginPending}
												>
													{#if ui.oauthLoginPending}
														<Loader2 size={12} class="animate-spin" />
													{:else}
														<Key size={12} />
													{/if}
													브라우저 로그인
												</button>
												{#if ui.oauthCodexDetail.tokenStored && !ui.oauthCodexDetail.authenticated}
													<div class="text-[10px] text-amber-400 mt-2">저장된 토큰이 있지만 현재는 유효하지 않습니다. 다시 로그인하세요.</div>
												{/if}
											</div>
										{/if}

										<!-- Gemini OAuth -->
										{#if name === "gemini" && !info.available}
											<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
												{#if !ui.geminiDetail.sdkInstalled}
													<div class="text-[12px] text-dl-text mb-2.5">google-genai 패키지가 필요합니다</div>
													<div class="text-[10px] text-dl-text-dim"><code class="px-1 py-0.5 rounded bg-dl-bg-darker">pip install dartlab[llm]</code></div>
												{:else if !ui.geminiDetail.clientSecretExists}
													<div class="text-[12px] text-dl-text mb-2.5">Google OAuth 설정 (최초 1회)</div>
													<div class="text-[10px] text-dl-text-dim mb-2">
														<a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener" class="text-dl-primary-light hover:underline">Google Cloud Console</a> → OAuth 2.0 Client ID (Desktop app) → JSON 다운로드 후 아래에 붙여넣기
													</div>
													<textarea
														bind:value={ui.geminiClientSecretInput}
														placeholder="Google Cloud Console에서 다운로드한 JSON 내용을 붙여넣기"
														rows="3"
														class="w-full bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[10px] text-dl-text placeholder:text-dl-text-dim/40 outline-none focus:border-dl-primary/50 transition-colors font-mono resize-none mt-1"
													></textarea>
													{#if ui.geminiClientSecretInput.trim()}
														<button
															class="mt-2 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors"
															onclick={() => ui.handleGeminiSaveClientSecret()}
														>
															<Key size={12} />
															설정 저장
														</button>
													{/if}
												{:else}
													<div class="text-[12px] text-dl-text mb-2.5">Google OAuth 로그인이 필요합니다</div>
													<div class="text-[10px] text-dl-text-dim mb-2.5">
														Google 계정으로 로그인하면 Gemini를 무료로 사용할 수 있습니다.
													</div>
													<button
														class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"
														onclick={() => ui.handleGeminiOauthLogin()}
														disabled={ui.geminiLoginPending}
													>
														{#if ui.geminiLoginPending}
															<Loader2 size={12} class="animate-spin" />
														{:else}
															<Key size={12} />
														{/if}
														Google 로그인
													</button>
												{/if}
											</div>
										{/if}
										{#if name === "gemini" && info.available}
											<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5">
												<div class="flex items-center gap-2">
													<CheckCircle2 size={13} class="text-dl-success" />
													<span class="text-[11px] text-dl-success">OAuth 인증됨</span>
													<span class="text-[10px] text-dl-text-dim">— Google 계정</span>
												</div>
												<button
													class="mt-2 text-[10px] text-dl-text-dim hover:text-dl-text transition-colors"
													onclick={() => ui.handleGeminiOauthLogout()}
												>
													로그아웃
												</button>
											</div>
										{/if}

										<!-- API Key authenticated -->
										{#if needsKey && info.available}
											<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5">
												<div class="flex items-center gap-2">
													<CheckCircle2 size={13} class="text-dl-success" />
													<span class="text-[11px] text-dl-success">인증됨</span>
													<span class="text-[10px] text-dl-text-dim">— 다른 키로 변경하려면 입력하세요</span>
												</div>
												<div class="flex items-center gap-2 mt-2">
													<input
														type="password"
														bind:value={ui.apiKeyInput}
														placeholder="새 API 키 (변경 시에만)"
														class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
														onkeydown={(e) => { if (e.key === 'Enter') ui.submitApiKey(); }}
													/>
													{#if ui.apiKeyInput.trim()}
														<button
															class="px-2.5 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] hover:bg-dl-primary/30 transition-colors disabled:opacity-40"
															onclick={() => ui.submitApiKey()}
															disabled={ui.apiKeyVerifying}
														>
															{#if ui.apiKeyVerifying}<Loader2 size={10} class="animate-spin" />{:else}변경{/if}
														</button>
													{/if}
												</div>
											</div>
										{/if}

										<!-- Ollama install guide -->
										{#if name === "ollama" && !ui.ollamaDetail.installed}
											<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
												<div class="text-[12px] text-dl-text mb-2">Ollama가 설치되어 있지 않습니다</div>
												<a
													href="https://ollama.com/download"
													target="_blank"
													rel="noopener noreferrer"
													class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/30 transition-colors"
												>
													<Download size={14} />
													Ollama 다운로드 (ollama.com)
													<ExternalLink size={10} class="ml-auto" />
												</a>
												<div class="text-[10px] text-dl-text-dim mt-2">설치 후 Ollama를 실행하고 새로고침하세요</div>
											</div>
										{:else if name === "ollama" && ui.ollamaDetail.installed && ui.ollamaDetail.checked && ui.ollamaDetail.running === false}
											<div class="px-4 pb-3 border-t border-dl-border/50 pt-3">
												<div class="flex items-center gap-2 text-[12px] text-amber-400">
													<AlertCircle size={14} />
													Ollama가 설치되었지만 실행되지 않고 있습니다
												</div>
												<div class="text-[10px] text-dl-text-dim mt-1">터미널에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">ollama serve</code>를 실행하세요</div>
											</div>
										{/if}

										<!-- CLI provider install guide -->
										{#if needsCli && !info.available}
											<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
												{#if name === "codex"}
													<div class="text-[12px] text-dl-text mb-2.5">
														{ui.codexDetail.installed ? "Codex CLI가 설치되었지만 로그인이 필요합니다" : "Codex CLI 설치가 필요합니다"}
													</div>
													<div class="space-y-2">
														{#if !ui.codexDetail.installed}
															<div class="flex items-start gap-2.5">
																<span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">1.</span>
																<div class="flex-1">
																	<div class="text-[10px] text-dl-text-dim mb-1">Node.js 설치 후 실행</div>
																	<div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">
																		npm install -g @openai/codex
																	</div>
																</div>
															</div>
														{/if}
														<div class="flex items-start gap-2.5">
															<span class="text-[10px] text-dl-text-dim mt-0.5 flex-shrink-0">{ui.codexDetail.installed ? "1." : "2."}</span>
															<div class="flex-1">
																<div class="text-[10px] text-dl-text-dim mb-1">브라우저 인증 (ChatGPT 계정)</div>
																<div class="p-2 rounded-lg bg-dl-bg-darker border border-dl-border text-[11px] text-dl-text-muted font-mono">
																	codex login
																</div>
															</div>
														</div>
													</div>
													{#if ui.codexDetail.loginStatus}
														<div class="text-[10px] text-dl-text-dim mt-2">{ui.codexDetail.loginStatus}</div>
													{/if}
													<div class="flex items-center gap-1.5 mt-2.5 px-2.5 py-2 rounded-lg bg-amber-500/5 border border-amber-500/20">
														<AlertCircle size={12} class="text-amber-400 flex-shrink-0" />
														<span class="text-[10px] text-amber-400/80">ChatGPT Plus 또는 Pro 구독이 필요합니다</span>
													</div>
												{/if}
												<div class="text-[10px] text-dl-text-dim mt-2">{ui.codexDetail.installed ? "로그인 완료 후 새로고침하세요" : "설치 완료 후 새로고침하세요"}</div>
											</div>
										{/if}

										<!-- Codex authenticated + logout -->
										{#if name === "codex" && info.available}
											<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5">
												<div class="flex items-center justify-between">
													<div class="flex items-center gap-2">
														<CheckCircle2 size={13} class="text-dl-success" />
														<span class="text-[11px] text-dl-success">ChatGPT 계정 인증됨</span>
													</div>
													<button
														class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"
														onclick={() => ui.handleCodexLogout()}
													>
														<LogOut size={11} />
														로그아웃
													</button>
												</div>
											</div>
										{/if}

										{#if name === "oauth-codex" && info.available}
											<div class="px-4 pb-2 border-t border-dl-border/50 pt-2.5">
												<div class="flex items-center justify-between">
													<div class="flex items-center gap-2">
														<CheckCircle2 size={13} class="text-dl-success" />
														<span class="text-[11px] text-dl-success">ChatGPT OAuth 인증됨</span>
														{#if ui.oauthCodexDetail.accountId}
															<span class="text-[10px] text-dl-text-dim">({ui.oauthCodexDetail.accountId})</span>
														{/if}
													</div>
													<button
														class="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:bg-white/5 transition-colors"
														onclick={() => ui.handleOauthCodexLogout()}
													>
														<LogOut size={11} />
														로그아웃
													</button>
												</div>
											</div>
										{/if}

										<!-- Model Selection -->
										{#if info.available || needsKey || needsCli || needsOAuth}
											<div class="px-4 pb-4 border-t border-dl-border/50 pt-3">
												<div class="flex items-center justify-between mb-2.5">
													<span class="text-[11px] font-medium text-dl-text-muted">모델 선택</span>
													{#if isModelsLoading}
														<Loader2 size={12} class="animate-spin text-dl-text-dim" />
													{/if}
												</div>

												{#if isModelsLoading && models.length === 0}
													<div class="flex items-center gap-2 py-3 text-[12px] text-dl-text-dim">
														<Loader2 size={14} class="animate-spin" />
														모델 목록 불러오는 중...
													</div>
												{:else if models.length > 0}
													<div class="flex flex-wrap gap-1.5">
														{#each models as model}
															<button
																class={cn(
																	"px-3 py-1.5 rounded-lg text-[11px] border transition-all",
																	model === ui.activeModel && isActive
																		? "border-dl-primary/50 bg-dl-primary/10 text-dl-primary-light font-medium"
																		: "border-dl-border text-dl-text-muted hover:border-dl-primary/30 hover:text-dl-text"
																)}
																onclick={() => {
																	if (name !== ui.activeProvider) ui.selectProvider(name);
																	ui.selectModel(model);
																}}
															>
																{model}
																{#if model === ui.activeModel && isActive}
																	<Check size={10} class="inline ml-1" />
																{/if}
															</button>
														{/each}
													</div>
												{:else}
													<div class="text-[11px] text-dl-text-dim py-2">사용 가능한 모델이 없습니다</div>
												{/if}

												<!-- Ollama model download -->
												{#if name === "ollama"}
													<div class="mt-3 pt-3 border-t border-dl-border/30">
														<div class="flex items-center justify-between mb-2">
															<span class="text-[11px] text-dl-text-muted">모델 다운로드</span>
															<a
																href="https://ollama.com/library"
																target="_blank"
																rel="noopener noreferrer"
																class="flex items-center gap-1 text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors"
															>
																전체 목록 <ExternalLink size={9} />
															</a>
														</div>

														{#if ui.isPulling}
															<div class="p-3 rounded-lg border border-dl-border bg-dl-bg-darker">
																<div class="flex items-center justify-between mb-1.5">
																	<span class="text-[11px] text-dl-text flex items-center gap-1.5">
																		<Loader2 size={12} class="animate-spin text-dl-primary-light" />
																		다운로드 중
																	</span>
																	<button
																		class="px-2 py-0.5 rounded text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors"
																		onclick={() => ui.cancelPull()}
																	>
																		취소
																	</button>
																</div>
																<div class="w-full h-1.5 rounded-full bg-dl-bg-dark overflow-hidden">
																	<div
																		class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-primary-light transition-all duration-300"
																		style="width: {ui.pullPercent}%"
																	></div>
																</div>
																<div class="text-[10px] text-dl-text-dim mt-1">{ui.pullProgress}</div>
															</div>
														{:else}
															<div class="flex items-center gap-1.5">
																<input
																	type="text"
																	bind:value={ui.pullModelName}
																	placeholder="모델명 (예: gemma3)"
																	class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-2.5 py-1.5 text-[11px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
																	onkeydown={(e) => { if (e.key === 'Enter') ui.startPullModel(); }}
																/>
																<button
																	class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"
																	onclick={() => ui.startPullModel()}
																	disabled={!ui.pullModelName.trim()}
																>
																	<Download size={12} />
																	받기
																</button>
															</div>

															<div class="mt-2.5 space-y-1">
																{#each ui.OLLAMA_MODELS as m}
																	{@const installed = models.some(i => i === m.name || i === m.name.split(":")[0])}
																	{#if !installed}
																		<button
																			class="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg border border-dl-border/50 text-left hover:border-dl-primary/30 hover:bg-white/[0.02] transition-all group"
																			onclick={() => { ui.pullModelName = m.name; ui.startPullModel(); }}
																		>
																			<div class="flex-1 min-w-0">
																				<div class="flex items-center gap-1.5">
																					<span class="text-[11px] font-medium text-dl-text">{m.name}</span>
																					<span class="px-1 py-px rounded text-[9px] bg-dl-bg-darker text-dl-text-dim">{m.size}</span>
																					{#if m.tag}
																						<span class="px-1 py-px rounded text-[9px] bg-dl-primary/15 text-dl-primary-light">{m.tag}</span>
																					{/if}
																				</div>
																				<div class="text-[10px] text-dl-text-dim mt-0.5">{m.desc}</div>
																			</div>
																			<div class="flex items-center gap-1.5 flex-shrink-0">
																				<span class="text-[9px] text-dl-text-dim">{m.gb} GB</span>
																				<Download size={12} class="text-dl-text-dim group-hover:text-dl-primary-light transition-colors" />
																			</div>
																		</button>
																	{/if}
																{/each}
															</div>
														{/if}
													</div>
												{/if}
											</div>
										{/if}
									{/if}
								</div>
							{/each}
						</div>

					<!-- ━━━ TAB: 공시 API ━━━ -->
					{:else if ui.settingsSection === "openDart"}
						<div class="space-y-4">
							<div class="flex items-center gap-2">
								<span class="text-[13px] font-medium text-dl-text">OpenDART API 키</span>
								{#if ui.openDart.configured}
									<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-success/15 text-dl-success">설정됨</span>
								{:else}
									<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-amber-500/15 text-amber-400">필요</span>
								{/if}
							</div>
							<div class="text-[11px] text-dl-text-dim">
								한국 최근 공시목록 조회와 공시 원문 읽기에 사용합니다. 예: 수주공시, 단일판매공급계약, 최근 공시 요약.
							</div>

							<div class="rounded-lg border border-dl-border/60 bg-dl-bg-darker px-3 py-3">
								<div class="flex items-center justify-between gap-3">
									<div>
										<div class="text-[11px] font-medium text-dl-text">처음 설정하는 방법</div>
										<div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim">
											1. OpenDART에서 API 키를 발급받습니다.
											<br />
											2. 아래 입력칸에 붙여넣고 `검증` 또는 `저장`을 누릅니다.
											<br />
											3. 저장 후 `최근 7일 수주공시 알려줘`처럼 바로 질문하면 됩니다.
										</div>
									</div>
									<a
										class="inline-flex items-center gap-1 rounded-lg border border-dl-border px-2.5 py-1.5 text-[10px] text-dl-text-dim hover:text-dl-text hover:border-dl-primary/30 transition-colors"
										href="https://opendart.fss.or.kr/intro/main.do"
										target="_blank"
										rel="noreferrer"
									>
										<ExternalLink size={11} />
										키 발급
									</a>
								</div>
							</div>

							<div class="grid gap-2 text-[11px]">
								<div class="flex items-center justify-between gap-3 rounded-lg border border-dl-border/60 bg-dl-bg-darker px-3 py-2">
									<span class="text-dl-text-dim">현재 적용 위치</span>
									<span class="text-dl-text">{openDartSourceLabel(ui.openDart.source)}</span>
								</div>
								<div class="flex items-center justify-between gap-3 rounded-lg border border-dl-border/60 bg-dl-bg-darker px-3 py-2">
									<span class="text-dl-text-dim">지금 바로 사용 가능</span>
									<span class="text-dl-text">{ui.openDart.configured ? "예" : "아니오"}</span>
								</div>
								<div class="flex items-center justify-between gap-3 rounded-lg border border-dl-border/60 bg-dl-bg-darker px-3 py-2">
									<span class="text-dl-text-dim">이 프로젝트에 저장 가능</span>
									<span class="text-dl-text">{ui.openDart.writable ? "예" : "아니오"}</span>
								</div>
								{#if ui.openDart.envPath}
									<div class="rounded-lg border border-dl-border/60 bg-dl-bg-darker px-3 py-2">
										<div class="text-dl-text-dim">저장 경로</div>
										<div class="mt-1 break-all text-dl-text">{ui.openDart.envPath}</div>
									</div>
								{/if}
							</div>

							{#if ui.openDart.source === "env"}
								<div class="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2">
									<AlertCircle size={12} class="mt-0.5 text-amber-400 flex-shrink-0" />
									<div class="text-[10px] text-amber-400/90">
										현재는 OS 환경변수의 DART 키가 우선 적용 중입니다. 아래 저장은 프로젝트 `.env`를 갱신하지만 실제 사용 키는 OS env가 계속 우선입니다.
									</div>
								</div>
							{/if}

							<div class="grid gap-2">
								<div class="flex items-center gap-2">
									<input
										type="password"
										bind:value={ui.dartKeyInput}
										placeholder="OpenDART API 키"
										class="flex-1 bg-dl-bg-darker border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
										onkeydown={(e) => { if (e.key === 'Enter') ui.validateDartKey(); }}
									/>
									<button
										class="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"
										onclick={() => ui.validateDartKey()}
										disabled={!ui.dartKeyInput.trim() || ui.dartKeyValidating}
									>
										{#if ui.dartKeyValidating}
											<Loader2 size={12} class="animate-spin" />
										{:else}
											<Check size={12} />
										{/if}
										검증
									</button>
									<button
										class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-dl-border text-[12px] text-dl-text-dim hover:text-dl-text hover:border-dl-primary/30 transition-colors disabled:opacity-40 flex-shrink-0"
										onclick={() => ui.submitDartKey()}
										disabled={!ui.dartKeyInput.trim() || ui.dartKeySaving}
									>
										저장
									</button>
								</div>
								{#if ui.dartKeyResult === "valid"}
									<div class="flex items-center gap-1.5 text-[11px] text-dl-success">
										<CheckCircle2 size={12} />
										유효한 키입니다. 저장하면 바로 사용됩니다.
									</div>
								{:else if ui.dartKeyResult === "saved"}
									<div class="flex items-center gap-1.5 text-[11px] text-dl-success">
										<CheckCircle2 size={12} />
										저장되었습니다.
									</div>
								{:else if ui.dartKeyResult === "invalid"}
									<div class="flex items-center gap-1.5 text-[11px] text-dl-primary-light">
										<AlertCircle size={12} />
										유효하지 않은 키입니다. 다시 확인해주세요.
									</div>
								{:else if ui.dartKeyResult === "error"}
									<div class="flex items-center gap-1.5 text-[11px] text-dl-primary-light">
										<AlertCircle size={12} />
										오류가 발생했습니다.
									</div>
								{/if}
							</div>

							{#if ui.openDart.configured}
								<div class="flex items-center justify-between rounded-lg border border-dl-border/60 bg-dl-bg-darker px-3 py-2">
									<div class="flex items-center gap-2">
										<CheckCircle2 size={13} class="text-dl-success" />
										<span class="text-[11px] text-dl-success">현재 키가 적용 중입니다</span>
									</div>
									<button
										class="text-[10px] text-dl-text-dim hover:text-dl-primary-light transition-colors"
										onclick={() => ui.removeDartKey()}
									>
										키 삭제
									</button>
								</div>
							{/if}

							<div class="rounded-lg border border-dl-border/60 bg-dl-bg-darker px-3 py-3">
								<div class="text-[11px] font-medium text-dl-text">예시 질문</div>
								<div class="mt-2 space-y-1 text-[10px] text-dl-text-dim">
									<div>`최근 7일 수주공시 알려줘`</div>
									<div>`이번 주 삼성전자 공시 뭐 있었어`</div>
									<div>`최근 2주 단일판매공급계약 공시 요약해줘`</div>
								</div>
							</div>
						</div>

					<!-- ━━━ TAB: 채널 ━━━ -->
					{:else if ui.settingsSection === "channels"}
						<div class="space-y-4">
							<div>
								<div class="flex items-center gap-2">
									<span class="text-[13px] font-medium text-dl-text">외부 채널 연결</span>
									<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-bg-darker text-dl-text-dim">세션 전용</span>
								</div>
								<div class="mt-1.5 text-[11px] text-dl-text-dim">
									Telegram / Slack / Discord 봇을 현재 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">dartlab ai</code> 서버 세션에 바로 연결합니다. 토큰은 UI에 저장하지 않습니다.
								</div>
							</div>

							<div class="space-y-3">
								{#each Object.entries(ui.channels) as [platform, info]}
									{@const isSlack = platform === "slack"}
									<div class="rounded-xl border border-dl-border/60 bg-dl-bg-darker/80 px-4 py-4">
										<div class="flex items-start justify-between gap-3">
											<div>
												<div class="flex items-center gap-2">
													<span class="text-[12px] font-medium text-dl-text">{info.label}</span>
													<span class={cn(
														"px-1.5 py-0.5 rounded text-[9px] font-semibold",
														info.running
															? "bg-dl-success/15 text-dl-success"
															: "bg-dl-border/40 text-dl-text-dim"
													)}>
														{info.running ? "연결됨" : "미연결"}
													</span>
												</div>
												<div class="mt-1 text-[10px] text-dl-text-dim">{info.description}</div>
												{#if info.error}
													<div class="mt-1 text-[10px] text-dl-primary-light">{info.error}</div>
												{/if}
											</div>
											<div class="text-[10px] text-dl-text-dim">
												{#if info.startedAt}
													실행 중
												{:else}
													대기
												{/if}
											</div>
										</div>

										<!-- 플랫폼별 토큰 발급 가이드 -->
										{#if !info.running}
											{#if platform === "telegram"}
												<div class="mt-3 rounded-lg border border-dl-primary/20 bg-dl-primary/[0.03] px-3 py-3">
													<div class="flex items-center gap-1.5 mb-2">
														<span class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-dl-success/15 text-dl-success">1분 완료</span>
														<span class="text-[11px] font-medium text-dl-text">가장 쉬운 방법</span>
													</div>
													<div class="space-y-2.5 text-[11px] text-dl-text-dim leading-relaxed">
														<div class="flex gap-2">
															<span class="text-dl-primary-light font-semibold flex-shrink-0">1</span>
															<div>
																휴대폰이나 PC에서 텔레그램을 열고, 상단 검색창에 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">BotFather</code>를 검색해서 대화를 시작하세요.
																<a href="https://t.me/BotFather" target="_blank" rel="noreferrer" class="ml-1 text-dl-primary-light hover:underline">바로가기</a>
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-primary-light font-semibold flex-shrink-0">2</span>
															<div>
																채팅창에 <code class="px-1.5 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted font-mono">/newbot</code>을 보내세요. BotFather가 봇 이름과 아이디를 물어봅니다. 아무거나 입력하면 됩니다.
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-primary-light font-semibold flex-shrink-0">3</span>
															<div>
																완료되면 BotFather가 긴 문자열을 하나 보내줍니다.<br />
																<code class="px-1.5 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted font-mono text-[10px]">123456789:ABCdefGHIjklMNOpqrsTUVwxyz</code><br />
																이게 토큰입니다. 복사해서 아래에 붙여넣고 <strong class="text-dl-text">연결</strong>을 누르세요.
															</div>
														</div>
													</div>
												</div>
											{:else if platform === "slack"}
												<div class="mt-3 rounded-lg border border-dl-border/40 bg-dl-bg-dark/50 px-3 py-3">
													<div class="text-[11px] font-medium text-dl-text mb-2">설정 방법 (5분)</div>
													<div class="space-y-2.5 text-[11px] text-dl-text-dim leading-relaxed">
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">1</span>
															<div>
																<a href="https://api.slack.com/apps" target="_blank" rel="noreferrer" class="text-dl-primary-light hover:underline">api.slack.com/apps</a>에 접속 → <strong class="text-dl-text">Create New App</strong> → From scratch 선택 → 앱 이름과 워크스페이스를 고릅니다.
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">2</span>
															<div>
																왼쪽 메뉴 <strong class="text-dl-text">Socket Mode</strong> → Enable 켜기 → 토큰 이름 아무거나 입력하면 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted font-mono">xapp-...</code>으로 시작하는 App 토큰이 나옵니다. 복사하세요.
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">3</span>
															<div>
																왼쪽 메뉴 <strong class="text-dl-text">OAuth & Permissions</strong> → Scopes에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">chat:write</code>, <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">app_mentions:read</code> 추가 → 상단 <strong class="text-dl-text">Install to Workspace</strong> → <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted font-mono">xoxb-...</code>로 시작하는 Bot 토큰을 복사하세요.
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">4</span>
															<div>아래 두 칸에 각각 붙여넣고 <strong class="text-dl-text">연결</strong>을 누르세요.</div>
														</div>
													</div>
												</div>
											{:else if platform === "discord"}
												<div class="mt-3 rounded-lg border border-dl-border/40 bg-dl-bg-dark/50 px-3 py-3">
													<div class="text-[11px] font-medium text-dl-text mb-2">설정 방법 (5분)</div>
													<div class="space-y-2.5 text-[11px] text-dl-text-dim leading-relaxed">
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">1</span>
															<div>
																<a href="https://discord.com/developers/applications" target="_blank" rel="noreferrer" class="text-dl-primary-light hover:underline">discord.com/developers</a>에 접속 → <strong class="text-dl-text">New Application</strong> → 이름을 정합니다.
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">2</span>
															<div>
																왼쪽 메뉴 <strong class="text-dl-text">Bot</strong> → <strong class="text-dl-text">Reset Token</strong> 클릭 → 나온 토큰을 복사하세요. 같은 페이지 아래쪽 <strong class="text-dl-text">Message Content Intent</strong>를 켜 주세요.
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">3</span>
															<div>
																왼쪽 메뉴 <strong class="text-dl-text">OAuth2</strong> → URL Generator에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">bot</code> 체크 → Permissions에서 <code class="px-1 py-0.5 rounded bg-dl-bg-darker text-dl-text-muted">Send Messages</code> 체크 → 생성된 URL로 접속해서 서버에 봇을 추가하세요.
															</div>
														</div>
														<div class="flex gap-2">
															<span class="text-dl-text font-semibold flex-shrink-0">4</span>
															<div>아래에 토큰을 붙여넣고 <strong class="text-dl-text">연결</strong>을 누르세요.</div>
														</div>
													</div>
												</div>
											{/if}
										{/if}

										<div class="mt-3 grid gap-2">
											{#if isSlack}
												<input
													type="password"
													value={ui.channelInputs.slack?.botToken || ""}
													placeholder="Bot token (xoxb-...)"
													class="w-full bg-dl-bg-dark border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
													oninput={(e) => ui.setChannelInput("slack", "botToken", e.currentTarget.value)}
												/>
												<input
													type="password"
													value={ui.channelInputs.slack?.appToken || ""}
													placeholder="App token (xapp-...)"
													class="w-full bg-dl-bg-dark border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
													oninput={(e) => ui.setChannelInput("slack", "appToken", e.currentTarget.value)}
												/>
											{:else}
												<input
													type="password"
													value={ui.channelInputs[platform]?.token || ""}
													placeholder={platform === "telegram" ? "BotFather 토큰 (123456:ABC-DEF...)" : platform === "discord" ? "Bot token" : `${info.label} token`}
													class="w-full bg-dl-bg-dark border border-dl-border rounded-lg px-3 py-2 text-[12px] text-dl-text placeholder:text-dl-text-dim outline-none focus:border-dl-primary/50 transition-colors"
													oninput={(e) => ui.setChannelInput(platform, "token", e.currentTarget.value)}
												/>
											{/if}
										</div>

										<div class="mt-3 flex items-center justify-end gap-2">
											<button
												class="px-3 py-2 rounded-lg border border-dl-border text-[11px] text-dl-text-dim hover:text-dl-text hover:border-dl-primary/30 transition-colors disabled:opacity-40"
												onclick={() => ui.stopChannel(platform)}
												disabled={!info.running || ui.channelBusy[platform]}
											>
												{#if ui.channelBusy[platform]}<Loader2 size={12} class="animate-spin inline-block mr-1" />{/if}종료
											</button>
											<button
												class="px-3 py-2 rounded-lg bg-dl-primary/20 text-dl-primary-light text-[11px] font-medium hover:bg-dl-primary/30 transition-colors disabled:opacity-40"
												onclick={() => ui.startChannel(platform)}
												disabled={ui.channelBusy[platform]}
											>
												{#if ui.channelBusy[platform]}<Loader2 size={12} class="animate-spin inline-block mr-1" />{/if}연결
											</button>
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			</div>

			<!-- Modal Footer -->
			<div class="flex items-center justify-between px-6 py-3 border-t border-dl-border">
				<div class="text-[10px] text-dl-text-dim">
					{#if ui.activeProvider && ui.activeModel}
						현재: {ui.providers[ui.activeProvider]?.label || ui.activeProvider} / {ui.activeModel}
					{:else if ui.activeProvider}
						현재: {ui.providers[ui.activeProvider]?.label || ui.activeProvider}
					{/if}
				</div>
				<button
					class="px-4 py-2 rounded-xl bg-dl-primary/20 text-dl-primary-light text-[12px] font-medium hover:bg-dl-primary/30 transition-colors"
					onclick={() => ui.settingsOpen = false}
				>
					닫기
				</button>
			</div>
		</div>
	</div>
{/if}
