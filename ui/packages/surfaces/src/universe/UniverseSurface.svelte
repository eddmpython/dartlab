<script lang="ts">
	import { onMount } from 'svelte';
	import type {
		UniverseCatalogCoverage,
		UniverseChangeMark,
		UniverseChangeSet,
		UniverseEntityProfile,
		UniverseEntitySearchRequest,
		UniverseEntitySearchResult,
		UniverseEvidenceQuery,
		UniverseEvidenceResolution,
		UniverseKnowledgeContent,
		UniverseKnowledgeCoverage,
		UniverseKnowledgeOverview,
		UniverseKnowledgeScene,
		UniverseKnowledgeSearchRequest,
		UniverseKnowledgeSearchResult,
		UniverseLensRef,
		UniverseLensTray,
		UniversePairComparison,
		UniverseRouteSeed,
		UniverseUrlState,
		UniverseWorkflowCompilation,
		UniverseWorkflowId
	} from '@dartlab/ui-contracts';
	import { compileLensTray, compileUniverseWorkflow, UNIVERSE_WORKFLOWS } from '@dartlab/ui-runtime/data/universe';
	import ChangeUniverse from './components/ChangeUniverse.svelte';
	import EvidenceDrawer from './components/EvidenceDrawer.svelte';
	import GlobalUniverse from './components/GlobalUniverse.svelte';
	import KillChain from './components/KillChain.svelte';
	import KnowledgeUniverse from './components/KnowledgeUniverse.svelte';
	import LensTray from './components/LensTray.svelte';
	import UniverseCanvas from './components/UniverseCanvas.svelte';
	import RelationTable from './components/RelationTable.svelte';
	import TimeLens from './components/TimeLens.svelte';
	import { DEFAULT_UNIVERSE_URL_STATE, parseUniverseUrl, universeUrl } from './url';

	interface Props {
		seed: UniverseRouteSeed;
		mapHref?: string;
		loadKnowledgeOverview: () => Promise<UniverseKnowledgeOverview>;
		loadKnowledgeCoverage: () => Promise<UniverseKnowledgeCoverage>;
		loadKnowledgeContent: (targetId: string, rowStart?: number, columnStart?: number) => Promise<UniverseKnowledgeContent>;
		searchKnowledge: (request: UniverseKnowledgeSearchRequest) => Promise<UniverseKnowledgeSearchResult>;
		openKnowledge: (targetId: string) => Promise<UniverseKnowledgeScene>;
		loadChanges?: (maxMarks?: number) => Promise<UniverseChangeSet>;
		resolveEvidence?: (query: UniverseEvidenceQuery) => Promise<UniverseEvidenceResolution>;
		loadGlobalCoverage: () => Promise<UniverseCatalogCoverage>;
		searchEntities: (request: UniverseEntitySearchRequest) => Promise<UniverseEntitySearchResult>;
		loadEntityProfile: (entityId: string) => Promise<UniverseEntityProfile>;
		compareEntities: (krEntityId: string, usEntityId: string) => Promise<UniversePairComparison>;
		writeRouteUrl?: (next: URL, push: boolean) => void;
	}

	let { seed, mapHref = '/map', loadKnowledgeOverview, loadKnowledgeCoverage, loadKnowledgeContent, searchKnowledge, openKnowledge, loadChanges, resolveEvidence, loadGlobalCoverage, searchEntities, loadEntityProfile, compareEntities, writeRouteUrl }: Props = $props();
	type PrimaryMode = 'knowledge' | 'global' | 'atlas' | 'change' | 'workflow';
	type ViewMode = 'universe' | 'table';
	let primaryMode = $state<PrimaryMode>('knowledge');
	let viewMode = $state<ViewMode>('universe');
	let query = $state('');
	let selectedId = $state<string | null>(null);
	let urlState = $state<UniverseUrlState>({ ...DEFAULT_UNIVERSE_URL_STATE });
	let nodeById = $derived(new Map(seed.scene.nodes.map((node) => [node.nodeId, node])));
	let queryMatches = $derived(query.trim()
		? seed.scene.nodes.filter((node) => `${node.label} ${node.nodeId}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())).slice(0, 8)
		: []);
	let highlightedIds = $derived(new Set(queryMatches.map((node) => node.nodeId)));
	let selectedNode = $derived(selectedId ? nodeById.get(selectedId) ?? null : null);
	let connectedEdges = $derived(selectedId ? seed.scene.edges.filter((edge) => edge.sourceId === selectedId || edge.targetId === selectedId) : []);
	let atlasNodeCount = $derived(seed.atlas.industries.reduce((total, industry) => total + industry.nodeCount, 0));
	let changeSet = $state<UniverseChangeSet | null>(null);
	let changeLoading = $state(false);
	let changeError = $state<string | null>(null);
	let selectedChange = $state<UniverseChangeMark | null>(null);
	let evidenceResolution = $state<UniverseEvidenceResolution | null>(null);
	let evidenceLoading = $state(false);
	let evidenceError = $state<string | null>(null);
	let selectedWorkflowId = $state<UniverseWorkflowId>('growthSustainability');
	let workflowCompilation = $state<UniverseWorkflowCompilation | null>(null);
	let workflowLoading = $state(false);
	let workflowError = $state<string | null>(null);
	let lensTray = $state<UniverseLensTray | null>(null);
	let lensRevision = 0;

	function formatRevenue(value: number): string {
		return `${(value / 10_000).toLocaleString('ko-KR', { maximumFractionDigits: 1 })}조`;
	}

	function stageLabel(stage: string | undefined): string {
		return stage === 'upstream' ? '상류' : stage === 'midstream' ? '중류' : stage === 'downstream' ? '하류' : '미분류';
	}

	function commitUrl(push: boolean): void {
		if (typeof window === 'undefined') return;
		urlState = { ...urlState, selectedId, seedIds: selectedId ? [selectedId] : [] };
		const next = universeUrl(urlState, new URL(window.location.href));
		if (next.href === window.location.href) return;
		writeRouteUrl?.(next, push);
	}

	function selectNode(nodeId: string, push = true): void {
		if (!nodeById.has(nodeId)) return;
		selectedId = nodeId;
		query = '';
		commitUrl(push);
	}

	function selectPrimaryMode(mode: PrimaryMode): void {
		primaryMode = mode;
		selectedChange = null;
		evidenceResolution = null;
		if (mode === 'change' && !changeSet) void ensureChanges();
		if (mode === 'workflow' && !workflowCompilation) void compileWorkflow();
	}

	async function ensureChanges(): Promise<void> {
		if (!loadChanges || changeLoading || changeSet) return;
		changeLoading = true;
		changeError = null;
		try {
			changeSet = await loadChanges(160);
		} catch (error) {
			changeError = error instanceof Error ? error.message : '변화 원천을 불러오지 못했습니다.';
		} finally {
			changeLoading = false;
		}
	}

	function selectChange(mark: UniverseChangeMark): void {
		selectedChange = mark;
		evidenceResolution = null;
		evidenceError = null;
	}

	async function searchChangeEvidence(): Promise<void> {
		if (!selectedChange || !resolveEvidence || evidenceLoading) return;
		evidenceLoading = true;
		evidenceError = null;
		try {
			evidenceResolution = await resolveEvidence({
				claimId: selectedChange.changeId,
				text: `${selectedChange.entityLabel} ${selectedChange.summary}`,
				subjectId: selectedChange.entityId,
				predicate: 'filed',
				objectId: 'filing:unresolved',
				direction: 'subjectToObject',
				validAt: urlState.validAt ?? selectedChange.eventAt,
				knownAt: urlState.knownAt ?? selectedChange.knownAt,
				pointer: null
			});
		} catch {
			evidenceResolution = null;
			evidenceError = '공시 검색 원천에 연결하지 못했습니다.';
		} finally {
			evidenceLoading = false;
		}
	}

	function setWorkflow(workflowId: UniverseWorkflowId): void {
		selectedWorkflowId = workflowId;
		workflowCompilation = null;
		workflowError = null;
		void compileWorkflow();
	}

	async function compileWorkflow(): Promise<void> {
		if (workflowLoading) return;
		workflowLoading = true;
		workflowError = null;
		try {
			workflowCompilation = await compileUniverseWorkflow({
				workflowId: selectedWorkflowId,
				snapshotSetId: seed.snapshot.snapshotSetId,
				seedIds: selectedId ? [selectedId] : [seed.scene.nodes[0]?.nodeId ?? 'market'],
				validAt: urlState.validAt,
				knownAt: urlState.knownAt,
				generatedAt: seed.meta.buildTime
			});
		} catch {
			workflowCompilation = null;
			workflowError = '검증 워크플로를 컴파일하지 못했습니다.';
		} finally {
			workflowLoading = false;
		}
	}

	function setTimeLens(validAt: string | null, knownAt: string | null): void {
		urlState = { ...urlState, validAt, knownAt };
		workflowCompilation = null;
		commitUrl(true);
		if (primaryMode === 'workflow') void compileWorkflow();
	}

	function lensRef(nodeId: string, role: 'primary' | 'comparison'): UniverseLensRef | null {
		const node = nodeById.get(nodeId);
		if (!node) return null;
		const value = node.presentation?.metricValue ?? null;
		return {
			refId: `atlas:${role}:${node.nodeId}`,
			kind: 'valueRef',
			engine: 'industry',
			axis: 'atlasRevenue',
			label: `${node.label} 지도 매출`,
			sourceRef: node.sourceRef,
			dataAsOf: seed.meta.dataAsOf.finance ?? null,
			unit: value === null ? null : '억원',
			value,
			columns: [],
			rows: [],
			executedAt: seed.meta.buildTime,
			status: value === null ? 'missing' : 'available',
			limitation: '현행 산업 지도 집계값입니다. 원문 assertion 또는 기업 간 사실 관계가 아닙니다.'
		};
	}

	async function refreshLens(nodeId: string | null): Promise<void> {
		const revision = ++lensRevision;
		if (!nodeId) { lensTray = null; return; }
		const primary = lensRef(nodeId, 'primary');
		const neighborId = connectedEdges[0]
			? (connectedEdges[0].sourceId === nodeId ? connectedEdges[0].targetId : connectedEdges[0].sourceId)
			: null;
		const comparison = neighborId ? lensRef(neighborId, 'comparison') : null;
		if (!primary) { lensTray = null; return; }
		const next = await compileLensTray(primary, comparison);
		if (revision === lensRevision) lensTray = next;
	}

	$effect(() => { void refreshLens(selectedId); });

	function clearSelection(): void {
		selectedId = null;
		commitUrl(true);
	}

	function submitSearch(event: SubmitEvent): void {
		event.preventDefault();
		const first = queryMatches[0];
		if (first) selectNode(first.nodeId);
	}

	onMount(() => {
		const restore = () => {
			const parsed = parseUniverseUrl(new URL(window.location.href));
			urlState = { ...parsed, snapshotSetId: parsed.snapshotSetId ?? seed.snapshot.snapshotSetId, buildId: parsed.buildId ?? seed.meta.buildId };
			selectedId = parsed.selectedId && nodeById.has(parsed.selectedId) ? parsed.selectedId : null;
		};
		restore();
		window.addEventListener('popstate', restore);
		return () => window.removeEventListener('popstate', restore);
	});
</script>

<main id="universe-main" class="universeShell" class:knowledgeMode={primaryMode === 'knowledge'}>
	{#if primaryMode !== 'knowledge'}
	<section class="hero">
		<div>
			<div class="eyebrow"><span class="pulse"></span>DARTLAB UNIVERSE <b>PRODUCTION</b></div>
			<h1>DART와 EDGAR를 연결하되,<br /><em>근거보다 먼저 확신하지 않습니다.</em></h1>
			<p>글로벌 법인 검색, 기업별 재무 관측, 한미 20문항 비교와 한국 산업 관계 장면을 한곳에서 탐색합니다. 대규모 카탈로그는 필요한 순간에만 원본 Parquet에서 읽고, 직접 비교가 불가능한 값은 <strong>BLOCKED</strong>로 남깁니다.</p>
		</div>
		<div class="heroMeta">
			<div><span>STATUS</span><strong>GA</strong></div>
			<div><span>DATA AS OF</span><strong>{seed.meta.dataAsOf.finance?.slice(0, 10) ?? '결손'}</strong></div>
			<div><span>BUILD</span><strong>{seed.meta.buildId}</strong></div>
			<div><span>REPLAY</span><strong class:warn={!seed.snapshot.exactReplayReady}>{seed.snapshot.exactReplayReady ? 'EXACT' : 'CURRENT ONLY'}</strong></div>
		</div>
	</section>

	<section class="metrics" aria-label="데이터 커버리지">
		<div><span>ATLAS INDUSTRIES</span><strong>{seed.atlas.industries.length}</strong><small>한국 산업 분류</small></div>
		<div><span>KR ATLAS NODES</span><strong>{atlasNodeCount.toLocaleString()}</strong><small>전체 법인 수가 아닌 지도 배치 노드</small></div>
		<div><span>AGGREGATE FLOWS</span><strong>{seed.scene.edges.length}</strong><small>파생 집계선</small></div>
		<div><span>GLOBAL CATALOG</span><strong>DART + EDGAR</strong><small>탭 진입 시 원본 지연 로드</small></div>
	</section>
	{/if}

	<section class="workbench" class:knowledgeWorkbench={primaryMode === 'knowledge'}>
		<header class="toolbar" class:knowledgeToolbar={primaryMode === 'knowledge'}>
			<div class="sceneSwitch" aria-label="Universe 장면">
				<button class:active={primaryMode === 'knowledge'} onclick={() => selectPrimaryMode('knowledge')}>지식 우주</button>
				<button class:active={primaryMode === 'global'} onclick={() => selectPrimaryMode('global')}>글로벌</button>
				<button class:active={primaryMode === 'atlas'} onclick={() => selectPrimaryMode('atlas')}>아틀라스</button>
				<button class:active={primaryMode === 'change'} onclick={() => selectPrimaryMode('change')}>변화</button>
				<button class:active={primaryMode === 'workflow'} onclick={() => selectPrimaryMode('workflow')}>Kill-Chain</button>
			</div>
			<form class="search" class:hidden={primaryMode !== 'atlas'} onsubmit={submitSearch}>
				<label for="universe-search">산업 검색</label>
				<div><input id="universe-search" bind:value={query} autocomplete="off" placeholder="반도체, 자동차, 소프트웨어…" /><button type="submit">찾기</button></div>
				{#if queryMatches.length > 0}
					<ul>{#each queryMatches as node (node.nodeId)}<li><button type="button" onclick={() => selectNode(node.nodeId)}>{node.label}<span>{stageLabel(node.presentation?.stage)}</span></button></li>{/each}</ul>
				{/if}
			</form>
			<div class="viewSwitch" class:hidden={primaryMode !== 'atlas'} aria-label="보기 방식">
				<button class:active={viewMode === 'universe'} onclick={() => (viewMode = 'universe')}>우주</button>
				<button class:active={viewMode === 'table'} onclick={() => (viewMode = 'table')}>관계표</button>
			</div>
		</header>

		<div class="workspace" class:globalMode={primaryMode === 'global' || primaryMode === 'knowledge'}>
			<div class="scenePanel">
				{#if primaryMode === 'knowledge'}
					<KnowledgeUniverse loadOverview={loadKnowledgeOverview} loadCoverage={loadKnowledgeCoverage} loadContent={loadKnowledgeContent} {searchKnowledge} {openKnowledge} />
				{:else if primaryMode === 'global'}
					<GlobalUniverse loadCoverage={loadGlobalCoverage} {searchEntities} loadProfile={loadEntityProfile} {compareEntities} />
				{:else if primaryMode === 'atlas'}
					<div class="sceneHeader">
						<div><span>SCENE 01</span><h2>한국 시장 산업 아틀라스</h2></div>
						<div class="legend"><span class="candidate">후보 노드</span><span class="derived">파생 흐름</span></div>
					</div>
					{#if viewMode === 'universe'}
						<UniverseCanvas scene={seed.scene} {selectedId} {highlightedIds} onSelect={selectNode} />
					{:else}
						<RelationTable scene={seed.scene} {selectedId} onSelect={selectNode} />
					{/if}
				{:else if primaryMode === 'change'}
					<ChangeUniverse data={changeSet} loading={changeLoading} error={changeError} onLoad={() => void ensureChanges()} onSelect={selectChange} />
				{:else}
					<KillChain workflows={UNIVERSE_WORKFLOWS} {selectedWorkflowId} compilation={workflowCompilation} loading={workflowLoading} error={workflowError} onSelectWorkflow={setWorkflow} onCompile={() => void compileWorkflow()} />
				{/if}
			</div>

			{#if primaryMode !== 'global' && primaryMode !== 'knowledge'}<aside class="inspector" class:drawerOpen={selectedChange !== null}>
				{#if selectedChange}
					<EvidenceDrawer change={selectedChange} resolution={evidenceResolution} loading={evidenceLoading} error={evidenceError} onResolve={() => void searchChangeEvidence()} onClose={() => { selectedChange = null; evidenceResolution = null; evidenceError = null; }} />
				{:else if selectedNode}
					<div class="inspectorHead"><span>SELECTED ENTITY</span><button aria-label="선택 해제" onclick={clearSelection}>×</button></div>
					<h2>{selectedNode.label}</h2>
					<p class="entityId">{selectedNode.nodeId} · {stageLabel(selectedNode.presentation?.stage)}</p>
					<div class="entityStats">
						<div><span>구성 종목</span><strong>{selectedNode.presentation?.memberCount?.toLocaleString() ?? '결손'}</strong></div>
						<div><span>지도 매출</span><strong>{selectedNode.presentation?.metricValue != null ? formatRevenue(selectedNode.presentation.metricValue) : '결손'}</strong></div>
						<div><span>연결 흐름</span><strong>{connectedEdges.length}</strong></div>
					</div>
					<div class="truthCard candidate">
						<div><span>⌕</span><strong>근거 탐색 중</strong></div>
						<p>이 노드는 현행 지도 분류에서 가져온 후보입니다. 사람 검수와 원문 locator가 결속되기 전에는 사실 lane으로 승격되지 않습니다.</p>
					</div>
					<div class="sourceRef"><span>SOURCE REF</span><code>{selectedNode.sourceRef}</code></div>
					<button class="tableCta" onclick={() => (viewMode = 'table')}>연결 관계표 열기 →</button>
					<LensTray tray={lensTray} />
				{:else}
					<div class="emptyInspector">
						<span>ORIENT</span><h2>산업을 선택하세요.</h2>
						<p>원 하나를 선택하면 집계 규모, 가치사슬 위치, 연결 흐름과 현재 근거 상태를 함께 보여줍니다.</p>
						<div class="workflowList">
							<button onclick={() => selectNode(seed.scene.nodes[0]?.nodeId ?? '')}><b>01</b><span>가장 큰 산업에서 시작</span></button>
							<button onclick={() => (viewMode = 'table')}><b>02</b><span>산업 간 집계 흐름 점검</span></button>
							<a href={mapHref}><b>03</b><span>기존 시장 지도로 이동</span></a>
						</div>
					</div>
				{/if}
			</aside>{/if}
		</div>
		{#if primaryMode === 'workflow' || selectedChange}
			<TimeLens validAt={urlState.validAt} knownAt={urlState.knownAt} onChange={setTimeLens} />
		{/if}
	</section>

	{#if primaryMode !== 'knowledge'}<section class="integrity">
		<div><span>SCENE HASH</span><code>{seed.scene.sceneHash}</code></div>
		<div><span>SNAPSHOT</span><code>{seed.snapshot.snapshotSetId}</code></div>
		<p>현재 route는 meta와 atlas만 초기 로드합니다. ecosystem과 기업 JSON은 선택 전 요청하지 않습니다. 정확 재현 불가 소스 {seed.snapshot.unreplayableSourceIds.length}개를 숨기지 않았으며, 제품 입장 검사는 {seed.product.capabilities.length}개 기능 lane을 독립적으로 보호합니다.</p>
	</section>{/if}
</main>

<style>
	:global(body) { background: #070a11; }
	.universeShell { min-height: 100vh; padding: 92px clamp(18px, 4vw, 64px) 56px; color: #dce5f2; background: radial-gradient(circle at 78% 6%, rgba(52,96,160,.14), transparent 28%), radial-gradient(circle at 12% 32%, rgba(234,70,71,.08), transparent 26%), #070a11; font-family: 'Pretendard Variable', Pretendard, system-ui, sans-serif; }
	.universeShell.knowledgeMode { padding: 49px 0 0; background: #06090f; }
	.hero { max-width: 1420px; margin: 0 auto 38px; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 48px; align-items: end; }
	.eyebrow { display: flex; align-items: center; gap: 9px; margin-bottom: 18px; color: #8798af; font: 600 10px/1 ui-monospace, monospace; letter-spacing: .16em; }
	.eyebrow b { margin-left: 5px; padding: 4px 7px; border: 1px solid rgba(245,184,75,.28); border-radius: 999px; color: #e8b861; font-size: 8px; letter-spacing: .1em; }
	.pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--dl-red); box-shadow: 0 0 0 4px rgba(var(--dl-red-rgb), .13); }
	h1 { max-width: 850px; margin: 0; color: #f4f7fb; font-size: clamp(34px, 5vw, 68px); line-height: 1.06; letter-spacing: -.045em; font-weight: 650; }
	h1 em { color: #8493a8; font-style: normal; font-weight: 450; }
	.hero p { max-width: 760px; margin: 24px 0 0; color: #8493a8; font-size: 14px; line-height: 1.75; }
	.hero p strong { color: #78aff4; }
	.heroMeta { min-width: 225px; border-left: 1px solid #1b2635; }
	.heroMeta div { display: flex; justify-content: space-between; gap: 20px; padding: 11px 0 11px 18px; border-bottom: 1px solid #151f2c; }
	.heroMeta span, .metrics span, .integrity span { color: #586980; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .12em; }
	.heroMeta strong { color: #aab8ca; font: 600 10px/1 ui-monospace, monospace; }
	.heroMeta strong.warn { color: #e0a84c; }
	.metrics { max-width: 1420px; margin: 0 auto 18px; display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid #172231; border-radius: 15px; overflow: hidden; background: rgba(12,17,27,.72); }
	.metrics > div { padding: 18px 20px; border-right: 1px solid #172231; }
	.metrics > div:last-child { border-right: 0; }
	.metrics strong { display: block; margin: 9px 0 3px; color: #eef3f9; font: 500 clamp(22px, 2.4vw, 34px)/1 ui-monospace, monospace; letter-spacing: -.05em; }
	.metrics small { color: #5f7086; font-size: 10px; }
	.workbench { max-width: 1420px; margin: 0 auto; border: 1px solid #192434; border-radius: 21px; overflow: hidden; background: rgba(9,13,21,.88); box-shadow: 0 40px 100px rgba(0,0,0,.28); }
	.workbench.knowledgeWorkbench { max-width: none; margin: 0; border: 0; border-radius: 0; box-shadow: none; }
	.knowledgeWorkbench > .toolbar { align-items: center; min-height: 63px; padding: 10px clamp(12px, 2vw, 28px); border-color: rgba(98, 121, 151, .12); background: #080c13; }
	.knowledgeWorkbench > .toolbar.knowledgeToolbar { grid-template-columns: 1fr; justify-items: center; }
	.knowledgeToolbar .search, .knowledgeToolbar .viewSwitch { display: none; }
	.knowledgeWorkbench > .workspace { min-height: 0; }
	.knowledgeWorkbench .scenePanel { padding: 0; border-right: 0; }
	.toolbar { position: relative; z-index: 5; display: grid; grid-template-columns: auto minmax(260px, 480px) auto; justify-content: space-between; align-items: end; gap: 20px; padding: 15px 18px; border-bottom: 1px solid #182333; background: #0b1019; }
	.sceneSwitch { display: flex; gap: 3px; padding: 3px; border: 1px solid #202c3f; border-radius: 9px; background: #080c13; }
	.sceneSwitch button { border: 0; border-radius: 6px; padding: 8px 10px; background: transparent; color: #66778e; font-size: 10px; cursor: pointer; }
	.sceneSwitch button.active { color: #dce5f2; background: #1a2637; }
	.hidden { visibility: hidden; pointer-events: none; }
	.search { position: relative; width: min(480px, 70%); }
	.search label { display: block; margin-bottom: 7px; color: #607188; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .11em; }
	.search > div { display: flex; }
	.search input { width: 100%; border: 1px solid #223047; border-right: 0; border-radius: 9px 0 0 9px; padding: 10px 12px; outline: none; background: #080c13; color: #e1e8f1; font-size: 12px; }
	.search input:focus { border-color: #526c8f; }
	.search > div button { min-width: 58px; border: 1px solid #29384e; border-radius: 0 9px 9px 0; padding: 0 15px; background: #131c2a; color: #aab7c9; white-space: nowrap; cursor: pointer; }
	.search ul { position: absolute; top: 58px; left: 0; right: 0; margin: 0; padding: 6px; list-style: none; border: 1px solid #26344a; border-radius: 10px; background: #101722; box-shadow: 0 20px 45px rgba(0,0,0,.45); }
	.search li button { width: 100%; display: flex; justify-content: space-between; border: 0; border-radius: 7px; padding: 9px 10px; background: transparent; color: #cad5e3; text-align: left; cursor: pointer; }
	.search li button:hover { background: #172131; }
	.search li span { color: #64758c; font-size: 10px; }
	.viewSwitch { display: flex; padding: 3px; border: 1px solid #202c3f; border-radius: 9px; background: #080c13; }
	.viewSwitch button { border: 0; border-radius: 6px; padding: 7px 12px; background: transparent; color: #66778e; font-size: 11px; cursor: pointer; }
	.viewSwitch button.active { background: #1a2637; color: #dce5f2; }
	.workspace { display: grid; grid-template-columns: minmax(0, 1fr) 310px; min-height: 650px; }
	.workspace.globalMode { grid-template-columns: minmax(0, 1fr); }
	.scenePanel { min-width: 0; padding: 18px; border-right: 1px solid #172231; }
	.sceneHeader { display: flex; justify-content: space-between; align-items: end; margin: 0 2px 13px; }
	.sceneHeader span, .inspectorHead span, .emptyInspector > span, .sourceRef span { color: #53657d; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .12em; }
	.sceneHeader h2 { margin: 6px 0 0; font-size: 15px; font-weight: 600; }
	.legend { display: flex; gap: 14px; }
	.legend span { display: inline-flex; align-items: center; gap: 6px; color: #75869c; font: 500 9px/1 system-ui; letter-spacing: 0; }
	.legend span::before { content: ''; width: 18px; border-top: 2px solid; }
	.legend .candidate::before { border-top-style: dashed; border-color: #f5b84b; }
	.legend .derived::before { border-color: #64a8ff; }
	.inspector { padding: 23px 20px; background: #0a0f17; }
	.inspector.drawerOpen { padding: 0; }
	.inspectorHead { display: flex; justify-content: space-between; align-items: center; }
	.inspectorHead button { border: 0; background: none; color: #65758c; font-size: 20px; cursor: pointer; }
	.inspector h2 { margin: 34px 0 6px; color: #f0f4f9; font-size: 27px; letter-spacing: -.03em; }
	.entityId { color: #65758c; font: 500 10px/1.4 ui-monospace, monospace; }
	.entityStats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin: 22px 0; }
	.entityStats div { padding: 10px 8px; border: 1px solid #182434; border-radius: 9px; background: #0d141f; }
	.entityStats span { display: block; color: #5e6e84; font-size: 9px; }
	.entityStats strong { display: block; margin-top: 6px; color: #dbe4ef; font: 600 12px/1 ui-monospace, monospace; }
	.truthCard { margin: 20px 0; padding: 14px; border-radius: 12px; background: rgba(245,184,75,.055); border: 1px dashed rgba(245,184,75,.28); }
	.truthCard > div { display: flex; gap: 8px; align-items: center; color: #e5b960; font-size: 12px; }
	.truthCard p { margin: 10px 0 0; color: #75869b; font-size: 11px; line-height: 1.62; }
	.sourceRef { margin-top: 18px; }
	.sourceRef code { display: block; margin-top: 8px; overflow-wrap: anywhere; color: #71829a; font-size: 9px; }
	.tableCta { width: 100%; margin-top: 22px; border: 1px solid #26364d; border-radius: 9px; padding: 10px; background: #121b28; color: #aebbd0; cursor: pointer; }
	.emptyInspector { padding-top: 72px; }
	.emptyInspector h2 { margin-top: 13px; font-size: 22px; }
	.emptyInspector p { color: #718198; font-size: 12px; line-height: 1.65; }
	.workflowList { margin-top: 26px; display: grid; gap: 7px; }
	.workflowList button, .workflowList a { display: flex; gap: 11px; align-items: center; width: 100%; border: 1px solid #192536; border-radius: 9px; padding: 11px; background: #0d141f; color: #9aa9bd; text-decoration: none; text-align: left; cursor: pointer; }
	.workflowList b { color: #50627a; font: 600 9px/1 ui-monospace, monospace; }
	.workflowList span { font-size: 11px; }
	.integrity { max-width: 1420px; margin: 14px auto 0; display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; padding: 15px 18px; border: 1px solid #15202e; border-radius: 13px; background: rgba(10,15,23,.6); }
	.integrity div { min-width: 0; display: flex; align-items: center; gap: 10px; }
	.integrity code { overflow: hidden; color: #52637a; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
	.integrity p { grid-column: 1 / -1; margin: 2px 0 0; color: #586980; font-size: 10px; }
	@media (max-width: 980px) { .hero { grid-template-columns: 1fr; gap: 20px; } .heroMeta { max-width: 430px; } .workspace { grid-template-columns: 1fr; } .scenePanel { border-right: 0; } .inspector { border-top: 1px solid #172231; } .metrics { grid-template-columns: repeat(2, 1fr); } .metrics > div:nth-child(2) { border-right: 0; } .metrics > div:nth-child(-n+2) { border-bottom: 1px solid #172231; } }
	@media (max-width: 760px) { .toolbar { grid-template-columns: 1fr auto; } .search { grid-column: 1 / -1; grid-row: 2; width: 100%; } .search.hidden { display: none; } .sceneSwitch { overflow-x: auto; } }
	@media (max-width: 620px) { .universeShell { padding: 76px 12px 32px; } .hero { margin-bottom: 24px; } h1 { font-size: 36px; } .metrics > div { padding: 14px; } .metrics strong { font-size: 21px; } .toolbar { align-items: center; gap: 9px; padding: 10px; } .search { width: 100%; } .search label { display: none; } .viewSwitch { flex-shrink: 0; } .sceneSwitch button { padding: 7px; } .scenePanel { padding: 10px; } .sceneHeader { align-items: center; } .legend { display: none; } .integrity { grid-template-columns: 1fr; } .integrity p { grid-column: 1; } }
</style>
