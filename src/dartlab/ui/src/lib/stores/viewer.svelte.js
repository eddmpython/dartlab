/**
 * Viewer state — 공시 뷰어 전용 상태 관리.
 *
 * toc(목차), 선택 topic, 로딩 상태, 캐시 등을 관리한다.
 * workspace store와 독립 — viewer 내부 네비게이션에만 사용.
 */
import { fetchCompanyToc, fetchCompanyViewer, fetchCompanyDiffSummary, fetchCompanyInsights } from "$lib/api.js";

function loadBookmarks() {
	try {
		const raw = localStorage.getItem("dartlab-bookmarks");
		return raw ? JSON.parse(raw) : {};
	} catch { return {}; }
}

function saveBookmarks(bm) {
	try { localStorage.setItem("dartlab-bookmarks", JSON.stringify(bm)); } catch {}
}

export function createViewerStore() {
	let stockCode = $state(null);
	let corpName = $state(null);

	// TOC
	let toc = $state(null); // { chapters: [...] }
	let tocLoading = $state(false);

	// Selected topic
	let selectedTopic = $state(null);
	let selectedChapter = $state(null);
	let expandedChapters = $state(new Set());

	// Topic content
	let topicData = $state(null); // viewer API response
	let topicLoading = $state(false);

	// Diff summary
	let diffSummary = $state(null);

	// Cache
	let topicCache = new Map();

	// Insights (P1)
	let insightData = $state(null);
	let insightLoading = $state(false);

	// Topic AI summary cache (P2)
	let topicSummaryCache = $state(new Map());

	// Bookmarks (P6)
	let allBookmarks = $state(loadBookmarks());

	async function loadCompany(code) {
		if (code === stockCode && toc) return;
		stockCode = code;
		corpName = null;
		toc = null;
		selectedTopic = null;
		selectedChapter = null;
		topicData = null;
		diffSummary = null;
		topicCache = new Map();
		expandedChapters = new Set();
		insightData = null;
		topicSummaryCache = new Map();

		tocLoading = true;
		try {
			const res = await fetchCompanyToc(code);
			toc = res;
			corpName = res.corpName;
			// 첫 번째 chapter 자동 확장
			if (res.chapters?.length > 0) {
				expandedChapters = new Set([res.chapters[0].chapter]);
				// 첫 번째 topic 자동 선택
				if (res.chapters[0].topics?.length > 0) {
					const first = res.chapters[0].topics[0];
					await selectTopic(first.topic, res.chapters[0].chapter);
				}
			}
			// 병렬로 insights 로드 (P1)
			loadInsights(code);
		} catch (e) {
			console.error("TOC 로드 실패:", e);
		}
		tocLoading = false;
	}

	async function loadInsights(code) {
		if (insightData?.stockCode === code) return;
		insightLoading = true;
		try {
			const res = await fetchCompanyInsights(code);
			if (res.available) insightData = res;
			else insightData = null;
		} catch {
			insightData = null;
		}
		insightLoading = false;
	}

	async function selectTopic(topic, chapter) {
		if (topic === selectedTopic) return;
		selectedTopic = topic;
		selectedChapter = chapter;

		// 선택된 chapter 자동 확장
		if (chapter && !expandedChapters.has(chapter)) {
			expandedChapters = new Set([...expandedChapters, chapter]);
		}

		// 캐시 확인
		if (topicCache.has(topic)) {
			topicData = topicCache.get(topic);
			return;
		}

		topicLoading = true;
		topicData = null;
		diffSummary = null;

		try {
			const [viewerRes, diffRes] = await Promise.allSettled([
				fetchCompanyViewer(stockCode, topic),
				fetchCompanyDiffSummary(stockCode, topic),
			]);
			if (viewerRes.status === "fulfilled") {
				topicData = viewerRes.value;
				topicCache.set(topic, viewerRes.value);
			}
			if (diffRes.status === "fulfilled") {
				diffSummary = diffRes.value;
			}
		} catch (e) {
			console.error("Topic 로드 실패:", e);
		}
		topicLoading = false;
	}

	function toggleChapter(chapter) {
		const next = new Set(expandedChapters);
		if (next.has(chapter)) {
			next.delete(chapter);
		} else {
			next.add(chapter);
		}
		expandedChapters = next;
	}

	// P2: topic summary cache
	function getTopicSummary(topic) {
		return topicSummaryCache.get(topic) ?? null;
	}
	function setTopicSummary(topic, text) {
		const next = new Map(topicSummaryCache);
		next.set(topic, text);
		topicSummaryCache = next;
	}

	// P6: bookmarks
	function getBookmarks() {
		return allBookmarks[stockCode] || [];
	}
	function isBookmarked(topic) {
		return (allBookmarks[stockCode] || []).includes(topic);
	}
	function toggleBookmark(topic) {
		const current = allBookmarks[stockCode] || [];
		const next = current.includes(topic) ? current.filter(t => t !== topic) : [topic, ...current];
		allBookmarks = { ...allBookmarks, [stockCode]: next };
		saveBookmarks(allBookmarks);
	}

	return {
		get stockCode() { return stockCode; },
		get corpName() { return corpName; },
		get toc() { return toc; },
		get tocLoading() { return tocLoading; },
		get selectedTopic() { return selectedTopic; },
		get selectedChapter() { return selectedChapter; },
		get expandedChapters() { return expandedChapters; },
		get topicData() { return topicData; },
		get topicLoading() { return topicLoading; },
		get diffSummary() { return diffSummary; },
		get insightData() { return insightData; },
		get insightLoading() { return insightLoading; },
		loadCompany,
		selectTopic,
		toggleChapter,
		getTopicSummary,
		setTopicSummary,
		getBookmarks,
		isBookmarked,
		toggleBookmark,
	};
}
