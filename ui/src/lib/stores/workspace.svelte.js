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

	function clearSelectedCompany() {
		selectedCompany = null;
		persist();
	}

	function resetChatContext() {
		clearSelectedCompany();
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

	return {
		get selectedCompany() { return selectedCompany; },
		get recentCompanies() { return recentCompanies; },
		resetChatContext,
		selectCompany,
		clearSelectedCompany,
		syncCompanyFromMessage,
	};
}
