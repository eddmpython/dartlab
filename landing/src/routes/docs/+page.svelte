<script lang="ts">
	import { base } from '$app/paths';
	import { navigation } from '$lib/docs/navigation';
</script>

<svelte:head>
	<title>DartLab 문서 — DART 전자공시 분석 가이드</title>
	<meta name="description" content="DartLab 설치부터 API 레퍼런스까지. DART 전자공시 문서를 파싱하고 재무제표를 시계열로 정렬하는 방법을 안내한다." />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/docs/" />
</svelte:head>

<div class="docs-index">
	<h1>DartLab 문서</h1>
	<p class="subtitle">DART 전자공시 문서를 파싱하고 시계열로 정렬하는 Python 라이브러리</p>

	<div class="cards">
		{#each navigation as section}
			<div class="card">
				<h2>{section.title}</h2>
				{#if section.items}
					<ul>
						{#each section.items as item}
							<li><a href="{base}{item.href}">{item.title}</a></li>
						{/each}
					</ul>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style>
	.docs-index {
		max-width: 900px;
		margin: 0 auto;
		padding: 3rem 1.5rem;
	}
	h1 {
		font-size: 2.25rem;
		font-weight: 700;
		color: #fafaf9;
		margin-bottom: 0.5rem;
	}
	.subtitle {
		color: #a8a29e;
		font-size: 1.1rem;
		margin-bottom: 2.5rem;
	}
	.cards {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
		gap: 1.25rem;
	}
	.card {
		background: #1c1917;
		border: 1px solid #292524;
		border-radius: 10px;
		padding: 1.5rem;
		transition: border-color 0.2s;
	}
	.card:hover {
		border-color: #f59e0b;
	}
	.card h2 {
		font-size: 1.1rem;
		font-weight: 600;
		color: #fafaf9;
		margin-bottom: 0.75rem;
	}
	.card ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.card li {
		margin: 0.35rem 0;
	}
	.card a {
		color: #a8a29e;
		text-decoration: none;
		font-size: 0.9rem;
		transition: color 0.15s;
	}
	.card a:hover {
		color: #f59e0b;
	}
</style>
