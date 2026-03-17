<script>
	import { cn } from "$lib/utils.js";
	import { searchCompany, fetchDataSources, fetchDataPreview, downloadExcel, fetchCompany } from "$lib/api.js";
	import {
		X, Search, Database, ChevronRight, ChevronDown, Table2, FileText, Loader2,
		Download, Languages, Sparkles, Wrench, Brain, Link2, RotateCcw, Eye, CheckCircle2, ScrollText
	} from "lucide-svelte";
	import SectionsViewer from "./SectionsViewer.svelte";

	let {
		selectedCompany = null,
		recentCompanies = [],
		activeTab = "explore",
		evidenceMessage = null,
		activeEvidenceSection = null,
		selectedEvidenceIndex = null,
		onSelectCompany,
		onChangeTab,
		onAskAboutModule,
		onNotify,
		onClose,
	} = $props();

	let searchQuery = $state("");
	let searchResults = $state([]);
	let searchLoading = $state(false);
	let searchTimer = null;

	let sourceData = $state(null);
	let sourcesLoading = $state(false);
	let expandedCategories = $state(new Set());
	let activeModule = $state(null);
	let previewData = $state(null);
	let previewLoading = $state(false);
	let excelDownloading = $state(false);
	let useKoreanLabel = $state(true);
	let selectedModuleNames = $state(new Set());
	let loadedStockCode = $state(null);
	let companyInfo = $state(null);
	let overviewLoading = $state(false);
	let overviewCards = $state([]);
	let overviewHighlights = $state([]);
	let overviewSourceLabel = $state("");
	let overviewTrend = $state([]);
	let overviewNarrative = $state([]);
	let moduleQuery = $state("");
	let overviewError = $state("");
	let sourceError = $state("");
	let copiedLink = $state(false);
	let actionStatus = $state(null);
	let detailModal = $state(null);
	let detailDialog = $state(null);
	let overviewActions = $state([]);

	const CATEGORY_LABELS = {
		finance: "재무제표",
		report: "정기보고서",
		disclosure: "공시 서술",
		notes: "K-IFRS 주석",
		analysis: "분석",
		raw: "원본 데이터",
	};

	const CATEGORY_HINTS = {
		finance: "실적, 재무상태, 현금흐름을 빠르게 확인합니다.",
		report: "정기보고서에서 구조화된 회사 정보를 확인합니다.",
		disclosure: "사업, MD&A, 원재료 등 서술형 공시를 읽습니다.",
		notes: "주석 계정과 세부 항목을 깊게 확인합니다.",
		analysis: "파생 분석이나 인사이트 결과를 확인합니다.",
		raw: "원본 데이터나 가공 전 결과를 검증합니다.",
	};

	function categoryLabel(cat) {
		return CATEGORY_LABELS[cat] || cat;
	}

	function categoryHint(cat) {
		return CATEGORY_HINTS[cat] || "관련 데이터를 탐색합니다.";
	}

	function categoryStats(items) {
		const available = items.filter((item) => item.available).length;
		return `${available}/${items.length}`;
	}

	function getModuleDescription(source) {
		if (source.dataType === "timeseries") return "시계열 비교에 적합한 구조화 데이터";
		if (source.dataType === "table" || source.dataType === "dataframe") return "행·열 기준으로 직접 확인 가능한 표 데이터";
		if (source.dataType === "dict") return "핵심 필드를 빠르게 점검하는 요약 데이터";
		if (source.dataType === "text") return "원문 또는 긴 서술 데이터를 직접 읽는 모듈";
		return "구조화된 모듈 데이터";
	}

	function getSuggestedQuestion(source) {
		if (source.category === "finance") return `${selectedCompany?.corpName || "이 회사"}의 ${source.label}에서 가장 중요한 변화만 요약해줘`;
		if (source.category === "notes") return `${selectedCompany?.corpName || "이 회사"}의 ${source.label}에서 주의할 점을 설명해줘`;
		if (source.category === "disclosure") return `${selectedCompany?.corpName || "이 회사"}의 ${source.label} 핵심 내용을 요약해줘`;
		return `${selectedCompany?.corpName || "이 회사"}의 ${source.label} 데이터를 바탕으로 핵심 포인트를 정리해줘`;
	}

	function getAccountLabel(snakeId) {
		if (!previewData?.meta?.labels || !useKoreanLabel) return snakeId;
		return previewData.meta.labels[snakeId] || snakeId;
	}

	function getAccountLevel(snakeId) {
		if (!previewData?.meta?.levels) return 1;
		return previewData.meta.levels[snakeId] || 1;
	}

	function getUnit() {
		if (previewData?.meta?.unit) return previewData.meta.unit;
		if (previewData?.unit) return previewData.unit;
		return "";
	}

	function isFinanceTimeseries() {
		return !!previewData?.meta?.labels;
	}

	function getDataColumns() {
		if (!previewData?.columns) return [];
		return previewData.columns.filter((column) => column !== "계정명");
	}

	function isYearValue(val) {
		return Number.isInteger(val) && val >= 1900 && val <= 2100;
	}

	function formatWon(val) {
		if (val === null || val === undefined) return "-";
		if (typeof val !== "number") return String(val);
		if (val === 0) return "0";
		const abs = Math.abs(val);
		const sign = val < 0 ? "-" : "";
		if (abs >= 1e12) return `${sign}${(abs / 1e12).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}조`;
		if (abs >= 1e8) return `${sign}${Math.round(abs / 1e8).toLocaleString("ko-KR")}억`;
		if (abs >= 1e4) return `${sign}${Math.round(abs / 1e4).toLocaleString("ko-KR")}만`;
		return val.toLocaleString("ko-KR");
	}

	function formatCellValue(val, unit) {
		if (val === null || val === undefined) return "-";
		if (typeof val === "number") {
			if (isYearValue(val)) return String(val);
			if (unit === "원" || unit === "백만원") {
				if (unit === "백만원") val *= 1_000_000;
				return formatWon(val);
			}
			if (Number.isInteger(val) && Math.abs(val) >= 1000) {
				return val.toLocaleString("ko-KR");
			}
			if (!Number.isInteger(val)) {
				return val.toLocaleString("ko-KR", { maximumFractionDigits: 2 });
			}
		}
		return String(val);
	}

	function buildPreviewHighlights(data) {
		if (!data) return [];
		if (data.type === "table") {
			return [
				`${(data.totalRows || data.rows?.length || 0).toLocaleString()}개 행`,
				`${(data.columns?.length || 0).toLocaleString()}개 열`,
				data.truncated ? "일부 행만 미리보기" : "전체 미리보기 범위",
			];
		}
		if (data.type === "text") {
			return [
				`${(data.text?.length || 0).toLocaleString()}자 텍스트`,
				data.truncated ? "긴 텍스트 일부만 노출" : "본문 전체 미리보기",
			];
		}
		if (data.type === "dict") {
			return [`${Object.keys(data.data || {}).length.toLocaleString()}개 필드`, "요약 필드 구조"];
		}
		return ["구조화 데이터", "원본 확인 가능"];
	}

	function summarizePreviewText(text) {
		if (!text) return [];
		return text
			.split(/\n+/)
			.map((line) => line.trim())
			.filter(Boolean)
			.filter((line) => line.length > 18)
			.slice(0, 3);
	}

	async function loadCompanySources(company) {
		if (!company?.stockCode) {
			sourceData = null;
			companyInfo = null;
			overviewCards = [];
			overviewHighlights = [];
			overviewTrend = [];
			sourceError = "";
			return;
		}

		sourcesLoading = true;
		activeModule = null;
		previewData = null;
		selectedModuleNames = new Set();

		try {
			sourceData = await fetchDataSources(company.stockCode);
			const cats = Object.keys(sourceData.categories || {});
			expandedCategories = new Set(cats.slice(0, 2));
			loadedStockCode = company.stockCode;
			sourceError = "";
		} catch {
			sourceData = null;
			sourceError = "데이터 소스 목록을 불러오지 못했습니다. 다시 시도해 주세요.";
		}

		sourcesLoading = false;
	}

	$effect(() => {
		const stockCode = selectedCompany?.stockCode || null;
		if (!stockCode || stockCode === loadedStockCode) return;
		loadCompanySources(selectedCompany);
	});

	$effect(() => {
		const stockCode = selectedCompany?.stockCode || null;
		if (!stockCode || !sourceData) return;
		loadOverview(selectedCompany, sourceData);
	});

	function handleSearchInput() {
		const query = searchQuery.trim();
		if (searchTimer) clearTimeout(searchTimer);
		if (query.length < 2) {
			searchResults = [];
			searchLoading = false;
			return;
		}

		searchLoading = true;
		searchTimer = setTimeout(async () => {
			try {
				const data = await searchCompany(query);
				searchResults = data.results?.slice(0, 8) || [];
			} catch {
				searchResults = [];
			}
			searchLoading = false;
		}, 250);
	}

	async function selectCompany(item) {
		onSelectCompany?.(item);
		searchQuery = "";
		searchResults = [];
		onChangeTab?.("overview");
		await loadCompanySources(item);
	}

	function resetCompany() {
		onSelectCompany?.(null);
		searchQuery = "";
		searchResults = [];
		sourceData = null;
		activeModule = null;
		previewData = null;
		loadedStockCode = null;
		companyInfo = null;
		overviewCards = [];
		overviewHighlights = [];
		overviewTrend = [];
		overviewError = "";
		selectedModuleNames = new Set();
		onChangeTab?.("explore");
	}

	function toggleCategory(category) {
		const next = new Set(expandedCategories);
		if (next.has(category)) next.delete(category);
		else next.add(category);
		expandedCategories = next;
	}

	async function selectModule(source) {
		if (!source.available || !selectedCompany?.stockCode) return;
		activeModule = source;
		onChangeTab?.("explore");
		previewLoading = true;
		previewData = null;
		try {
			previewData = await fetchDataPreview(selectedCompany.stockCode, source.name, 200);
		} catch (error) {
			previewData = { type: "error", error: error.message };
		}
		previewLoading = false;
	}

	async function handleDownloadExcel(modules = null) {
		if (!selectedCompany) return;
		excelDownloading = true;
		try {
			await downloadExcel(selectedCompany.stockCode, modules);
			const label = modules?.length ? `선택한 ${modules.length}개 모듈을 다운로드했습니다.` : "전체 Excel 다운로드를 시작했습니다.";
			pushActionStatus("success", label);
			onNotify?.(label, "success");
		} catch {
			const label = "Excel 다운로드를 시작하지 못했습니다. 다시 시도해 주세요.";
			pushActionStatus("error", label);
			onNotify?.(label);
		}
		excelDownloading = false;
	}

	function toggleModuleSelection(source) {
		if (!source?.available) return;
		const next = new Set(selectedModuleNames);
		if (next.has(source.name)) next.delete(source.name);
		else next.add(source.name);
		selectedModuleNames = next;
	}

	function handleAskAboutModule() {
		if (!selectedCompany || !activeModule) return;
		onAskAboutModule?.(selectedCompany, activeModule, previewData);
	}

	function pushActionStatus(type, text) {
		actionStatus = { type, text };
		setTimeout(() => {
			if (actionStatus?.text === text) actionStatus = null;
		}, 2600);
	}

	let categoryEntries = $derived.by(() => {
		const query = moduleQuery.trim().toLowerCase();
		const entries = Object.entries(sourceData?.categories || {});
		if (!query) return entries;
		return entries
			.map(([category, items]) => [
				category,
				items.filter((item) => {
					const haystack = `${item.label} ${item.name} ${item.description || ""}`.toLowerCase();
					return haystack.includes(query);
				}),
			])
			.filter(([, items]) => items.length > 0);
	});
	let availableSources = $derived(sourceData?.availableSources || 0);
	let availableCategoryCount = $derived(categoryEntries.filter(([, items]) => items.some((item) => item.available)).length);
	let recommendedModules = $derived.by(() => {
		const flattened = categoryEntries.flatMap(([category, items]) =>
			items
				.filter((item) => item.available)
				.map((item) => ({ ...item, category }))
		);
		return flattened.slice(0, 5);
	});
	let evidenceContexts = $derived(evidenceMessage?.contexts || []);
	let evidenceTools = $derived((evidenceMessage?.toolEvents || []).filter((event) => event.type === "call"));
	let evidenceToolResults = $derived((evidenceMessage?.toolEvents || []).filter((event) => event.type === "result"));
	let evidenceStats = $derived.by(() => {
		const stats = [];
		if (evidenceMessage?.snapshot?.items?.length) stats.push({ label: "핵심 수치", value: evidenceMessage.snapshot.items.length, tone: "success" });
		if (evidenceContexts.length) stats.push({ label: "컨텍스트", value: evidenceContexts.length, tone: "default" });
		if (evidenceTools.length) stats.push({ label: "툴 호출", value: evidenceTools.length, tone: "accent" });
		if (evidenceToolResults.length) stats.push({ label: "툴 결과", value: evidenceToolResults.length, tone: "success" });
		if (evidenceMessage?.systemPrompt) stats.push({ label: "프롬프트", value: 1, tone: "default" });
		return stats;
	});
	let previewHighlights = $derived(buildPreviewHighlights(previewData));
	let previewTextSummary = $derived.by(() => previewData?.type === "text" ? summarizePreviewText(previewData.text) : []);
	let hasModuleFilter = $derived(moduleQuery.trim().length > 0);
	let selectedModuleList = $derived([...selectedModuleNames]);
	let selectedModuleRecords = $derived.by(() => {
		const sourceMap = new Map(
			Object.values(sourceData?.categories || {})
				.flat()
				.map((item) => [item.name, item])
		);
		return selectedModuleList.map((name) => sourceMap.get(name)).filter(Boolean);
	});

	function setTab(tab) {
		onChangeTab?.(tab);
	}

	function openDetailModal(type, payload, title) {
		detailModal = { type, payload, title };
	}

	function closeDetailModal() {
		detailModal = null;
	}

	function selectPreferredModule(sourceMap, names) {
		for (const name of names) {
			if (sourceMap.has(name) && sourceMap.get(name).available) return sourceMap.get(name);
		}
		return null;
	}

	function extractMetricFromTimeseries(preview, keys) {
		if (!preview?.rows?.length || !preview?.columns?.length) return null;
		const valueColumns = preview.columns.filter((column) => column !== "계정명");
		if (!valueColumns.length) return null;
		const latestColumn = valueColumns[valueColumns.length - 1];
		for (const row of preview.rows) {
			const account = row["계정명"];
			if (keys.includes(account)) {
				return { value: row[latestColumn], period: latestColumn };
			}
		}
		return null;
	}

	function buildOverviewCards(isPreview, bsPreview) {
		const cards = [];
		const revenue = extractMetricFromTimeseries(isPreview, ["revenue", "sales"]);
		const operatingIncome = extractMetricFromTimeseries(isPreview, ["operating_income"]);
		const netIncome = extractMetricFromTimeseries(isPreview, ["net_income", "profit_loss"]);
		const totalAssets = extractMetricFromTimeseries(bsPreview, ["total_assets"]);

		if (revenue) cards.push({ label: "최근 매출", value: formatCellValue(revenue.value, isPreview?.meta?.unit || isPreview?.unit || "원"), period: revenue.period });
		if (operatingIncome) cards.push({ label: "최근 영업이익", value: formatCellValue(operatingIncome.value, isPreview?.meta?.unit || isPreview?.unit || "원"), period: operatingIncome.period });
		if (netIncome) cards.push({ label: "최근 순이익", value: formatCellValue(netIncome.value, isPreview?.meta?.unit || isPreview?.unit || "원"), period: netIncome.period });
		if (totalAssets) cards.push({ label: "최근 총자산", value: formatCellValue(totalAssets.value, bsPreview?.meta?.unit || bsPreview?.unit || "원"), period: totalAssets.period });

		return cards;
	}

	function buildOverviewTrend(preview, keys) {
		if (!preview?.rows?.length || !preview?.columns?.length) return [];
		const target = preview.rows.find((row) => keys.includes(row["계정명"]));
		if (!target) return [];
		const columns = preview.columns.filter((column) => column !== "계정명");
		const points = columns.slice(-5).map((column) => ({ label: column, value: typeof target[column] === "number" ? target[column] : null }));
		const numeric = points.filter((point) => typeof point.value === "number").map((point) => Math.abs(point.value));
		const max = Math.max(...numeric, 0);
		return points.map((point) => ({
			...point,
			ratio: max > 0 && typeof point.value === "number" ? Math.max(8, Math.round(Math.abs(point.value) / max * 100)) : 0,
		}));
	}

	function buildOverviewHighlights(company, sources, sourceMap, cards) {
		const highlights = [];
		const availableCategories = Object.entries(sources.categories || {})
			.filter(([, items]) => items.some((item) => item.available))
			.map(([category]) => categoryLabel(category));
		if (availableCategories.length > 0) {
			highlights.push(`활성 카테고리 ${availableCategories.slice(0, 3).join(", ")}`);
		}
		if (sourceMap.get("dividend")?.available) highlights.push("배당 데이터 확인 가능");
		if (sourceMap.get("majorHolder")?.available) highlights.push("최대주주 데이터 확인 가능");
		if (sourceMap.get("business")?.available || sourceMap.get("mdna")?.available) highlights.push("서술형 사업/리스크 공시 탐색 가능");
		if (!cards.length) highlights.push("핵심 재무 카드는 원본 표 탐색 후 질문으로 이어가는 흐름에 최적화됨");
		if (company?.market) highlights.push(`${company.market} 상장사`);
		return highlights.slice(0, 4);
	}

	function buildOverviewActions(sourceMap) {
		const actions = [];
		if (selectPreferredModule(sourceMap, ["annual.IS", "IS", "fsSummary"])) {
			actions.push({
				label: "실적 구조 보기",
				description: "표준화된 계정을 바로 열어 비교 가능한 숫자 구조를 확인합니다.",
				tab: "explore",
			});
		}
		if (sourceMap.get("business")?.available || sourceMap.get("mdna")?.available) {
			actions.push({
				label: "사업/리스크 읽기",
				description: "서술형 공시 텍스트와 원문 근거를 같이 훑습니다.",
				tab: "explore",
			});
		}
		actions.push({
			label: "현재 근거 보기",
			description: "채팅에서 사용된 스냅샷, 컨텍스트, 툴 결과를 검증합니다.",
			tab: "evidence",
		});
		return actions.slice(0, 3);
	}

	async function loadOverview(company, sources) {
		if (!company?.stockCode || !sources) return;
		overviewLoading = true;
		overviewError = "";

		const sourceMap = new Map(
			Object.values(sources.categories || {})
				.flat()
				.map((item) => [item.name, item])
		);

		const incomeModule = selectPreferredModule(sourceMap, ["annual.IS", "IS", "fsSummary"]);
		const balanceModule = selectPreferredModule(sourceMap, ["annual.BS", "BS"]);

		try {
			const [baseInfo, incomePreview, balancePreview] = await Promise.all([
				fetchCompany(company.stockCode).catch(() => company),
				incomeModule ? fetchDataPreview(company.stockCode, incomeModule.name, 80).catch(() => null) : Promise.resolve(null),
				balanceModule ? fetchDataPreview(company.stockCode, balanceModule.name, 80).catch(() => null) : Promise.resolve(null),
			]);
			companyInfo = { ...company, ...(baseInfo || {}) };
			overviewCards = buildOverviewCards(incomePreview, balancePreview);
			overviewHighlights = buildOverviewHighlights(companyInfo, sources, sourceMap, overviewCards);
			overviewTrend = buildOverviewTrend(incomePreview, ["revenue", "sales"]);
			overviewSourceLabel = [incomeModule?.label, balanceModule?.label].filter(Boolean).join(" / ");
			overviewActions = buildOverviewActions(sourceMap);
			overviewNarrative = [
				overviewCards[0] ? `${overviewCards[0].label} 기준 최근 관측 시점은 ${overviewCards[0].period}입니다.` : "핵심 재무 카드는 원본 시계열이 있을 때 자동 생성됩니다.",
				overviewTrend.length > 1 ? "추세 막대는 최근 5개 시점의 절대 규모를 기준으로 시각화합니다." : "추세 데이터가 충분하지 않으면 Explore에서 원본 표를 먼저 확인하는 편이 낫습니다.",
				overviewSourceLabel ? `현재 Overview는 ${overviewSourceLabel} 모듈을 기준으로 조립되었습니다.` : "현재 Overview는 기본 회사 정보와 사용 가능한 모듈 중심으로 조립되었습니다.",
			];
		} catch {
			companyInfo = company;
			overviewCards = [];
			overviewHighlights = ["회사 기본 정보만 확인할 수 있습니다."];
			overviewTrend = [];
			overviewSourceLabel = "";
			overviewError = "Overview 데이터를 만들지 못했습니다. Explore에서 원본 모듈을 확인해 주세요.";
			overviewActions = [];
			overviewNarrative = ["Overview 조립 실패로 인해 원본 모듈 탐색 흐름이 우선입니다."];
		}

		overviewLoading = false;
	}

	async function copyWorkspaceLink() {
		if (typeof navigator === "undefined" || !navigator.clipboard) return;
		await navigator.clipboard.writeText(window.location.href);
		copiedLink = true;
		pushActionStatus("success", "워크스페이스 링크를 복사했습니다.");
		onNotify?.("워크스페이스 링크를 복사했습니다.", "success");
		setTimeout(() => { copiedLink = false; }, 1500);
	}

	$effect(() => {
		if (activeTab !== "evidence" || !activeEvidenceSection || !evidenceMessage) return;
		requestAnimationFrame(() => {
			document
				.querySelector(`[data-evidence-section="${activeEvidenceSection}"]`)
				?.scrollIntoView({ block: "start", behavior: "smooth" });
			if (activeEvidenceSection === "snapshot" && evidenceMessage.snapshot) {
				detailModal = { type: "snapshot", payload: evidenceMessage.snapshot, title: "핵심 수치" };
				return;
			}
			if (activeEvidenceSection === "contexts" && evidenceContexts.length > 0) {
				const target = evidenceContexts[selectedEvidenceIndex ?? 0];
				if (target) detailModal = { type: "context", payload: target, title: target.label || target.module || "컨텍스트" };
				return;
			}
			if (activeEvidenceSection === "tool-calls" && evidenceTools.length > 0) {
				const target = evidenceTools[selectedEvidenceIndex ?? 0];
				if (target) detailModal = { type: "tool-call", payload: target, title: `${target.name} 호출` };
				return;
			}
			if (activeEvidenceSection === "tool-results" && evidenceToolResults.length > 0) {
				const target = evidenceToolResults[selectedEvidenceIndex ?? 0];
				if (target) detailModal = { type: "tool-result", payload: target, title: `${target.name} 결과` };
				return;
			}
			if (activeEvidenceSection === "system" && evidenceMessage.systemPrompt) {
				detailModal = { type: "system", payload: evidenceMessage.systemPrompt, title: "System Prompt" };
				return;
			}
			if (activeEvidenceSection === "input" && evidenceMessage.userContent) {
				detailModal = { type: "user", payload: evidenceMessage.userContent, title: "LLM Input" };
			}
		});
	});

	$effect(() => {
		if (!detailModal || !detailDialog) return;
		requestAnimationFrame(() => detailDialog?.focus());
	});
</script>

<div class="surface-panel flex h-full min-h-0 flex-col bg-dl-bg-card/92 backdrop-blur-sm">
	<div class="border-b border-dl-border/60 px-4 py-3">
		<div class="flex items-center justify-between gap-3">
			<div class="min-w-0">
				<div class="flex items-center gap-2 text-[14px] font-semibold text-dl-text">
					<Database size={16} class="text-dl-primary-light" />
					<span>Workspace</span>
				</div>
				<div class="mt-0.5 text-[11px] text-dl-text-dim">
					표준화된 계정, 서술형 텍스트, 원문 근거를 한 화면에서 검증하는 분석 워크벤치
				</div>
			</div>
			{#if onClose}
				<button
					class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text"
					onclick={() => onClose?.()}
					aria-label="워크스페이스 닫기"
				>
					<X size={16} />
				</button>
			{/if}
		</div>

		<div class="relative mt-3">
			<Search size={14} class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim" />
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="종목명 또는 종목코드 검색"
				class="w-full rounded-xl border border-dl-border bg-dl-bg-darker py-2.5 pl-9 pr-9 text-[12px] text-dl-text outline-none transition-colors placeholder:text-dl-text-dim focus:border-dl-primary/40"
				oninput={handleSearchInput}
			/>
			{#if searchLoading}
				<Loader2 size={14} class="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-dl-text-dim" />
			{/if}
		</div>

		{#if searchResults.length > 0}
			<div class="mt-2 space-y-1 rounded-xl border border-dl-border/50 bg-dl-bg-darker/95 p-1">
				{#each searchResults as item}
					<button
						class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors hover:bg-white/[0.04]"
						onclick={() => selectCompany(item)}
					>
						<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-dl-primary/10 text-[11px] font-semibold text-dl-primary-light">
							{item.corpName[0]}
						</div>
						<div class="min-w-0 flex-1">
							<div class="truncate text-[12px] font-medium text-dl-text">{item.corpName}</div>
							<div class="text-[10px] text-dl-text-dim">{item.stockCode} · {item.market || "미분류"}</div>
						</div>
						<ChevronRight size={14} class="flex-shrink-0 text-dl-text-dim" />
					</button>
				{/each}
			</div>
		{/if}

		{#if selectedCompany}
			<div class="mt-3 rounded-2xl border border-dl-primary/20 bg-dl-primary/[0.05] p-3">
				<div class="flex items-start justify-between gap-3">
					<div class="min-w-0">
						<div class="text-[13px] font-semibold text-dl-text">{selectedCompany.corpName || selectedCompany.company || companyInfo?.corpName || selectedCompany.stockCode}</div>
						<div class="mt-0.5 text-[10px] text-dl-text-dim">
							{selectedCompany.stockCode}
							{#if selectedCompany.market} · {selectedCompany.market}{/if}
							{#if availableSources} · {availableSources}개 데이터{/if}
						</div>
					</div>
					<button
						class="rounded-lg px-2 py-1 text-[10px] text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text"
						onclick={resetCompany}
					>
						초기화
					</button>
				</div>
				<div class="mt-2 flex gap-2">
					<button
						class="rounded-lg border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
						onclick={copyWorkspaceLink}
					>
						<Link2 size={10} class="mr-1 inline" />
						{copiedLink ? "링크 복사됨" : "링크 복사"}
					</button>
					<button
						class="rounded-lg border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
						onclick={() => loadCompanySources(selectedCompany)}
					>
						<RotateCcw size={10} class="mr-1 inline" />
						새로고침
					</button>
				</div>
			</div>
		{:else if recentCompanies.length > 0}
			<div class="mt-3 rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-3">
				<div class="mb-2 text-[11px] font-medium text-dl-text">최근 본 회사</div>
				<div class="flex flex-wrap gap-1.5">
					{#each recentCompanies as company}
						<button
							class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
							onclick={() => selectCompany(company)}
						>
							{company.corpName || company.company} · {company.stockCode}
						</button>
					{/each}
				</div>
			</div>
		{/if}

		<div class="mt-3 grid grid-cols-4 gap-1.5 rounded-xl bg-dl-bg-darker p-1">
			<button
				class={cn(
					"rounded-lg px-2 py-1.5 text-[11px] transition-colors",
					activeTab === "sections" ? "bg-dl-bg-card text-dl-text" : "text-dl-text-dim hover:text-dl-text-muted"
				)}
				onclick={() => setTab("sections")}
			>
				공시
			</button>
			<button
				class={cn(
					"rounded-lg px-2 py-1.5 text-[11px] transition-colors",
					activeTab === "overview" ? "bg-dl-bg-card text-dl-text" : "text-dl-text-dim hover:text-dl-text-muted"
				)}
				onclick={() => setTab("overview")}
			>
				Overview
			</button>
			<button
				class={cn(
					"rounded-lg px-2 py-1.5 text-[11px] transition-colors",
					activeTab === "explore" ? "bg-dl-bg-card text-dl-text" : "text-dl-text-dim hover:text-dl-text-muted"
				)}
				onclick={() => setTab("explore")}
			>
				Explore
			</button>
			<button
				class={cn(
					"rounded-lg px-2 py-1.5 text-[11px] transition-colors",
					activeTab === "evidence" ? "bg-dl-bg-card text-dl-text" : "text-dl-text-dim hover:text-dl-text-muted"
				)}
				onclick={() => setTab("evidence")}
			>
				Evidence
			</button>
		</div>

		{#if selectedCompany}
			<div class="mt-3 grid grid-cols-3 gap-2">
				<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2">
					<div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">View</div>
					<div class="mt-1 text-[12px] font-medium text-dl-text">{activeTab === "sections" ? "공시" : activeTab === "overview" ? "Overview" : activeTab === "explore" ? "Explore" : "Evidence"}</div>
				</div>
				<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2">
					<div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Modules</div>
					<div class="mt-1 text-[12px] font-medium text-dl-text">{availableSources}</div>
				</div>
				<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2">
					<div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Selected</div>
					<div class="mt-1 text-[12px] font-medium text-dl-text">{selectedModuleList.length}</div>
				</div>
			</div>
			<div class="mt-3 grid grid-cols-2 gap-2">
				<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2">
					<div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Schema</div>
					<div class="mt-1 text-[12px] font-medium text-dl-text">표준화 계정 비교</div>
				</div>
				<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2">
					<div class="text-[9px] uppercase tracking-[0.16em] text-dl-text-dim">Evidence</div>
					<div class="mt-1 text-[12px] font-medium text-dl-text">원문 근거 보존</div>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex-1 overflow-y-auto p-4">
		{#if actionStatus}
			<div class={cn(
				"mb-3 rounded-xl border px-3 py-2 text-[10px]",
				actionStatus.type === "success"
					? "border-dl-success/30 bg-dl-success/10 text-dl-success"
					: "border-dl-primary/20 bg-dl-primary/[0.05] text-dl-primary-light"
			)}>
				{actionStatus.text}
			</div>
		{/if}
		{#if activeTab === "sections"}
			{#if selectedCompany}
				<SectionsViewer
					stockCode={selectedCompany.stockCode}
					corpName={selectedCompany.corpName}
				/>
			{:else}
				<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center">
					<ScrollText size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
					<div class="text-[13px] font-medium text-dl-text">공시 뷰어</div>
					<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
						회사를 선택하면 전자공시 전체를 탐색할 수 있습니다.
					</div>
				</div>
			{/if}
		{:else if activeTab === "overview"}
			{#if !selectedCompany}
				<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center">
					<Database size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
					<div class="text-[13px] font-medium text-dl-text">회사별 워크스페이스 준비</div>
					<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
						회사를 먼저 선택하면 추후 대시보드가 들어갈 Overview 슬롯과 추천 모듈 요약을 바로 볼 수 있습니다.
					</div>
				</div>
			{:else}
				<div class="space-y-3">
					<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="flex items-start justify-between gap-3">
							<div>
								<div class="text-[14px] font-semibold text-dl-text">{companyInfo?.corpName || selectedCompany.corpName || selectedCompany.company || selectedCompany.stockCode}</div>
								<div class="mt-1 text-[10px] text-dl-text-dim">
									{companyInfo?.stockCode || selectedCompany.stockCode}
									{#if companyInfo?.market || selectedCompany.market} · {companyInfo?.market || selectedCompany.market}{/if}
									{#if companyInfo?.sector || selectedCompany.sector} · {companyInfo?.sector || selectedCompany.sector}{/if}
								</div>
							</div>
							<span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light">Overview</span>
						</div>
						<div class="mt-3 grid grid-cols-2 gap-2">
							<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3">
								<div class="text-[10px] text-dl-text-dim">사용 가능 데이터</div>
								<div class="mt-1 text-[22px] font-semibold text-dl-text">{availableSources}</div>
							</div>
							<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/80 p-3">
								<div class="text-[10px] text-dl-text-dim">활성 카테고리</div>
								<div class="mt-1 text-[22px] font-semibold text-dl-text">{availableCategoryCount}</div>
							</div>
						</div>
					</div>

					<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="flex items-center gap-2 text-[12px] font-medium text-dl-text">
							<Sparkles size={13} class="text-dl-accent" />
							핵심 재무 카드
						</div>
						{#if overviewLoading}
							<div class="mt-3 space-y-2">
								<div class="skeleton-line w-full"></div>
								<div class="skeleton-line w-[82%]"></div>
								<div class="skeleton-line w-[68%]"></div>
							</div>
						{:else if overviewCards.length > 0}
							<div class="mt-3 grid grid-cols-2 gap-2">
								{#each overviewCards as card}
									<div class="rounded-xl bg-dl-bg-card/60 p-3">
										<div class="text-[10px] text-dl-text-dim">{card.label}</div>
										<div class="mt-1 text-[13px] font-semibold text-dl-text">{card.value}</div>
										<div class="mt-1 text-[9px] text-dl-text-dim">{card.period}</div>
									</div>
								{/each}
							</div>
							{#if overviewSourceLabel}
								<div class="mt-2 text-[10px] text-dl-text-dim">출처: {overviewSourceLabel}</div>
							{/if}
							{#if overviewTrend.length > 0}
								<div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3">
									<div class="mb-2 text-[10px] uppercase tracking-wide text-dl-text-dim">매출 추세</div>
									<div class="flex items-end gap-2">
										{#each overviewTrend as point}
											<div class="flex flex-1 flex-col items-center gap-1">
												<div
													class="w-full rounded-t-md bg-gradient-to-t from-dl-primary to-dl-accent transition-all"
													style={`height: ${point.ratio || 8}px`}
													title={point.value === null ? "-" : formatCellValue(point.value, "원")}
												></div>
												<div class="text-[9px] text-dl-text-dim">{point.label}</div>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						{:else}
							<div class="mt-2 text-[11px] leading-relaxed text-dl-text-dim">
								핵심 재무 카드를 자동으로 만들 수 있는 시계열 데이터가 부족합니다. Explore에서 원본 모듈을 먼저 확인하는 흐름이 적합합니다.
							</div>
						{/if}
						{#if overviewError}
							<div class="mt-3 rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light">
								{overviewError}
							</div>
						{/if}
					</div>

					<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="mb-2 text-[12px] font-medium text-dl-text">Overview 노트</div>
						<div class="space-y-2">
							{#each overviewNarrative as line}
								<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/40 px-3 py-2 text-[11px] leading-relaxed text-dl-text-muted">
									{line}
								</div>
							{/each}
						</div>
					</div>

					<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="mb-2 text-[12px] font-medium text-dl-text">읽기 포인트</div>
						<div class="space-y-2">
							{#each overviewHighlights as item}
								<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2 text-[11px] text-dl-text-muted">
									{item}
								</div>
							{/each}
						</div>
					</div>

					{#if overviewActions.length > 0}
						<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
							<div class="mb-2 text-[12px] font-medium text-dl-text">추천 액션</div>
							<div class="space-y-2">
								{#each overviewActions as action}
									<button
										class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"
										onclick={() => setTab(action.tab)}
									>
										<div class="text-[11px] font-medium text-dl-text">{action.label}</div>
										<div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim">{action.description}</div>
									</button>
								{/each}
							</div>
						</div>
					{/if}

					<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="mb-2 text-[12px] font-medium text-dl-text">추천 모듈</div>
						<div class="space-y-2">
							{#each recommendedModules as module}
								<button
									class="w-full rounded-xl border border-dl-border/50 bg-dl-bg-card/40 p-3 text-left transition-colors hover:border-dl-primary/30 hover:bg-white/[0.02]"
									onclick={() => selectModule(module)}
								>
									<div class="flex items-center justify-between gap-3">
										<div class="min-w-0">
											<div class="truncate text-[12px] font-medium text-dl-text">{module.label}</div>
											<div class="mt-0.5 text-[10px] text-dl-text-dim">{getModuleDescription(module)}</div>
										</div>
										<span class="rounded-full bg-dl-primary/10 px-2 py-0.5 text-[9px] text-dl-primary-light">
											{categoryLabel(module.category)}
										</span>
									</div>
								</button>
							{/each}
						</div>
					</div>

					<div class="flex gap-2">
						<button
							class="flex-1 rounded-xl bg-dl-primary/20 px-3 py-2 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30"
							onclick={() => setTab("explore")}
						>
							모듈 탐색
						</button>
						<button
							class="flex-1 rounded-xl border border-dl-border/60 px-3 py-2 text-[11px] text-dl-text-muted transition-colors hover:border-dl-primary/30 hover:text-dl-text"
							onclick={() => setTab("evidence")}
						>
							현재 근거 보기
						</button>
					</div>
				</div>
			{/if}
		{:else if activeTab === "evidence"}
			{#if !evidenceMessage}
				<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center">
					<Database size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
					<div class="text-[13px] font-medium text-dl-text">아직 연결된 응답이 없습니다</div>
					<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
						채팅을 시작하면 이 패널에서 스냅샷, 사용한 모듈, 도구 호출, 시스템 프롬프트 요약을 함께 확인할 수 있습니다.
					</div>
				</div>
			{:else}
				<div class="space-y-3">
					{#if evidenceStats.length > 0}
						<div class="grid grid-cols-2 gap-2">
							{#each evidenceStats as stat}
								<div class={cn(
									"rounded-2xl border px-3 py-3",
									stat.tone === "success"
										? "border-dl-success/20 bg-dl-success/[0.06]"
										: stat.tone === "accent"
											? "border-dl-accent/20 bg-dl-accent/[0.06]"
											: "border-dl-border/40 bg-dl-bg-darker/70"
								)}>
									<div class="text-[10px] text-dl-text-dim">{stat.label}</div>
									<div class="mt-1 text-[18px] font-semibold text-dl-text">{stat.value}</div>
								</div>
							{/each}
						</div>
					{/if}

					{#if evidenceMessage.meta?.company || evidenceMessage.meta?.dataYearRange}
						<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
							<div class="text-[12px] font-medium text-dl-text">현재 답변 컨텍스트</div>
							<div class="mt-2 flex flex-wrap gap-1.5">
								{#if evidenceMessage.meta?.company}
									<span class="rounded-full bg-dl-primary/10 px-2 py-1 text-[10px] text-dl-primary-light">{evidenceMessage.meta.company}</span>
								{/if}
								{#if evidenceMessage.meta?.dataYearRange}
									<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted">
										{typeof evidenceMessage.meta.dataYearRange === "string"
											? evidenceMessage.meta.dataYearRange
											: `${evidenceMessage.meta.dataYearRange.min_year}~${evidenceMessage.meta.dataYearRange.max_year}년`}
									</span>
								{/if}
								{#each evidenceMessage.meta?.includedModules || [] as moduleName}
									<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[10px] text-dl-text-muted">
										{moduleName}
									</span>
								{/each}
							</div>
						</div>
					{/if}

					{#if evidenceMessage.snapshot?.items?.length > 0}
						<button
							data-evidence-section="snapshot"
							class="block w-full rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4 text-left transition-colors hover:border-dl-primary/25 hover:bg-dl-bg-darker/85"
							onclick={() => openDetailModal("snapshot", evidenceMessage.snapshot, "핵심 수치")}
						>
							<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
								<Database size={13} class="text-dl-success" />
								핵심 수치
							</div>
							<div class="grid grid-cols-2 gap-2">
								{#each evidenceMessage.snapshot.items as item}
									<div class="rounded-xl bg-dl-bg-card/60 p-2.5">
										<div class="text-[10px] text-dl-text-dim">{item.label}</div>
										<div class="mt-1 text-[12px] font-semibold text-dl-text">{item.value}</div>
									</div>
								{/each}
							</div>
						</button>
					{/if}

					<div data-evidence-section="contexts" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
							<Database size={13} class="text-dl-accent" />
							근거 모듈
						</div>
						{#if evidenceContexts.length > 0}
							<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">
								이 답변에 직접 투입된 원문/구조화 데이터입니다. 각 카드를 누르면 전문을 확인할 수 있습니다.
							</div>
							<div class="space-y-2">
								{#each evidenceContexts as ctx}
									<button
										class="w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"
										onclick={() => openDetailModal("context", ctx, ctx.label || ctx.module || "컨텍스트")}
									>
										<div class="flex items-center justify-between gap-2">
											<div class="text-[11px] font-medium text-dl-text">{ctx.label || ctx.module}</div>
											<span class="inline-flex items-center gap-1 text-[10px] text-dl-primary-light">
												<Eye size={11} />
												상세
											</span>
										</div>
										<div class="mt-1 line-clamp-3 text-[10px] leading-relaxed text-dl-text-dim">{ctx.text}</div>
									</button>
								{/each}
							</div>
						{:else}
							<div class="text-[11px] text-dl-text-dim">표시할 컨텍스트 데이터가 없습니다.</div>
						{/if}
					</div>

					<div data-evidence-section="tool-calls" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
							<Wrench size={13} class="text-dl-primary-light" />
							도구 호출
						</div>
						{#if evidenceTools.length > 0}
							<div class="space-y-1.5">
								{#each evidenceTools as tool}
									<button
										class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"
										onclick={() => openDetailModal("tool-call", tool, `${tool.name} 호출`)}
									>
										<span>
											{tool.name}
											{#if tool.arguments?.module} · {tool.arguments.module}{/if}
											{#if tool.arguments?.keyword} · {tool.arguments.keyword}{/if}
										</span>
										<span class="inline-flex items-center gap-1 text-dl-primary-light">
											<CheckCircle2 size={11} />
											JSON
										</span>
									</button>
								{/each}
							</div>
						{:else}
							<div class="text-[11px] text-dl-text-dim">도구 호출 기록이 없습니다.</div>
						{/if}
					</div>

					<div data-evidence-section="tool-results" class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
							<CheckCircle2 size={13} class="text-dl-success" />
							도구 결과
						</div>
						{#if evidenceToolResults.length > 0}
							<div class="mb-2 rounded-xl border border-dl-border/40 bg-dl-bg-card/35 px-3 py-2 text-[10px] leading-relaxed text-dl-text-dim">
								LLM이 받은 실제 툴 결과입니다. 요약만 보지 말고 상세를 열어 반환 구조를 검증할 수 있습니다.
							</div>
							<div class="space-y-1.5">
								{#each evidenceToolResults as tool}
									<button
										class="flex w-full items-center justify-between gap-3 rounded-xl bg-dl-bg-card/50 px-3 py-2 text-left text-[10px] text-dl-text-muted transition-colors hover:bg-dl-bg-card/70"
										onclick={() => openDetailModal("tool-result", tool, `${tool.name} 결과`)}
									>
										<span class="min-w-0 flex-1 truncate">
											{tool.name}
											{#if typeof tool.result === "string"} · {tool.result.slice(0, 80)}{/if}
										</span>
										<span class="inline-flex items-center gap-1 text-dl-success">
											<Eye size={11} />
											상세
										</span>
									</button>
								{/each}
							</div>
						{:else}
							<div class="text-[11px] text-dl-text-dim">도구 결과 기록이 없습니다.</div>
						{/if}
					</div>

					{#if evidenceMessage.systemPrompt || evidenceMessage.userContent}
						<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
							<div class="mb-2 flex items-center gap-2 text-[12px] font-medium text-dl-text">
								<Brain size={13} class="text-dl-accent-light" />
								프롬프트 투명성
							</div>
							{#if evidenceMessage.systemPrompt}
								<button
									data-evidence-section="system"
									class="mb-2 block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"
									onclick={() => openDetailModal("system", evidenceMessage.systemPrompt, "System Prompt")}
								>
									<div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">System</div>
									<div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted">{evidenceMessage.systemPrompt}</div>
								</button>
							{/if}
							{#if evidenceMessage.userContent}
								<button
									data-evidence-section="input"
									class="block w-full rounded-xl bg-dl-bg-card/50 p-3 text-left transition-colors hover:bg-dl-bg-card/70"
									onclick={() => openDetailModal("user", evidenceMessage.userContent, "LLM Input")}
								>
									<div class="mb-1 text-[10px] uppercase tracking-wide text-dl-text-dim">LLM Input</div>
									<div class="line-clamp-4 text-[10px] leading-relaxed text-dl-text-muted">{evidenceMessage.userContent}</div>
								</button>
							{/if}
						</div>
					{/if}
				</div>
			{/if}
		{:else}
			{#if !selectedCompany}
				<div class="rounded-2xl border border-dl-border/60 bg-dl-bg-darker/70 p-4 text-center">
					<Database size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
					<div class="text-[13px] font-medium text-dl-text">회사를 선택하면 탐색이 시작됩니다</div>
					<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
						채팅 없이도 검색 후 모듈을 열어 표, 요약, 텍스트를 직접 확인할 수 있습니다.
					</div>
				</div>
			{:else}
				<div class="space-y-3">
					<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70 p-4">
						<div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 px-3 py-2">
							<div class="flex items-center justify-between gap-2">
								<div>
									<div class="text-[12px] font-medium text-dl-text">데이터 탐색</div>
									<div class="mt-0.5 text-[10px] text-dl-text-dim">카테고리를 열고 모듈을 선택하면 우측에서 바로 미리볼 수 있습니다.</div>
								</div>
								<div class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[9px] text-dl-primary-light">
									{availableSources}개 모듈
								</div>
							</div>
						</div>

						<div class="sticky top-0 z-[8] mb-3 rounded-xl border border-dl-border/50 bg-dl-bg-card/92 px-3 py-2 backdrop-blur-sm">
							<div>
								<div class="text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">Download Actions</div>
								<div class="mt-1 text-[11px] text-dl-text-muted">
									{selectedModuleList.length > 0 ? `${selectedModuleList.length}개 모듈 선택됨` : "다운로드할 모듈을 선택하거나 전체 Excel을 받으세요."}
								</div>
							</div>
							<div class="mt-2 flex items-center gap-2">
								<button
									class="flex items-center gap-1 rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40"
									onclick={() => handleDownloadExcel(selectedModuleList)}
									disabled={excelDownloading || selectedModuleList.length === 0}
								>
									{#if excelDownloading && selectedModuleList.length > 0}
										<Loader2 size={11} class="animate-spin" />
									{:else}
										<Download size={11} />
									{/if}
									선택 다운로드
								</button>
								<button
									class="rounded-lg border border-dl-border/50 px-2.5 py-1.5 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text disabled:opacity-40"
									onclick={() => selectedModuleNames = new Set()}
									disabled={selectedModuleList.length === 0}
								>
									선택 해제
								</button>
								<button
									class="flex items-center gap-1 rounded-lg bg-dl-success/10 px-2.5 py-1.5 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20 disabled:opacity-40"
									onclick={() => handleDownloadExcel()}
									disabled={excelDownloading}
								>
									{#if excelDownloading && selectedModuleList.length === 0}
										<Loader2 size={11} class="animate-spin" />
									{:else}
										<Download size={11} />
									{/if}
									전체 Excel
								</button>
							</div>
						</div>

						{#if selectedModuleList.length > 0}
							<div class="mb-3 flex flex-wrap gap-1.5 rounded-xl border border-dl-border/40 bg-dl-bg-card/40 p-2">
								{#each selectedModuleRecords as module}
									<button
										class="rounded-full bg-dl-primary/10 px-2.5 py-1 text-[10px] text-dl-primary-light"
										onclick={() => selectedModuleNames = new Set(selectedModuleList.filter((item) => item !== module.name))}
									>
										{module.label} ×
									</button>
								{/each}
								<button
									class="rounded-full border border-dl-border/50 px-2.5 py-1 text-[10px] text-dl-text-dim transition-colors hover:border-dl-primary/30 hover:text-dl-text"
									onclick={() => selectedModuleNames = new Set()}
								>
									선택 해제
								</button>
							</div>
						{/if}

						<div class="space-y-2">
							<div class="relative">
								<Search size={12} class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dl-text-dim" />
								<input
									type="text"
									bind:value={moduleQuery}
									placeholder="모듈 이름 또는 설명 필터"
									class="w-full rounded-xl border border-dl-border bg-dl-bg-card/50 py-2 pl-8 pr-3 text-[11px] text-dl-text outline-none transition-colors placeholder:text-dl-text-dim focus:border-dl-primary/40"
								/>
							</div>
							{#if sourceError}
								<div class="rounded-xl border border-dl-primary/20 bg-dl-primary/[0.05] px-3 py-2 text-[10px] text-dl-primary-light">
									{sourceError}
								</div>
							{/if}
							{#if sourcesLoading}
								<div class="flex items-center gap-2 py-4 text-[11px] text-dl-text-dim">
									<Loader2 size={14} class="animate-spin" />
									모듈 목록을 불러오는 중...
								</div>
							{:else if categoryEntries.length === 0 && hasModuleFilter}
								<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30 px-3 py-4 text-[11px] text-dl-text-dim">
									필터와 일치하는 모듈이 없습니다.
								</div>
							{:else}
								{#each categoryEntries as [category, items]}
									<div class="rounded-xl border border-dl-border/40 bg-dl-bg-card/30">
										<button
											class="flex w-full items-start gap-2 px-3 py-2.5 text-left"
											onclick={() => toggleCategory(category)}
										>
											{#if expandedCategories.has(category)}
												<ChevronDown size={13} class="mt-0.5 flex-shrink-0 text-dl-text-dim" />
											{:else}
												<ChevronRight size={13} class="mt-0.5 flex-shrink-0 text-dl-text-dim" />
											{/if}
											<div class="min-w-0 flex-1">
												<div class="flex items-center justify-between gap-2">
													<span class="text-[11px] font-medium text-dl-text">{categoryLabel(category)}</span>
													<span class="text-[9px] text-dl-text-dim">{categoryStats(items)}</span>
												</div>
												<div class="mt-0.5 text-[10px] leading-relaxed text-dl-text-dim">{categoryHint(category)}</div>
											</div>
										</button>

										{#if expandedCategories.has(category)}
											<div class="space-y-1 border-t border-dl-border/30 px-2 pb-2 pt-1">
												{#each items as source}
													<div
														class={cn(
															"flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-all",
															!source.available && "cursor-default opacity-35",
															source.available && activeModule?.name === source.name
																? "border-dl-primary/40 bg-dl-primary/[0.08]"
																: source.available
																	? "border-transparent bg-white/[0.01] hover:border-dl-primary/20 hover:bg-white/[0.03]"
																	: "border-transparent bg-transparent"
														)}
													>
														{#if source.available}
															<button
																type="button"
																class={cn(
																	"flex h-4 w-4 items-center justify-center rounded border flex-shrink-0",
																	selectedModuleNames.has(source.name)
																		? "border-dl-primary bg-dl-primary/20 text-dl-primary-light"
																		: "border-dl-border text-transparent"
																)}
																onclick={() => toggleModuleSelection(source)}
																aria-label={`${source.label} 선택`}
															>
																✓
															</button>
														{:else}
															<span class="h-4 w-4 flex-shrink-0"></span>
														{/if}
														<button
															type="button"
															class="flex min-w-0 flex-1 items-center gap-2 text-left"
															disabled={!source.available}
															onclick={() => selectModule({ ...source, category })}
														>
															{#if source.dataType === "timeseries" || source.dataType === "table" || source.dataType === "dataframe"}
																<Table2 size={11} class="flex-shrink-0 text-dl-text-dim" />
															{:else}
																<FileText size={11} class="flex-shrink-0 text-dl-text-dim" />
															{/if}
															<div class="min-w-0 flex-1">
																<div class="truncate text-[11px] font-medium text-dl-text">{source.label}</div>
																<div class="mt-0.5 text-[10px] text-dl-text-dim">{getModuleDescription(source)}</div>
															</div>
														</button>
													</div>
												{/each}
											</div>
										{/if}
									</div>
								{/each}
							{/if}
						</div>
					</div>

					<div class="rounded-2xl border border-dl-border/50 bg-dl-bg-darker/70">
						{#if !activeModule}
							<div class="p-4 text-center">
								<Table2 size={28} class="mx-auto mb-3 text-dl-text-dim/50" />
								<div class="text-[13px] font-medium text-dl-text">모듈을 선택하세요</div>
								<div class="mt-1 text-[11px] leading-relaxed text-dl-text-dim">
									선택한 모듈은 표 미리보기와 함께 질문으로 이어갈 수 있습니다.
								</div>
							</div>
						{:else if previewLoading}
							<div class="flex items-center gap-2 p-4 text-[11px] text-dl-text-dim">
								<Loader2 size={14} class="animate-spin" />
								{activeModule.label} 미리보기 로딩 중...
							</div>
						{:else if previewData}
							<div class="border-b border-dl-border/40 px-4 py-3">
								<div class="flex items-start justify-between gap-3">
									<div class="min-w-0">
										<div class="text-[13px] font-medium text-dl-text">{activeModule.label}</div>
										<div class="mt-1 text-[10px] leading-relaxed text-dl-text-dim">{getModuleDescription(activeModule)}</div>
									</div>
									<div class="flex items-center gap-1.5">
										{#if isFinanceTimeseries()}
											<button
												class={cn(
													"rounded-lg px-2 py-1 text-[10px] transition-colors",
													useKoreanLabel ? "bg-dl-primary/15 text-dl-primary-light" : "text-dl-text-dim hover:bg-white/5 hover:text-dl-text"
												)}
												onclick={() => useKoreanLabel = !useKoreanLabel}
											>
												<Languages size={11} class="inline mr-1" />
												{useKoreanLabel ? "한글" : "EN"}
											</button>
										{/if}
										<button
											class="rounded-lg bg-dl-success/10 px-2 py-1 text-[10px] text-dl-success transition-colors hover:bg-dl-success/20"
											onclick={() => handleDownloadExcel([activeModule.name])}
										>
											<Download size={11} class="inline mr-1" />
											Excel
										</button>
									</div>
								</div>

								<div class="mt-3 flex flex-wrap gap-1.5">
									{#each previewHighlights as highlight}
										<span class="rounded-full bg-dl-bg-card px-2 py-1 text-[9px] text-dl-text-muted">{highlight}</span>
									{/each}
								</div>

								<div class="mt-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/50 p-3">
									<div class="text-[10px] uppercase tracking-wide text-dl-text-dim">추천 질문</div>
									<div class="mt-1 text-[11px] leading-relaxed text-dl-text-muted">{getSuggestedQuestion(activeModule)}</div>
									<button
										class="mt-3 rounded-lg bg-dl-primary/20 px-3 py-1.5 text-[11px] font-medium text-dl-primary-light transition-colors hover:bg-dl-primary/30"
										onclick={handleAskAboutModule}
									>
										이 데이터로 질문하기
									</button>
								</div>
							</div>

							{#if previewData.type === "table" && isFinanceTimeseries()}
								<div class="max-h-[360px] overflow-auto">
									<table class="w-full border-collapse text-[11px]">
										<thead class="sticky top-0 z-[5]">
											<tr>
												<th class="sticky left-0 z-[6] min-w-[180px] border-b border-r border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted">계정명</th>
												{#each getDataColumns() as col}
													<th class="min-w-[96px] border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-right text-[10px] font-medium text-dl-text-muted">{col}</th>
												{/each}
											</tr>
										</thead>
										<tbody>
											{#each previewData.rows as row}
												{@const snakeId = row["계정명"]}
												{@const level = getAccountLevel(snakeId)}
												<tr class="hover:bg-white/[0.02]">
													<td
														class={cn(
															"sticky left-0 border-b border-r border-dl-border/10 bg-dl-bg-card/95 px-3 py-1.5 whitespace-nowrap",
															level === 1 && "font-semibold text-dl-text",
															level === 2 && "text-dl-text-muted",
															level >= 3 && "text-dl-text-dim"
														)}
														style={`padding-left: ${8 + (level - 1) * 12}px`}
													>
														{getAccountLabel(snakeId)}
													</td>
													{#each getDataColumns() as col}
														{@const val = row[col]}
														<td class={cn(
															"border-b border-dl-border/10 px-3 py-1.5 text-right font-mono text-[10px]",
															val === null || val === undefined ? "text-dl-text-dim/30" :
															typeof val === "number" && val < 0 ? "text-dl-primary-light" : "text-dl-accent-light"
														)}>
															{formatCellValue(val, getUnit())}
														</td>
													{/each}
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							{:else if previewData.type === "table"}
								<div class="max-h-[360px] overflow-auto">
									<table class="w-full border-collapse text-[11px]">
										<thead class="sticky top-0 z-[5]">
											<tr>
												{#each previewData.columns as col}
													<th class="border-b border-dl-border/30 bg-dl-bg-darker px-3 py-2 text-left text-[10px] font-medium text-dl-text-muted">{col}</th>
												{/each}
											</tr>
										</thead>
										<tbody>
											{#each previewData.rows as row}
												<tr class="hover:bg-white/[0.02]">
													{#each previewData.columns as col}
														{@const val = row[col]}
														<td class={cn(
															"border-b border-dl-border/10 px-3 py-1.5 whitespace-nowrap",
															typeof val === "number" ? "text-right font-mono text-[10px] text-dl-accent-light" : "text-dl-text-muted"
														)}>
															{formatCellValue(val, getUnit())}
														</td>
													{/each}
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							{:else if previewData.type === "dict"}
								<div class="space-y-1.5 p-4">
									{#each Object.entries(previewData.data || {}) as [key, value]}
										<div class="rounded-xl bg-dl-bg-card/50 px-3 py-2">
											<div class="text-[10px] text-dl-text-dim">{key}</div>
											<div class="mt-1 text-[11px] text-dl-text-muted">{value ?? "-"}</div>
										</div>
									{/each}
								</div>
							{:else if previewData.type === "text"}
								<div class="p-4">
									{#if previewTextSummary.length > 0}
										<div class="mb-3 rounded-xl border border-dl-border/40 bg-dl-bg-card/45 p-3">
											<div class="mb-2 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">핵심 문장</div>
											<div class="space-y-2">
												{#each previewTextSummary as sentence}
													<div class="text-[11px] leading-relaxed text-dl-text-muted">{sentence}</div>
												{/each}
											</div>
										</div>
									{/if}
									<pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted">{previewData.text}</pre>
								</div>
							{:else if previewData.type === "error"}
								<div class="p-4 text-[11px] text-dl-primary-light">{previewData.error || "데이터를 불러올 수 없습니다."}</div>
							{:else}
								<div class="p-4">
									<pre class="whitespace-pre-wrap text-[11px] text-dl-text-muted">{previewData.data || JSON.stringify(previewData, null, 2)}</pre>
								</div>
							{/if}
						{/if}
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>

{#if detailModal}
	<div
		class="fixed inset-0 z-[320] flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm"
		onclick={(event) => { if (event.target === event.currentTarget) closeDetailModal(); }}
		role="presentation"
	>
		<div
			bind:this={detailDialog}
			class="max-h-[80vh] w-full max-w-2xl overflow-hidden rounded-2xl border border-dl-border bg-dl-bg-card shadow-2xl shadow-black/30"
			role="dialog"
			aria-modal="true"
			aria-labelledby="workspace-detail-title"
			tabindex="-1"
			onkeydown={(event) => { if (event.key === "Escape") closeDetailModal(); }}
		>
			<div class="flex items-center justify-between border-b border-dl-border/50 px-5 py-4">
				<div>
					<div id="workspace-detail-title" class="text-[14px] font-semibold text-dl-text">{detailModal.title}</div>
					<div class="mt-1 text-[10px] uppercase tracking-[0.16em] text-dl-text-dim">
						{detailModal.type === "context"
							? "Context Detail"
							: detailModal.type === "tool" || detailModal.type === "tool-call" || detailModal.type === "tool-result"
								? "Tool Event"
								: detailModal.type === "snapshot"
									? "Snapshot"
									: "Prompt Detail"}
					</div>
				</div>
				<button
					class="rounded-lg p-1.5 text-dl-text-dim transition-colors hover:bg-white/5 hover:text-dl-text"
					onclick={closeDetailModal}
					aria-label="상세 데이터 닫기"
				>
					<X size={16} />
				</button>
			</div>
			<div class="max-h-[calc(80vh-76px)] overflow-y-auto p-5">
				{#if detailModal.type === "context"}
					<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4">
						<pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted">{detailModal.payload?.text || "-"}</pre>
					</div>
				{:else if detailModal.type === "tool" || detailModal.type === "tool-call" || detailModal.type === "tool-result"}
					<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted">{JSON.stringify(detailModal.payload, null, 2)}</pre>
				{:else if detailModal.type === "snapshot"}
					<pre class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4 text-[11px] leading-relaxed text-dl-text-muted">{JSON.stringify(detailModal.payload, null, 2)}</pre>
				{:else}
					<div class="rounded-xl border border-dl-border/40 bg-dl-bg-darker/70 p-4">
						<pre class="whitespace-pre-wrap text-[11px] leading-relaxed text-dl-text-muted">{detailModal.payload || "-"}</pre>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
