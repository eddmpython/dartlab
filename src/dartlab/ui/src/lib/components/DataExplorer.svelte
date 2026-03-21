<script>
	import { cn } from "$lib/utils.js";
	import { searchCompany, fetchDataSources, fetchDataPreview, downloadExcel, fetchCompany } from "$lib/api.js";
	import {
		X, Search, Database, ChevronRight, Loader2,
		Link2, RotateCcw, ScrollText
	} from "lucide-svelte";
	import SectionsViewer from "./SectionsViewer.svelte";
	import OverviewTab from "./workspace/OverviewTab.svelte";
	import EvidenceTab from "./workspace/EvidenceTab.svelte";
	import ExploreTab from "./workspace/ExploreTab.svelte";
	import DetailModal from "./workspace/DetailModal.svelte";

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
			<OverviewTab
				{selectedCompany}
				{companyInfo}
				{overviewLoading}
				{overviewCards}
				{overviewHighlights}
				{overviewTrend}
				{overviewNarrative}
				{overviewSourceLabel}
				{overviewError}
				{overviewActions}
				{availableSources}
				{availableCategoryCount}
				{recommendedModules}
				onSetTab={setTab}
				onSelectModule={selectModule}
				{formatCellValue}
				{categoryLabel}
				{getModuleDescription}
			/>
		{:else if activeTab === "evidence"}
			<EvidenceTab
				{evidenceMessage}
				{evidenceStats}
				{evidenceContexts}
				{evidenceTools}
				{evidenceToolResults}
				onOpenDetailModal={openDetailModal}
			/>
		{:else}
			<ExploreTab
				{selectedCompany}
				{sourceData}
				{sourcesLoading}
				{sourceError}
				{categoryEntries}
				bind:expandedCategories
				bind:activeModule
				{previewData}
				{previewLoading}
				{previewHighlights}
				{previewTextSummary}
				bind:useKoreanLabel
				bind:selectedModuleNames
				{selectedModuleList}
				{selectedModuleRecords}
				{excelDownloading}
				bind:moduleQuery
				{hasModuleFilter}
				{availableSources}
				onSelectModule={selectModule}
				onToggleCategory={toggleCategory}
				onToggleModuleSelection={toggleModuleSelection}
				onDownloadExcel={handleDownloadExcel}
				onAskAboutModule={handleAskAboutModule}
				{formatCellValue}
				{categoryLabel}
				{categoryHint}
				{categoryStats}
				{getModuleDescription}
				{getSuggestedQuestion}
				{getAccountLabel}
				{getAccountLevel}
				{getUnit}
				{isFinanceTimeseries}
				{getDataColumns}
			/>
		{/if}
	</div>
</div>

<DetailModal {detailModal} onClose={closeDetailModal} />
