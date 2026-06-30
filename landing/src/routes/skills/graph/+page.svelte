<script lang="ts">
	import Header from '$lib/components/sections/Header.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import SkillGraphCanvas from '$lib/components/skills/SkillGraphCanvas.svelte';
	import { categoryColor } from '$lib/skills/categoryColors';

	let { data } = $props();
	const graph = $derived(data.graph);

	let mode = $state<'tree' | 'force'>('force');
	let filterCategory = $state('all');
	let query = $state('');

	const categories = ['all', 'start', 'runtime', 'operation', 'engines', 'recipes'];
</script>

<svelte:head>
	<title>Skill Graph · DartLab</title>
	<meta name="description" content="DartLab Skill OS 그래프 · 257 노드 + 1337 엣지를 클릭으로 탐색." />
</svelte:head>

<Header context="skills" />

<main class="graph-page">
	<header class="page-head">
		<p class="kicker">Skill Graph</p>
		<h1>DartLab Skill Map</h1>
		<p class="lead">
			카테고리별 영역으로 나눠 skill 관계를 읽는다. 작은 점은 개별 skill, 선은 실행 순서·레시피 연결·지식 참조다.
		</p>
		<div class="metric-row">
			<span>257 skills</span>
			<span>{graph.entries.length} entries</span>
			<span>cycle {graph.cycles.length}</span>
			<span>orphan {graph.orphans.length}</span>
			<span>unreachable {graph.unreachable.length}</span>
		</div>
	</header>

	<div class="controls">
		<div class="control-group">
			<span class="control-label">레이아웃</span>
			<button class:active={mode === 'force'} onclick={() => (mode = 'force')}>분류 맵</button>
			<button class:active={mode === 'tree'} onclick={() => (mode = 'tree')}>Tree</button>
		</div>
		<div class="control-group">
			<label for="skill-graph-category">카테고리</label>
			<select id="skill-graph-category" bind:value={filterCategory}>
				{#each categories as cat}
					<option value={cat}>{cat === 'all' ? '전체' : cat}</option>
				{/each}
			</select>
		</div>
		<div class="control-group">
			<label for="skill-graph-query">검색</label>
			<input id="skill-graph-query" type="text" bind:value={query} placeholder="skill id · title · purpose" />
		</div>
	</div>

	<div class="legend">
		{#each ['start', 'runtime', 'operation', 'engines', 'recipes'] as cat}
			<span class="legend-item">
				<span class="dot" style="background: {categoryColor[cat]}"></span>
				{cat}
			</span>
		{/each}
		<span class="legend-item">실선 = successor / linkedRecipe</span>
		<span class="legend-item">점선 = knowledge</span>
	</div>

	<SkillGraphCanvas {graph} {mode} {filterCategory} {query} width={1360} height={900} />
</main>

<Footer />

<style>
	.graph-page {
		max-width: none;
		margin: 0 auto;
		padding: 6.5rem 1.25rem 4rem;
		background:
			radial-gradient(circle at 24% 0%, rgba(234, 70, 71, 0.12), transparent 32rem),
			var(--dl-bg-base);
		color: var(--dl-ink);
	}

	.page-head,
	.controls,
	.legend,
	.graph-page :global(.graph-wrap) {
		max-width: 1440px;
		margin-left: auto;
		margin-right: auto;
	}

	.kicker {
		margin: 0 0 0.45rem;
		color: var(--dl-orange);
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.12em;
	}

	.page-head h1 {
		margin: 0 0 0.75rem;
		font-family: var(--dl-font-head);
		font-size: clamp(2rem, 4vw, 3.25rem);
		line-height: 1.05;
		color: var(--dl-ink-print);
	}

	.lead {
		max-width: 54rem;
		margin: 0 0 1rem;
		color: var(--dl-ink-mute);
		font-size: 1rem;
		line-height: 1.7;
	}

	.metric-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-bottom: 1.35rem;
	}

	.metric-row span {
		padding: 0.28rem 0.5rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-raised);
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
	}

	.controls {
		display: flex;
		gap: 1rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		align-items: center;
	}
	.control-group {
		display: flex;
		align-items: center;
		gap: 0.45rem;
	}
	.control-group label,
	.control-label {
		font-size: 0.78rem;
		color: var(--dl-ink-dim);
	}
	.control-group button {
		padding: 0.35rem 0.7rem;
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-raised);
		color: var(--dl-ink-mute);
		border-radius: var(--dl-r-sm);
		cursor: pointer;
		font-size: 0.78rem;
	}
	.control-group button.active {
		background: var(--dl-orange-soft);
		color: var(--dl-orange);
		border-color: rgba(251, 146, 60, 0.4);
	}
	.control-group select,
	.control-group input {
		padding: 0.42rem 0.6rem;
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-raised);
		color: var(--dl-ink);
		font-size: 0.78rem;
	}
	.legend {
		display: flex;
		gap: 0.9rem;
		margin-bottom: 1rem;
		font-size: 0.75rem;
		color: var(--dl-ink-dim);
		flex-wrap: wrap;
	}
	.legend-item {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		display: inline-block;
	}
</style>
