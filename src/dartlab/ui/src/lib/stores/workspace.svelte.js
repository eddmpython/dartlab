const STORAGE_KEY = "dartlab-workspace";
const VALID_TABS = new Set(["overview", "explore", "evidence"]);
const MAX_RECENT_COMPANIES = 6;

function normalizeTab(tab) {
	return VALID_TABS.has(tab) ? tab : "overview";
}

function canUseBrowser() {
	return typeof window !== "undefined" && typeof localStorage !== "undefined";
}

function readUrlState() {
	if (!canUseBrowser()) return {};
	const params = new URLSearchParams(window.location.search);
	const stockCode = params.get("company") || null;
	const tab = params.get("tab");
	const panel = params.get("panel");
	return {
		stockCode,
		tab: tab ? normalizeTab(tab) : null,
		isOpen: panel === "open" ? true : panel === "closed" ? false : null,
	};
}

function loadStoredState() {
	if (!canUseBrowser()) return {};
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return {};
		const parsed = JSON.parse(raw);
		return {
			isOpen: typeof parsed.isOpen === "boolean" ? parsed.isOpen : true,
			activeTab: normalizeTab(parsed.activeTab),
			selectedCompany: parsed.selectedCompany || null,
			userPinnedCompany: !!parsed.userPinnedCompany,
			recentCompanies: Array.isArray(parsed.recentCompanies) ? parsed.recentCompanies : [],
			activeEvidenceSection: parsed.activeEvidenceSection || null,
			selectedEvidenceIndex: Number.isInteger(parsed.selectedEvidenceIndex) ? parsed.selectedEvidenceIndex : null,
		};
	} catch {
		return {};
	}
}

function persistState(state) {
	if (!canUseBrowser()) return;
	localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function syncUrl(state) {
	if (!canUseBrowser()) return;
	const url = new URL(window.location.href);
	if (state.selectedCompany?.stockCode) {
		url.searchParams.set("company", state.selectedCompany.stockCode);
	} else {
		url.searchParams.delete("company");
	}
	url.searchParams.set("tab", normalizeTab(state.activeTab));
	url.searchParams.set("panel", state.isOpen ? "open" : "closed");
	window.history.replaceState({}, "", url);
}

export function createWorkspaceStore() {
	const stored = loadStoredState();
	const urlState = readUrlState();
	const initialSelectedCompany = urlState.stockCode
		? { ...(stored.selectedCompany || {}), stockCode: urlState.stockCode }
		: (stored.selectedCompany || null);

	let isOpen = $state(urlState.isOpen ?? stored.isOpen ?? true);
	let activeTab = $state(urlState.tab ?? stored.activeTab ?? "overview");
	let selectedCompany = $state(initialSelectedCompany);
	let userPinnedCompany = $state(stored.userPinnedCompany ?? !!initialSelectedCompany);
	let recentCompanies = $state(stored.recentCompanies || []);
	let activeEvidenceSection = $state(stored.activeEvidenceSection ?? null);
	let selectedEvidenceIndex = $state(stored.selectedEvidenceIndex ?? null);

	function updateRecentCompanies(company) {
		if (!company?.stockCode) return;
		const normalized = {
			stockCode: company.stockCode,
			corpName: company.corpName || company.company || company.stockCode,
			company: company.company || company.corpName || company.stockCode,
			market: company.market || "",
			sector: company.sector || "",
		};
		const deduped = recentCompanies.filter((item) => item.stockCode !== normalized.stockCode);
		recentCompanies = [normalized, ...deduped].slice(0, MAX_RECENT_COMPANIES);
	}

	function sync() {
		const snapshot = {
			isOpen,
			activeTab,
			selectedCompany,
			userPinnedCompany,
			recentCompanies,
			activeEvidenceSection,
			selectedEvidenceIndex,
		};
		persistState(snapshot);
		syncUrl(snapshot);
	}

	function open(tab = "explore") {
		activeTab = normalizeTab(tab);
		isOpen = true;
		if (activeTab !== "evidence") {
			activeEvidenceSection = null;
			selectedEvidenceIndex = null;
		}
		sync();
	}

	function close() {
		isOpen = false;
		sync();
	}

	function setTab(tab) {
		activeTab = normalizeTab(tab);
		if (activeTab !== "evidence") {
			activeEvidenceSection = null;
			selectedEvidenceIndex = null;
		}
		sync();
	}

	function openEvidence(section, index = null) {
		activeTab = "evidence";
		isOpen = true;
		activeEvidenceSection = section || null;
		selectedEvidenceIndex = Number.isInteger(index) ? index : null;
		sync();
	}

	function clearEvidenceSelection() {
		activeEvidenceSection = null;
		selectedEvidenceIndex = null;
		sync();
	}

	function selectCompany(company, { pin = true, openTab = null } = {}) {
		selectedCompany = company;
		userPinnedCompany = company ? pin : false;
		activeEvidenceSection = null;
		selectedEvidenceIndex = null;
		if (company) updateRecentCompanies(company);
		if (openTab) {
			activeTab = normalizeTab(openTab);
			isOpen = true;
		}
		sync();
	}

	function syncCompanyFromMessage(meta = {}, fallback = null) {
		if (!meta?.company && !meta?.stockCode) return;
		selectedCompany = {
			...(selectedCompany || {}),
			...(fallback || {}),
			corpName: meta.company || selectedCompany?.corpName || fallback?.corpName || fallback?.company,
			company: meta.company || selectedCompany?.company || fallback?.company || fallback?.corpName,
			stockCode: meta.stockCode || selectedCompany?.stockCode || fallback?.stockCode,
			market: selectedCompany?.market || fallback?.market || "",
			sector: selectedCompany?.sector || fallback?.sector || "",
		};
		userPinnedCompany = true;
		updateRecentCompanies(selectedCompany);
		sync();
	}

	function resetCompany() {
		selectedCompany = null;
		userPinnedCompany = false;
		activeEvidenceSection = null;
		selectedEvidenceIndex = null;
		sync();
	}

	return {
		get isOpen() { return isOpen; },
		get activeTab() { return activeTab; },
		get selectedCompany() { return selectedCompany; },
		get userPinnedCompany() { return userPinnedCompany; },
		get recentCompanies() { return recentCompanies; },
		get activeEvidenceSection() { return activeEvidenceSection; },
		get selectedEvidenceIndex() { return selectedEvidenceIndex; },
		open,
		close,
		setTab,
		openEvidence,
		clearEvidenceSelection,
		selectCompany,
		syncCompanyFromMessage,
		resetCompany,
	};
}
