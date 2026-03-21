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

	// Main view state
	let activeView = $state("chat"); // "chat" | "viewer"

	// Panel state
	let panelOpen = $state(false);
	let panelMode = $state(null); // "viewer" | "data"
	let panelData = $state(null); // data to display in panel
	let activeTab = $state("explore");
	let activeEvidenceSection = $state(null);
	let selectedEvidenceIndex = $state(null);

	// Viewer에서 현재 보고 있는 topic (AI 컨텍스트용)
	let viewerTopic = $state(null);     // "companyOverview", "BS" 등
	let viewerTopicLabel = $state(null); // "회사 개요", "재무상태표" 등
	let viewerPeriod = $state(null);    // "2024Q4" 등 (B2: 기간 동기화)

	// Artifact: AI 생성물 히스토리
	let artifactHistory = $state([]);  // [{view, timestamp}]
	let artifactIndex = $state(-1);    // 현재 보고 있는 artifact 인덱스

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

	function switchView(view) {
		activeView = view;
	}

	// Open disclosure viewer for a company
	function openViewer(company) {
		if (company) {
			selectedCompany = company;
			updateRecent(company);
		}
		activeView = "viewer";
		panelOpen = false;
		persist();
	}

	// Open data panel (badge click, AI data, etc.)
	function openData(data) {
		panelMode = "data";
		panelData = data;
		panelOpen = true;
		setTab("explore");
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
	function setViewerTopic(topic, label, period = null) {
		viewerTopic = topic;
		viewerTopicLabel = label || topic;
		viewerPeriod = period;
	}

	// Artifact 패널 열기
	function openArtifact(view) {
		const entry = { view, timestamp: Date.now() };
		// 중복 방지: 같은 제목의 최근 항목이 있으면 교체
		const existing = artifactHistory.findIndex(
			a => a.view?.title === view?.title && Date.now() - a.timestamp < 60000
		);
		if (existing >= 0) {
			artifactHistory[existing] = entry;
			artifactIndex = existing;
		} else {
			artifactHistory = [...artifactHistory, entry].slice(-20);  // 최대 20개
			artifactIndex = artifactHistory.length - 1;
		}
		panelMode = "artifact";
		panelData = view;
		panelOpen = true;
	}

	function navigateArtifact(index) {
		if (index < 0 || index >= artifactHistory.length) return;
		artifactIndex = index;
		panelData = artifactHistory[index].view;
	}

	function openEvidence(section, index = null) {
		panelMode = "data";
		panelOpen = true;
		activeTab = "evidence";
		activeEvidenceSection = section;
		selectedEvidenceIndex = Number.isInteger(index) ? index : null;
	}

	function clearEvidenceSelection() {
		activeEvidenceSection = null;
		selectedEvidenceIndex = null;
	}

	function setTab(tab) {
		activeTab = tab || "explore";
		if (activeTab !== "evidence") {
			clearEvidenceSelection();
		}
	}

	// Context for AI — what the user is currently viewing
	function getViewContext() {
		// Viewer 탭에서 보고 있는 topic도 AI 컨텍스트로 전달
		if (activeView === "viewer" && selectedCompany && viewerTopic) {
			return {
				type: "viewer",
				company: selectedCompany,
				topic: viewerTopic,
				topicLabel: viewerTopicLabel,
				period: viewerPeriod,
			};
		}
		if (!panelOpen) return null;
		if (panelMode === "viewer" && selectedCompany) {
			return {
				type: "viewer",
				company: selectedCompany,
				topic: viewerTopic,
				topicLabel: viewerTopicLabel,
				period: viewerPeriod,
			};
		}
		if (panelMode === "data" && panelData) {
			return { type: "data", data: panelData };
		}
		return null;
	}

	return {
		get activeView() { return activeView; },
		get panelOpen() { return panelOpen; },
		get panelMode() { return panelMode; },
		get panelData() { return panelData; },
		get activeTab() { return activeTab; },
		get activeEvidenceSection() { return activeEvidenceSection; },
		get selectedEvidenceIndex() { return selectedEvidenceIndex; },
		get selectedCompany() { return selectedCompany; },
		get recentCompanies() { return recentCompanies; },
		get viewerTopic() { return viewerTopic; },
		get viewerTopicLabel() { return viewerTopicLabel; },
		get viewerPeriod() { return viewerPeriod; },
		get artifactHistory() { return artifactHistory; },
		get artifactIndex() { return artifactIndex; },
		switchView,
		openViewer,
		openData,
		openArtifact,
		navigateArtifact,
		openEvidence,
		closePanel,
		selectCompany,
		setViewerTopic,
		clearEvidenceSelection,
		setTab,
		syncCompanyFromMessage,
		getViewContext,
	};
}
