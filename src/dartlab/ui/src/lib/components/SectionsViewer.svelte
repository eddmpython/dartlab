<script>
	import { fetchCompanyIndex, fetchCompanyDiff, fetchCompanyTopicDiff, fetchCompanyShow } from "$lib/api.js";
	import { ChevronRight, ChevronDown, FileText, Table2, GitCompare, Loader2 } from "lucide-svelte";

	let { stockCode = null, corpName = "" } = $props();

	let index = $state(null);
	let diffSummary = $state(null);
	let loading = $state(false);
	let selectedTopic = $state(null);
	let topicData = $state(null);
	let topicDiff = $state(null);
	let topicLoading = $state(false);
	let viewMode = $state("latest"); // "latest" | "changes" | "diff"
	let expandedChapters = $state(new Set());

	// diff에서 기간 선택
	let diffFrom = $state("");
	let diffTo = $state("");

	$effect(() => {
		if (stockCode) loadData();
	});

	async function loadData() {
		loading = true;
		try {
			const [idxRes, diffRes] = await Promise.all([
				fetchCompanyIndex(stockCode),
				fetchCompanyDiff(stockCode),
			]);
			index = idxRes.payload;
			diffSummary = diffRes.payload;
		} catch (e) {
			console.error("viewer load error:", e);
		}
		loading = false;
	}

	async function selectTopic(topic) {
		selectedTopic = topic;
		topicData = null;
		topicDiff = null;
		topicLoading = true;
		try {
			const res = await fetchCompanyShow(stockCode, topic);
			topicData = res.payload;
		} catch (e) {
			console.error("topic load error:", e);
		}
		topicLoading = false;
	}

	async function loadTopicDiff() {
		if (!diffFrom || !diffTo || !selectedTopic) return;
		topicDiff = null;
		topicLoading = true;
		try {
			const res = await fetchCompanyTopicDiff(stockCode, selectedTopic, diffFrom, diffTo);
			topicDiff = res.payload;
		} catch (e) {
			console.error("diff load error:", e);
		}
		topicLoading = false;
	}

	function toggleChapter(ch) {
		const next = new Set(expandedChapters);
		if (next.has(ch)) next.delete(ch);
		else next.add(ch);
		expandedChapters = next;
	}

	function getChangeInfo(topic) {
		if (!diffSummary?.rows) return null;
		return diffSummary.rows.find(r => r.topic === topic);
	}

	// index를 chapter별로 그룹
	function groupByChapter(rows) {
		const groups = [];
		let current = null;
		for (const row of rows) {
			const ch = row.chapter || "";
			if (!current || current.chapter !== ch) {
				current = { chapter: ch, topics: [] };
				groups.push(current);
			}
			current.topics.push(row);
		}
		return groups;
	}
</script>

<div class="viewer">
	<div class="viewer-header">
		<h2>{corpName || stockCode}</h2>
		<div class="view-modes">
			<button class:active={viewMode === "latest"} onclick={() => viewMode = "latest"}>최종</button>
			<button class:active={viewMode === "changes"} onclick={() => viewMode = "changes"}>변화 지점</button>
			<button class:active={viewMode === "diff"} onclick={() => viewMode = "diff"}>변화 과정</button>
		</div>
	</div>

	{#if loading}
		<div class="loading"><Loader2 class="spin" size={20} /> 로딩 중...</div>
	{:else if index?.rows}
		<div class="viewer-body">
			<!-- 좌: 목차 -->
			<nav class="toc">
				{#each groupByChapter(index.rows) as group}
					<div class="toc-chapter">
						<button class="toc-chapter-btn" onclick={() => toggleChapter(group.chapter)}>
							{#if expandedChapters.has(group.chapter)}
								<ChevronDown size={14} />
							{:else}
								<ChevronRight size={14} />
							{/if}
							<span>{group.chapter || "기타"}</span>
						</button>
						{#if expandedChapters.has(group.chapter)}
							{#each group.topics as row}
								{@const change = getChangeInfo(row.topic)}
								<button
									class="toc-topic"
									class:active={selectedTopic === row.topic}
									onclick={() => selectTopic(row.topic)}
								>
									<span class="toc-label">{row.label || row.topic}</span>
									{#if change?.changed && change.changed > 0}
										<span class="change-badge">{change.changed}</span>
									{/if}
								</button>
							{/each}
						{/if}
					</div>
				{/each}
			</nav>

			<!-- 우: 콘텐츠 -->
			<main class="content">
				{#if !selectedTopic}
					<div class="empty">좌측에서 topic을 선택하세요</div>
				{:else if topicLoading}
					<div class="loading"><Loader2 class="spin" size={20} /></div>
				{:else if viewMode === "latest"}
					<!-- 최종 상태 -->
					{#if topicData?.type === "table"}
						<table class="data-table">
							<thead>
								<tr>
									{#each topicData.columns as col}
										<th>{col}</th>
									{/each}
								</tr>
							</thead>
							<tbody>
								{#each topicData.rows as row}
									<tr>
										{#each topicData.columns as col}
											<td>{row[col] ?? ""}</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					{:else if topicData?.type === "text"}
						<div class="text-content">{topicData.data}</div>
					{:else}
						<div class="empty">데이터 없음</div>
					{/if}

				{:else if viewMode === "changes"}
					<!-- 변화 지점 -->
					{@const change = getChangeInfo(selectedTopic)}
					{#if change}
						<div class="change-summary">
							<p>전체 기간: {change.totalPeriods}개 | 변경: {change.changed}회 | 안정: {change.stable}회</p>
							<p>변경률: {((change.changeRate || 0) * 100).toFixed(1)}%</p>
						</div>
						<!-- 변경 지점 목록 -->
						{#if diffSummary?.rows}
							{@const entries = diffSummary.rows.filter(r => r.topic === selectedTopic)}
							{#each entries as entry}
								{#if entry.fromPeriod && entry.toPeriod}
									<div class="change-entry">
										<span class="period">{entry.fromPeriod} → {entry.toPeriod}</span>
										<span class="status">{entry.status}</span>
										<button class="diff-btn" onclick={() => { diffFrom = entry.fromPeriod; diffTo = entry.toPeriod; viewMode = "diff"; loadTopicDiff(); }}>
											<GitCompare size={14} /> 비교
										</button>
									</div>
								{/if}
							{/each}
						{/if}
					{:else}
						<div class="empty">변화 정보 없음</div>
					{/if}

				{:else if viewMode === "diff"}
					<!-- 변화 과정 (줄 단위 diff) -->
					<div class="diff-controls">
						<label>
							이전: <input bind:value={diffFrom} placeholder="2023" />
						</label>
						<label>
							이후: <input bind:value={diffTo} placeholder="2024" />
						</label>
						<button onclick={loadTopicDiff}>비교</button>
					</div>

					{#if topicDiff?.type === "table" && topicDiff.rows}
						<div class="diff-view">
							{#each topicDiff.rows as line}
								<div class="diff-line" class:added={line.status === "+"} class:removed={line.status === "-"}>
									<span class="diff-marker">{line.status || " "}</span>
									<span class="diff-text">{line.text}</span>
								</div>
							{/each}
						</div>
					{:else if topicDiff}
						<div class="empty">이 기간에는 변화가 없습니다</div>
					{:else}
						<div class="empty">기간을 선택하고 비교를 누르세요</div>
					{/if}
				{/if}
			</main>
		</div>
	{/if}
</div>

<style>
	.viewer { display: flex; flex-direction: column; height: 100%; font-family: system-ui, sans-serif; }
	.viewer-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #e5e7eb; }
	.viewer-header h2 { margin: 0; font-size: 16px; }
	.view-modes { display: flex; gap: 4px; }
	.view-modes button { padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer; font-size: 13px; }
	.view-modes button.active { background: #1f2937; color: white; border-color: #1f2937; }

	.viewer-body { display: flex; flex: 1; overflow: hidden; }

	.toc { width: 260px; overflow-y: auto; border-right: 1px solid #e5e7eb; padding: 8px 0; flex-shrink: 0; }
	.toc-chapter-btn { display: flex; align-items: center; gap: 4px; width: 100%; padding: 6px 12px; border: none; background: none; cursor: pointer; font-size: 13px; font-weight: 600; color: #374151; }
	.toc-topic { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 4px 12px 4px 28px; border: none; background: none; cursor: pointer; font-size: 12px; color: #6b7280; text-align: left; }
	.toc-topic:hover { background: #f3f4f6; }
	.toc-topic.active { background: #eff6ff; color: #1d4ed8; font-weight: 500; }
	.change-badge { background: #fbbf24; color: #78350f; font-size: 10px; padding: 1px 5px; border-radius: 8px; font-weight: 600; }

	.content { flex: 1; overflow-y: auto; padding: 16px; }
	.empty { color: #9ca3af; text-align: center; padding: 40px; }
	.loading { display: flex; align-items: center; gap: 8px; justify-content: center; padding: 40px; color: #6b7280; }

	.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
	.data-table th { background: #f9fafb; padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb; font-weight: 600; position: sticky; top: 0; }
	.data-table td { padding: 6px 8px; border-bottom: 1px solid #f3f4f6; white-space: pre-wrap; }
	.text-content { white-space: pre-wrap; font-size: 14px; line-height: 1.7; }

	.change-summary { background: #f9fafb; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 13px; }
	.change-entry { display: flex; align-items: center; gap: 12px; padding: 8px 12px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }
	.change-entry .period { font-weight: 500; }
	.change-entry .status { color: #dc2626; font-size: 11px; }
	.diff-btn { display: flex; align-items: center; gap: 4px; padding: 2px 8px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer; font-size: 12px; }

	.diff-controls { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
	.diff-controls input { width: 80px; padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; }
	.diff-controls button { padding: 4px 12px; border: 1px solid #1d4ed8; border-radius: 4px; background: #1d4ed8; color: white; cursor: pointer; font-size: 13px; }

	.diff-view { font-family: monospace; font-size: 13px; line-height: 1.6; }
	.diff-line { display: flex; padding: 1px 8px; }
	.diff-line.added { background: #dcfce7; }
	.diff-line.removed { background: #fee2e2; text-decoration: line-through; }
	.diff-marker { width: 16px; flex-shrink: 0; color: #9ca3af; }
	.diff-text { white-space: pre-wrap; }

	:global(.spin) { animation: spin 1s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
</style>
