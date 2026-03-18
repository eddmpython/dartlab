<!--
	RightPanel — 오른쪽 디스플레이 영역

	보여줄 게 있으면 열리고, 닫으면 사라진다.
	내용: 공시 뷰어 / 뱃지 데이터 / 종목 데이터
-->
<script>
	import { X, Download, Loader2, Maximize2, Minimize2 } from "lucide-svelte";
	import { downloadExcel } from "$lib/api.js";
	import { renderMarkdown } from "$lib/markdown.js";
	import SectionsViewer from "./SectionsViewer.svelte";

	let {
		mode = null,       // "viewer" | "data"
		company = null,    // selected company
		data = null,       // data for "data" mode
		onClose,
		onTopicChange = null,
		onFullscreen = null,  // 전체화면 토글 콜백
		isFullscreen = false,
	} = $props();

	let downloading = $state(false);

	async function handleDownload() {
		if (!company?.stockCode || downloading) return;
		downloading = true;
		try {
			await downloadExcel(company.stockCode);
		} catch (e) {
			console.error("Excel download error:", e);
		}
		downloading = false;
	}

	/** 텍스트에 마크다운 테이블이 포함되어 있는지 */
	function hasMarkdownContent(text) {
		if (!text) return false;
		return /^\|.+\|$/m.test(text) || /^#{1,3} /m.test(text) || /\*\*[^*]+\*\*/m.test(text) || /```/.test(text);
	}
</script>

<div class="flex flex-col h-full min-h-0 bg-dl-bg-dark">
	<!-- Panel header — pt-8로 우상단 fixed 컨트롤과 겹침 방지 -->
	<div class="flex items-center justify-between h-10 mt-8 px-4 border-b border-dl-border/40 flex-shrink-0">
		<div class="flex items-center gap-2 min-w-0">
			{#if mode === "viewer" && company}
				<span class="text-[12px] font-semibold text-dl-text truncate">{company.corpName || company.company}</span>
				<span class="text-[10px] font-mono text-dl-text-dim">{company.stockCode}</span>
			{:else if mode === "data" && data?.label}
				<span class="text-[12px] font-semibold text-dl-text">{data.label}</span>
			{:else if mode === "data"}
				<span class="text-[12px] font-semibold text-dl-text">데이터</span>
			{/if}
		</div>
		<div class="flex items-center gap-1">
			{#if mode === "viewer" && company?.stockCode}
				<button
					class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={handleDownload}
					disabled={downloading}
					title="Excel 다운로드"
				>
					{#if downloading}
						<Loader2 size={14} class="animate-spin" />
					{:else}
						<Download size={14} />
					{/if}
				</button>
				<button
					class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
					onclick={() => onFullscreen?.()}
					title={isFullscreen ? "패널 모드로" : "전체 화면"}
				>
					{#if isFullscreen}
						<Minimize2 size={14} />
					{:else}
						<Maximize2 size={14} />
					{/if}
				</button>
			{/if}
			<button
				class="p-1.5 rounded-lg text-dl-text-dim hover:text-dl-text hover:bg-white/5 transition-colors"
				onclick={() => onClose?.()}
			>
				<X size={15} />
			</button>
		</div>
	</div>

	<!-- Panel content -->
	<div class="flex-1 overflow-auto min-h-0">
		{#if mode === "viewer" && company}
			<SectionsViewer
				stockCode={company.stockCode}
				onTopicChange={onTopicChange}
			/>
		{:else if mode === "data" && data}
			<div class="p-4">
				{#if typeof data === "string"}
					{#if hasMarkdownContent(data)}
						<div class="prose-dartlab text-[13px] leading-[1.7]">
							{@html renderMarkdown(data)}
						</div>
					{:else}
						<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed">{data}</pre>
					{/if}
				{:else if data?.text}
					{#if data.module}
						<div class="text-[10px] text-dl-text-dim uppercase tracking-wider mb-2">{data.module}</div>
					{/if}
					{#if hasMarkdownContent(data.text)}
						<div class="prose-dartlab text-[13px] leading-[1.7]">
							{@html renderMarkdown(data.text)}
						</div>
					{:else}
						<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40">{data.text}</pre>
					{/if}
				{:else}
					<pre class="text-[12px] text-dl-text-muted whitespace-pre-wrap font-mono leading-relaxed bg-dl-bg-darker rounded-xl p-4 border border-dl-border/40">{JSON.stringify(data, null, 2)}</pre>
				{/if}
			</div>
		{:else}
			<div class="flex-1 flex items-center justify-center text-[13px] text-dl-text-dim p-8">
				표시할 내용이 없습니다
			</div>
		{/if}
	</div>
</div>
