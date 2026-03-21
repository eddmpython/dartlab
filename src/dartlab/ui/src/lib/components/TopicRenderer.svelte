<!--
	TopicRenderer — topic 콘텐츠 렌더러.
	textDocument가 있으면 SectionsViewer 수준의 rich 렌더링.
	없으면 viewerBlocks 기반 fallback.
	타임라인 바로 기간 전환 + 인라인 diff + 상태 뱃지.
-->
<script>
	import { renderMarkdown } from "$lib/markdown.js";
	import { streamTopicSummary, fetchCompanyTopicDiff } from "$lib/api.js";
	import { financeBlockToChartSpec } from "$lib/chart/specs.js";
	import {
		escapeHtml, normalizeDisclosureLine, isStructuralHeadingLine,
		periodDisplayLabel as periodDisplayLabelBase,
	} from "$lib/viewer/disclosureText.js";
	import TimelineBar from "./TimelineBar.svelte";
	import TableRenderer from "./TableRenderer.svelte";
	import DiffSummary from "./DiffSummary.svelte";
	import DiffCompare from "./DiffCompare.svelte";
	import { MessageSquare, Copy, Check, Sparkles, Star, Loader2, ArrowLeftRight, BarChart3, Table2 } from "lucide-svelte";

	let {
		topicData = null,    // viewer API response (blocks + textDocument)
		diffSummary = null,  // diff summary API response
		viewer = null,       // viewer store (for summary cache + bookmarks)
		onAskAI = null,      // (selectedText) => void
		searchHighlight = null, // B3: 검색어 하이라이트
	} = $props();

	// ── State ──
	let selectedPeriods = $state(new Map());     // blockIdx → period
	let sectionTimeline = $state(new Map());     // sectionId → periodLabel
	let copiedTable = $state(null);              // blockIdx of copied table
	let chartMode = $state(new Map());           // blockIdx → boolean (true = chart view)

	// Lazy rendering — 초기 8개만 표시, 스크롤 시 점진 렌더
	let visibleCount = $state(8);
	let sentinelEl = $state(null);

	// topic 변경 시 visibleCount 초기화
	$effect(() => {
		if (topicData?.topic) visibleCount = 8;
	});

	$effect(() => {
		if (!sentinelEl) return;
		const observer = new IntersectionObserver((entries) => {
			if (entries[0]?.isIntersecting) {
				visibleCount = Math.min(visibleCount + 10, topicData?.textDocument?.entries?.length || topicData?.textDocument?.sections?.length || 999);
			}
		}, { rootMargin: '200px' });
		observer.observe(sentinelEl);
		return () => observer.disconnect();
	});

	// "AI에게 물어보기" floating button
	let floatBtn = $state({ show: false, x: 0, y: 0, text: "" });

	// P2: AI 요약
	let summaryStreaming = $state(false);
	let summaryText = $state("");
	let summaryError = $state(null);
	let summaryHandle = $state(null);

	// Reset summary when topic changes
	$effect(() => {
		if (topicData?.topic) {
			summaryStreaming = false;
			summaryError = null;
			const cached = viewer?.getTopicSummary?.(topicData.topic);
			summaryText = cached || "";
			if (summaryHandle) { summaryHandle.abort(); summaryHandle = null; }
		}
	});

	function startSummary() {
		if (!viewer?.stockCode || !topicData?.topic) return;
		summaryStreaming = true;
		summaryText = "";
		summaryError = null;

		summaryHandle = streamTopicSummary(viewer.stockCode, topicData.topic, {
			onContext() {},
			onChunk(text) { summaryText += text; },
			onDone() {
				summaryStreaming = false;
				summaryHandle = null;
				if (summaryText) viewer?.setTopicSummary?.(topicData.topic, summaryText);
			},
			onError(err) {
				summaryStreaming = false;
				summaryHandle = null;
				summaryError = err;
			},
		});
	}

	// P6: bookmark derived
	let isBookmarked = $derived(viewer?.isBookmarked?.(topicData?.topic) ?? false);

	// charDiff 캐시 — sectionId:periodLabel → { diff: [...], from, to }
	// LRU 제한: 최대 100 엔트리, 초과 시 오래된 것부터 제거
	const CHAR_DIFF_CACHE_MAX = 100;
	let charDiffCache = $state(new Map());
	let charDiffLoading = $state(new Set());

	async function loadCharDiff(sectionId, toPeriodLabel, fromPeriodLabel) {
		if (!viewer?.stockCode || !topicData?.topic || !fromPeriodLabel || !toPeriodLabel) return;
		const cacheKey = `${sectionId}:${toPeriodLabel}`;
		if (charDiffCache.has(cacheKey) || charDiffLoading.has(cacheKey)) return;

		charDiffLoading = new Set([...charDiffLoading, cacheKey]);
		try {
			const res = await fetchCompanyTopicDiff(viewer.stockCode, topicData.topic, fromPeriodLabel, toPeriodLabel);
			const next = new Map(charDiffCache);
			next.set(cacheKey, res);
			// LRU eviction: 오래된 엔트리 제거
			if (next.size > CHAR_DIFF_CACHE_MAX) {
				const keysToDelete = [...next.keys()].slice(0, next.size - CHAR_DIFF_CACHE_MAX);
				for (const k of keysToDelete) next.delete(k);
			}
			charDiffCache = next;
		} catch {
			// charDiff 실패 시 무시 — paragraph diff는 유지
		}
		const ns = new Set(charDiffLoading);
		ns.delete(cacheKey);
		charDiffLoading = ns;
	}

	// 기간 비교 모드
	let showDiffCompare = $state(false);

	// topic 변경 시 비교 모드 닫기 + charDiff 캐시 초기화
	$effect(() => {
		if (topicData?.topic) {
			showDiffCompare = false;
			charDiffCache = new Map();
			charDiffLoading = new Set();
		}
	});

	// updated section의 charDiff 자동 프리로드
	$effect(() => {
		const sections = topicData?.textDocument?.sections;
		if (!sections || !viewer?.stockCode || !topicData?.topic) return;
		for (const s of sections) {
			if (s.status !== 'updated' || !s.timeline || s.timeline.length < 2) continue;
			const latest = s.timeline[0]?.period?.label || periodDisplayLabel(s.timeline[0]?.period);
			const prev = s.timeline[1]?.period?.label || periodDisplayLabel(s.timeline[1]?.period);
			if (latest && prev) loadCharDiff(s.id, latest, prev);
		}
	});

	// 사용 가능한 기간 목록 (textDocument에서 추출)
	let availablePeriods = $derived.by(() => {
		if (!topicData?.textDocument?.sections?.length) return [];
		const periods = new Set();
		for (const s of topicData.textDocument.sections) {
			if (s.timeline) {
				for (const entry of s.timeline) {
					const label = entry.period?.label || (entry.period?.year && entry.period?.quarter ? `${entry.period.year}Q${entry.period.quarter}` : null);
					if (label) periods.add(label);
				}
			}
		}
		return [...periods].sort().reverse();
	});

	// ── textDocument helpers ──
	let hasTextDoc = $derived(topicData?.textDocument?.sections?.length > 0);
	let hasEntries = $derived(topicData?.textDocument?.entries?.length > 0);
	// entries 기반 렌더링용 lookup maps
	let sectionsByRef = $derived(new Map((topicData?.textDocument?.sections ?? []).map(s => [s.id, s])));
	let blocksByRef = $derived(new Map((topicData?.blocks ?? []).map(b => [b.block, b])));
	let docEntries = $derived(topicData?.textDocument?.entries ?? []);

	function periodDisplayLabel(p) {
		if (!p) return "";
		if (typeof p === "string") {
			const m = p.match(/^(\d{4})(Q([1-4]))?$/);
			if (!m) return p;
			return m[3] ? `${m[1]}Q${m[3]}` : m[1];
		}
		if (p.kind === "annual") return `${p.year}`;
		if (p.year && p.quarter) return `${p.year}Q${p.quarter}`;
		return p.label || "";
	}

	function sectionStatusLabel(s) {
		if (s === "updated") return "수정됨";
		if (s === "new") return "신규";
		if (s === "stale") return "과거유지";
		return "유지";
	}

	function sectionStatusClass(s) {
		if (s === "updated") return "bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20";
		if (s === "new") return "bg-blue-500/10 text-blue-400/80 border-blue-500/20";
		if (s === "stale") return "bg-amber-500/10 text-amber-400/80 border-amber-500/20";
		return "bg-dl-border/10 text-dl-text-dim border-dl-border/20";
	}

	function getActiveView(section) {
		const label = sectionTimeline.get(section.id);
		if (label && section.views?.[label]) return section.views[label];
		return section.latest || null;
	}

	function isActivePeriod(section, periodLabel) {
		const explicit = sectionTimeline.get(section.id);
		if (explicit) return explicit === periodLabel;
		return section.latest?.period?.label === periodLabel;
	}

	function hasExplicitSelection(section) {
		return sectionTimeline.has(section.id);
	}

	function selectSectionPeriod(sectionId, periodLabel, section) {
		const next = new Map(sectionTimeline);
		if (next.get(sectionId) === periodLabel) next.delete(sectionId);
		else {
			next.set(sectionId, periodLabel);
			// charDiff 자동 로드 — 직전 기간 찾기
			if (section?.timeline?.length > 1) {
				const labels = section.timeline.map(e => e.period?.label || periodDisplayLabel(e.period));
				const idx = labels.indexOf(periodLabel);
				const prevLabel = idx >= 0 && idx < labels.length - 1 ? labels[idx + 1] : null;
				if (prevLabel) {
					loadCharDiff(sectionId, periodLabel, prevLabel);
				}
			}
		}
		sectionTimeline = next;
	}

	// ── Disclosure text rendering ──
	// escapeHtml, normalizeDisclosureLine, isStructuralHeadingLine imported from disclosureText.js

	function isStructuralHeading(line) {
		if (!line || line.length > 88) return false;
		return isStructuralHeadingLine(line) || /^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(line);
	}

	function headingLevel(line) {
		if (/^[가나다라마바사아자차카타파하]\.\s/.test(line)) return 1;
		if (/^\d+\.\s/.test(line)) return 2;
		if (/^\(\d+\)\s/.test(line) || /^\([가-힣]\)\s/.test(line)) return 3;
		if (/^[①②③④⑤⑥⑦⑧⑨⑩]\s/.test(line)) return 4;
		if (/^\[.+\]$/.test(line) || /^【.+】$/.test(line)) return 1;
		return 2;
	}

	function renderDisclosureText(text) {
		if (!text) return "";
		if (/^\|.+\|$/m.test(text)) return renderMarkdown(text);

		const lines = text.split("\n");
		let html = "";
		let paragraph = [];

		function flushParagraph() {
			if (paragraph.length === 0) return;
			html += `<p class="vw-para">${escapeHtml(paragraph.join(" "))}</p>`;
			paragraph = [];
		}

		for (const rawLine of lines) {
			const line = normalizeDisclosureLine(rawLine);
			if (!line) { flushParagraph(); continue; }
			if (isStructuralHeading(line)) {
				flushParagraph();
				const lvl = headingLevel(line);
				html += `<div class="ko-h${lvl}">${escapeHtml(line)}</div>`;
			} else {
				paragraph.push(line);
			}
		}
		flushParagraph();
		return html;
	}

	// ── Diff rendering ──
	function buildDiffUnits(view) {
		if (!view?.diff?.length) return null;
		const items = [];
		for (const chunk of view.diff) {
			for (const para of chunk.paragraphs || []) {
				items.push({ kind: chunk.kind, text: normalizeDisclosureLine(para) });
			}
		}
		return items;
	}

	// ── Heading path ──
	function formatHeadingPath(headingPath) {
		if (!headingPath?.length) return "";
		return headingPath.map(h => h.text?.trim()).filter(Boolean).join(" › ");
	}

	// ── viewerBlocks fallback (text) ──
	function getSelectedPeriod(blockIdx) {
		return selectedPeriods.get(blockIdx) ?? null;
	}

	function selectPeriod(blockIdx, period) {
		const next = new Map(selectedPeriods);
		next.set(blockIdx, period);
		selectedPeriods = next;
	}

	function textForPeriod(block, period) {
		if (!block?.data?.rows?.[0]) return null;
		return block.data.rows[0][period] ?? null;
	}

	function latestText(block) {
		if (!block?.data?.rows?.[0]) return null;
		const row = block.data.rows[0];
		for (const p of (block.meta?.periods ?? [])) {
			if (row[p]) return { period: p, text: row[p] };
		}
		return null;
	}

	function textPeriods(block) {
		if (!block?.data?.rows?.[0]) return [];
		const row = block.data.rows[0];
		return (block.meta?.periods ?? []).filter(p => row[p] != null);
	}

	function isTextBlock(block) { return block.kind === "text"; }
	function isTableBlock(block) {
		return block.kind === "finance" || block.kind === "structured" || block.kind === "report" || block.kind === "raw_markdown";
	}
	function isChartable(block) {
		return block.kind === "finance" && block.data?.rows?.length > 0 && block.data?.columns?.length > 2;
	}
	function getChartSpec(block) {
		return financeBlockToChartSpec(block);
	}
	function toggleChart(blockIdx) {
		const next = new Map(chartMode);
		next.set(blockIdx, !next.get(blockIdx));
		chartMode = next;
	}

	// ── Table copy ──
	function copyTable(block, blockIdx) {
		if (!block?.data?.rows?.length) return;
		const cols = block.data.columns || [];
		const lines = [cols.join("\t")];
		for (const row of block.data.rows) {
			lines.push(cols.map(c => row[c] ?? "").join("\t"));
		}
		navigator.clipboard.writeText(lines.join("\n")).then(() => {
			copiedTable = blockIdx;
			setTimeout(() => { copiedTable = null; }, 2000);
		});
	}

	// ── "AI에게 물어보기" ──
	function handleTextMouseUp(e) {
		if (!onAskAI) return;
		const sel = window.getSelection();
		const text = sel?.toString().trim();
		if (!text || text.length < 5) {
			floatBtn = { show: false, x: 0, y: 0, text: "" };
			return;
		}
		const range = sel.getRangeAt(0);
		const rect = range.getBoundingClientRect();
		floatBtn = { show: true, x: rect.left + rect.width / 2, y: rect.top - 8, text: text.slice(0, 500) };
	}

	function handleAskAI() {
		if (floatBtn.text && onAskAI) onAskAI(floatBtn.text);
		floatBtn = { show: false, x: 0, y: 0, text: "" };
	}

	/** 블록 단위 AI 분석 요청 */
	function handleBlockAnalyze(block) {
		if (!onAskAI) return;
		const topic = topicData?.topicLabel || topicData?.topic || "";
		const blockData = {
			topic: topicData?.topic,
			topicLabel: topic,
			blockIndex: block.block,
			blockType: block.type || block.kind,
			preview: block.preview || block.label || "",
		};
		if (block.data?.rows?.length) {
			const cols = block.data.columns || [];
			const rows = block.data.rows.slice(0, 30);
			blockData.table = { columns: cols, rows };
		}
		onAskAI(`[${topic}] 이 블록을 분석해줘`, blockData);
	}

	function handleDocClick() {
		if (floatBtn.show) floatBtn = { show: false, x: 0, y: 0, text: "" };
	}

	// B3: 검색어 하이라이트 적용
	function applyHighlight(html) {
		if (!searchHighlight || !html) return html;
		const escaped = searchHighlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
		const re = new RegExp(`(${escaped})`, 'gi');
		return html.replace(re, '<mark class="bg-amber-400/30 text-dl-text rounded-sm px-0.5">$1</mark>');
	}

	// B3: 하이라이트 후 첫 번째 mark로 스크롤
	$effect(() => {
		if (searchHighlight && topicData?.topic) {
			requestAnimationFrame(() => {
				const firstMark = document.querySelector('.disclosure-text mark');
				if (firstMark) firstMark.scrollIntoView({ block: 'center', behavior: 'smooth' });
			});
		}
	});
</script>

<svelte:document onclick={handleDocClick} />

{#if topicData}
	<div class="space-y-4">
		<!-- Topic header -->
		<div class="flex items-center gap-2">
			<h2 class="text-[16px] font-semibold text-dl-text flex-1">
				{topicData.topicLabel || ""}
			</h2>
			<!-- P6: Bookmark -->
			{#if viewer}
				<button
					class="p-1 rounded transition-colors {isBookmarked ? 'text-amber-400' : 'text-dl-text-dim/30 hover:text-amber-400/60'}"
					onclick={() => viewer.toggleBookmark(topicData.topic)}
					title={isBookmarked ? "북마크 해제" : "북마크 추가"}
				>
					<Star size={14} fill={isBookmarked ? "currentColor" : "none"} />
				</button>
			{/if}
			<!-- 기간 비교 버튼 -->
			{#if availablePeriods.length >= 2}
				<button
					class="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						{showDiffCompare ? 'border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light' : 'border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5'}"
					onclick={() => { showDiffCompare = !showDiffCompare; }}
				>
					<ArrowLeftRight size={10} />
					<span>기간 비교</span>
				</button>
			{/if}
			<!-- P2: AI 요약 버튼 -->
			{#if viewer?.stockCode}
				<button
					class="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] transition-colors border
						{summaryStreaming ? 'border-dl-accent/30 bg-dl-accent/10 text-dl-accent-light' : 'border-dl-border/20 text-dl-text-dim hover:text-dl-text hover:bg-white/5'}"
					onclick={startSummary}
					disabled={summaryStreaming}
				>
					{#if summaryStreaming}
						<Loader2 size={10} class="animate-spin" />
					{:else}
						<Sparkles size={10} />
					{/if}
					<span>AI 요약</span>
				</button>
			{/if}
		</div>

		<!-- P2: AI Summary result -->
		{#if summaryText || summaryStreaming || summaryError}
			<div class="px-3 py-2 rounded-lg bg-dl-accent/5 border border-dl-accent/15 text-[12px] text-dl-text-muted leading-relaxed">
				{#if summaryError}
					<div class="text-red-400/80">{summaryError}</div>
				{:else}
					<div class="whitespace-pre-wrap">{summaryText}{#if summaryStreaming}<span class="inline-block w-1.5 h-3 bg-dl-accent/60 animate-pulse ml-0.5"></span>{/if}</div>
				{/if}
			</div>
		{/if}

		<!-- Diff summary card -->
		<DiffSummary summary={diffSummary} />

		<!-- 기간 비교 뷰 -->
		{#if showDiffCompare && viewer?.stockCode}
			<DiffCompare
				stockCode={viewer.stockCode}
				topic={topicData.topic}
				periods={availablePeriods}
				onClose={() => { showDiffCompare = false; }}
			/>
		{/if}

		<!-- ═══ Rich textDocument 렌더링 ═══ -->
		{#if hasTextDoc}
			{@const td = topicData.textDocument}

			<!-- Document meta badges -->
			<div class="flex flex-wrap gap-1.5 text-[10px] max-w-4xl">
				{#if td.latestPeriod}
					<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim">
						최신 {periodDisplayLabel(td.latestPeriod)}
					</span>
				{/if}
				{#if td.sectionCount}
					<span class="px-2 py-0.5 rounded-full border border-dl-border/20 bg-dl-surface-card text-dl-text-dim">
						{td.sectionCount}개 섹션
					</span>
				{/if}
				{#if td.updatedCount > 0}
					<span class="px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 text-emerald-400/80">
						{td.updatedCount}개 수정
					</span>
				{/if}
				{#if td.newCount > 0}
					<span class="px-2 py-0.5 rounded-full border border-blue-500/20 bg-blue-500/8 text-blue-400/80">
						{td.newCount}개 신규
					</span>
				{/if}
			</div>

			<!-- Entries 기반 인터리브 렌더링 — 원본 blockOrder 순서 유지 -->
			{#each docEntries.slice(0, visibleCount) as entry (entry.order)}
				{#if entry.kind === "section"}
					{@const section = sectionsByRef.get(entry.sectionId)}
					{#if section}
					{@const activeView = getActiveView(section)}
					{@const explicit = hasExplicitSelection(section)}
					{@const diffUnits = buildDiffUnits(activeView)}
					{@const hasDiff = diffUnits && diffUnits.length > 0}
					{@const charDiffKey = `${section.id}:${sectionTimeline.get(section.id) || section.timeline?.[0]?.period?.label || ''}`}
					{@const charDiffData = charDiffCache.get(charDiffKey)}
					{@const isCharDiffLoading = charDiffLoading.has(charDiffKey)}
					{@const showingDiff = (hasDiff || charDiffData?.diff) && (explicit || section.status === "updated")}
					{@const showNoDiffNote = explicit && !hasDiff && section.periodCount > 1}

					<div class="max-w-4xl pt-2 pb-6 border-b border-dl-border/8 last:border-b-0 {section.status === 'stale' ? 'border-l-2 border-l-amber-400/40 pl-3' : ''}">
						<!-- Heading path -->
						{#if section.headingPath?.length > 0}
							<div class="mb-2 mt-2">
								{#each section.headingPath as heading}
									{@const text = heading.text?.trim()}
									{#if text}
										{@const level = heading.level || headingLevel(text)}
										{#if level > 0 || isStructuralHeading(text)}
											<div class="ko-h{level || headingLevel(text)}">{text}</div>
										{:else}
											<h4 class="text-[14px] font-semibold text-dl-text">{text}</h4>
										{/if}
									{/if}
								{/each}
							</div>
						{/if}

						<!-- heading-only section (preview 짧고 heading만 있음)은 제목만 표시 -->
						{#if !section.preview || section.preview.length < 30}
							<!-- heading-only: 제목만 렌더, body/status/timeline 생략 -->
						{:else}
						<!-- Status + meta -->
						<div class="flex flex-wrap items-center gap-1.5 mb-2">
							<span class="px-1.5 py-0.5 rounded text-[9px] font-medium border {sectionStatusClass(section.status)}">
								{sectionStatusLabel(section.status)}
							</span>
							{#if section.latestChange}
								<span class="text-[10px] text-dl-text-dim font-mono">{section.latestChange}</span>
							{/if}
							{#if section.periodCount > 1}
								<span class="text-[10px] text-dl-text-dim">{section.periodCount}기간</span>
							{/if}
						</div>

						<!-- Section timeline -->
						{#if section.timeline?.length >= 1 && section.preview && section.preview.length >= 30}
							<div class="flex flex-wrap gap-1 mb-2">
								{#each section.timeline as entry}
									{@const pl = entry.period?.label || periodDisplayLabel(entry.period)}
									<button
										class="px-2 py-1 rounded-lg text-[10px] font-mono transition-colors border
											{isActivePeriod(section, pl)
												? 'border-dl-accent/30 bg-dl-accent/8 text-dl-accent-light font-medium'
												: entry.status === 'updated'
													? 'border-emerald-500/15 text-emerald-400/60 hover:bg-emerald-500/5'
													: 'border-dl-border/15 text-dl-text-dim hover:bg-white/3'}"
										onclick={() => selectSectionPeriod(section.id, pl, section)}
									>
										{periodDisplayLabel(entry.period)}
										{#if entry.status === "updated"}
											<span class="ml-0.5 text-emerald-400/50">*</span>
										{/if}
									</button>
								{/each}
							</div>
						{/if}

						<!-- Digest (change summary) -->
						{#if activeView?.digest?.items?.length > 0}
							{@const dg = activeView.digest}
							<div class="mb-3 px-3 py-2 rounded-lg border border-dl-border/15 bg-dl-surface-card/50 text-[11px] space-y-0.5 max-w-2xl">
								<div class="text-dl-text-dim font-medium">{dg.to} vs {dg.from}</div>
								{#each dg.items.filter(it => it.kind === "numeric") as it}
									<div class="text-blue-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-blue-400/60 mt-1.5 shrink-0"></span>{it.text}</div>
								{/each}
								{#each dg.items.filter(it => it.kind === "added") as it}
									<div class="text-emerald-400/70 flex gap-1"><span class="w-1 h-1 rounded-full bg-emerald-400/50 mt-1.5 shrink-0"></span>{it.text}</div>
								{/each}
								{#each dg.items.filter(it => it.kind === "removed") as it}
									<div class="text-dl-text-dim/50 flex gap-1"><span class="w-1 h-1 rounded-full bg-red-400/40 mt-1.5 shrink-0"></span>{it.text}</div>
								{/each}
							</div>
						{/if}

						<!-- B1: 기간 선택 시 diff 없으면 "이전과 동일" 안내 -->
						{#if showNoDiffNote}
							<div class="mb-2 px-3 py-1.5 rounded-lg border border-dl-border/15 bg-dl-surface-card/30 text-[11px] text-dl-text-dim">
								이전 기간과 동일 — 변경 없음
							</div>
						{/if}

						<!-- Body text — charDiff / paragraph diff / 원문 -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div class="disclosure-text max-w-3xl" onmouseup={handleTextMouseUp}>
							{#if showingDiff && charDiffData?.diff}
								{#each charDiffData.diff as chunk}
									{#if chunk.kind === "added"}
										<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-[14px] leading-[1.85] rounded-r">
											<span class="text-emerald-500/50 text-[10px] mr-1">+</span>
											{#if chunk.parts}
												{#each chunk.parts as part}
													{#if part.kind === "insert"}
														<mark class="bg-emerald-400/25 text-emerald-300 rounded-sm px-[1px]">{part.text}</mark>
													{:else if part.kind === "equal"}
														<span class="text-dl-text/85">{part.text}</span>
													{/if}
												{/each}
											{:else}
												<span class="text-dl-text/85">{chunk.text}</span>
											{/if}
										</div>
									{:else if chunk.kind === "removed"}
										<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-[14px] leading-[1.85] rounded-r">
											<span class="text-red-400/60 text-[10px] mr-1">-</span>
											{#if chunk.parts}
												{#each chunk.parts as part}
													{#if part.kind === "delete"}
														<mark class="bg-red-400/25 text-red-300 line-through decoration-red-400/40 rounded-sm px-[1px]">{part.text}</mark>
													{:else if part.kind === "equal"}
														<span class="text-dl-text/40">{part.text}</span>
													{/if}
												{/each}
											{:else}
												<span class="text-dl-text/40 line-through decoration-red-400/30">{chunk.text}</span>
											{/if}
										</div>
									{:else}
										<p class="vw-para">{chunk.text}</p>
									{/if}
								{/each}
							{:else if showingDiff}
								{#if isCharDiffLoading}
									<div class="text-[10px] text-dl-text-dim/40 mb-1">글자 단위 비교 로딩 중...</div>
								{/if}
								{#each diffUnits as unit}
									{#if unit.kind === "same"}
										<p class="vw-para">{unit.text}</p>
									{:else if unit.kind === "added"}
										<div class="pl-3 py-1 mb-1 border-l-2 border-emerald-400 bg-emerald-500/5 text-dl-text/85 text-[14px] leading-[1.85] rounded-r">
											<span class="text-emerald-500/50 text-[10px] mr-1">+</span>{unit.text}
										</div>
									{:else if unit.kind === "removed"}
										<div class="pl-3 py-1 mb-1 border-l-2 border-red-400 bg-red-500/5 text-dl-text/50 text-[14px] leading-[1.85] rounded-r line-through decoration-red-400/30">
											<span class="text-red-400/50 text-[10px] mr-1">-</span>{unit.text}
										</div>
									{/if}
								{/each}
							{:else if activeView?.body}
								{@html applyHighlight(renderDisclosureText(activeView.body))}
							{/if}
						</div>
					{/if}
					</div>
					{/if}
				{:else if entry.kind === "block_ref"}
					{@const block = blocksByRef.get(entry.blockRef)}
					{#if block}
					{@const chartable = isChartable(block)}
					{@const showChart = chartable && chartMode.get(block.block)}
					{@const spec = showChart ? getChartSpec(block) : null}
					<div class="group relative">
						<div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
							{#if chartable}
								<button
									class="p-1 rounded transition-colors {showChart ? 'text-dl-accent-light bg-dl-accent/10' : 'text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5'}"
									onclick={() => toggleChart(block.block)}
									title={showChart ? '표로 보기' : '차트로 보기'}
								>
									{#if showChart}<Table2 size={12} />{:else}<BarChart3 size={12} />{/if}
								</button>
							{/if}
							{#if block.data?.rows?.length > 0}
								<button
									class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors"
									onclick={() => copyTable(block, block.block)}
									title="테이블 복사"
								>
									{#if copiedTable === block.block}
										<Check size={12} class="text-dl-success" />
									{:else}
										<Copy size={12} />
									{/if}
								</button>
							{/if}
							{#if onAskAI}
								<button
									class="p-1 rounded text-dl-text-dim/30 hover:text-[#a78bfa] hover:bg-white/5 transition-colors"
									onclick={() => handleBlockAnalyze(block)}
									title="AI 분석"
								>
									<Sparkles size={12} />
								</button>
							{/if}
						</div>
						{#if showChart && spec}
							{#await import("$lib/chart/ChartRenderer.svelte") then { default: ChartRenderer }}
								<ChartRenderer {spec} />
							{/await}
						{:else}
							<TableRenderer {block} />
						{/if}
					</div>
					{/if}
				{/if}
			{/each}

			<!-- Lazy rendering sentinel -->
			{#if visibleCount < docEntries.length}
				<div bind:this={sentinelEl} class="h-16 flex items-center justify-center">
					<div class="text-[10px] text-dl-text-dim/40">더 불러오는 중... ({visibleCount}/{docEntries.length})</div>
				</div>
			{/if}

		<!-- ═══ Fallback: viewerBlocks 기반 렌더링 ═══ -->
		{:else}
			{#each topicData.blocks as block, i (block.block)}
				{#if isTextBlock(block)}
					{@const selected = getSelectedPeriod(i)}
					{@const latest = latestText(block)}
					{@const periods = textPeriods(block)}
					{@const displayPeriod = selected || latest?.period}
					{@const displayText = displayPeriod ? textForPeriod(block, displayPeriod) : latest?.text}

					{#if displayText}
						<div class="group">
							{#if block.textType === "heading"}
								<h3 class="text-[14px] font-semibold text-dl-text mt-4 mb-1">{displayText}</h3>
							{:else}
								{#if periods.length > 1}
									<div class="mb-1 opacity-0 group-hover:opacity-100 transition-opacity">
										<TimelineBar
											{periods}
											selected={displayPeriod}
											onSelect={(p) => selectPeriod(i, p)}
										/>
									</div>
								{/if}
								<div class="text-[10px] text-dl-text-dim mb-1 font-mono">{displayPeriod}</div>
								<!-- svelte-ignore a11y_no_static_element_interactions -->
								<div class="disclosure-text" onmouseup={handleTextMouseUp}>
									{@html applyHighlight(renderDisclosureText(displayText))}
								</div>
							{/if}
						</div>
					{/if}
				{:else if isTableBlock(block)}
					{@const chartable2 = isChartable(block)}
					{@const showChart2 = chartable2 && chartMode.get(block.block)}
					{@const spec2 = showChart2 ? getChartSpec(block) : null}
					<div class="group relative">
						<div class="absolute top-1 right-1 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
							{#if chartable2}
								<button
									class="p-1 rounded transition-colors {showChart2 ? 'text-dl-accent-light bg-dl-accent/10' : 'text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5'}"
									onclick={() => toggleChart(block.block)}
									title={showChart2 ? '표로 보기' : '차트로 보기'}
								>
									{#if showChart2}<Table2 size={12} />{:else}<BarChart3 size={12} />{/if}
								</button>
							{/if}
							{#if block.data?.rows?.length > 0}
								<button
									class="p-1 rounded text-dl-text-dim/30 hover:text-dl-text-muted hover:bg-white/5 transition-colors"
									onclick={() => copyTable(block, block.block)}
									title="테이블 복사"
								>
									{#if copiedTable === block.block}
										<Check size={12} class="text-dl-success" />
									{:else}
										<Copy size={12} />
									{/if}
								</button>
							{/if}
							{#if onAskAI}
								<button
									class="p-1 rounded text-dl-text-dim/30 hover:text-[#a78bfa] hover:bg-white/5 transition-colors"
									onclick={() => handleBlockAnalyze(block)}
									title="AI 분석"
								>
									<Sparkles size={12} />
								</button>
							{/if}
						</div>
						{#if showChart2 && spec2}
							{#await import("$lib/chart/ChartRenderer.svelte") then { default: ChartRenderer }}
								<ChartRenderer spec={spec2} />
							{/await}
						{:else}
							<TableRenderer {block} />
						{/if}
					</div>
				{/if}
			{/each}
		{/if}

		{#if topicData.blocks?.length === 0 && !hasTextDoc}
			<div class="text-center py-12 text-[13px] text-dl-text-dim">
				이 topic에 표시할 데이터가 없습니다
			</div>
		{/if}
	</div>
{/if}

<!-- "AI에게 물어보기" floating button -->
{#if floatBtn.show}
	<button
		class="ask-ai-float"
		style="left: {floatBtn.x}px; top: {floatBtn.y}px; transform: translate(-50%, -100%)"
		onclick={handleAskAI}
	>
		<span class="flex items-center gap-1">
			<MessageSquare size={10} />
			AI에게 물어보기
		</span>
	</button>
{/if}
