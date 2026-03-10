<!--
	[최우선 UX 원칙] 데이터 투명성 — 절대 제거 금지

	LLM이 보는 모든 데이터는 UI에서 실시간으로 뱃지/태그로 표시해야 한다.
	시스템이 LLM에 제공하는 데이터(컨텍스트, 모듈, 시스템프롬프트)는 반드시 사용자에게 보여야 한다.

	SSE 이벤트 흐름과 UI 표시:
	  meta          → 회사 뱃지, 연도 범위 뱃지, includedModules
	  snapshot      → 핵심 수치 카드 (클릭 시 원본 JSON)
	  context       → 모듈별 데이터 뱃지 (클릭 시 원문/렌더링 모달)
	  system_prompt → "시스템 프롬프트" 버튼 (클릭 시 전문 확인)
	  tool_call     → 도구 호출 뱃지
	  tool_result   → 도구 결과 (toolEvents에 누적)
	  chunk         → 응답 텍스트 스트리밍
	  done          → 완료 (duration, 토큰 추정, 재생성 버튼)

	하단 메타: 응답 시간, 추정 토큰(입력↑/출력↓), 시스템 프롬프트, LLM 입력 전문
-->
<script>
	import { cn } from "$lib/utils.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import {
		Database, X, FileText, Code, Wrench, Loader2,
		AlertTriangle, Clock, Brain,
		RefreshCw
	} from "lucide-svelte";

	let { message, onRegenerate } = $props();
	let openModal = $state(null);
	let modalType = $state("context");
	let contextTab = $state("raw");

	let loadingPhase = $derived.by(() => {
		if (!message.loading) return "";
		if (message.text) return "응답 작성 중";
		if (message.toolEvents?.length > 0) {
			const lastCall = [...message.toolEvents].reverse().find(e => e.type === "call");
			const detail = lastCall?.arguments?.module || lastCall?.arguments?.keyword || "";
			return `도구 실행 중 — ${lastCall?.name || ""}${detail ? ` (${detail})` : ""}`;
		}
		if (message.contexts?.length > 0) {
			const last = message.contexts[message.contexts.length - 1];
			return `데이터 분석 중 — ${last?.label || last?.module || ""}`;
		}
		if (message.snapshot) return "핵심 수치 확인 완료, 데이터 검색 중";
		if (message.meta?.company) return `${message.meta.company} 데이터 검색 중`;
		if (message.meta?.includedModules) return "분석 모듈 선택 완료";
		return "생각 중";
	});

	let companyName = $derived(message.company || message.meta?.company || null);

	let hasTransparencyData = $derived(
		message.systemPrompt || message.contexts?.length > 0 || message.meta?.includedModules
	);

	let dataYearRange = $derived.by(() => {
		const raw = message.meta?.dataYearRange;
		if (!raw) return null;
		if (typeof raw === "string") return raw;
		if (raw.min_year && raw.max_year) return `${raw.min_year}~${raw.max_year}년`;
		return null;
	});

	function estimateTokens(text) {
		if (!text) return 0;
		const korean = (text.match(/[\uac00-\ud7af]/g) || []).length;
		const rest = text.length - korean;
		return Math.round(korean * 1.5 + rest / 3.5);
	}

	function formatTokens(n) {
		if (n >= 1000) return (n / 1000).toFixed(1) + "k";
		return String(n);
	}

	let inputTokens = $derived.by(() => {
		let total = 0;
		if (message.systemPrompt) total += estimateTokens(message.systemPrompt);
		if (message.userContent) total += estimateTokens(message.userContent);
		else if (message.contexts?.length > 0) {
			for (const ctx of message.contexts) total += estimateTokens(ctx.text);
		}
		return total;
	});

	let outputTokens = $derived(estimateTokens(message.text));

	function isNumericCell(text) {
		const s = text.replace(/<\/?strong>/g, '').replace(/\*\*/g, '').trim();
		return /^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(s) || s === '-' || s === '0';
	}

	function renderMarkdown(text) {
		if (!text) return "";

		let codeBlocks = [];
		let tableBlocks = [];
		let processed = text.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
			const idx = codeBlocks.length;
			codeBlocks.push(code.trimEnd());
			return `\n%%CODE_${idx}%%\n`;
		});

		processed = processed.replace(/((?:^\|.+\|$\n?)+)/gm, (block) => {
			const lines = block.trim().split('\n').filter(l => l.trim());
			let headerLine = null;
			let sepIdx = -1;
			let dataLines = [];

			for (let i = 0; i < lines.length; i++) {
				const cells = lines[i].slice(1, -1).split('|').map(c => c.trim());
				if (cells.every(c => /^[\-:]+$/.test(c))) {
					sepIdx = i;
					break;
				}
			}

			if (sepIdx > 0) {
				headerLine = lines[sepIdx - 1];
				dataLines = lines.slice(sepIdx + 1);
			} else if (sepIdx === 0) {
				dataLines = lines.slice(1);
			} else {
				headerLine = lines[0];
				dataLines = lines.slice(1);
			}

			let tableHtml = '<table>';
			if (headerLine) {
				const hCells = headerLine.slice(1, -1).split('|').map(c => c.trim());
				tableHtml += '<thead><tr>' + hCells.map(c => {
					let rendered = c.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
					return `<th>${rendered}</th>`;
				}).join('') + '</tr></thead>';
			}

			if (dataLines.length > 0) {
				tableHtml += '<tbody>';
				for (const line of dataLines) {
					const cells = line.slice(1, -1).split('|').map(c => c.trim());
					tableHtml += '<tr>' + cells.map(c => {
						let rendered = c.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
						const align = isNumericCell(c) ? ' class="num"' : '';
						return `<td${align}>${rendered}</td>`;
					}).join('') + '</tr>';
				}
				tableHtml += '</tbody>';
			}
			tableHtml += '</table>';

			let idx = tableBlocks.length;
			tableBlocks.push(tableHtml);
			return `\n%%TABLE_${idx}%%\n`;
		});

		let html = processed
			.replace(/`([^`]+)`/g, '<code>$1</code>')
			.replace(/^### (.+)$/gm, '<h3>$1</h3>')
			.replace(/^## (.+)$/gm, '<h2>$1</h2>')
			.replace(/^# (.+)$/gm, '<h1>$1</h1>')
			.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
			.replace(/\*([^*]+)\*/g, '<em>$1</em>')
			.replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
			.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
			.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
			.replace(/\n\n/g, '</p><p>')
			.replace(/\n/g, '<br>');
		html = html.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g, m => '<ul>' + m.replace(/<br>/g, '') + '</ul>');

		for (let i = 0; i < tableBlocks.length; i++) {
			html = html.replace(`%%TABLE_${i}%%`, tableBlocks[i]);
		}

		for (let i = 0; i < codeBlocks.length; i++) {
			const escaped = codeBlocks[i].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
			html = html.replace(`%%CODE_${i}%%`,
				`<div class="code-block-wrap"><button class="code-copy-btn" data-code-idx="${i}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code>${escaped}</code></pre></div>`
			);
		}

		html = html.replace(/(?<=>|^)([^<]*?)(?=<|$)/g, (_, text) => {
			return text.replace(/(?<![a-zA-Z가-힣/\-])([−\-+]?\d[\d,]*\.?\d*)(\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)/g,
				'<span class="num-highlight">$1$2$3</span>');
		});

		return '<p>' + html + '</p>';
	}

	let contentEl = $state();

	const ICON_COPY = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
	const ICON_CHECK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

	function handleContentClick(e) {
		const btn = e.target.closest('.code-copy-btn');
		if (!btn) return;
		const wrap = btn.closest('.code-block-wrap');
		const code = wrap?.querySelector('code')?.textContent || "";
		navigator.clipboard.writeText(code).then(() => {
			btn.innerHTML = ICON_CHECK;
			setTimeout(() => { btn.innerHTML = ICON_COPY; }, 2000);
		});
	}

	function openContextModal(idx) {
		openModal = idx;
		modalType = "context";
		contextTab = "rendered";
	}

	function openSystemPromptModal() {
		openModal = 0;
		modalType = "system";
		contextTab = "raw";
	}

	function openSnapshotModal() {
		openModal = 0;
		modalType = "snapshot";
	}

	function closeModal() {
		openModal = null;
	}

	let loadingSteps = $derived.by(() => {
		if (!message.loading) return [];
		const steps = [];
		if (message.meta?.company) steps.push({ label: `${message.meta.company} 인식`, done: true });
		if (message.snapshot) steps.push({ label: "핵심 수치 확인", done: true });
		if (message.meta?.includedModules) {
			steps.push({ label: `모듈 ${message.meta.includedModules.length}개 선택`, done: true });
		}
		if (message.contexts?.length > 0) {
			steps.push({ label: `데이터 ${message.contexts.length}건 로드`, done: true });
		}
		if (message.systemPrompt) steps.push({ label: "프롬프트 조립", done: true });
		if (message.text) steps.push({ label: "응답 작성 중", done: false });
		else steps.push({ label: loadingPhase || "준비 중", done: false });
		return steps;
	});
</script>

{#if message.role === "user"}
	<div class="flex items-start gap-3 animate-fadeIn">
		<div class="w-7 h-7 rounded-full bg-dl-bg-card-hover border border-dl-border flex items-center justify-center text-[10px] font-semibold text-dl-text-muted flex-shrink-0 mt-0.5">
			You
		</div>
		<div class="flex-1 pt-0.5">
			<p class="text-[15px] text-dl-text leading-relaxed">{message.text}</p>
		</div>
	</div>
{:else}
	<div class="flex items-start gap-3 animate-fadeIn">
		<img src="/avatar.png" alt="DartLab" class="w-7 h-7 rounded-full flex-shrink-0 mt-0.5" />
		<div class="flex-1 pt-0.5 min-w-0">

			<!-- ── 상단 메타 뱃지 (데이터 투명성: LLM이 보는 데이터를 뱃지로 표시) ── -->
			{#if companyName || dataYearRange || message.contexts?.length > 0 || message.meta?.includedModules}
				<div class="flex flex-wrap items-center gap-1.5 mb-2">
					{#if companyName}
						<Badge variant="muted">{companyName}</Badge>
					{/if}
					{#if dataYearRange}
						<Badge variant="accent">{dataYearRange}</Badge>
					{/if}
					{#if message.contexts?.length > 0}
						{#each message.contexts as ctx, i}
							<button
								class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all cursor-pointer"
								onclick={() => openContextModal(i)}
							>
								<Database size={10} class="flex-shrink-0" />
								{ctx.label || ctx.module}
							</button>
						{/each}
					{:else if message.meta?.includedModules?.length > 0}
						<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/50 bg-dl-bg-card/40 text-[11px] text-dl-text-dim">
							<Database size={10} class="flex-shrink-0" />
							모듈 {message.meta.includedModules.length}개
						</span>
					{/if}
				</div>
			{/if}

			<!-- ── Snapshot 카드 (클릭하면 원본 JSON) ── -->
			{#if message.snapshot?.items?.length > 0}
				<button
					class="mb-3 rounded-xl border border-dl-border/60 bg-dl-bg-card/40 overflow-hidden animate-fadeIn shadow-sm shadow-black/10 w-full text-left cursor-pointer hover:border-dl-primary/30 transition-colors"
					onclick={openSnapshotModal}
				>
					<div class="grid gap-px" style="grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));">
						{#each message.snapshot.items as item}
							{@const statusColor = item.status === "good" ? "text-dl-success" : item.status === "danger" ? "text-dl-primary-light" : item.status === "caution" ? "text-amber-400" : "text-dl-text"}
							<div class="px-3 py-2 bg-dl-bg-card/50">
								<div class="text-[10px] text-dl-text-dim leading-tight">{item.label}</div>
								<div class={cn("text-[14px] font-semibold leading-snug mt-0.5", statusColor)}>
									{item.value}
								</div>
							</div>
						{/each}
					</div>
					{#if message.snapshot.warnings?.length > 0}
						<div class="px-3 py-1.5 border-t border-dl-border/30 flex flex-wrap gap-2">
							{#each message.snapshot.warnings as warn}
								<span class="flex items-center gap-1 text-[10px] text-amber-400">
									<AlertTriangle size={10} />
									{warn}
								</span>
							{/each}
						</div>
					{/if}
				</button>
			{/if}

			<!-- ── Tool Events (데이터 투명성: LLM이 조회한 데이터를 실시간 표시) ── -->
			{#if message.toolEvents?.length > 0}
				<div class="mb-3">
					<div class="flex flex-wrap items-center gap-1.5">
						{#each message.toolEvents as ev}
							{#if ev.type === "call"}
								{@const detail = ev.arguments?.module || ev.arguments?.keyword || ev.arguments?.engine || ev.arguments?.name || ""}
								<span class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-dl-accent/30 bg-dl-accent/[0.06] text-[11px] text-dl-accent">
									<Wrench size={11} />
									{ev.name}{detail ? `: ${detail}` : ""}
								</span>
							{/if}
						{/each}
					</div>
				</div>
			{/if}

			<!-- ── 로딩: 진행 단계 표시 ── -->
			{#if message.loading && !message.text}
				<div class="animate-fadeIn">
					<div class="space-y-1 mb-3">
						{#each loadingSteps as step}
							<div class="flex items-center gap-2 text-[11px]">
								{#if step.done}
									<span class="w-3.5 h-3.5 rounded-full bg-dl-success/20 flex items-center justify-center flex-shrink-0">
										<svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="var(--color-dl-success)" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
									</span>
									<span class="text-dl-text-muted">{step.label}</span>
								{:else}
									<Loader2 size={14} class="animate-spin flex-shrink-0 text-dl-text-dim" />
									<span class="text-dl-text-dim">{step.label}</span>
								{/if}
							</div>
						{/each}
					</div>
					<div class="space-y-2.5">
						<div class="skeleton-line w-full"></div>
						<div class="skeleton-line w-[85%]"></div>
						<div class="skeleton-line w-[70%]"></div>
					</div>
				</div>
			{:else}
				{#if message.loading}
					<div class="flex items-center gap-2 mb-2 text-[11px] text-dl-text-dim">
						<Loader2 size={12} class="animate-spin flex-shrink-0" />
						<span>{loadingPhase}</span>
					</div>
				{/if}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class={cn("prose-dartlab text-[15px] leading-[1.75]", message.error && "text-dl-primary")}
					bind:this={contentEl}
					onclick={handleContentClick}
				>
					{@html renderMarkdown(message.text)}
				</div>

				<!-- ── 하단 메타 (응답 완료 후) ── -->
				{#if !message.loading && (message.duration || hasTransparencyData || onRegenerate)}
					<div class="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-dl-border/20">
						{#if message.duration}
							<span class="flex items-center gap-1 text-[10px] text-dl-text-dim">
								<Clock size={10} />
								{message.duration}초
							</span>
						{/if}

						{#if inputTokens > 0 || outputTokens > 0}
							<span class="flex items-center gap-1.5 text-[10px] text-dl-text-dim font-mono" title="추정 토큰 (입력 ↑ / 출력 ↓)">
								{#if inputTokens > 0}
									<span class="text-dl-accent/60">↑{formatTokens(inputTokens)}</span>
								{/if}
								{#if outputTokens > 0}
									<span class="text-dl-success/60">↓{formatTokens(outputTokens)}</span>
								{/if}
							</span>
						{/if}

						{#if onRegenerate}
							<button
								class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"
								onclick={() => onRegenerate?.()}
							>
								<RefreshCw size={10} />
								재생성
							</button>
						{/if}

						{#if message.systemPrompt}
							<button
								class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-primary-light hover:border-dl-primary/30 transition-all"
								onclick={openSystemPromptModal}
							>
								<Brain size={10} />
								시스템 프롬프트
							</button>
						{/if}

						{#if message.userContent}
							<button
								class="flex items-center gap-1 px-2 py-0.5 rounded-full border border-dl-border/40 text-[10px] text-dl-text-dim hover:text-dl-accent hover:border-dl-accent/30 transition-all"
								onclick={() => { openModal = 0; modalType = "userContent"; contextTab = "raw"; }}
							>
								<FileText size={10} />
								LLM 입력 ({message.userContent.length.toLocaleString()}자 · ~{formatTokens(estimateTokens(message.userContent))}tok)
							</button>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	</div>
{/if}

<!-- ═══ Modal: Context / System Prompt / User Content / Snapshot ═══ -->
{#if openModal !== null}
	{@const isSystemPrompt = modalType === "system"}
	{@const isUserContent = modalType === "userContent"}
	{@const isContext = modalType === "context"}
	{@const isSnapshot = modalType === "snapshot"}
	{@const ctx = isContext ? message.contexts?.[openModal] : null}
	{@const modalTitle = isSnapshot ? "핵심 수치 (원본 데이터)" : isSystemPrompt ? "시스템 프롬프트" : isUserContent ? "LLM에 전달된 입력" : (ctx?.label || ctx?.module || "")}
	{@const modalText = isSnapshot ? JSON.stringify(message.snapshot, null, 2) : isSystemPrompt ? message.systemPrompt : isUserContent ? message.userContent : ctx?.text}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) closeModal(); }}
		onkeydown={(e) => { if (e.key === "Escape") closeModal(); }}
	>
		<div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl shadow-black/40 overflow-hidden flex flex-col">
			<div class="flex-shrink-0 border-b border-dl-border/50">
				<div class="flex items-center justify-between px-5 pt-4 pb-3">
					<div class="flex items-center gap-2 text-[14px] font-medium text-dl-text">
						{#if isSnapshot}
							<Database size={15} class="text-dl-success flex-shrink-0" />
						{:else if isSystemPrompt}
							<Brain size={15} class="text-dl-primary-light flex-shrink-0" />
						{:else if isUserContent}
							<FileText size={15} class="text-dl-accent flex-shrink-0" />
						{:else}
							<Database size={15} class="flex-shrink-0" />
						{/if}
						<span>{modalTitle}</span>
						{#if isSystemPrompt}
							<span class="text-[10px] text-dl-text-dim">({modalText?.length?.toLocaleString()}자)</span>
						{/if}
					</div>
					<div class="flex items-center gap-2">
						{#if isContext}
							<div class="flex items-center gap-0.5 bg-dl-bg-darker rounded-lg p-0.5">
								<button
									class={cn(
										"flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",
										contextTab === "rendered"
											? "bg-dl-bg-card text-dl-text shadow-sm"
											: "text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => contextTab = "rendered"}
								>
									<FileText size={11} />
									렌더링
								</button>
								<button
									class={cn(
										"flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] transition-colors",
										contextTab === "raw"
											? "bg-dl-bg-card text-dl-text shadow-sm"
											: "text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => contextTab = "raw"}
								>
									<Code size={11} />
									원문
								</button>
							</div>
						{/if}
						<button
							class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
							onclick={closeModal}
						>
							<X size={18} />
						</button>
					</div>
				</div>

				{#if isContext && message.contexts?.length > 1}
					<div class="px-5 pb-2.5 overflow-x-auto scrollbar-hide">
						<div class="flex items-center gap-1.5">
							{#each message.contexts as _, idx}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",
										idx === openModal
											? "bg-dl-primary/20 text-dl-primary-light font-medium"
											: "bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted hover:bg-dl-bg-darker/80"
									)}
									onclick={() => { openModal = idx; }}
								>
									{message.contexts[idx].label || message.contexts[idx].module}
								</button>
							{/each}
						</div>
					</div>
				{/if}

				{#if !isContext && !isSnapshot}
					<div class="px-5 pb-2.5">
						<div class="flex items-center gap-1.5">
							{#if message.systemPrompt}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",
										isSystemPrompt
											? "bg-dl-primary/20 text-dl-primary-light font-medium"
											: "bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => { modalType = "system"; }}
								>
									시스템 프롬프트
								</button>
							{/if}
							{#if message.userContent}
								<button
									class={cn(
										"px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-colors flex-shrink-0",
										isUserContent
											? "bg-dl-accent/20 text-dl-accent font-medium"
											: "bg-dl-bg-darker text-dl-text-dim hover:text-dl-text-muted"
									)}
									onclick={() => { modalType = "userContent"; }}
								>
									LLM 입력
								</button>
							{/if}
						</div>
					</div>
				{/if}
			</div>

			<div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0">
				{#if isContext && contextTab === "rendered"}
					<div class="prose-dartlab text-[13px] leading-[1.7] pt-3">
						{@html renderMarkdown(ctx?.text)}
					</div>
				{:else}
					<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 mt-3 overflow-x-auto whitespace-pre-wrap break-words">{modalText}</pre>
				{/if}
			</div>
		</div>
	</div>
{/if}
