/**
 * Viewer state — 공시 뷰어 전용 상태 관리.
 *
 * toc(목차), 선택 topic, 로딩 상태, 캐시 등을 관리한다.
 * workspace store와 독립 — viewer 내부 네비게이션에만 사용.
 */
import { fetchCompanyInit, fetchCompanyToc, fetchCompanyViewer, fetchCompanyViewerBatch, fetchCompanyDiffSummary, fetchCompanyInsights, fetchCompanyNetwork, fetchSearchIndex } from "$lib/api.js";
import MiniSearch from "minisearch";

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

	// Network (ego graph)
	let networkData = $state(null);
	let networkLoading = $state(false);

	// Topic AI summary cache (P2)
	let topicSummaryCache = $state(new Map());

	// B3: Search highlight
	let searchHighlight = $state(null);  // string | null

	// MiniSearch — 브라우저 내 전문 검색
	let miniSearchInstance = null;
	let searchIndexReady = $state(false);

	// Bookmarks (P6)
	let allBookmarks = $state(loadBookmarks());

	async function loadCompany(code) {
		if (code === stockCode && (toc || tocLoading)) return;
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
		networkData = null;
		topicSummaryCache = new Map();
		miniSearchInstance = null;
		searchIndexReady = false;

		tocLoading = true;
		try {
			// 배치 API — toc + 첫 topic viewer + diffSummary를 1회 왕복으로 수신
			const res = await fetchCompanyInit(code);
			toc = res.toc;
			corpName = res.corpName;

			// 첫 번째 chapter 자동 확장 + topic 선택
			if (res.toc?.chapters?.length > 0) {
				expandedChapters = new Set([res.toc.chapters[0].chapter]);
			}
			if (res.firstTopic && res.viewer) {
				selectedTopic = res.firstTopic;
				selectedChapter = res.firstChapter;
				topicData = res.viewer;
				topicCache.set(res.firstTopic, res.viewer);
				visitedTopics = new Set([res.firstTopic]);
			}
			if (res.diffSummary) {
				diffSummary = res.diffSummary;
			}

			// 병렬로 insights + network + searchIndex 로드
			loadInsights(code);
			loadNetwork(code);
			loadSearchIndex(code);
		} catch (e) {
			console.error("초기 로드 실패:", e);
			// fallback: 개별 API 호출
			try {
				const tocRes = await fetchCompanyToc(code);
				toc = tocRes;
				corpName = tocRes.corpName;
				if (tocRes.chapters?.length > 0) {
					expandedChapters = new Set([tocRes.chapters[0].chapter]);
					if (tocRes.chapters[0].topics?.length > 0) {
						const first = tocRes.chapters[0].topics[0];
						await selectTopic(first.topic, tocRes.chapters[0].chapter);
					}
				}
				loadInsights(code);
				loadNetwork(code);
				loadSearchIndex(code);
			} catch (e2) {
				console.error("TOC 로드 실패:", e2);
			}
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

	async function loadNetwork(code) {
		networkLoading = true;
		try {
			const res = await fetchCompanyNetwork(code);
			if (res.available) networkData = res;
			else networkData = null;
		} catch {
			networkData = null;
		}
		networkLoading = false;
	}

	async function loadSearchIndex(code) {
		try {
			const res = await fetchSearchIndex(code);
			if (!res.documents || res.documents.length === 0) return;
			const ms = new MiniSearch({
				fields: ["label", "text"],
				storeFields: ["topic", "label", "chapter", "period", "blockType"],
				searchOptions: {
					boost: { label: 3 },
					fuzzy: 0.2,
					prefix: true,
				},
			});
			ms.addAll(res.documents);
			miniSearchInstance = ms;
			searchIndexReady = true;
		} catch (e) {
			console.error("SearchIndex 로드 실패:", e);
		}
	}

	function searchSections(query) {
		if (!miniSearchInstance || !query?.trim()) return [];
		const raw = miniSearchInstance.search(query.trim(), {
			fuzzy: 0.2,
			prefix: true,
			boost: { label: 3 },
		});
		// topic 단위로 deduplicate, 최고 score 유지
		const byTopic = new Map();
		for (const r of raw) {
			const key = r.topic;
			if (!byTopic.has(key) || byTopic.get(key).score < r.score) {
				byTopic.set(key, r);
			}
		}
		return [...byTopic.values()]
			.sort((a, b) => b.score - a.score)
			.slice(0, 20)
			.map(r => ({
				topic: r.topic,
				label: r.label,
				chapter: r.chapter,
				period: r.period,
				blockType: r.blockType,
				score: r.score,
				source: "minisearch",
			}));
	}

	function setSearchHighlight(query) {
		searchHighlight = query || null;
	}

	async function selectTopic(topic, chapter) {
		if (topic === selectedTopic) return;
		selectedTopic = topic;
		searchHighlight = null;  // topic 변경 시 하이라이트 초기화
		selectedChapter = chapter;

		// 선택된 chapter 자동 확장
		if (chapter && !expandedChapters.has(chapter)) {
			expandedChapters = new Set([...expandedChapters, chapter]);
		}

		// 캐시 확인
		if (topicCache.has(topic)) {
			topicData = topicCache.get(topic);
			visitedTopics = new Set([...visitedTopics, topic]);
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

	// Prefetch — 캐시만 채우고 selectedTopic 변경 안 함
	let prefetchInFlight = new Set();
	let visitedTopics = $state(new Set());

	async function prefetchTopic(topic) {
		if (!topic || !stockCode || topicCache.has(topic) || prefetchInFlight.has(topic)) return;
		prefetchInFlight.add(topic);
		try {
			const res = await fetchCompanyViewer(stockCode, topic);
			topicCache.set(topic, res);
		} catch { /* 프리페치 실패는 무시 */ }
		prefetchInFlight.delete(topic);
	}

	function getAllTopics() {
		if (!toc?.chapters) return [];
		return toc.chapters.flatMap(ch => (ch.topics || []).map(t => ({ topic: t.topic, chapter: ch.chapter })));
	}

	function toggleChapter(chapter) {
		const next = new Set(expandedChapters);
		if (next.has(chapter)) {
			next.delete(chapter);
		} else {
			next.add(chapter);
			// chapter 확장 시 해당 chapter의 미캐시 topic들을 batch prefetch
			batchPrefetchChapter(chapter);
		}
		expandedChapters = next;
	}

	async function batchPrefetchChapter(chapter) {
		if (!toc?.chapters || !stockCode) return;
		const ch = toc.chapters.find(c => c.chapter === chapter);
		if (!ch?.topics) return;
		const uncached = ch.topics
			.map(t => t.topic)
			.filter(t => !topicCache.has(t) && !prefetchInFlight.has(t));
		if (uncached.length === 0) return;
		for (const t of uncached) prefetchInFlight.add(t);
		try {
			const res = await fetchCompanyViewerBatch(stockCode, uncached);
			if (res.results) {
				for (const [topic, data] of Object.entries(res.results)) {
					if (data) topicCache.set(topic, data);
				}
			}
		} catch { /* batch prefetch 실패는 무시 — 개별 fetch로 fallback */ }
		for (const t of uncached) prefetchInFlight.delete(t);
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
		get networkData() { return networkData; },
		get networkLoading() { return networkLoading; },
		get searchHighlight() { return searchHighlight; },
		get searchIndexReady() { return searchIndexReady; },
		loadCompany,
		setSearchHighlight,
		searchSections,
		get visitedTopics() { return visitedTopics; },
		selectTopic,
		prefetchTopic,
		toggleChapter,
		getTopicSummary,
		setTopicSummary,
		getBookmarks,
		isBookmarked,
		toggleBookmark,
	};
}
