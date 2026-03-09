<script>
	import { cn } from "$lib/utils.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Database, X, FileText, Code, Wrench, Loader2, Check, TrendingUp, TrendingDown, Minus, AlertTriangle, Clock } from "lucide-svelte";

	let { message } = $props();
	let openModal = $state(null);
	let contextTab = $state("rendered");

	let loadingPhase = $derived.by(() => {
		if (!message.loading) return "";
		if (message.text) return "응답 생성 중...";
		if (message.contexts?.length > 0) return "분석 중...";
		if (message.snapshot) return "데이터 확인 중...";
		if (message.meta) return "기업 데이터 로딩 중...";
		return "생각 중...";
	});

	let latestContextLabel = $derived.by(() => {
		if (!message.loading || !message.contexts?.length) return "";
		const last = message.contexts[message.contexts.length - 1];
		return last?.label || last?.module || "";
	});

	function renderMarkdown(text) {
		if (!text) return "";
		let html = text
			.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
			.replace(/`([^`]+)`/g, '<code>$1</code>')
			.replace(/^### (.+)$/gm, '<h3>$1</h3>')
			.replace(/^## (.+)$/gm, '<h2>$1</h2>')
			.replace(/^# (.+)$/gm, '<h1>$1</h1>')
			.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
			.replace(/\*([^*]+)\*/g, '<em>$1</em>')
			.replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
			.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
			.replace(/^\|(.+)\|$/gm, (match) => {
				const cells = match.slice(1, -1).split('|').map(c => c.trim());
				if (cells.every(c => /^[\-:]+$/.test(c))) return '';
				return '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
			})
			.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
			.replace(/\n\n/g, '</p><p>')
			.replace(/\n/g, '<br>');
		html = html.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g, m => '<ul>' + m.replace(/<br>/g, '') + '</ul>');
		html = html.replace(/(<tr>.*?<\/tr>(\s*<br>)?)+/g, m => '<table>' + m.replace(/<br>/g, '') + '</table>');
		return '<p>' + html + '</p>';
	}

	function openBadge(idx) {
		openModal = idx;
		contextTab = "rendered";
	}
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
			{#if message.company}
				<Badge variant="muted" class="mb-2">{message.company}</Badge>
			{/if}

			{#if message.snapshot?.items?.length > 0}
				<div class="mb-3 rounded-xl border border-dl-border/50 bg-dl-bg-card/30 overflow-hidden animate-fadeIn">
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
				</div>
			{/if}

			{#if message.contexts?.length > 0}
				<div class="mb-3">
					<div class="flex items-center gap-1.5 mb-1.5 text-[11px] text-dl-text-dim">
						<Database size={11} />
						<span>분석에 사용된 데이터</span>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						{#each message.contexts as ctx, i}
							<button
								class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dl-border/60 bg-dl-bg-card/60 text-[12px] text-dl-text-muted hover:text-dl-text hover:border-dl-primary/40 hover:bg-dl-primary/[0.05] transition-all"
								onclick={() => openBadge(i)}
							>
								<Database size={13} class="flex-shrink-0" />
								<span>{ctx.label || ctx.module}</span>
							</button>
						{/each}
					</div>
				</div>
			{:else if message.loading && !message.text}
				<div class="flex items-center gap-1.5 mb-3 text-[12px] text-dl-text-dim">
					<Loader2 size={13} class="animate-spin" />
					<span>{loadingPhase}</span>
				</div>
			{/if}

			{#if message.toolEvents?.length > 0}
				<div class="mb-3">
					<div class="flex items-center gap-1.5 mb-1.5 text-[11px] text-dl-text-dim">
						<Wrench size={11} />
						<span>사용된 도구</span>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						{#each message.toolEvents as ev}
							{#if ev.type === "call"}
								<span class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dl-accent/30 bg-dl-accent/5 text-[12px] text-dl-accent">
									<Wrench size={13} />
									{ev.name}
								</span>
							{/if}
						{/each}
					</div>
				</div>
			{/if}

			{#if message.loading && !message.text}
				<div class="flex items-center gap-2 h-6 text-[12px] text-dl-text-dim">
					<Loader2 size={14} class="animate-spin flex-shrink-0" />
					<span>{loadingPhase}</span>
					{#if latestContextLabel}
						<span class="text-dl-text-muted">— {latestContextLabel}</span>
					{/if}
				</div>
			{:else}
				<div class={cn("prose-dartlab text-[15px] leading-[1.75]", message.error && "text-dl-primary")}>
					{@html renderMarkdown(message.text)}
				</div>
				{#if message.duration && !message.loading}
					<div class="flex items-center gap-1 mt-2 text-[10px] text-dl-text-dim">
						<Clock size={10} />
						<span>{message.duration}초</span>
					</div>
				{/if}
			{/if}
		</div>
	</div>
{/if}

{#if openModal !== null && message.contexts?.[openModal]}
	{@const ctx = message.contexts[openModal]}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[300] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn"
		onclick={(e) => { if (e.target === e.currentTarget) openModal = null; }}
		onkeydown={(e) => { if (e.key === "Escape") openModal = null; }}
	>
		<div class="w-full max-w-3xl max-h-[80vh] mx-4 bg-dl-bg-card border border-dl-border rounded-2xl shadow-2xl overflow-hidden flex flex-col">
			<div class="flex-shrink-0 border-b border-dl-border/50">
				<div class="flex items-center justify-between px-5 pt-4 pb-3">
					<div class="flex items-center gap-1.5 text-[14px] font-medium text-dl-text">
						<Database size={15} class="flex-shrink-0" />
						<span>{ctx.label || ctx.module}</span>
					</div>
					<div class="flex items-center gap-2">
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
						<button
							class="p-1 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
							onclick={() => openModal = null}
						>
							<X size={18} />
						</button>
					</div>
				</div>
				{#if message.contexts.length > 1}
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
			</div>

			<div class="flex-1 overflow-y-auto px-5 pb-5 min-h-0">
				{#if contextTab === "rendered"}
					<div class="prose-dartlab text-[13px] leading-[1.7]">
						{@html renderMarkdown(ctx.text)}
					</div>
				{:else}
					<pre class="text-[11px] text-dl-text-muted font-mono bg-dl-bg-darker rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-words">{ctx.text}</pre>
				{/if}
			</div>
		</div>
	</div>
{/if}

