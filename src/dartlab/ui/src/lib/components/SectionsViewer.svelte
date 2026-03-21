<script>
	import { fetchCompanySections, fetchCompanyShowAll } from "$lib/api.js";
	import { renderMarkdown } from "$lib/markdown.js";
	import { ChevronRight, ChevronDown, FileText, Loader2, BookOpen, BarChart3, Maximize2, Minimize2 } from "lucide-svelte";
	import {
		topicLabel, chapterLabel, romanToInt,
	} from "$lib/viewer/topicLabels.js";
	import {
		escapeHtml, normalizeDisclosureLine, isStructuralHeadingLine,
		parseDisclosureUnits, formatDisclosureText, formatHeadingText,
		isNumericCell, isNegative, formatScaledCell, formatCell,
		sortPeriodsDesc, periodDisplayLabel,
		sectionStatusLabel, sectionStatusClass, renderDiffStatus,
	} from "$lib/viewer/disclosureText.js";
	import "$lib/viewer/viewer.css";

	let { stockCode = null, onTopicChange = null } = $props();

	let sections = $state(null);
	let loading = $state(false);
	let expandedChapters = $state(new Set());
	let selectedTopic = $state(null);
	let selectedChapter = $state(null);
	let topicBlocks = $state([]);
	let textDocument = $state(null);
	let contentLoading = $state(false);
	let periods = $state([]);
	let selectedTextTimeline = $state(new Map());
	let topicCache = new Map();
	let isFullscreen = $state(false);
	let rawMdPeriodIdx = $state(new Map());

	// 점진 렌더 — 초기 10개 섹션만 표시, 스크롤 시 추가
	let visibleSections = $state(10);
	let sectionSentinel = $state(null);

	$effect(() => { if (selectedTopic) visibleSections = 10; });

	$effect(() => {
		if (!sectionSentinel) return;
		const obs = new IntersectionObserver((entries) => {
			if (entries[0]?.isIntersecting) {
				visibleSections = Math.min(visibleSections + 10, textDocument?.sections?.length || 999);
			}
		}, { rootMargin: "400px" });
		obs.observe(sectionSentinel);
		return () => obs.disconnect();
	});

	$effect(() => { if (stockCode) loadData(); });

	async function loadData() {
		loading = true;
		sections = null;
		selectedTopic = null;
		selectedChapter = null;
		topicBlocks = [];
		textDocument = null;
		topicCache = new Map();
		try {
			const secRes = await fetchCompanySections(stockCode);
			sections = secRes.payload;
			if (sections?.columns) {
				periods = sections.columns.filter(c => /^\d{4}(Q[1-4])?$/.test(c));
			}
			const tree = buildTocTree(sections?.rows);
			if (tree.length > 0) {
				expandedChapters = new Set([tree[0].chapter]);
				if (tree[0].topics.length > 0) {
					selectTopic(tree[0].topics[0].topic, tree[0].chapter);
				}
			}
		} catch (e) { console.error("viewer load error:", e); }
		loading = false;
	}

	async function selectTopic(topic, chapter) {
		if (selectedTopic === topic) return;
		selectedTopic = topic;
		selectedChapter = chapter || null;
		selectedTextTimeline = new Map();
		rawMdPeriodIdx = new Map();
		onTopicChange?.(topic, topicLabel(topic));
		if (topicCache.has(topic)) {
			const cached = topicCache.get(topic);
			topicBlocks = cached.blocks || [];
			textDocument = cached.textDocument || null;
			return;
		}
		topicBlocks = [];
		textDocument = null;
		contentLoading = true;
		try {
			const res = await fetchCompanyShowAll(stockCode, topic);
			topicBlocks = res.blocks || [];
			textDocument = res.textDocument || null;
			topicCache.set(topic, { blocks: topicBlocks, textDocument });
		} catch (e) { console.error("topic load error:", e); topicBlocks = []; textDocument = null; }
		contentLoading = false;
	}

	function toggleChapter(ch) {
		const next = new Set(expandedChapters);
		if (next.has(ch)) next.delete(ch); else next.add(ch);
		expandedChapters = next;
	}

	function selectTextTimelinePeriod(sectionId, periodLabel) {
		const next = new Map(selectedTextTimeline);
		if (next.get(sectionId) === periodLabel) next.delete(sectionId);
		else next.set(sectionId, periodLabel);
		selectedTextTimeline = next;
	}

	function selectRawMdPeriod(blockIdx, periodIdx) {
		const next = new Map(rawMdPeriodIdx);
		next.set(blockIdx, periodIdx);
		rawMdPeriodIdx = next;
	}

	function buildTocTree(rows) {
		if (!rows) return [];
		const chapterMap = new Map();
		const seenTopics = new Set();
		for (const row of rows) {
			const ch = row.chapter || "";
			if (!chapterMap.has(ch)) chapterMap.set(ch, { chapter: ch, topics: [] });
			if (!seenTopics.has(row.topic)) {
				seenTopics.add(row.topic);
				chapterMap.get(ch).topics.push({ topic: row.topic, source: row.source || "docs" });
			}
		}
		return [...chapterMap.values()].sort((a, b) => romanToInt(a.chapter) - romanToInt(b.chapter));
	}

	function getActiveSectionView(section) {
		const label = selectedTextTimeline.get(section.id);
		if (label && section?.views?.[label]) return section.views[label];
		return section?.latest || null;
	}

	function isActiveTimelinePeriod(section, periodLabel) {
		const explicit = selectedTextTimeline.get(section.id);
		if (explicit) return explicit === periodLabel;
		return section?.latest?.period?.label === periodLabel;
	}

	function hasExplicitTimelineSelection(section) {
		return selectedTextTimeline.has(section.id);
	}

	function buildDiffRenderUnits(view) {
		if (!view) return [];
		const units = parseDisclosureUnits(view.body);
		if (units.length === 0 || units[0]?.kind === "markdown") return units;
		if (!view.prevPeriod?.label || !view.diff?.length) return units;

		const diffItems = [];
		for (const chunk of view.diff) {
			for (const paragraph of chunk.paragraphs || []) {
				diffItems.push({ kind: chunk.kind, text: normalizeDisclosureLine(paragraph) });
			}
		}

		const renderUnits = [];
		let diffIdx = 0;
		for (const unit of units) {
			if (unit.kind !== "paragraph") {
				renderUnits.push(unit);
				continue;
			}
			while (diffIdx < diffItems.length && diffItems[diffIdx].kind === "removed") {
				renderUnits.push({ kind: "removed", text: diffItems[diffIdx].text });
				diffIdx += 1;
			}
			if (diffIdx < diffItems.length && ["same", "added"].includes(diffItems[diffIdx].kind)) {
				renderUnits.push({ kind: diffItems[diffIdx].kind, text: diffItems[diffIdx].text || unit.text });
				diffIdx += 1;
			} else {
				renderUnits.push({ kind: "same", text: unit.text });
			}
		}
		while (diffIdx < diffItems.length) {
			renderUnits.push({ kind: diffItems[diffIdx].kind, text: diffItems[diffIdx].text });
			diffIdx += 1;
		}
		return renderUnits;
	}

	function getTopicChapter(topic) {
		if (!sections?.rows) return null;
		return sections.rows.find(r => r.topic === topic)?.chapter || null;
	}

	let nonTextBlocks = $derived(topicBlocks.filter(block => block.kind !== "text"));
	let totalTopics = $derived(sections?.rows ? new Set(sections.rows.map(r => r.topic)).size : 0);
</script>

<div class="flex flex-col h-full font-sans bg-dl-bg-dark">
	{#if loading}
		<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim">
			<Loader2 size={18} class="animate-spin" />
			<span class="text-[13px]">공시 데이터 로딩 중...</span>
		</div>

	{:else if sections?.rows}
		<div class="flex flex-1 overflow-hidden min-h-0">
			<!-- 좌측 목차 -->
			{#if !isFullscreen}
			<nav class="w-[220px] flex-shrink-0 overflow-y-auto border-r border-dl-border/20 bg-dl-bg-card/50">
				<div class="px-3 py-2.5 border-b border-dl-border/20">
					{#if periods.length > 0}
						<div class="text-[11px] text-dl-text-dim">{periods.length}개 기간 · {periods[0]} ~ {periods[periods.length-1]}</div>
					{/if}
				</div>
				{#each buildTocTree(sections.rows) as group}
					<div>
						<button
							class="flex items-center gap-1.5 w-full px-3 py-2 text-left text-[11px] font-semibold tracking-wide text-dl-text-dim border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"
							onclick={() => toggleChapter(group.chapter)}
						>
							{#if expandedChapters.has(group.chapter)}
								<ChevronDown size={11} class="flex-shrink-0 opacity-40" />
							{:else}
								<ChevronRight size={11} class="flex-shrink-0 opacity-40" />
							{/if}
							<span class="truncate">{chapterLabel(group.chapter)}</span>
							<span class="ml-auto text-[9px] opacity-30 font-normal">{group.topics.length}</span>
						</button>
						{#if expandedChapters.has(group.chapter)}
							<div class="py-0.5">
								{#each group.topics as item}
									<button
										class="group flex items-center gap-1.5 w-full px-2 py-[7px] pl-6 text-left text-[12px] transition-all duration-100
											{selectedTopic === item.topic
												? 'bg-white/[0.06] text-dl-text font-medium border-l-2 border-dl-text/60 pl-[22px]'
												: 'text-dl-text-muted hover:bg-white/[0.03] hover:text-dl-text border-l-2 border-transparent'}"
										onclick={() => selectTopic(item.topic, group.chapter)}
									>
										{#if item.source === "finance"}
											<BarChart3 size={11} class="flex-shrink-0 text-blue-400/40" />
										{:else if item.source === "report"}
											<BookOpen size={11} class="flex-shrink-0 text-emerald-400/40" />
										{:else}
											<FileText size={11} class="flex-shrink-0 opacity-30" />
										{/if}
										<span class="truncate flex-1">{topicLabel(item.topic)}</span>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				{/each}
			</nav>
			{/if}

			<!-- 우측 본문 -->
			<main class="flex-1 overflow-y-auto min-w-0">
				{#if !selectedTopic}
					<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim">
						<FileText size={32} strokeWidth={1} class="opacity-20" />
						<p class="text-[13px]">좌측에서 섹션을 선택하세요</p>
					</div>
				{:else}
					<!-- topic 헤더 (sticky) -->
					<div class="sticky top-0 z-10 px-8 py-3 bg-dl-bg-card/95 backdrop-blur-md border-b border-dl-border/20 flex items-center">
						<div class="flex-1 min-w-0">
							{#if selectedChapter || getTopicChapter(selectedTopic)}
								<div class="text-[10px] text-dl-text-dim/50 mb-0.5">{chapterLabel(selectedChapter || getTopicChapter(selectedTopic))}</div>
							{/if}
							<h3 class="text-[16px] font-semibold text-dl-text">{topicLabel(selectedTopic)}</h3>
						</div>
						<button
							class="p-1.5 rounded hover:bg-white/[0.06] text-dl-text-dim/50 hover:text-dl-text transition-colors"
							onclick={() => isFullscreen = !isFullscreen}
							title="{isFullscreen ? '목차 표시' : '전체화면'}"
						>
							{#if isFullscreen}
								<Minimize2 size={15} />
							{:else}
								<Maximize2 size={15} />
							{/if}
						</button>
					</div>

					{#if contentLoading}
						<div class="flex items-center justify-center gap-2 p-12 text-dl-text-dim">
							<Loader2 size={16} class="animate-spin" />
						</div>
					{:else}
						<article class="py-6 px-8">
							{#if topicBlocks.length === 0 && !(textDocument?.sections?.length > 0)}
								<div class="text-center text-[13px] text-dl-text-dim py-8">데이터 없음</div>
							{/if}

							{#if textDocument?.sections?.length > 0}
								<section class="vw-report-shell">
									<div class="vw-report-header">
										<div class="vw-report-badges">
											{#if textDocument.latestPeriod}
												<span class="vw-meta-pill">최신 기준 {periodDisplayLabel(textDocument.latestPeriod)}</span>
											{/if}
											{#if textDocument.firstPeriod}
												<span class="vw-meta-pill">커버리지 {periodDisplayLabel(textDocument.firstPeriod)}~{periodDisplayLabel(textDocument.latestPeriod)}</span>
											{/if}
											<span class="vw-meta-pill">본문 {textDocument.sectionCount}개</span>
											{#if textDocument.updatedCount > 0}
												<span class="vw-meta-pill">최근 수정 {textDocument.updatedCount}개</span>
											{/if}
											{#if textDocument.newCount > 0}
												<span class="vw-meta-pill">신규 {textDocument.newCount}개</span>
											{/if}
											{#if textDocument.staleCount > 0}
												<span class="vw-meta-pill">과거 유지 {textDocument.staleCount}개</span>
											{/if}
										</div>
									</div>

									{#each textDocument.sections.slice(0, visibleSections) as section}
										{@const activeView = getActiveSectionView(section)}
										{@const explicitSelection = hasExplicitTimelineSelection(section)}
										<div class="vw-text-section {section.status === 'stale' ? 'vw-text-section-stale' : ''}">
											{#if section.headingPath?.length > 0}
												<div class="vw-heading-block">
													{#each section.headingPath as heading}
														<div class="vw-heading-node">
															{@html formatHeadingText(heading.text)}
														</div>
													{/each}
												</div>
											{/if}

											<div class="vw-section-meta">
												<span class="vw-status-pill {sectionStatusClass(section.status)}">{sectionStatusLabel(section.status)}</span>
												{#if section.latestPeriod?.label}
													<span class="vw-meta-pill">최신 {periodDisplayLabel(section.latestPeriod)}</span>
												{/if}
												{#if section.firstPeriod?.label && section.firstPeriod.label !== section.latestPeriod?.label}
													<span class="vw-meta-pill">최초 {periodDisplayLabel(section.firstPeriod)}</span>
												{/if}
												{#if section.periodCount > 0}
													<span class="vw-meta-pill">{section.periodCount}기간</span>
												{/if}
												{#if section.latestChange}
													<span class="vw-meta-pill">최근 변경 {section.latestChange}</span>
												{/if}
											</div>

											{#if section.timeline?.length > 0}
												<div class="vw-section-timeline">
													{#each section.timeline as entry}
														<button
															class="vw-timeline-chip {isActiveTimelinePeriod(section, entry.period.label) ? 'is-active' : ''}"
															onclick={() => selectTextTimelinePeriod(section.id, entry.period.label)}
														>
															<span class="vw-timeline-label">{periodDisplayLabel(entry.period)}</span>
														</button>
													{/each}
												</div>
											{/if}

											{#if explicitSelection && activeView}
												<div class="vw-section-actions">
													<span class="vw-meta-pill">선택 {periodDisplayLabel(activeView.period)}</span>
													{#if activeView.prevPeriod?.label}
														<span class="vw-meta-pill">비교 {periodDisplayLabel(activeView.prevPeriod)}</span>
													{:else}
														<span class="vw-meta-pill">비교 없음</span>
													{/if}
													<span class="vw-meta-pill">{renderDiffStatus(activeView.status)}</span>
												</div>
											{/if}

											{#if explicitSelection && activeView?.digest?.items?.length > 0}
												{@const dg = activeView.digest}
												<div class="vw-digest">
													<div class="flex items-center gap-2 mb-2">
														<span class="text-[11px] font-medium text-dl-text">{dg.to} vs {dg.from}</span>
														<span class="text-[10px] text-dl-text-dim/40">선택 시점 기준 변경 요약</span>
													</div>
													<div class="space-y-1">
														{#each dg.items.filter(it => it.kind === "numeric") as it}
															<div class="text-[12px] text-dl-text/80 flex items-center gap-1.5">
																<span class="w-[5px] h-[5px] rounded-full bg-blue-400/60 shrink-0"></span>
																{it.text}
															</div>
														{/each}
														{#each dg.items.filter(it => it.kind === "added") as it}
															<div class="text-[12px] text-emerald-400/70 flex items-start gap-1.5">
																<span class="w-[5px] h-[5px] rounded-full bg-emerald-400/50 shrink-0 mt-1.5"></span>
																<span class="flex-1">{it.text}</span>
															</div>
														{/each}
														{#each dg.items.filter(it => it.kind === "removed") as it}
															<div class="text-[12px] text-dl-text/50 flex items-start gap-1.5">
																<span class="w-[5px] h-[5px] rounded-full bg-red-400/40 shrink-0 mt-1.5"></span>
																<span class="flex-1">{it.text}</span>
															</div>
														{/each}
														{#if dg.wordingCount > 0}
															<div class="text-[10px] text-dl-text-dim/35 mt-1">외 {dg.wordingCount}건 문구 수정</div>
														{/if}
													</div>
												</div>
											{/if}

											{#if activeView}
												{#if explicitSelection && activeView.prevPeriod?.label && activeView.diff?.length > 0}
													<div class="disclosure-text vw-section-body vw-body-frame vw-diff-flow">
														{#each buildDiffRenderUnits(activeView) as unit}
															{#if unit.kind === "heading"}
																{@html formatHeadingText(unit.text)}
															{:else if unit.kind === "same"}
																<p class="vw-para">{unit.text}</p>
															{:else if unit.kind === "added"}
																<div class="vw-diff-added">{unit.text}</div>
															{:else if unit.kind === "removed"}
																<div class="vw-diff-deleted">{unit.text}</div>
															{/if}
														{/each}
													</div>
												{:else}
													<div class="disclosure-text vw-section-body vw-body-frame">
														{@html formatDisclosureText(activeView.body)}
													</div>
												{/if}
											{/if}
										</div>
									{/each}
									{#if visibleSections < (textDocument?.sections?.length || 0)}
										<div bind:this={sectionSentinel} class="h-4"></div>
									{/if}
								</section>
							{/if}

							{#if nonTextBlocks.length > 0}
								<div class="vw-data-divider">
									<div class="vw-data-kicker">Structured Data</div>
									<div class="vw-data-title">표 / 정형 데이터</div>
								</div>
							{/if}

							{#each nonTextBlocks as block}
								<!-- ═══ FINANCE ═══ -->
								{#if block.kind === "finance"}
									{@const cols = block.data?.columns || []}
									{@const rows = block.data?.rows || []}
									{@const meta = block.meta || {}}
									{@const divisor = meta.scaleDivisor || 1}
									{#if meta.scale}
										<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1">(단위: {meta.scale})</div>
									{/if}
									<div class="vw-table-wrap">
										<div class="overflow-x-auto">
											<table class="w-full border-collapse text-[12px]">
												<thead>
													<tr>
														{#each cols as col, ci}
															{@const isPeriod = /^\d{4}/.test(col)}
															<th class="px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																{isPeriod ? 'text-right text-dl-text-dim/70' : 'text-left text-dl-text'}
																{ci === 0 ? 'sticky left-0 z-[2] bg-dl-bg-card' : 'bg-dl-bg-card'}">{col}</th>
														{/each}
													</tr>
												</thead>
												<tbody>
													{#each rows as row, ri}
														<tr class="hover:bg-white/[0.03] {ri % 2 === 1 ? 'bg-white/[0.012]' : ''}">
															{#each cols as col, ci}
																{@const val = row[col] ?? ""}
																{@const numeric = isNumericCell(val)}
																{@const neg = isNegative(val)}
																{@const formatted = numeric ? formatScaledCell(val, divisor) : val}
																<td class="px-3 py-1.5 border-b border-white/[0.025]
																	{numeric ? 'text-right tabular-nums font-mono text-[11.5px]' : 'whitespace-nowrap'}
																	{neg ? 'text-red-400/60' : numeric ? 'text-dl-text/90' : ''}
																	{ci === 0 ? 'text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark text-[12px]' : 'text-dl-text-muted'}
																	{ci === 0 && ri % 2 === 1 ? '!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]' : ''}">{formatted}</td>
															{/each}
														</tr>
													{/each}
												</tbody>
											</table>
										</div>
									</div>

								<!-- ═══ STRUCTURED 테이블 ═══ -->
								{:else if block.kind === "structured"}
									{@const cols = block.data?.columns || []}
									{@const rows = block.data?.rows || []}
									{@const meta = block.meta || {}}
									{@const divisor = meta.scaleDivisor || 1}
									{#if meta.scale}
										<div class="text-[10px] text-dl-text-dim/50 text-right mb-1 pr-1">(단위: {meta.scale})</div>
									{/if}
									<div class="vw-table-wrap">
										<div class="overflow-x-auto">
											<table class="w-full border-collapse text-[12px]">
												<thead>
													<tr>
														{#each cols as col, ci}
															{@const isPeriod = /^\d{4}/.test(col)}
															<th class="px-3 py-2 font-semibold text-[10.5px] tracking-wide border-b border-dl-border/20 whitespace-nowrap
																{isPeriod ? 'text-right text-dl-text-dim/70' : 'text-left text-dl-text'}
																{ci === 0 ? 'sticky left-0 z-[2] bg-dl-bg-card' : 'bg-dl-bg-card'}">{col}</th>
														{/each}
													</tr>
												</thead>
												<tbody>
													{#each rows as row, ri}
														<tr class="hover:bg-white/[0.03] {ri % 2 === 1 ? 'bg-white/[0.012]' : ''}">
															{#each cols as col, ci}
																{@const val = row[col] ?? ""}
																{@const numeric = isNumericCell(val)}
																{@const neg = isNegative(val)}
																{@const formatted = numeric ? (divisor > 1 ? formatScaledCell(val, divisor) : formatCell(val)) : val}
																<td class="px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	{numeric ? 'text-right tabular-nums' : 'whitespace-pre-wrap'}
																	{neg ? 'text-red-400/60' : numeric ? 'text-dl-text/90' : ''}
																	{ci === 0 ? 'text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark' : 'text-dl-text-muted'}
																	{ci === 0 && ri % 2 === 1 ? '!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]' : ''}">{formatted}</td>
															{/each}
														</tr>
													{/each}
												</tbody>
											</table>
										</div>
									</div>

								<!-- ═══ RAW MARKDOWN ═══ -->
								{:else if block.kind === "raw_markdown" && block.rawMarkdown}
									{@const mdPeriods = sortPeriodsDesc(Object.keys(block.rawMarkdown))}
									{@const selIdx = rawMdPeriodIdx.get(block.block) ?? 0}
									{@const selPeriod = mdPeriods[selIdx] || mdPeriods[0]}
									<div class="vw-table-wrap bg-dl-bg-card/10">
										{#if mdPeriods.length > 1}
											<div class="flex items-center gap-1 px-4 py-2 border-b border-dl-border/10 overflow-x-auto">
												{#each mdPeriods.slice(0, 8) as p, pi}
													<button
														class="px-2 py-0.5 rounded text-[10px] transition-colors
															{pi === selIdx ? 'bg-white/[0.08] text-dl-text font-medium' : 'text-dl-text-dim/50 hover:text-dl-text-dim hover:bg-white/[0.03]'}"
														onclick={() => selectRawMdPeriod(block.block, pi)}
													>{p}</button>
												{/each}
												{#if mdPeriods.length > 8}
													<span class="text-[9px] text-dl-text-dim/30">외 {mdPeriods.length - 8}개</span>
												{/if}
											</div>
										{/if}
										<div class="px-4 py-3">
											<div class="markdown-table overflow-x-auto">
												{@html renderMarkdown(block.rawMarkdown[selPeriod])}
											</div>
										</div>
									</div>

								<!-- ═══ REPORT ═══ -->
								{:else if block.kind === "report"}
									{@const cols = block.data?.columns || []}
									{@const rows = block.data?.rows || []}
									<div class="vw-table-wrap border-emerald-500/15 bg-emerald-500/[0.02]">
										<div class="px-4 py-1.5 flex items-center gap-2 border-b border-emerald-500/10">
											<BookOpen size={12} class="text-emerald-400/50" />
											<span class="text-[10px] text-emerald-400/60">OpenDART 정형 데이터</span>
										</div>
										<div class="overflow-x-auto">
											<table class="w-full border-collapse text-[12px]">
												<thead><tr>
													{#each cols as col, ci}
														{@const isPeriod = /^\d{4}/.test(col)}
														<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap
															{isPeriod ? 'text-right text-dl-text-dim/70' : 'text-left text-dl-text'}
															{ci === 0 ? 'sticky left-0 z-[2] bg-dl-bg-card' : 'bg-dl-bg-card'}">{col}</th>
													{/each}
												</tr></thead>
												<tbody>
													{#each rows as row, ri}
														<tr class="hover:bg-white/[0.03] {ri % 2 === 1 ? 'bg-white/[0.012]' : ''}">
															{#each cols as col, ci}
																{@const val = row[col] ?? ""}
																{@const numeric = isNumericCell(val)}
																{@const neg = isNegative(val)}
																<td class="px-3 py-1.5 border-b border-white/[0.025] max-w-[300px]
																	{numeric ? 'text-right tabular-nums' : 'whitespace-pre-wrap'}
																	{neg ? 'text-red-400/60' : numeric ? 'text-dl-text/90' : ''}
																	{ci === 0 ? 'text-dl-text font-medium sticky left-0 z-[1] bg-dl-bg-dark' : 'text-dl-text-muted'}
																	{ci === 0 && ri % 2 === 1 ? '!bg-[color-mix(in_srgb,var(--color-dl-bg-dark),white_1.2%)]' : ''}">{numeric ? formatCell(val) : val}</td>
															{/each}
														</tr>
													{/each}
												</tbody>
											</table>
										</div>
									</div>

								<!-- ═══ FALLBACK ═══ -->
								{:else if block.data?.columns?.length > 0}
									{@const cols = block.data.columns}
									{@const rows = block.data.rows || []}
									<div class="vw-table-wrap">
										<div class="overflow-x-auto">
											<table class="w-full border-collapse text-[12px]">
												<thead><tr>
													{#each cols as col}
														<th class="px-3 py-2 font-semibold text-[10.5px] border-b border-dl-border/20 whitespace-nowrap text-left text-dl-text bg-dl-bg-card">{col}</th>
													{/each}
												</tr></thead>
												<tbody>
													{#each rows as row, ri}
														<tr class="hover:bg-white/[0.03] {ri % 2 === 1 ? 'bg-white/[0.012]' : ''}">
															{#each cols as col}
																<td class="px-3 py-1.5 border-b border-white/[0.025] text-dl-text-muted">{row[col] ?? ""}</td>
															{/each}
														</tr>
													{/each}
												</tbody>
											</table>
										</div>
									</div>
								{/if}
							{/each}
						</article>
					{/if}
				{/if}
			</main>
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center h-full gap-3 text-dl-text-dim p-8">
			<FileText size={36} strokeWidth={1} class="opacity-20" />
			<p class="text-[13px]">공시 데이터를 불러올 수 없습니다</p>
		</div>
	{/if}
</div>
