<script lang="ts">
	import { base } from '$app/paths';
	import { UniverseSurface } from '@dartlab/ui-surfaces/universe';
	import { createUniverseBrowser } from '$lib/browser/universeBrowser';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const universe = createUniverseBrowser({ fetchFn: fetch });
</script>

<svelte:head>
	<title>DartLab Universe · 시장 관계 탐색</title>
	<meta name="description" content="산업 구조와 집계 흐름을 근거 상태와 함께 탐색하는 DartLab Universe 로컬 리뷰 화면" />
	<meta name="robots" content="noindex,nofollow" />
</svelte:head>

<header class="universeTopbar">
	<a class="brand" href={`${base}/`} aria-label="DartLab 홈">
		<picture><source srcset={`${base}/avatar.webp`} type="image/webp" /><img src={`${base}/avatar.png`} alt="" width="24" height="24" /></picture>
		<strong>DartLab</strong><span>/</span><b>Universe</b>
	</a>
	<nav aria-label="Universe 탐색">
		<span>LOCAL REVIEW</span>
		<a href={`${base}/map`}>Map</a>
		<a href={`${base}/`}>Home</a>
	</nav>
</header>
<UniverseSurface seed={data} mapHref={`${base}/map`} loadChanges={universe.changes} resolveEvidence={universe.resolveEvidence} />

<style>
	.universeTopbar { position: fixed; z-index: 50; top: 0; left: 0; right: 0; height: 49px; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(18px, 4vw, 64px); border-bottom: 1px solid rgba(94,112,137,.18); background: rgba(7,10,17,.88); backdrop-filter: blur(18px); font-family: 'Pretendard Variable', Pretendard, system-ui, sans-serif; }
	.brand { display: flex; align-items: center; gap: 7px; color: #dfe7f1; text-decoration: none; font-size: 13px; }
	.brand img { display: block; border-radius: 50%; }
	.brand span { color: #36445a; font-weight: 300; }
	.brand b { color: #8292a8; font-size: 12px; font-weight: 550; }
	nav { display: flex; align-items: center; gap: 5px; }
	nav span { margin-right: 8px; padding: 4px 7px; border: 1px solid rgba(245,184,75,.25); border-radius: 999px; color: #d9a94f; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .08em; }
	nav a { padding: 6px 9px; border-radius: 6px; color: #718198; text-decoration: none; font-size: 11px; }
	nav a:hover { color: #e6ecf4; background: rgba(255,255,255,.05); }
	@media (max-width: 520px) { .universeTopbar { padding: 0 12px; } nav span { display: none; } .brand b { display: none; } }
</style>
