<!--
	AI Provider 설정 모달 — provider 선택/검증, API key, OAuth, Ollama pull, 모델 선택.
	ui store에서 모든 상태를 읽고 메서드를 호출한다.
-->
<script>
	import { cn } from "$lib/utils.js";
	import {
		X, Loader2, Settings, Check, ExternalLink,
		Key, AlertCircle, CheckCircle2, Terminal, LogOut,
		Download
	} from "lucide-svelte";

	const { ui } = $props();

	let dialogEl = $state(null);

	$effect(() => {
		if (!ui.settingsOpen || !dialogEl) return;
		requestAnimationFrame(() => dialogEl?.focus());
	});

	// SSE cleanup on destroy
	$effect(() => {
		return () => ui.cleanupProfileEvents();
	});
</script>

{#if ui.settingsOpen}
	<div
		class="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) ui.settingsOpen = false; }}
		role="presentation"
	>
		<div
			bind:this={dialogEl}
			class="surface-overlay w-full max-w-xl bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden"
			role="dialog"
			aria-modal="true"
			aria-labelledby="settings-dialog-title"
			tabindex="-1"
		>
			<!-- Modal Header -->
			<div class="border-b border-dl-border/40 px-6 pt-5 pb-3">
				<div class="flex items-center justify-between">
					<div>
						<div id="settings-dialog-title" class="text-[14px] font-semibold text-dl-text">AI Provider 설정</div>
						<div class="mt-1 text-[11px] text-dl-text-dim">사용할 모델과 인증 상태를 한 곳에서 관리합니다.</div>
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

			<div class="px-6 pb-5 max-h-[70vh] overflow-y-auto">
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

								{#if needsOAuth && !info.available}
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
