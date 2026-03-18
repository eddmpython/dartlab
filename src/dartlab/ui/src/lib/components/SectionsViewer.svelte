<script>
	import { fetchCompanySections, fetchCompanyShowAll } from "$lib/api.js";
	import { renderMarkdown } from "$lib/markdown.js";
	import { ChevronRight, ChevronDown, FileText, Loader2, BookOpen, BarChart3, Maximize2, Minimize2 } from "lucide-svelte";

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
	let rawMdPeriodIdx = $state(new Map()); // blockIdx → selected period index

	const TOPIC_LABELS = {
		companyOverview: "회사 개요", companyHistory: "회사 연혁", articlesOfIncorporation: "정관 사항",
		capitalChange: "자본금 변동", shareCapital: "주식 현황", dividend: "배당",
		productService: "사업 내용", rawMaterial: "원재료", businessOverview: "사업 개요",
		salesOrder: "매출/수주", riskDerivative: "위험관리/파생", majorContractsAndRnd: "주요 계약/R&D",
		otherReferences: "기타 참고사항", consolidatedStatements: "연결 재무제표", fsSummary: "재무제표 요약",
		consolidatedNotes: "연결 주석", financialStatements: "개별 재무제표", financialNotes: "개별 주석",
		fundraising: "자금조달", BS: "재무상태표", IS: "손익계산서", CIS: "포괄손익계산서",
		CF: "현금흐름표", SCE: "자본변동표", ratios: "재무비율", audit: "감사 의견",
		mdna: "경영진 분석(MD&A)", internalControl: "내부통제", auditContract: "감사 계약",
		nonAuditContract: "비감사 계약", boardOfDirectors: "이사회", shareholderMeeting: "주주총회",
		auditSystem: "감사 체계", outsideDirector: "사외이사", majorHolder: "주요 주주",
		majorHolderChange: "주주 변동", minorityHolder: "소수주주", stockTotal: "주식 총수",
		treasuryStock: "자기주식", employee: "직원 현황", executivePay: "임원 보수",
		executive: "임원 현황", executivePayAllTotal: "전체 보수 총액", executivePayIndividual: "개인별 보수",
		topPay: "5억이상 상위 보수", unregisteredExecutivePay: "미등기임원 보수", affiliateGroup: "계열회사",
		investedCompany: "투자회사", relatedPartyTx: "특수관계 거래", corporateBond: "사채 관리",
		privateOfferingUsage: "사모자금 사용", publicOfferingUsage: "공모자금 사용", shortTermBond: "단기사채",
		investorProtection: "투자자 보호", disclosureChanges: "공시변경 사항", contingentLiability: "우발채무",
		sanction: "제재/조치", subsequentEvents: "후발사건", expertConfirmation: "전문가 확인",
		subsidiaryDetail: "종속회사 상세", affiliateGroupDetail: "계열회사 상세",
		investmentInOtherDetail: "타법인 출자 상세", rndDetail: "R&D 상세",
	};

	const CHAPTER_LABELS = {
		"I": "I. 회사의 개요", "II": "II. 사업의 내용", "III": "III. 재무에 관한 사항",
		"IV": "IV. 감사인의 감사의견 등", "V": "V. 이사의 경영진단 및 분석의견",
		"VI": "VI. 이사회 등 회사의 기관에 관한 사항", "VII": "VII. 주주에 관한 사항",
		"VIII": "VIII. 임원 및 직원 등에 관한 사항", "IX": "IX. 계열회사 등에 관한 사항",
		"X": "X. 대주주 등과의 거래내용", "XI": "XI. 그 밖에 투자자 보호를 위하여 필요한 사항",
		"XII": "XII. 상세표",
	};

	const ROMAN_ORDER = { I:1, II:2, III:3, IV:4, V:5, VI:6, VII:7, VIII:8, IX:9, X:10, XI:11, XII:12 };
	function romanToInt(ch) { return ROMAN_ORDER[ch] ?? 99; }
	function topicLabel(topic) { return TOPIC_LABELS[topic] || topic; }
	function chapterLabel(ch) { return CHAPTER_LABELS[ch] || ch || "기타"; }

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

	function sectionStatusLabel(status) {
		if (status === "updated") return "최근 수정";
		if (status === "new") return "신규";
		if (status === "stale") return "과거 유지";
		return "유지";
	}

	function sectionStatusClass(status) {
		if (status === "updated") return "updated";
		if (status === "new") return "new";
		if (status === "stale") return "stale";
		return "stable";
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

	// ── 텍스트 ──

	function escapeHtml(text) {
		return String(text)
			.replaceAll("&", "&amp;")
			.replaceAll("<", "&lt;")
			.replaceAll(">", "&gt;")
			.replaceAll('"', "&quot;")
			.replaceAll("'", "&#39;");
	}

	function normalizeDisclosureLine(line) {
		return String(line || "")
			.replaceAll("\u00a0", " ")
			.replace(/\s+/g, " ")
			.trim();
	}

	function isStructuralHeadingLine(line) {
		if (!line || line.length > 88) return false;
		return /^\[.+\]$/.test(line)
			|| /^【.+】$/.test(line)
			|| /^[IVX]+\.\s/.test(line)
			|| /^\d+\.\s/.test(line)
			|| /^[가-힣]\.\s/.test(line)
			|| /^\(\d+\)\s/.test(line)
			|| /^\([가-힣]\)\s/.test(line);
	}

	function headingTag(line) {
		if (/^\(\d+\)\s/.test(line) || /^\([가-힣]\)\s/.test(line)) return "h5";
		return "h4";
	}

	function headingClass(line) {
		if (/^\[.+\]$/.test(line) || /^【.+】$/.test(line)) return "vw-h-bracket";
		if (/^\(\d+\)\s/.test(line) || /^\([가-힣]\)\s/.test(line)) return "vw-h-sub";
		return "vw-h-section";
	}

	function parseDisclosureUnits(text) {
		if (!text) return [];
		if (/^\|.+\|$/m.test(text) || /^#{1,3} /m.test(text) || /```/.test(text)) {
			return [{ kind: "markdown", text }];
		}

		const units = [];
		let paragraph = [];
		const flushParagraph = () => {
			if (paragraph.length === 0) return;
			units.push({ kind: "paragraph", text: paragraph.join(" ") });
			paragraph = [];
		};

		for (const rawLine of String(text).split("\n")) {
			const line = normalizeDisclosureLine(rawLine);
			if (!line) {
				flushParagraph();
				continue;
			}
			if (isStructuralHeadingLine(line)) {
				flushParagraph();
				units.push({ kind: "heading", text: line, tag: headingTag(line), className: headingClass(line) });
				continue;
			}
			paragraph.push(line);
		}
		flushParagraph();
		return units;
	}

	function periodDisplayLabel(period) {
		if (!period) return "";
		if (period.kind === "annual") return `${period.year}Q4`;
		if (period.year && period.quarter) return `${period.year}Q${period.quarter}`;
		return period.label || "";
	}

	function formatDisclosureText(text) {
		const units = parseDisclosureUnits(text);
		if (units.length === 0) return "";
		if (units[0]?.kind === "markdown") return renderMarkdown(text);
		let html = "";
		for (const unit of units) {
			if (unit.kind === "heading") {
				html += `<${unit.tag} class="${unit.className}">${escapeHtml(unit.text)}</${unit.tag}>`;
				continue;
			}
			html += `<p class="vw-para">${escapeHtml(unit.text)}</p>`;
		}
		return html;
	}

	function formatHeadingText(text) {
		if (!text) return "";
		const lines = text.trim().split("\n").filter(l => l.trim());
		let html = "";
		for (const line of lines) {
			const t = line.trim();
			if (/^[가-힣]\.\s/.test(t) || /^\d+[-.]/.test(t))
				html += `<h4 class="vw-h-section">${t}</h4>`;
			else if (/^\(\d+\)\s/.test(t) || /^\([가-힣]\)\s/.test(t))
				html += `<h5 class="vw-h-sub">${t}</h5>`;
			else if (/^\[.+\]$/.test(t) || /^【.+】$/.test(t))
				html += `<h4 class="vw-h-bracket">${t}</h4>`;
			else
				html += `<h5 class="vw-h-sub">${t}</h5>`;
		}
		return html;
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

	function renderDiffStatus(status) {
		if (status === "updated") return "변경 있음";
		if (status === "new") return "직전 없음";
		return "직전과 동일";
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

	// ── 숫자 ──

	function isNumericCell(val) {
		if (val == null) return false;
		return /^-?[\d,.]+%?$/.test(String(val).trim().replace(/,/g, ""));
	}
	function isNegative(val) {
		if (val == null) return false;
		return /^-[\d.]+/.test(String(val).trim().replace(/,/g, ""));
	}
	function formatScaledCell(val, divisor) {
		if (val == null || val === "") return "";
		const num = typeof val === "number" ? val : Number(String(val).replace(/,/g, ""));
		if (isNaN(num)) return String(val);
		if (divisor <= 1) return num.toLocaleString("ko-KR");
		const scaled = num / divisor;
		return Number.isInteger(scaled) ? scaled.toLocaleString("ko-KR")
			: scaled.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	}
	function formatCell(val) {
		if (val == null || val === "") return "";
		const s = String(val).trim();
		if (s.includes(",")) return s;
		const m = s.match(/^(-?\d+)(\.\d+)?(%?)$/);
		if (m) return m[1].replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (m[2] || "") + (m[3] || "");
		return s;
	}

	function getTopicChapter(topic) {
		if (!sections?.rows) return null;
		return sections.rows.find(r => r.topic === topic)?.chapter || null;
	}

	/** 기간 정렬키: 최신 먼저 */
	function periodSortKey(p) {
		const m = p.match(/^(\d{4})(Q([1-4]))?$/);
		if (!m) return "0000_0";
		const y = m[1];
		const q = m[3] || "5"; // 연간은 Q4 뒤
		return `${y}_${q}`;
	}
	function sortPeriodsDesc(arr) {
		return [...arr].sort((a, b) => periodSortKey(b).localeCompare(periodSortKey(a)));
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

									{#each textDocument.sections as section}
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

<style>
	.vw-report-shell {
		display: flex;
		flex-direction: column;
		gap: 22px;
		margin-bottom: 44px;
	}
	.vw-report-header {
		max-width: 840px;
		padding-bottom: 4px;
	}
	.vw-report-badges,
	.vw-section-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
	.vw-text-section {
		padding-bottom: 38px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	.vw-text-section:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}
	.vw-text-section-stale {
		position: relative;
	}
	.vw-text-section-stale::before {
		content: "";
		position: absolute;
		left: -14px;
		top: 0;
		bottom: 0;
		width: 2px;
		border-radius: 999px;
		background: linear-gradient(180deg, rgba(251, 191, 36, 0.65), rgba(251, 191, 36, 0.08));
	}
	.vw-section-meta {
		margin-bottom: 18px;
	}
	.vw-section-timeline {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		max-width: 840px;
		margin-bottom: 18px;
	}
	.vw-timeline-chip {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 9px 11px;
		border-radius: 10px;
		border: 1px solid rgba(148, 163, 184, 0.12);
		background: rgba(8, 11, 18, 0.32);
		color: rgba(226, 232, 240, 0.72);
		cursor: pointer;
		transition: border-color 120ms ease, background 120ms ease, color 120ms ease;
	}
	.vw-timeline-chip:hover {
		border-color: rgba(148, 163, 184, 0.22);
		background: rgba(255, 255, 255, 0.04);
		color: rgba(241, 245, 249, 0.88);
	}
	.vw-timeline-chip.is-active {
		border-color: rgba(251, 146, 60, 0.35);
		background: rgba(251, 146, 60, 0.08);
		color: rgba(255, 237, 213, 0.95);
	}
	.vw-timeline-label {
		font-size: 11.5px;
		font-weight: 600;
		letter-spacing: 0.01em;
	}
	.vw-timeline-overflow {
		display: inline-flex;
		align-items: center;
		padding: 0 4px;
		font-size: 10px;
		color: rgba(148, 163, 184, 0.46);
	}
	.vw-meta-pill,
	.vw-status-pill {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 4px 9px;
		border-radius: 999px;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.01em;
		border: 1px solid rgba(148, 163, 184, 0.14);
		background: rgba(15, 18, 25, 0.46);
		color: rgba(226, 232, 240, 0.76);
	}
	.vw-status-pill.stable {
		border-color: rgba(148, 163, 184, 0.16);
		color: rgba(226, 232, 240, 0.72);
	}
	.vw-status-pill.updated {
		border-color: rgba(52, 211, 153, 0.18);
		background: rgba(52, 211, 153, 0.08);
		color: rgba(167, 243, 208, 0.92);
	}
	.vw-status-pill.new {
		border-color: rgba(96, 165, 250, 0.2);
		background: rgba(59, 130, 246, 0.08);
		color: rgba(191, 219, 254, 0.92);
	}
	.vw-status-pill.stale {
		border-color: rgba(251, 191, 36, 0.18);
		background: rgba(251, 191, 36, 0.08);
		color: rgba(253, 230, 138, 0.92);
	}
	.vw-section-body {
		margin-bottom: 18px;
	}
	.vw-body-frame {
		padding: 24px 26px 10px;
		border-radius: 16px;
		border: 1px solid rgba(148, 163, 184, 0.1);
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.028), rgba(255, 255, 255, 0.012)),
			rgba(7, 10, 17, 0.72);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
	}
	.vw-section-actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 8px;
		margin-top: 4px;
		margin-bottom: 12px;
	}
	.vw-data-divider {
		margin: 6px 0 18px;
		padding-top: 14px;
		border-top: 1px solid rgba(255, 255, 255, 0.06);
	}
	.vw-data-kicker {
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: rgba(148, 163, 184, 0.42);
		margin-bottom: 6px;
	}
	.vw-data-title {
		font-size: 13px;
		font-weight: 600;
		color: rgba(226, 232, 240, 0.9);
	}
	.vw-heading-block {
		margin-top: 28px;
		margin-bottom: 12px;
	}
	.vw-heading-node + .vw-heading-node {
		margin-top: 2px;
	}
	.vw-heading-block :global(.vw-h-section) {
		margin-top: 40px;
		margin-bottom: 12px;
		font-size: 18px;
		font-weight: 700;
		color: var(--color-dl-text);
		line-height: 1.55;
		letter-spacing: -0.01em;
	}
	.vw-heading-block :global(.vw-h-sub) {
		margin-top: 20px;
		margin-bottom: 8px;
		font-size: 15.5px;
		font-weight: 600;
		color: var(--color-dl-text);
		opacity: 0.92;
		line-height: 1.55;
	}
	.vw-heading-block :global(.vw-h-bracket) {
		margin-top: 34px;
		margin-bottom: 12px;
		font-size: 18.5px;
		font-weight: 700;
		color: var(--color-dl-text);
		letter-spacing: -0.01em;
	}
	.vw-body-block {
		margin-bottom: 28px;
	}
	.disclosure-text {
		font-size: 15px;
		line-height: 1.92;
		max-width: 820px;
	}
	.disclosure-text :global(.vw-h-bracket) {
		margin-top: 34px;
		margin-bottom: 12px;
		font-size: 18px;
		font-weight: 700;
		color: var(--color-dl-text);
		letter-spacing: -0.01em;
	}
	.disclosure-text :global(.vw-h-section) {
		margin-top: 34px;
		margin-bottom: 12px;
		font-size: 17px;
		font-weight: 700;
		color: var(--color-dl-text);
	}
	.disclosure-text :global(.vw-h-sub) {
		margin-top: 18px;
		margin-bottom: 8px;
		font-size: 15.5px;
		font-weight: 600;
		color: var(--color-dl-text);
		opacity: 0.92;
	}
	.disclosure-text :global(.vw-para) {
		margin-bottom: 14px;
		color: rgba(241, 245, 249, 0.82);
	}
	.disclosure-text :global(.vw-para:first-child) {
		font-size: 15.5px;
		color: rgba(248, 250, 252, 0.92);
	}
	.vw-digest {
		margin-top: 12px;
		margin-bottom: 14px;
		padding: 14px 16px;
		border-radius: 6px;
		border: 1px solid rgba(30, 36, 51, 0.35);
		background: rgba(15, 18, 25, 0.5);
		max-width: 720px;
	}
	.vw-diff-deleted {
		padding: 9px 14px 9px 16px;
		margin-bottom: 8px;
		border-left: 3px solid #f87171;
		background: rgba(248, 113, 113, 0.06);
		color: rgba(241, 245, 249, 0.55);
		font-size: 14px;
		line-height: 1.85;
		border-radius: 0 4px 4px 0;
		max-width: 820px;
	}
	.vw-diff-added {
		padding: 9px 14px 9px 16px;
		margin-bottom: 8px;
		border-left: 3px solid #34d399;
		background: rgba(52, 211, 153, 0.06);
		color: rgba(241, 245, 249, 0.82);
		font-size: 14px;
		line-height: 1.85;
		border-radius: 0 4px 4px 0;
		max-width: 820px;
	}
	.vw-diff-flow {
		padding-top: 2px;
	}
	.vw-table-wrap {
		margin-top: 4px;
		margin-bottom: 28px;
		border-radius: 6px;
		border: 1px solid rgba(30, 36, 51, 0.4);
		overflow: hidden;
	}
	.markdown-table :global(table) {
		width: 100%;
		border-collapse: collapse;
		font-size: 12px;
	}
	.markdown-table :global(th),
	.markdown-table :global(td) {
		padding: 6px 10px;
		border-bottom: 1px solid rgba(255,255,255,0.04);
		text-align: left;
		white-space: nowrap;
	}
	.markdown-table :global(th) {
		font-weight: 600;
		font-size: 10.5px;
		color: rgba(148, 163, 184, 0.7);
	}
	.markdown-table :global(td) {
		color: rgba(148, 163, 184, 0.85);
	}
	.markdown-table :global(tr:nth-child(even)) {
		background: rgba(255,255,255,0.012);
	}
</style>
