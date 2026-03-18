const STORAGE_KEY = "dartlab-workspace";
const MAX_RECENT = 6;

function canUseBrowser() {
	return typeof window !== "undefined" && typeof localStorage !== "undefined";
}

function loadState() {
	if (!canUseBrowser()) return {};
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		return raw ? JSON.parse(raw) : {};
	} catch { return {}; }
}

function saveState(s) {
	if (!canUseBrowser()) return;
	localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

export function createWorkspaceStore() {
	const stored = loadState();

	// Panel state
	let panelOpen = $state(false);
	let panelMode = $state(null); // "viewer" | "data"
	let panelData = $state(null); // data to display in panel

	// Viewer에서 현재 보고 있는 topic (AI 컨텍스트용)
	let viewerTopic = $state(null);     // "companyOverview", "BS" 등
	let viewerTopicLabel = $state(null); // "회사 개요", "재무상태표" 등

	// Company state (persisted)
	let selectedCompany = $state(stored.selectedCompany || null);
	let recentCompanies = $state(stored.recentCompanies || []);

	function persist() {
		saveState({ selectedCompany, recentCompanies });
	}

	function updateRecent(company) {
		if (!company?.stockCode) return;
		const norm = {
			stockCode: company.stockCode,
			corpName: company.corpName || company.company || company.stockCode,
			company: company.company || company.corpName || company.stockCode,
			market: company.market || "",
		};
		recentCompanies = [norm, ...recentCompanies.filter(c => c.stockCode !== norm.stockCode)].slice(0, MAX_RECENT);
	}

	// Open disclosure viewer for a company
	function openViewer(company) {
		if (company) {
			selectedCompany = company;
			updateRecent(company);
		}
		panelMode = "viewer";
		panelData = null;
		panelOpen = true;
		persist();
	}

	// Open data panel (badge click, AI data, etc.)
	function openData(data) {
		panelMode = "data";
		panelData = data;
		panelOpen = true;
	}

	function closePanel() {
		panelOpen = false;
	}

	function selectCompany(company) {
		selectedCompany = company;
		if (company) updateRecent(company);
		persist();
	}

	// Called from SSE onMeta when AI detects a company
	function syncCompanyFromMessage(meta, fallback) {
		if (!meta?.company && !meta?.stockCode) return;
		selectedCompany = {
			...(selectedCompany || {}),
			...(fallback || {}),
			corpName: meta.company || selectedCompany?.corpName || fallback?.corpName || fallback?.company,
			company: meta.company || selectedCompany?.company || fallback?.company || fallback?.corpName,
			stockCode: meta.stockCode || selectedCompany?.stockCode || fallback?.stockCode,
			market: selectedCompany?.market || fallback?.market || "",
		};
		updateRecent(selectedCompany);
		persist();
	}

	// Viewer에서 topic 변경 시 호출
	function setViewerTopic(topic, label) {
		viewerTopic = topic;
		viewerTopicLabel = label || topic;
	}

	// Context for AI — what the user is currently viewing
	function getViewContext() {
		if (!panelOpen) return null;
		if (panelMode === "viewer" && selectedCompany) {
			return {
				type: "viewer",
				company: selectedCompany,
				topic: viewerTopic,
				topicLabel: viewerTopicLabel,
			};
		}
		if (panelMode === "data" && panelData) {
			return { type: "data", data: panelData };
		}
		return null;
	}

	return {
		get panelOpen() { return panelOpen; },
		get panelMode() { return panelMode; },
		get panelData() { return panelData; },
		get selectedCompany() { return selectedCompany; },
		get recentCompanies() { return recentCompanies; },
		get viewerTopic() { return viewerTopic; },
		get viewerTopicLabel() { return viewerTopicLabel; },
		openViewer,
		openData,
		closePanel,
		selectCompany,
		setViewerTopic,
		syncCompanyFromMessage,
		getViewContext,
	};
}
