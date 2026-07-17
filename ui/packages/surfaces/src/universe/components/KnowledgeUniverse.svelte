<script lang="ts">
	import { onMount } from 'svelte';
	import type {
		UniverseKnowledgeContent,
		UniverseKnowledgeCoverage,
		UniverseKnowledgeDomainId,
		UniverseKnowledgeNode,
		UniverseKnowledgeOverview,
		UniverseKnowledgeScene,
		UniverseKnowledgeSearchRequest,
		UniverseKnowledgeSearchResult
	} from '@dartlab/ui-contracts';
	import KnowledgeArticle from './KnowledgeArticle.svelte';
	import KnowledgeCanvas from './KnowledgeCanvas.svelte';

	interface Props {
		loadOverview: () => Promise<UniverseKnowledgeOverview>;
		loadCoverage: () => Promise<UniverseKnowledgeCoverage>;
		loadContent: (targetId: string, rowStart?: number) => Promise<UniverseKnowledgeContent>;
		searchKnowledge: (request: UniverseKnowledgeSearchRequest) => Promise<UniverseKnowledgeSearchResult>;
		openKnowledge: (targetId: string) => Promise<UniverseKnowledgeScene>;
	}

	let { loadOverview, loadCoverage, loadContent, searchKnowledge, openKnowledge }: Props = $props();
	let overview = $state<UniverseKnowledgeOverview | null>(null);
	let coverage = $state<UniverseKnowledgeCoverage | null>(null);
	let content = $state<UniverseKnowledgeContent | null>(null);
	let contentLoading = $state(false);
	let contentError = $state<string | null>(null);
	let contentRequest = 0;
	let contentTargetId = '';
	let scene = $state<UniverseKnowledgeScene | null>(null);
	let selectedId = $state<string | null>(null);
	let focusNodeId = $state<string | null>(null);
	let query = $state('');
	let searchResult = $state<UniverseKnowledgeSearchResult | null>(null);
	let loading = $state(true);
	let coverageLoading = $state(false);
	let error = $state<string | null>(null);
	let viewMode = $state<'space' | 'table'>('space');
	let filmIndex = $state(0);
	let filmActive = $state(false);
	let filmPlaying = $state(false);
	let filmSpeed = $state<0.5 | 1 | 2>(1);
	let idleHandle: number | null = null;
	let articleOpen = $state(false);

	const domainColors: Readonly<Record<UniverseKnowledgeDomainId, string>> = {
		sources: '#7f91aa', entities: '#76b8ff', securities: '#50d0be', filings: '#f0a66c',
		observations: '#f2cf6b', industry: '#7ed98a', marketData: '#58a9e8', macro: '#aa8cff',
		intelligence: '#e187b3', capabilities: '#ff786d', skills: '#b59cff', timeMedia: '#9aa8be'
	};

	let selectedNode = $derived(scene && selectedId ? scene.nodes.find((node) => node.nodeId === selectedId) ?? null : null);
	let connectedEdges = $derived(scene && selectedId ? scene.edges.filter((edge) => edge.sourceId === selectedId || edge.targetId === selectedId) : []);
	let currentBeat = $derived(scene?.film[Math.max(0, Math.min((scene?.film.length ?? 1) - 1, filmIndex))] ?? null);
	let selectedAttributes = $derived(selectedNode ? Object.entries(selectedNode.attributes).filter(([, value]) => value !== '' && value !== null).slice(0, 8) : []);
	let activeDomainId = $derived((scene?.targetId.startsWith('domain:') ? scene.targetId.slice('domain:'.length) : selectedNode?.domainId) as UniverseKnowledgeDomainId | null);

	function message(value: unknown, fallback: string): string {
		return value instanceof Error && value.message ? value.message : fallback;
	}

	function formatBytes(value: number): string {
		if (value >= 1e12) return `${(value / 1e12).toLocaleString('ko-KR', { maximumFractionDigits: 2 })} TB`;
		if (value >= 1e9) return `${(value / 1e9).toLocaleString('ko-KR', { maximumFractionDigits: 1 })} GB`;
		if (value >= 1e6) return `${(value / 1e6).toLocaleString('ko-KR', { maximumFractionDigits: 1 })} MB`;
		if (value >= 1e3) return `${(value / 1e3).toLocaleString('ko-KR', { maximumFractionDigits: 1 })} KB`;
		return `${value.toLocaleString()} B`;
	}

	function formatDate(value: string | null): string {
		if (!value) return '기록 없음';
		const date = new Date(value);
		if (Number.isNaN(date.getTime())) return value;
		return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
	}

	function domainCount(domainId: UniverseKnowledgeDomainId): number | null {
		return coverage?.domainCounts[domainId]
			?? overview?.domains.find((domain) => domain.domainId === domainId)?.itemCount
			?? null;
	}

	function domainLabel(domainId: UniverseKnowledgeDomainId | null): string {
		return overview?.domains.find((domain) => domain.domainId === domainId)?.label ?? '통합 지식';
	}

	function nodeKindLabel(node: UniverseKnowledgeNode): string {
		const labels: Readonly<Record<string, string>> = {
			root: '지식 루트', repository: '저장소', domain: '지식 은하', directory: '데이터 계층', file: '원본 파일', skill: 'Skill OS',
			capability: '엔진 능력', dataset: '데이터셋', entity: '법인과 기관', security: '증권 식별자', document: '문서',
			section: '공시 섹션', observation: '관측', media: '미디어', query: '질문'
		};
		return labels[node.kind] ?? node.kind;
	}

	async function hydrateCoverage(): Promise<void> {
		if (coverage || coverageLoading) return;
		coverageLoading = true;
		try {
			coverage = await loadCoverage();
		} catch {
			coverage = null;
		} finally {
			coverageLoading = false;
		}
	}

	async function hydrateOverview(): Promise<void> {
		loading = true;
		error = null;
		try {
			overview = await loadOverview();
			scene = overview.scene;
			selectedId = overview.scene.targetId;
			focusNodeId = overview.scene.targetId;
			const schedule = window.requestIdleCallback ?? ((callback: IdleRequestCallback) => window.setTimeout(() => callback({ didTimeout: false, timeRemaining: () => 16 }), 120));
			idleHandle = schedule(() => void hydrateCoverage());
		} catch (value) {
			error = message(value, '통합 지식 카탈로그에 연결하지 못했습니다.');
		} finally {
			loading = false;
		}
	}

	function applyScene(next: UniverseKnowledgeScene): void {
		scene = next;
		selectedId = next.targetId;
		focusNodeId = next.targetId;
		filmIndex = 0;
		filmActive = false;
		filmPlaying = false;
		searchResult = null;
		content = null;
		contentError = null;
		contentTargetId = '';
	}

	async function hydrateContent(targetId: string, rowStart = 0): Promise<void> {
		const request = ++contentRequest;
		contentLoading = true;
		contentError = null;
		try {
			const next = await loadContent(targetId, rowStart);
			if (request === contentRequest) content = next;
		} catch (value) {
			if (request === contentRequest) contentError = message(value, '원본 내용을 미리 볼 수 없습니다.');
		} finally {
			if (request === contentRequest) contentLoading = false;
		}
	}

	function moveTableWindow(direction: -1 | 1): void {
		if (!content || content.tableMeta.format !== 'parquet' || content.tableMeta.totalRows === null) return;
		const lastWindowStart = Math.floor(Math.max(0, content.tableMeta.totalRows - 1) / content.receipt.rowLimit) * content.receipt.rowLimit;
		const nextStart = Math.max(0, Math.min(
			lastWindowStart,
			content.tableMeta.rowStart + direction * content.receipt.rowLimit
		));
		void hydrateContent(content.targetId, nextStart);
	}

	async function openTarget(targetId: string): Promise<void> {
		if (!targetId || loading) return;
		loading = true;
		error = null;
		try {
			applyScene(await openKnowledge(targetId));
		} catch (value) {
			error = message(value, '선택한 지식 장면을 열지 못했습니다.');
		} finally {
			loading = false;
		}
	}

	function selectNode(nodeId: string): void {
		selectedId = nodeId;
		focusNodeId = nodeId;
		filmActive = false;
		filmPlaying = false;
	}

	function navigateArticle(nodeId: string): void {
		const nextNode = scene?.nodes.find((node) => node.nodeId === nodeId);
		selectNode(nodeId);
		if (nextNode?.expandable) void openTarget(nodeId);
	}

	async function submitSearch(event?: SubmitEvent): Promise<void> {
		event?.preventDefault();
		const value = query.trim();
		if (value.length < 2 || loading) return;
		loading = true;
		error = null;
		try {
			searchResult = await searchKnowledge({ query: value, limit: 56 });
			scene = searchResult.scene;
			selectedId = searchResult.scene.targetId;
			focusNodeId = searchResult.scene.targetId;
			filmIndex = 0;
			filmActive = false;
			filmPlaying = false;
		} catch (value) {
			error = message(value, '통합 지식 검색에 실패했습니다.');
		} finally {
			loading = false;
		}
	}

	function activateBeat(index: number, play = false): void {
		if (!scene?.film.length) return;
		filmIndex = Math.max(0, Math.min(scene.film.length - 1, index));
		filmActive = true;
		filmPlaying = play;
		const beat = scene.film[filmIndex];
		selectedId = beat.targetNodeId;
		focusNodeId = beat.targetNodeId;
	}

	function toggleFilm(): void {
		if (!scene?.film.length) return;
		if (filmPlaying) {
			filmPlaying = false;
			return;
		}
		activateBeat(filmIndex >= scene.film.length - 1 ? 0 : filmIndex, true);
	}

	function cycleSpeed(): void {
		filmSpeed = filmSpeed === 0.5 ? 1 : filmSpeed === 1 ? 2 : 0.5;
	}

	$effect(() => {
		if (!filmPlaying || !scene || !currentBeat) return;
		const activeScene = scene;
		const activeBeat = currentBeat;
		const timer = window.setTimeout(() => {
			if (filmIndex >= activeScene.film.length - 1) {
				filmPlaying = false;
				return;
			}
			activateBeat(filmIndex + 1, true);
		}, activeBeat.durationMs / filmSpeed);
		return () => window.clearTimeout(timer);
	});

	$effect(() => {
		const targetId = selectedNode?.nodeId ?? '';
		if (targetId.startsWith('hf:')) {
			if (targetId !== contentTargetId) {
				contentTargetId = targetId;
				void hydrateContent(targetId);
			}
			return;
		}
		contentTargetId = '';
		contentRequest += 1;
		content = null;
		contentLoading = false;
		contentError = null;
	});

	onMount(() => {
		void hydrateOverview();
		return () => {
			if (idleHandle !== null) {
				if (window.cancelIdleCallback) window.cancelIdleCallback(idleHandle);
				else window.clearTimeout(idleHandle);
			}
		};
	});
</script>

<section class="knowledgeUniverse" aria-label="DartLab 통합 지식 우주">
	<header class="commandBar">
		<div class="scenePath" aria-label="현재 지식 경로">
			{#if scene}
				{#each scene.breadcrumbs as crumb, index (crumb.targetId)}
					{#if index > 0}<i>/</i>{/if}
					<button type="button" onclick={() => void openTarget(crumb.targetId)}>{crumb.label}</button>
				{/each}
			{:else}
				<span>KNOWLEDGE UNIVERSE</span>
			{/if}
		</div>
		<form class="omnibox" onsubmit={submitSearch}>
			<span aria-hidden="true">⌕</span>
			<label class="srOnly" for="knowledge-query">모든 데이터와 지식 검색</label>
			<input id="knowledge-query" bind:value={query} autocomplete="off" spellcheck="false" placeholder="회사, 기술, 공시, 데이터, 엔진, 스킬을 한 번에 검색" />
			<button type="submit" disabled={query.trim().length < 2 || loading}>탐색</button>
		</form>
		<div class="catalogState">
			<span class:live={Boolean(coverage)}></span>
			<div><b>{coverage ? coverage.addressableItemCount.toLocaleString() : coverageLoading ? 'INDEXING' : 'CATALOG'}</b><small>{overview ? formatBytes(overview.repository.mainSizeBytes) : 'HF SSOT'}</small></div>
		</div>
	</header>

	<div class="universeBody">
		<nav class="galaxyRail" aria-label="지식 은하">
			<div class="railTitle"><span>GALAXIES</span><b>12</b></div>
			{#each overview?.domains ?? [] as domain, index (domain.domainId)}
				<button
					type="button"
					class:active={activeDomainId === domain.domainId}
					style:--domain-color={domainColors[domain.domainId]}
					onclick={() => void openTarget(`domain:${domain.domainId}`)}
				>
					<i>{String(index + 1).padStart(2, '0')}</i>
					<span><strong>{domain.label}</strong><small>{domainCount(domain.domainId)?.toLocaleString() ?? '탐색 가능'}</small></span>
				</button>
			{/each}
		</nav>

		<section class="sceneStage">
			<header class="sceneTitle">
				<div>
					<span>{scene?.targetId === 'knowledge:root' ? 'MACRO UNIVERSE' : selectedNode?.domainId ? domainLabel(selectedNode.domainId).toLocaleUpperCase() : 'KNOWLEDGE SCENE'}</span>
					<h1>{scene?.title ?? 'DartLab Knowledge Universe'}</h1>
					<p>{scene?.subtitle ?? '통합 카탈로그를 연결하고 있습니다.'}</p>
				</div>
				<div class="viewMode" aria-label="지식 보기 방식">
					<button type="button" class:active={viewMode === 'space'} onclick={() => (viewMode = 'space')}>공간</button>
					<button type="button" class:active={viewMode === 'table'} onclick={() => (viewMode = 'table')}>표</button>
				</div>
			</header>

			{#if error}
				<div class="errorNotice"><span>연결 실패</span><p>{error}</p><button type="button" onclick={() => void hydrateOverview()}>다시 연결</button></div>
		{:else if !scene}
				<div class="loadingScene"><i></i><span>Hugging Face와 Skill OS 주소 공간을 결속하는 중</span></div>
			{:else if viewMode === 'space'}
				<KnowledgeCanvas {scene} {selectedId} {focusNodeId} {filmActive} filmBeatIndex={filmIndex} onSelect={selectNode} onOpen={(nodeId) => void openTarget(nodeId)} />
			{:else}
				<div class="knowledgeTable" role="table" aria-label={`${scene.title} 지식 개체 표`}>
					<div class="tableRow tableHead" role="row"><span>지식 개체</span><span>유형</span><span>은하</span><span>근거 주소</span></div>
					{#each scene.nodes as node (node.nodeId)}
						<button class="tableRow" class:selected={selectedId === node.nodeId} role="row" onclick={() => selectNode(node.nodeId)} ondblclick={() => { if (node.expandable) void openTarget(node.nodeId); }}>
							<span><b>{node.label}</b><small>{node.secondaryLabel}</small></span>
							<span>{nodeKindLabel(node)}</span>
							<span>{domainLabel(node.domainId)}</span>
							<code>{node.sourceRef}</code>
						</button>
					{/each}
				</div>
			{/if}
			{#if loading && scene}<div class="sceneLoading"><i></i><span>장면 전환 중</span></div>{/if}
		</section>

		<aside class="knowledgeLens" aria-label="선택한 지식의 상세">
			{#if selectedNode}
				<header><span>KNOWLEDGE LENS</span><b style:--domain-color={domainColors[selectedNode.domainId ?? 'sources']}>{nodeKindLabel(selectedNode)}</b></header>
				<div class="nodeIdentity">
					<i style:--domain-color={domainColors[selectedNode.domainId ?? 'sources']}></i>
					<div><h2>{selectedNode.label}</h2><p>{selectedNode.secondaryLabel}</p></div>
				</div>
				<div class="lensStats">
					<div><span>DOMAIN</span><strong>{domainLabel(selectedNode.domainId)}</strong></div>
					<div><span>RELATIONS</span><strong>{connectedEdges.length.toLocaleString()}</strong></div>
					<div><span>LANE</span><strong>{selectedNode.lane.toLocaleUpperCase()}</strong></div>
					<div><span>WEIGHT</span><strong>{selectedNode.weight.toFixed(1)}</strong></div>
				</div>
				{#if contentLoading}
					<div class="contentLoading"><i></i><span>원본 내용을 revision에 맞춰 읽는 중</span></div>
				{:else if contentError}
					<div class="contentError"><span>PREVIEW UNAVAILABLE</span><p>{contentError}</p></div>
				{:else if content}
					<section class="contentPreview" aria-label={`${content.title} 원본 미리보기`}>
						<header><span>ORIGINAL CONTENT</span><b>{content.kind.toLocaleUpperCase()}</b></header>
						{#if content.kind === 'image'}
							<img src={content.contentRef} alt={content.title} loading="eager" />
						{:else if content.kind === 'video'}
							<!-- svelte-ignore a11y_media_has_caption -->
							<video src={content.contentRef} controls preload="metadata" aria-label={content.title}></video>
						{:else if content.kind === 'audio'}
							<audio src={content.contentRef} controls preload="metadata" aria-label={content.title}></audio>
						{:else if content.kind === 'table'}
							<div class="contentTableMeta">
								<div><span>ROWS</span><b>{content.tableMeta.totalRows?.toLocaleString() ?? `${content.rows.length} preview`}</b></div>
								<div><span>GROUPS</span><b>{content.tableMeta.rowGroupCount?.toLocaleString() ?? 'N/A'}</b></div>
								<div><span>FILE</span><b>{content.tableMeta.fileSizeBytes !== null ? formatBytes(content.tableMeta.fileSizeBytes) : 'RANGE'}</b></div>
								<div><span>TRANSFER</span><b>{content.tableMeta.transferredBytes !== null ? formatBytes(content.tableMeta.transferredBytes) : 'N/A'}</b></div>
							</div>
							{#if content.tableMeta.format === 'parquet' && content.tableMeta.totalRows !== null}
								<div class="tableNavigator">
									<button type="button" disabled={contentLoading || content.tableMeta.rowStart === 0} onclick={() => moveTableWindow(-1)}>이전 12행</button>
									<span>ROWS <b>{(content.tableMeta.rowStart + 1).toLocaleString()}-{content.tableMeta.rowEnd.toLocaleString()}</b> OF {content.tableMeta.totalRows.toLocaleString()}</span>
									<button type="button" disabled={contentLoading || content.tableMeta.rowEnd >= content.tableMeta.totalRows} onclick={() => moveTableWindow(1)}>다음 12행</button>
								</div>
							{/if}
							<div class="contentTableWrap">
								<table>
									<thead><tr>{#each content.columns as column (column)}<th>{column}</th>{/each}</tr></thead>
									<tbody>{#each content.rows as row, index (index)}<tr>{#each content.columns as column (column)}<td>{row[column]}</td>{/each}</tr>{/each}</tbody>
								</table>
							</div>
							{#if content.schema.length > 0}
								<details class="schemaDetails">
									<summary>SCHEMA <b>{content.schema.length} COLUMNS</b></summary>
									<div>{#each content.schema as column (column.name)}<p><b>{column.name}</b><span>{column.logicalType || column.physicalType}</span><small>{column.physicalType}</small></p>{/each}</div>
								</details>
							{/if}
						{:else if content.kind === 'json' && content.tree.length > 0}
							<div class="contentTree" aria-label="JSON 구조">
								{#each content.tree as node (node.nodeId)}
									<div class="treeRow" style:--tree-depth={node.depth}>
										<i>{node.valueKind === 'object' ? '{}' : node.valueKind === 'array' ? '[]' : '·'}</i>
										<b>{node.key}</b>
										{#if node.childCount > 0}<span class="treeCount">{node.childCount}</span>{:else}<span class={`treeValue ${node.valueKind}`}>{node.value}</span>{/if}
									</div>
								{/each}
							</div>
							<details class="rawDetails"><summary>RAW JSON</summary><pre>{content.text}</pre></details>
						{:else if content.kind === 'text' || content.kind === 'json'}
							<pre>{content.text}</pre>
						{:else}
							<div class="binaryPreview"><b>미리보기 미지원 형식</b><span>{content.mimeType}</span><a href={content.contentRef} target="_blank" rel="noreferrer">원본 열기</a></div>
						{/if}
						<footer>
							<span>{content.mimeType}</span>
							<code>{content.revision.slice(0, 9)}</code>
							{#if content.receipt.truncated}<b>BOUNDED PREVIEW</b>{/if}
						</footer>
					</section>
					<section class="fileProvenance" aria-label={`${content.title} 파일 계보`}>
						<header><span>FILE PROVENANCE</span><b>{content.fileMeta.securityStatus ?? 'UNKNOWN'}</b></header>
						<div class="provenanceFacts">
							<div><span>FILE SIZE</span><strong>{content.fileMeta.sizeBytes !== null ? formatBytes(content.fileMeta.sizeBytes) : '기록 없음'}</strong></div>
							<div><span>LAST COMMIT</span><strong>{formatDate(content.fileMeta.lastCommitAt)}</strong></div>
							<div><span>AV SCAN</span><strong>{content.fileMeta.antivirusStatus ?? '기록 없음'}</strong></div>
						</div>
						{#if content.fileMeta.lastCommitTitle}<p>{content.fileMeta.lastCommitTitle}</p>{/if}
						<div class="provenanceHashes">
							{#if content.fileMeta.lastCommitId}<div><span>COMMIT</span><code title={content.fileMeta.lastCommitId}>{content.fileMeta.lastCommitId}</code></div>{/if}
							{#if content.fileMeta.blobId}<div><span>BLOB</span><code title={content.fileMeta.blobId}>{content.fileMeta.blobId}</code></div>{/if}
							{#if content.fileMeta.lfsOid}<div><span>LFS</span><code title={content.fileMeta.lfsOid}>{content.fileMeta.lfsOid}</code></div>{/if}
							{#if content.fileMeta.xetHash}<div><span>XET</span><code title={content.fileMeta.xetHash}>{content.fileMeta.xetHash}</code></div>{/if}
						</div>
					</section>
				{/if}
				{#if selectedAttributes.length > 0}
					<dl>{#each selectedAttributes as [key, value] (key)}<div><dt>{key}</dt><dd>{typeof value === 'number' ? value.toLocaleString() : String(value)}</dd></div>{/each}</dl>
				{/if}
				{#if connectedEdges.length > 0}
					<div class="relationList"><span>CONNECTED KNOWLEDGE</span>{#each connectedEdges.slice(0, 6) as edge (edge.edgeId)}{@const otherId = edge.sourceId === selectedNode.nodeId ? edge.targetId : edge.sourceId}{@const other = scene?.nodes.find((node) => node.nodeId === otherId)}{#if other}<button type="button" onclick={() => selectNode(other.nodeId)}><b>{edge.relation}</b><em class:derived={edge.lane === 'derived'}>{edge.lane}</em><span>{other.label}</span></button>{/if}{/each}</div>
				{/if}
				<div class="sourceAddress"><span>SOURCE REF</span>{#if selectedNode.sourceRef.startsWith('https://')}<a href={selectedNode.sourceRef} target="_blank" rel="noreferrer">{selectedNode.sourceRef}</a>{:else}<code>{selectedNode.sourceRef}</code>{/if}</div>
				{#if selectedNode.evidenceRefs.length > 0}<div class="evidenceRefs"><span>EVIDENCE REFS</span>{#each selectedNode.evidenceRefs.slice(0, 3) as evidenceRef (evidenceRef)}<code title={evidenceRef}>{evidenceRef}</code>{/each}</div>{/if}
				<button class="openArticle" type="button" onclick={() => (articleOpen = true)}><span>WIKI LENS</span><b>지식 문서 열기</b></button>
				{#if selectedNode.expandable}<button class="openDeeper" type="button" onclick={() => void openTarget(selectedNode.nodeId)}>이 지식으로 확대</button>{/if}
			{:else}
				<div class="emptyLens"><span>KNOWLEDGE LENS</span><h2>관계를 선택하세요.</h2><p>선택한 데이터, 문서, 엔진과 스킬의 주소와 연결 근거가 여기에 열립니다.</p></div>
			{/if}
		</aside>
	</div>

	<footer class="knowledgeFilm">
		<div class="filmControls">
			<button type="button" aria-label="이전 장면" disabled={!scene?.film.length} onclick={() => activateBeat(filmIndex - 1)}>‹</button>
			<button class="play" type="button" disabled={!scene?.film.length} onclick={toggleFilm}>{filmPlaying ? 'Ⅱ' : '▶'}</button>
			<button type="button" aria-label="다음 장면" disabled={!scene?.film.length} onclick={() => activateBeat(filmIndex + 1)}>›</button>
			<button class="speed" type="button" onclick={cycleSpeed}>{filmSpeed}×</button>
		</div>
		<div class="filmNarration"><span>KNOWLEDGE FILM</span><strong>{currentBeat?.label ?? '장면 대기'}</strong><p>{currentBeat?.narration ?? '지식 장면이 준비되면 관계의 전개를 재생할 수 있습니다.'}</p></div>
		<div class="filmTimeline" aria-label="지식 필름 장면">
			{#each scene?.film ?? [] as beat, index (beat.beatId)}<button type="button" class:active={filmActive && filmIndex === index} aria-label={`${index + 1}장 ${beat.label}`} onclick={() => activateBeat(index)}><i></i><span>{String(index + 1).padStart(2, '0')}</span></button>{/each}
		</div>
		<div class="filmReceipt"><span>SCENE</span><b>{scene?.receipt.outputNodeCount ?? 0} NODES</b><small>{(scene?.receipt.indexedItemCount ?? 0).toLocaleString()} INDEXED · {scene?.receipt.sourceRevision.slice(0, 9) ?? 'loading'}</small></div>
	</footer>
	{#if articleOpen && selectedNode && scene}
		<KnowledgeArticle
			node={selectedNode}
			{scene}
			{content}
			{contentLoading}
			{contentError}
			domainLabel={domainLabel(selectedNode.domainId)}
			onClose={() => (articleOpen = false)}
			onNavigate={navigateArticle}
		/>
	{/if}
</section>

<style>
	.srOnly { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }
	.knowledgeUniverse { position: relative; min-height: 720px; height: calc(100vh - 112px); display: grid; grid-template-rows: 58px minmax(0, 1fr) 82px; overflow: hidden; color: #dce5f2; background: radial-gradient(circle at 46% 42%, rgba(38, 64, 103, .12), transparent 42%), linear-gradient(145deg, #080c13, #06090f 66%); font-family: 'Pretendard Variable', Pretendard, system-ui, sans-serif; }
	.knowledgeUniverse::before { content: ''; position: absolute; inset: 0; pointer-events: none; opacity: .22; background-image: linear-gradient(rgba(116, 139, 170, .025) 1px, transparent 1px), linear-gradient(90deg, rgba(116, 139, 170, .025) 1px, transparent 1px); background-size: 48px 48px; mask-image: radial-gradient(circle at 50% 50%, black, transparent 72%); }
	.commandBar { position: relative; z-index: 7; display: grid; grid-template-columns: minmax(160px, .8fr) minmax(360px, 1.7fr) minmax(150px, .7fr); align-items: center; gap: 18px; padding: 0 18px; border-bottom: 1px solid rgba(102, 125, 156, .13); background: rgba(7, 11, 18, .76); backdrop-filter: blur(18px); }
	.scenePath { min-width: 0; display: flex; align-items: center; gap: 6px; overflow: hidden; }
	.scenePath button, .scenePath span { flex-shrink: 0; max-width: 110px; overflow: hidden; border: 0; padding: 0; color: #71839a; background: none; font: 600 9px/1 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
	.scenePath button:last-child { color: #c4d0df; }
	.scenePath i { color: #334257; font-style: normal; }
	.omnibox { height: 38px; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; border: 1px solid rgba(108, 137, 177, .27); border-radius: 11px; background: rgba(11, 17, 27, .88); box-shadow: 0 10px 40px rgba(0, 0, 0, .22); }
	.omnibox > span { padding-left: 12px; color: #6783a8; font-size: 18px; }
	.omnibox input { min-width: 0; height: 100%; border: 0; padding: 0 10px; outline: none; color: #e5ecf5; background: transparent; font-size: 11px; }
	.omnibox input::placeholder { color: #54667e; }
	.omnibox button { align-self: stretch; border: 0; border-left: 1px solid rgba(104, 130, 165, .18); padding: 0 14px; color: #9eb5d1; background: rgba(45, 72, 107, .25); font-size: 10px; cursor: pointer; }
	.omnibox button:disabled { color: #485a71; cursor: default; }
	.catalogState { display: flex; align-items: center; justify-content: flex-end; gap: 9px; }
	.catalogState > span { width: 7px; height: 7px; border-radius: 50%; background: #d3a35e; box-shadow: 0 0 0 4px rgba(211, 163, 94, .08); }
	.catalogState > span.live { background: #59cc98; box-shadow: 0 0 0 4px rgba(89, 204, 152, .09); }
	.catalogState div { display: grid; text-align: right; }
	.catalogState b { color: #b8c6d8; font: 600 9px/1.2 ui-monospace, monospace; }
	.catalogState small { margin-top: 3px; color: #4f6076; font: 500 8px/1 ui-monospace, monospace; }
	.universeBody { position: relative; z-index: 2; min-height: 0; display: grid; grid-template-columns: 166px minmax(0, 1fr) clamp(320px, 24vw, 380px); }
	.galaxyRail { min-height: 0; overflow-y: auto; padding: 15px 10px; border-right: 1px solid rgba(101, 124, 154, .12); background: rgba(7, 11, 17, .54); scrollbar-width: thin; }
	.railTitle { display: flex; align-items: center; justify-content: space-between; margin: 0 7px 11px; }
	.railTitle span, .knowledgeLens header > span, .relationList > span, .sourceAddress > span, .filmNarration > span, .filmReceipt > span, .sceneTitle > div > span, .emptyLens > span { color: #4e6077; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .13em; }
	.railTitle b { color: #60728a; font: 600 8px/1 ui-monospace, monospace; }
	.galaxyRail > button { --domain-color: #8191a7; position: relative; width: 100%; display: grid; grid-template-columns: 20px minmax(0, 1fr); align-items: center; gap: 7px; border: 0; border-radius: 8px; padding: 8px 7px; color: #788aa1; background: transparent; text-align: left; cursor: pointer; }
	.galaxyRail > button::before { content: ''; position: absolute; left: 0; width: 2px; height: 18px; border-radius: 2px; background: var(--domain-color); opacity: 0; }
	.galaxyRail > button:hover, .galaxyRail > button.active { color: #d5dfeb; background: rgba(126, 151, 185, .07); }
	.galaxyRail > button.active::before { opacity: .9; }
	.galaxyRail > button > i { color: #42536a; font: 600 7px/1 ui-monospace, monospace; font-style: normal; }
	.galaxyRail > button.active > i { color: var(--domain-color); }
	.galaxyRail button span { min-width: 0; display: flex; justify-content: space-between; gap: 5px; align-items: center; }
	.galaxyRail strong { overflow: hidden; font-size: 9px; font-weight: 550; text-overflow: ellipsis; white-space: nowrap; }
	.galaxyRail small { color: #44566c; font: 500 7px/1 ui-monospace, monospace; }
	.sceneStage { position: relative; min-width: 0; min-height: 0; overflow: hidden; }
	.sceneTitle { position: absolute; z-index: 5; top: 0; left: 0; right: 0; display: flex; justify-content: space-between; gap: 18px; padding: 18px 20px 10px; pointer-events: none; background: linear-gradient(#080c13 6%, rgba(8, 12, 19, .88) 52%, transparent); }
	.sceneTitle h1 { margin: 6px 0 4px; color: #edf2f8; font-size: clamp(19px, 2vw, 29px); line-height: 1.1; letter-spacing: -.035em; font-weight: 560; }
	.sceneTitle p { max-width: 680px; margin: 0; color: #64768d; font-size: 9px; line-height: 1.5; }
	.viewMode { flex-shrink: 0; display: flex; align-self: start; padding: 3px; border: 1px solid rgba(99, 122, 153, .18); border-radius: 8px; background: rgba(7, 11, 18, .68); pointer-events: auto; }
	.viewMode button { border: 0; border-radius: 5px; padding: 6px 9px; color: #5f7188; background: transparent; font-size: 8px; white-space: nowrap; cursor: pointer; }
	.viewMode button.active { color: #d6e0ec; background: rgba(110, 137, 174, .15); }
	.loadingScene, .errorNotice { height: 100%; display: grid; place-content: center; justify-items: center; gap: 12px; color: #6d7e95; font-size: 10px; }
	.loadingScene i, .sceneLoading i { width: 17px; height: 17px; border: 2px solid #25364d; border-top-color: #7ba6dc; border-radius: 50%; animation: spin .9s linear infinite; }
	.errorNotice span { color: #dc8c91; font: 650 8px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.errorNotice p { margin: 0; color: #9c747d; }
	.errorNotice button { border: 1px solid #51343b; border-radius: 7px; padding: 7px 9px; color: #e2a0a7; background: #171014; cursor: pointer; }
	.sceneLoading { position: absolute; z-index: 8; inset: 0; display: flex; align-items: center; justify-content: center; gap: 9px; color: #8193aa; background: rgba(5, 8, 13, .58); font-size: 9px; backdrop-filter: blur(4px); }
	.knowledgeTable { height: 100%; overflow: auto; padding-top: 94px; background: rgba(6, 10, 16, .48); }
	.tableRow { width: 100%; display: grid; grid-template-columns: minmax(220px, 1.5fr) .55fr .65fr minmax(200px, 1fr); border: 0; border-bottom: 1px solid rgba(92, 115, 145, .1); color: #8495aa; background: transparent; text-align: left; }
	button.tableRow { cursor: pointer; }
	button.tableRow:hover, button.tableRow.selected { background: rgba(102, 133, 174, .07); }
	.tableRow > span, .tableRow > code { min-width: 0; padding: 10px 12px; overflow: hidden; color: inherit; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
	.tableRow b { display: block; color: #cbd6e3; font-size: 10px; font-weight: 550; }
	.tableRow small { display: block; margin-top: 4px; color: #56687f; }
	.tableRow code { color: #52647b; font-size: 8px; }
	.tableHead { position: sticky; z-index: 2; top: 0; background: #0b111a; }
	.tableHead span { color: #5b6e86; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .08em; }
	.knowledgeLens { min-height: 0; overflow-y: auto; padding: 17px 15px; border-left: 1px solid rgba(101, 124, 154, .12); background: rgba(8, 12, 19, .75); scrollbar-width: thin; }
	.knowledgeLens header { display: flex; justify-content: space-between; align-items: center; }
	.knowledgeLens header b { --domain-color: #9aa8be; padding: 4px 6px; border: 1px solid color-mix(in srgb, var(--domain-color) 30%, transparent); border-radius: 999px; color: var(--domain-color); font: 600 7px/1 ui-monospace, monospace; }
	.nodeIdentity { display: grid; grid-template-columns: 19px minmax(0, 1fr); gap: 10px; align-items: start; margin: 29px 0 17px; }
	.nodeIdentity > i { --domain-color: #9aa8be; width: 13px; height: 13px; margin-top: 4px; border: 2px solid var(--domain-color); border-radius: 50%; box-shadow: 0 0 0 5px color-mix(in srgb, var(--domain-color) 9%, transparent); }
	.nodeIdentity h2 { margin: 0; color: #edf2f8; font-size: 20px; line-height: 1.12; letter-spacing: -.03em; font-weight: 560; overflow-wrap: anywhere; }
	.nodeIdentity p { margin: 7px 0 0; color: #607289; font: 500 8px/1.45 ui-monospace, monospace; overflow-wrap: anywhere; }
	.lensStats { display: grid; grid-template-columns: 1.25fr .8fr .72fr .65fr; gap: 4px; }
	.lensStats div { min-width: 0; padding: 8px; border-top: 1px solid #172231; border-bottom: 1px solid #172231; }
	.lensStats span { display: block; color: #4d6077; font: 600 6px/1 ui-monospace, monospace; }
	.lensStats strong { display: block; margin-top: 6px; overflow: hidden; color: #9cadc1; font: 600 9px/1 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.contentLoading { display: flex; align-items: center; gap: 9px; margin-top: 14px; border: 1px solid rgba(96, 125, 163, .14); border-radius: 9px; padding: 11px; color: #71849c; background: rgba(14, 22, 33, .58); font-size: 8px; }
	.contentLoading i { width: 13px; height: 13px; flex: 0 0 auto; border: 2px solid #263950; border-top-color: #79a7df; border-radius: 50%; animation: spin .9s linear infinite; }
	.contentError { margin-top: 14px; border: 1px solid rgba(207, 105, 116, .2); border-radius: 9px; padding: 11px; background: rgba(43, 18, 24, .38); }
	.contentError span { color: #c87782; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.contentError p { margin: 7px 0 0; color: #997079; font-size: 8px; line-height: 1.45; overflow-wrap: anywhere; }
	.contentPreview { margin-top: 14px; overflow: hidden; border: 1px solid rgba(107, 139, 181, .18); border-radius: 11px; background: rgba(5, 9, 15, .72); box-shadow: 0 16px 38px rgba(0, 0, 0, .18); }
	.contentPreview > header { min-height: 31px; padding: 0 10px; border-bottom: 1px solid rgba(96, 124, 162, .13); background: rgba(18, 27, 40, .72); }
	.contentPreview > header span { color: #58708d; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.contentPreview > header b { border: 0; padding: 0; color: #91a9c4; background: transparent; font-size: 7px; }
	.contentPreview img, .contentPreview video { width: 100%; max-height: 300px; display: block; object-fit: contain; background: #03060a; }
	.contentPreview audio { width: calc(100% - 20px); height: 34px; display: block; margin: 12px 10px; }
	.contentPreview pre { max-height: 340px; margin: 0; overflow: auto; padding: 13px; color: #aab9ca; background: #070c13; font: 500 8px/1.65 ui-monospace, SFMono-Regular, Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; tab-size: 2; user-select: text; scrollbar-width: thin; }
	.contentTableMeta { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-bottom: 1px solid #172332; background: #0c131d; }
	.contentTableMeta div { min-width: 0; padding: 8px; border-right: 1px solid #172332; }
	.contentTableMeta div:last-child { border-right: 0; }
	.contentTableMeta span { display: block; color: #50647c; font: 600 6px/1 ui-monospace, monospace; }
	.contentTableMeta b { display: block; margin-top: 5px; overflow: hidden; color: #9aadc2; font: 600 8px/1 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.tableNavigator { min-height: 34px; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 8px; padding: 0 8px; border-bottom: 1px solid #172332; background: #090f18; }
	.tableNavigator button { border: 1px solid #23364d; border-radius: 6px; padding: 5px 7px; color: #8da7c4; background: #111e2d; font-size: 7px; cursor: pointer; }
	.tableNavigator button:disabled { opacity: .32; cursor: default; }
	.tableNavigator span { overflow: hidden; color: #52667e; font: 550 6px/1 ui-monospace, monospace; text-align: center; text-overflow: ellipsis; white-space: nowrap; }
	.tableNavigator b { color: #8da3bc; font-size: 7px; }
	.contentTableWrap { max-height: 320px; overflow: auto; scrollbar-width: thin; }
	.contentTableWrap table { width: max-content; min-width: 100%; border-collapse: collapse; color: #91a3b7; background: #070c13; font: 500 8px/1.35 ui-monospace, SFMono-Regular, Consolas, monospace; }
	.contentTableWrap th { position: sticky; z-index: 1; top: 0; padding: 8px 10px; border-right: 1px solid #182332; border-bottom: 1px solid #243348; color: #b9c9db; background: #101824; text-align: left; white-space: nowrap; }
	.contentTableWrap td { max-width: 220px; padding: 7px 10px; overflow: hidden; border-right: 1px solid #121c29; border-bottom: 1px solid #121c29; text-overflow: ellipsis; white-space: nowrap; }
	.contentTableWrap tr:hover td { color: #c8d5e3; background: rgba(92, 130, 177, .08); }
	.schemaDetails { border-top: 1px solid #172332; background: #080e16; }
	.schemaDetails summary { display: flex; justify-content: space-between; padding: 9px 11px; color: #60758f; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .08em; cursor: pointer; }
	.schemaDetails summary b { color: #7e92aa; font-size: 7px; }
	.schemaDetails > div { max-height: 230px; overflow: auto; scrollbar-width: thin; }
	.schemaDetails p { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 8px; margin: 0; padding: 7px 11px; border-top: 1px solid rgba(79, 102, 132, .08); }
	.schemaDetails p b { min-width: 0; overflow: hidden; color: #9bacc0; font: 550 8px/1.2 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.schemaDetails p span { color: #7796bb; font: 550 7px/1.2 ui-monospace, monospace; }
	.schemaDetails p small { grid-column: 1 / -1; color: #4d6077; font: 500 6px/1 ui-monospace, monospace; }
	.contentTree { max-height: 340px; overflow: auto; padding: 7px 0; background: #070c13; scrollbar-width: thin; }
	.treeRow { --tree-depth: 0; min-height: 27px; display: grid; grid-template-columns: 15px minmax(48px, auto) minmax(0, 1fr); align-items: center; gap: 6px; padding: 3px 10px 3px calc(10px + var(--tree-depth) * 13px); border-bottom: 1px solid rgba(80, 104, 135, .07); }
	.treeRow:hover { background: rgba(94, 129, 173, .07); }
	.treeRow i { color: #58718f; font: 600 7px/1 ui-monospace, monospace; font-style: normal; }
	.treeRow b { overflow: hidden; color: #91a6be; font: 550 8px/1.25 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.treeRow span { min-width: 0; overflow: hidden; font: 500 8px/1.25 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.treeCount { justify-self: start; border-radius: 999px; padding: 2px 5px; color: #617894; background: #101b29; }
	.treeValue { color: #8294aa; }
	.treeValue.string { color: #95b98f; }
	.treeValue.number { color: #d2a974; }
	.treeValue.boolean { color: #8aaee0; }
	.treeValue.null { color: #65758a; font-style: italic; }
	.rawDetails { border-top: 1px solid #172332; background: #080d15; }
	.rawDetails summary { padding: 9px 11px; color: #60758f; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .08em; cursor: pointer; }
	.rawDetails pre { border-top: 1px solid #172332; }
	.binaryPreview { display: grid; justify-items: start; gap: 7px; padding: 14px; }
	.binaryPreview b { color: #a8b7c9; font-size: 9px; }
	.binaryPreview span { color: #596d85; font: 500 8px/1 ui-monospace, monospace; }
	.binaryPreview a { margin-top: 3px; border: 1px solid #2a435f; border-radius: 7px; padding: 7px 9px; color: #a8c7e8; background: #122238; font-size: 8px; text-decoration: none; }
	.contentPreview > footer { min-height: 31px; display: flex; align-items: center; gap: 7px; padding: 0 10px; border-top: 1px solid rgba(96, 124, 162, .13); color: #51647b; background: rgba(13, 20, 30, .82); font: 500 7px/1 ui-monospace, monospace; }
	.contentPreview > footer span { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.contentPreview > footer code { margin-left: auto; color: #6d84a0; }
	.contentPreview > footer b { flex: 0 0 auto; color: #bc925b; font-size: 6px; letter-spacing: .06em; }
	.fileProvenance { margin-top: 8px; overflow: hidden; border: 1px solid rgba(93, 119, 152, .14); border-radius: 9px; background: rgba(8, 13, 21, .66); }
	.fileProvenance > header { min-height: 29px; display: flex; align-items: center; justify-content: space-between; padding: 0 10px; border-bottom: 1px solid rgba(84, 108, 139, .11); }
	.fileProvenance > header span { color: #58708d; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.fileProvenance > header b { border-radius: 999px; padding: 3px 5px; color: #b29362; background: rgba(178, 147, 98, .1); font: 650 6px/1 ui-monospace, monospace; letter-spacing: .06em; }
	.provenanceFacts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
	.provenanceFacts div { min-width: 0; padding: 9px; border-right: 1px solid rgba(84, 108, 139, .1); }
	.provenanceFacts div:last-child { border-right: 0; }
	.provenanceFacts span, .provenanceHashes span { display: block; color: #4f6279; font: 600 6px/1 ui-monospace, monospace; }
	.provenanceFacts strong { display: block; margin-top: 5px; overflow: hidden; color: #91a3b8; font: 550 7px/1.2 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.fileProvenance > p { margin: 0; padding: 9px 10px; border-top: 1px solid rgba(84, 108, 139, .08); color: #8395aa; font-size: 8px; line-height: 1.45; overflow-wrap: anywhere; }
	.provenanceHashes { border-top: 1px solid rgba(84, 108, 139, .08); padding: 5px 10px; }
	.provenanceHashes div { min-width: 0; display: grid; grid-template-columns: 48px minmax(0, 1fr); align-items: center; gap: 7px; padding: 4px 0; }
	.provenanceHashes code { min-width: 0; overflow: hidden; color: #677f9b; font: 500 7px/1 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; user-select: text; }
	dl { margin: 16px 0 0; }
	dl div { display: grid; grid-template-columns: 74px minmax(0, 1fr); gap: 8px; padding: 7px 0; border-bottom: 1px solid rgba(85, 106, 134, .1); }
	dt { color: #53667e; font: 600 7px/1.3 ui-monospace, monospace; overflow-wrap: anywhere; }
	dd { margin: 0; overflow: hidden; color: #8b9db3; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
	.relationList { margin-top: 18px; }
	.relationList > span { display: block; margin-bottom: 7px; }
	.relationList button { width: 100%; display: grid; grid-template-columns: 56px 42px minmax(0, 1fr); align-items: center; gap: 7px; border: 0; border-bottom: 1px solid rgba(85, 106, 134, .1); padding: 7px 0; color: #8799af; background: transparent; text-align: left; cursor: pointer; }
	.relationList b { color: #51647c; font: 600 7px/1 ui-monospace, monospace; }
	.relationList em { border: 1px solid rgba(93, 174, 139, .25); border-radius: 999px; padding: 3px 4px; color: #72b99a; font: 600 6px/1 ui-monospace, monospace; font-style: normal; text-align: center; text-transform: uppercase; }
	.relationList em.derived { border-color: rgba(217, 165, 91, .28); color: #c4975b; }
	.relationList span { overflow: hidden; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
	.evidenceRefs { display: grid; gap: 5px; margin-top: 12px; }
	.evidenceRefs > span { color: #4e6077; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .13em; }
	.evidenceRefs code { min-width: 0; overflow: hidden; color: #637994; font: 500 7px/1.35 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; user-select: text; }
	.openArticle { width: 100%; display: flex; align-items: center; justify-content: space-between; margin-top: 16px; border: 1px solid rgba(104, 145, 195, .28); border-radius: 9px; padding: 10px 11px; color: #b8cae0; background: linear-gradient(135deg, rgba(46, 77, 116, .34), rgba(20, 32, 49, .4)); text-align: left; cursor: pointer; }
	.openArticle span { color: #6e91bb; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.openArticle b { font-size: 9px; font-weight: 600; }
	.openArticle:hover { border-color: rgba(119, 169, 229, .48); background: linear-gradient(135deg, rgba(56, 91, 134, .42), rgba(23, 37, 56, .5)); }
	.sourceAddress { margin-top: 20px; padding-top: 12px; border-top: 1px solid #172230; }
	.sourceAddress > span { display: block; }
	.sourceAddress a, .sourceAddress code { display: block; margin-top: 8px; color: #6582a7; font: 500 8px/1.45 ui-monospace, monospace; overflow-wrap: anywhere; text-decoration: none; }
	.openDeeper { width: 100%; margin-top: 16px; border: 1px solid #2c4564; border-radius: 8px; padding: 9px; color: #b9d2ef; background: #14243a; font-size: 9px; cursor: pointer; }
	.emptyLens { padding-top: 76px; }
	.emptyLens h2 { margin: 14px 0 8px; color: #d7e0eb; font-size: 18px; font-weight: 550; }
	.emptyLens p { margin: 0; color: #617289; font-size: 9px; line-height: 1.6; }
	.knowledgeFilm { position: relative; z-index: 7; display: grid; grid-template-columns: auto minmax(240px, .8fr) minmax(280px, 1.6fr) auto; align-items: center; gap: 16px; padding: 10px 16px; border-top: 1px solid rgba(107, 132, 164, .14); background: rgba(7, 11, 18, .92); backdrop-filter: blur(18px); }
	.filmControls { display: flex; gap: 3px; }
	.filmControls button { width: 29px; height: 29px; border: 1px solid #1d2a3b; border-radius: 7px; color: #74879e; background: #0b121c; cursor: pointer; }
	.filmControls button.play { color: #d5e2f1; border-color: #314965; background: #16263a; }
	.filmControls button.speed { width: 36px; font: 600 8px/1 ui-monospace, monospace; }
	.filmControls button:disabled { opacity: .35; cursor: default; }
	.filmNarration { min-width: 0; }
	.filmNarration strong { display: inline-block; margin: 0 8px; color: #becbda; font-size: 9px; }
	.filmNarration p { display: inline; margin: 0; color: #61738a; font-size: 8px; }
	.filmTimeline { display: flex; align-items: center; }
	.filmTimeline button { position: relative; flex: 1; height: 34px; border: 0; padding: 0; color: #42536a; background: transparent; cursor: pointer; }
	.filmTimeline button::before { content: ''; position: absolute; top: 13px; left: 0; right: 0; height: 1px; background: #1d2a3b; }
	.filmTimeline i { position: relative; z-index: 1; display: block; width: 7px; height: 7px; margin: 10px auto 0; border: 1px solid #41536a; border-radius: 50%; background: #0a1019; }
	.filmTimeline button.active i { border-color: #88baf5; background: #6da8ed; box-shadow: 0 0 0 4px rgba(109, 168, 237, .1); }
	.filmTimeline span { display: block; margin-top: 6px; font: 600 6px/1 ui-monospace, monospace; }
	.filmReceipt { display: grid; grid-template-columns: auto auto; gap: 3px 8px; text-align: right; }
	.filmReceipt b { color: #8799ae; font: 600 8px/1 ui-monospace, monospace; }
	.filmReceipt small { grid-column: 1 / -1; color: #43546a; font: 500 7px/1 ui-monospace, monospace; }
	@keyframes spin { to { transform: rotate(360deg); } }
	@media (max-width: 1080px) { .universeBody { grid-template-columns: 142px minmax(0, 1fr) 300px; } .galaxyRail { padding-inline: 7px; } .knowledgeFilm { grid-template-columns: auto minmax(220px, 1fr) minmax(220px, 1fr); } .filmReceipt { display: none; } }
	@media (max-width: 820px) { .knowledgeUniverse { height: auto; min-height: calc(100vh - 96px); grid-template-rows: auto auto auto; overflow: visible; padding-bottom: 86px; } .commandBar { grid-template-columns: 1fr auto; padding: 9px 12px; } .scenePath { display: none; } .omnibox { min-width: 0; } .catalogState { grid-column: 2; grid-row: 1; } .universeBody { display: grid; grid-template-columns: 1fr; } .galaxyRail { display: flex; gap: 3px; overflow-x: auto; border-right: 0; border-bottom: 1px solid rgba(101, 124, 154, .12); padding: 7px; } .railTitle { display: none; } .galaxyRail > button { flex: 0 0 104px; } .galaxyRail button span { display: block; } .galaxyRail small { display: block; margin-top: 3px; } .sceneStage { min-height: 520px; } .knowledgeLens { max-height: 440px; border-left: 0; border-top: 1px solid rgba(101, 124, 154, .12); } .knowledgeFilm { position: fixed; z-index: 20; left: 0; right: 0; bottom: 0; grid-template-columns: auto minmax(0, 1fr); box-shadow: 0 -18px 42px rgba(0, 0, 0, .32); } .filmTimeline { grid-column: 1 / -1; } }
	@media (max-width: 560px) { .commandBar { grid-template-columns: 1fr; } .catalogState { display: none; } .omnibox { grid-column: 1; } .sceneTitle { gap: 8px; padding: 15px 12px 8px; } .sceneTitle > div:first-child { min-width: 0; } .sceneTitle p { max-width: 270px; } .sceneStage { min-height: 470px; } .knowledgeLens { padding: 15px 12px; } .knowledgeFilm { gap: 8px; padding: 8px 10px; } .filmNarration p { display: none; } .tableRow { grid-template-columns: minmax(160px, 1fr) .7fr; } .tableRow > span:nth-child(3), .tableRow > code { display: none; } }
	@media (prefers-reduced-motion: reduce) { .loadingScene i, .sceneLoading i, .contentLoading i { animation: none; } }
</style>
