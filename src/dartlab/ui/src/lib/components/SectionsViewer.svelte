<script>
	import { fetchCompanySections, fetchCompanyShow, fetchCompanyDiff, fetchCompanyTopicDiff } from "$lib/api.js";
	import { ChevronRight, ChevronDown, FileText, Table2, GitCompare, Loader2, Database, ClipboardList } from "lucide-svelte";

	let { stockCode = null, corpName = "" } = $props();

	let sections = $state(null);
	let diffSummary = $state(null);
	let loading = $state(false);

	// 좌측 목차
	let expandedChapters = $state(new Set());

	// 우측 콘텐츠
	let selectedTopic = $state(null);
	let blockIndex = $state(null);
	let blockData = $state(null);
	let selectedBlock = $state(null);
	let contentLoading = $state(false);

	// diff
	let diffFrom = $state("");
	let diffTo = $state("");
	let topicDiff = $state(null);
	let viewMode = $state("content"); // "content" | "diff"

	// 기간 목록 (sections에서 추출)
	let periods = $state([]);

	$effect(() => {
		if (stockCode) loadData();
	});

	async function loadData() {
		loading = true;
		try {
			const [secRes, diffRes] = await Promise.all([
				fetchCompanySections(stockCode),
				fetchCompanyDiff(stockCode),
			]);
			sections = secRes.payload;
			diffSummary = diffRes.payload;

			// 기간 목록 추출
			if (sections?.columns) {
				periods = sections.columns.filter(c =>
					/^\d{4}(Q[1-4])?$/.test(c)
				);
			}
		} catch (e) {
			console.error("viewer load error:", e);
		}
		loading = false;
	}

	async function selectTopic(topic) {
		selectedTopic = topic;
		blockIndex = null;
		blockData = null;
		selectedBlock = null;
		topicDiff = null;
		viewMode = "content";
		contentLoading = true;
		try {
			const res = await fetchCompanyShow(stockCode, topic);
			blockIndex = res.payload;
		} catch (e) {
			console.error("block index error:", e);
		}
		contentLoading = false;
	}

	async function selectBlock(block) {
		selectedBlock = block;
		blockData = null;
		contentLoading = true;
		try {
			const res = await fetchCompanyShow(stockCode, selectedTopic, block);
			blockData = res.payload;
		} catch (e) {
			console.error("block data error:", e);
		}
		contentLoading = false;
	}

	async function loadTopicDiff() {
		if (!diffFrom || !diffTo || !selectedTopic) return;
		topicDiff = null;
		contentLoading = true;
		try {
			const res = await fetchCompanyTopicDiff(stockCode, selectedTopic, diffFrom, diffTo);
			topicDiff = res.payload;
		} catch (e) {
			console.error("diff load error:", e);
		}
		contentLoading = false;
	}

	function toggleChapter(ch) {
		const next = new Set(expandedChapters);
		if (next.has(ch)) next.delete(ch);
		else next.add(ch);
		expandedChapters = next;
	}

	// sections를 chapter → topic 트리로 변환
	function buildTocTree(rows) {
		if (!rows) return [];
		const chapters = [];
		let current = null;
		const seenTopics = new Set();

		for (const row of rows) {
			const ch = row.chapter || "";
			if (!current || current.chapter !== ch) {
				current = { chapter: ch, topics: [] };
				chapters.push(current);
			}
			const topic = row.topic;
			if (!seenTopics.has(topic)) {
				seenTopics.add(topic);
				const source = row.source || "docs";
				current.topics.push({ topic, source });
			}
		}
		return chapters;
	}

	function getChangeInfo(topic) {
		if (!diffSummary?.rows) return null;
		return diffSummary.rows.find(r => r.topic === topic);
	}

	function sourceIcon(source) {
		if (source === "finance") return "📊";
		if (source === "report") return "📋";
		return "";
	}

	function blockTypeLabel(type) {
		if (type === "text") return "텍스트";
		if (type === "table") return "테이블";
		return type;
	}
</script>

<div class="viewer">
	<!-- 헤더 -->
	<div class="viewer-header">
		<div class="header-left">
			<h2>{corpName || stockCode}</h2>
			{#if periods.length}
				<span class="period-badge">{periods[0]} ~ {periods[periods.length - 1]}</span>
			{/if}
		</div>
		{#if selectedTopic}
			<div class="view-modes">
				<button class:active={viewMode === "content"} onclick={() => viewMode = "content"}>본문</button>
				<button class:active={viewMode === "diff"} onclick={() => viewMode = "diff"}>변화 비교</button>
			</div>
		{/if}
	</div>

	{#if loading}
		<div class="loading"><Loader2 class="spin" size={20} /> 공시 데이터 로딩 중...</div>
	{:else if sections?.rows}
		<div class="viewer-body">
			<!-- 좌: 목차 (DART 스타일) -->
			<nav class="toc">
				{#each buildTocTree(sections.rows) as group}
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
							{#each group.topics as item}
								{@const change = getChangeInfo(item.topic)}
								<button
									class="toc-topic"
									class:active={selectedTopic === item.topic}
									onclick={() => selectTopic(item.topic)}
								>
									<span class="toc-icon">{sourceIcon(item.source)}</span>
									<span class="toc-label">{item.topic}</span>
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
					<div class="empty">
						<FileText size={32} strokeWidth={1} />
						<p>좌측에서 섹션을 선택하세요</p>
					</div>

				{:else if contentLoading}
					<div class="loading"><Loader2 class="spin" size={20} /></div>

				{:else if viewMode === "content"}
					<!-- 블록 목차 + 콘텐츠 -->
					<div class="topic-header">
						<h3>{selectedTopic}</h3>
					</div>

					{#if blockIndex?.rows}
						<div class="block-list">
							{#each blockIndex.rows as row}
								<button
									class="block-item"
									class:active={selectedBlock === row.block}
									onclick={() => selectBlock(row.block)}
								>
									<span class="block-num">{row.block}</span>
									<span class="block-type" class:text={row.type === "text"} class:table={row.type === "table"}>
										{blockTypeLabel(row.type)}
									</span>
									<span class="block-source">{sourceIcon(row.source)}</span>
									<span class="block-preview">{row.preview || ""}</span>
								</button>
							{/each}
						</div>
					{/if}

					{#if blockData}
						<div class="block-content">
							{#if blockData.type === "table" && blockData.rows}
								<div class="table-wrapper">
									<table class="data-table">
										<thead>
											<tr>
												{#each blockData.columns as col}
													<th>{col}</th>
												{/each}
											</tr>
										</thead>
										<tbody>
											{#each blockData.rows as row}
												<tr>
													{#each blockData.columns as col}
														<td>{row[col] ?? ""}</td>
													{/each}
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							{:else if blockData.type === "text" && blockData.data}
								<div class="text-content">{blockData.data}</div>
							{:else if blockData.rows}
								<!-- DataFrame 형태 -->
								<div class="table-wrapper">
									<table class="data-table">
										<thead>
											<tr>
												{#each blockData.columns as col}
													<th>{col}</th>
												{/each}
											</tr>
										</thead>
										<tbody>
											{#each blockData.rows as row}
												<tr>
													{#each blockData.columns as col}
														<td>{row[col] ?? ""}</td>
													{/each}
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							{:else}
								<div class="empty">데이터 없음</div>
							{/if}
						</div>
					{/if}

				{:else if viewMode === "diff"}
					<!-- 변화 비교 -->
					<div class="topic-header">
						<h3>{selectedTopic} — 변화 비교</h3>
					</div>

					<div class="diff-controls">
						<select bind:value={diffFrom}>
							<option value="">이전 기간</option>
							{#each periods as p}
								<option value={p}>{p}</option>
							{/each}
						</select>
						<span class="diff-arrow">→</span>
						<select bind:value={diffTo}>
							<option value="">이후 기간</option>
							{#each periods as p}
								<option value={p}>{p}</option>
							{/each}
						</select>
						<button class="diff-run-btn" onclick={loadTopicDiff}>비교</button>
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
	.viewer {
		display: flex;
		flex-direction: column;
		height: 100%;
		font-family: 'Pretendard', system-ui, -apple-system, sans-serif;
		background: #fafbfc;
	}

	/* 헤더 */
	.viewer-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 14px 20px;
		background: white;
		border-bottom: 2px solid #1a365d;
	}
	.header-left {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.viewer-header h2 {
		margin: 0;
		font-size: 17px;
		font-weight: 700;
		color: #1a365d;
	}
	.period-badge {
		font-size: 11px;
		color: #64748b;
		background: #f1f5f9;
		padding: 2px 8px;
		border-radius: 4px;
	}
	.view-modes {
		display: flex;
		gap: 2px;
		background: #f1f5f9;
		border-radius: 6px;
		padding: 2px;
	}
	.view-modes button {
		padding: 5px 14px;
		border: none;
		border-radius: 4px;
		background: transparent;
		cursor: pointer;
		font-size: 13px;
		color: #64748b;
		font-weight: 500;
	}
	.view-modes button.active {
		background: white;
		color: #1a365d;
		box-shadow: 0 1px 2px rgba(0,0,0,0.08);
	}

	/* 본문 */
	.viewer-body {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	/* 좌: 목차 */
	.toc {
		width: 280px;
		overflow-y: auto;
		background: white;
		border-right: 1px solid #e2e8f0;
		flex-shrink: 0;
	}
	.toc-chapter-btn {
		display: flex;
		align-items: center;
		gap: 6px;
		width: 100%;
		padding: 10px 14px;
		border: none;
		border-bottom: 1px solid #f1f5f9;
		background: #f8fafc;
		cursor: pointer;
		font-size: 13px;
		font-weight: 700;
		color: #1e293b;
		text-align: left;
	}
	.toc-chapter-btn:hover {
		background: #f1f5f9;
	}
	.toc-topic {
		display: flex;
		align-items: center;
		gap: 6px;
		width: 100%;
		padding: 7px 14px 7px 32px;
		border: none;
		border-bottom: 1px solid #f8fafc;
		background: none;
		cursor: pointer;
		font-size: 12px;
		color: #475569;
		text-align: left;
	}
	.toc-topic:hover {
		background: #f1f5f9;
	}
	.toc-topic.active {
		background: #eff6ff;
		color: #1d4ed8;
		font-weight: 600;
		border-left: 3px solid #1d4ed8;
		padding-left: 29px;
	}
	.toc-icon {
		font-size: 11px;
		width: 16px;
		flex-shrink: 0;
	}
	.toc-label {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.change-badge {
		background: #fbbf24;
		color: #78350f;
		font-size: 10px;
		padding: 1px 5px;
		border-radius: 8px;
		font-weight: 700;
		flex-shrink: 0;
	}

	/* 우: 콘텐츠 */
	.content {
		flex: 1;
		overflow-y: auto;
		padding: 0;
	}
	.topic-header {
		padding: 16px 20px 12px;
		border-bottom: 1px solid #e2e8f0;
		background: white;
		position: sticky;
		top: 0;
		z-index: 10;
	}
	.topic-header h3 {
		margin: 0;
		font-size: 15px;
		font-weight: 600;
		color: #1e293b;
	}

	/* 블록 목록 */
	.block-list {
		padding: 8px 12px;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.block-item {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 12px;
		border: 1px solid #e2e8f0;
		border-radius: 6px;
		background: white;
		cursor: pointer;
		font-size: 12px;
		text-align: left;
	}
	.block-item:hover {
		border-color: #93c5fd;
		background: #f0f9ff;
	}
	.block-item.active {
		border-color: #1d4ed8;
		background: #eff6ff;
	}
	.block-num {
		width: 22px;
		height: 22px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #f1f5f9;
		border-radius: 4px;
		font-weight: 600;
		color: #64748b;
		font-size: 11px;
		flex-shrink: 0;
	}
	.block-type {
		font-size: 11px;
		padding: 1px 6px;
		border-radius: 3px;
		font-weight: 500;
		flex-shrink: 0;
	}
	.block-type.text {
		background: #ecfdf5;
		color: #065f46;
	}
	.block-type.table {
		background: #eff6ff;
		color: #1e40af;
	}
	.block-source {
		font-size: 11px;
		flex-shrink: 0;
	}
	.block-preview {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: #94a3b8;
		font-size: 11px;
	}

	/* 블록 콘텐츠 */
	.block-content {
		padding: 16px 20px;
	}

	.empty {
		color: #94a3b8;
		text-align: center;
		padding: 60px 20px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
	}
	.loading {
		display: flex;
		align-items: center;
		gap: 8px;
		justify-content: center;
		padding: 40px;
		color: #64748b;
	}

	/* 테이블 */
	.table-wrapper {
		overflow-x: auto;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
	}
	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
	}
	.data-table th {
		background: #f8fafc;
		padding: 10px 12px;
		text-align: left;
		border-bottom: 2px solid #e2e8f0;
		font-weight: 600;
		color: #1e293b;
		position: sticky;
		top: 0;
		white-space: nowrap;
	}
	.data-table td {
		padding: 8px 12px;
		border-bottom: 1px solid #f1f5f9;
		white-space: pre-wrap;
		color: #334155;
	}
	.data-table tr:hover td {
		background: #f8fafc;
	}

	/* 텍스트 */
	.text-content {
		white-space: pre-wrap;
		font-size: 14px;
		line-height: 1.8;
		color: #1e293b;
		padding: 4px 0;
	}

	/* diff */
	.diff-controls {
		display: flex;
		gap: 8px;
		align-items: center;
		padding: 12px 20px;
		background: #f8fafc;
		border-bottom: 1px solid #e2e8f0;
	}
	.diff-controls select {
		padding: 6px 10px;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 13px;
		background: white;
	}
	.diff-arrow {
		color: #94a3b8;
		font-weight: 600;
	}
	.diff-run-btn {
		padding: 6px 16px;
		border: none;
		border-radius: 6px;
		background: #1d4ed8;
		color: white;
		cursor: pointer;
		font-size: 13px;
		font-weight: 500;
	}
	.diff-run-btn:hover {
		background: #1e40af;
	}

	.diff-view {
		font-family: 'JetBrains Mono', monospace;
		font-size: 13px;
		line-height: 1.7;
		padding: 12px 20px;
	}
	.diff-line {
		display: flex;
		padding: 2px 8px;
		border-radius: 3px;
	}
	.diff-line.added {
		background: #dcfce7;
	}
	.diff-line.removed {
		background: #fee2e2;
		text-decoration: line-through;
		opacity: 0.7;
	}
	.diff-marker {
		width: 18px;
		flex-shrink: 0;
		color: #94a3b8;
		font-weight: 600;
	}
	.diff-text {
		white-space: pre-wrap;
	}

	:global(.spin) { animation: spin 1s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
</style>
