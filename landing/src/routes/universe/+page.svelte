<script lang="ts">
	import { base } from '$app/paths';
	import { pushState, replaceState } from '$app/navigation';
	import { UniverseSurface } from '@dartlab/ui-surfaces/universe';
	import { createUniverseBrowser } from '$lib/browser/universeBrowser';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const universe = createUniverseBrowser({ fetchFn: fetch });

	function writeRouteUrl(next: URL, push: boolean): void {
		if (push) pushState(next, {});
		else replaceState(next, {});
	}
</script>

<svelte:head>
	<title>DartLab Universe · 데이터와 지식의 우주</title>
	<meta name="description" content="Hugging Face의 모든 DartLab 데이터와 엔진, Skill OS, 공시, 재무, 시장, 지식 근거를 공간적으로 탐색하는 DartLab Universe" />
	<meta name="robots" content={data.releaseState === 'ga' ? 'index,follow' : 'noindex,nofollow'} />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/universe" />
	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab Universe · 데이터와 지식의 우주" />
	<meta property="og:description" content="DartLab의 모든 데이터와 지식, 엔진, 스킬과 근거를 하나의 공간에서 탐색합니다." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/universe" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab Universe · 데이터와 지식의 우주" />
	<meta name="twitter:description" content="DartLab의 데이터와 지식 관계가 연결되고 전개되는 과정을 탐색합니다." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
</svelte:head>

<a class="skipLink" href="#universe-main">Universe 본문으로 건너뛰기</a>
<header class="universeTopbar">
	<a class="brand" href={`${base}/`} aria-label="DartLab 홈">
		<picture><source srcset={`${base}/avatar.webp`} type="image/webp" /><img src={`${base}/avatar.png`} alt="" width="24" height="24" /></picture>
		<strong>DartLab</strong><span>/</span><b>Universe</b>
	</a>
	<nav aria-label="Universe 탐색">
		<span class:disabled={data.releaseState === 'disabled'}>{data.releaseState === 'ga' ? 'PRODUCTION' : 'MAINTENANCE'}</span>
		<a href={`${base}/universe`} aria-current="page">Universe</a>
		<a href={`${base}/map`}>Map</a>
		<a href={`${base}/`}>Home</a>
	</nav>
</header>
{#if data.product.routeReady}
	<UniverseSurface
		seed={data}
		loadKnowledgeOverview={universe.knowledgeOverview}
		loadKnowledgeCoverage={universe.knowledgeCoverage}
		searchKnowledge={universe.searchKnowledge}
		openKnowledge={universe.openKnowledge}
		mapHref={`${base}/map`}
		loadChanges={universe.changes}
		resolveEvidence={universe.resolveEvidence}
		loadGlobalCoverage={universe.globalCoverage}
		searchEntities={universe.searchEntities}
		loadEntityProfile={universe.entityProfile}
		compareEntities={universe.compareEntities}
		{writeRouteUrl}
	/>
{:else}
	<main id="universe-main" class="maintenance">
		<span>UNIVERSE MAINTENANCE</span>
		<h1>Universe를 안전하게 점검하고 있습니다.</h1>
		<p>시장 지도는 계속 사용할 수 있습니다. 데이터 무결성 확인이 끝나면 같은 주소에서 Universe가 다시 열립니다.</p>
		<a href={`${base}/map`}>시장 지도 열기</a>
	</main>
{/if}

<style>
	.skipLink { position: fixed; z-index: 100; top: 8px; left: 12px; transform: translateY(-150%); padding: 9px 12px; border-radius: 7px; color: #fff; background: #233b5d; font-size: 12px; text-decoration: none; }
	.skipLink:focus { transform: translateY(0); }
	.universeTopbar { position: fixed; z-index: 50; top: 0; left: 0; right: 0; height: 49px; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(18px, 4vw, 64px); border-bottom: 1px solid rgba(94,112,137,.18); background: rgba(7,10,17,.88); backdrop-filter: blur(18px); font-family: 'Pretendard Variable', Pretendard, system-ui, sans-serif; }
	.brand { display: flex; align-items: center; gap: 7px; color: #dfe7f1; text-decoration: none; font-size: 13px; }
	.brand img { display: block; border-radius: 50%; }
	.brand span { color: #36445a; font-weight: 300; }
	.brand b { color: #8292a8; font-size: 12px; font-weight: 550; }
	nav { display: flex; align-items: center; gap: 5px; }
	nav span { margin-right: 8px; padding: 4px 7px; border: 1px solid rgba(72,194,138,.27); border-radius: 999px; color: #6ed1a0; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .08em; }
	nav span.disabled { border-color: rgba(245,184,75,.25); color: #d9a94f; }
	nav a { padding: 6px 9px; border-radius: 6px; color: #718198; text-decoration: none; font-size: 11px; }
	nav a:hover { color: #e6ecf4; background: rgba(255,255,255,.05); }
	nav a[aria-current='page'] { color: #dce5f2; background: rgba(255,255,255,.05); }
	.maintenance { min-height: 100vh; display: grid; align-content: center; justify-items: start; padding: 90px clamp(24px, 8vw, 140px); color: #dce5f2; background: radial-gradient(circle at 72% 20%, rgba(52,96,160,.18), transparent 30%), #070a11; font-family: 'Pretendard Variable', Pretendard, system-ui, sans-serif; }
	.maintenance > span { color: #d9a94f; font: 600 9px/1 ui-monospace, monospace; letter-spacing: .14em; }
	.maintenance h1 { max-width: 720px; margin: 18px 0 12px; font-size: clamp(34px, 5vw, 64px); line-height: 1.05; }
	.maintenance p { max-width: 620px; color: #8191a7; line-height: 1.7; }
	.maintenance a { margin-top: 18px; padding: 10px 14px; border: 1px solid #2b3c54; border-radius: 8px; color: #cbd7e5; text-decoration: none; background: #101925; }
	@media (max-width: 520px) { .universeTopbar { padding: 0 12px; } nav span { display: none; } .brand b { display: none; } }
</style>
