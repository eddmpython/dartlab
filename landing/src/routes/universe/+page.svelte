<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import {
		BrandMark,
		BrandSocial,
		BrandSwitch,
		DARTLAB_BRAND_LINKS,
		SupportDialog,
		fetchGithubStars
	} from '@dartlab/ui-surfaces/terminal';
	import '../../../../tests/_attempts/dartlabUniverse/gui/universe.css';

	const links = DARTLAB_BRAND_LINKS;
	let ghStars = $state<number | null>(null);
	let supportOpen = $state(false);

	fetchGithubStars(links.repo).then((count) => (ghStars = count));

	onMount(() => {
		document.body.dataset.universeRoute = 'true';
		let active = true;
		let dispose: (() => void) | undefined;
		void import('../../../../tests/_attempts/dartlabUniverse/gui/app.js')
			.then((module) => {
				if (!active) return;
				dispose = module.disposeUniverse;
				return module.bootUniverse();
			})
			.catch((error: unknown) => {
				if (!active) return;
				const loading = document.getElementById('loading-state');
				const errorState = document.getElementById('error-state');
				const errorDetail = document.getElementById('error-detail');
				if (loading) loading.hidden = true;
				if (errorDetail) {
					errorDetail.textContent =
						error instanceof Error ? error.message : 'Universe 모듈을 불러오지 못했습니다';
				}
				if (errorState) errorState.hidden = false;
			});
		return () => {
			active = false;
			dispose?.();
			delete document.body.dataset.universeRoute;
		};
	});
</script>

<svelte:head>
	<title>DartLab Universe · 3D 지식 우주</title>
	<meta
		name="description"
		content="DartLab의 데이터, 공시, 재무, 엔진, 블로그와 근거를 탐색하는 3차원 지식 우주"
	/>
	<meta name="robots" content="noindex,nofollow" />
</svelte:head>

<main id="universe-shell" aria-label="DartLab 지식 우주 3D 검수 화면">
	<canvas id="universe-canvas" aria-label="상호작용 가능한 3차원 지식 우주"></canvas>
	<div id="label-layer" aria-hidden="true"></div>
	<header class="topbar">
		<div class="identity">
			<BrandMark tag="universe" href="{base}/" {base} title="DartLab 홈" />
		</div>
		<div class="scene-status" role="status" aria-live="polite">
			<span id="scope-label">전체 우주</span>
			<span class="separator" aria-hidden="true"></span>
			<span id="visible-count">불러오는 중</span>
		</div>
		<div class="topbar-actions">
			<div class="backend-state">
				<span class="pulse" aria-hidden="true"></span>
				<span id="backend-label">GPU 확인 중</span>
			</div>
			<div class="brand-social-theme">
				<BrandSocial {links} {ghStars} onSupport={() => (supportOpen = true)}>
					{#snippet leading()}<BrandSwitch />{/snippet}
				</BrandSocial>
			</div>
		</div>
	</header>

	<nav class="view-controls" aria-label="우주 탐색">
		<button id="back-button" type="button" aria-label="상위 우주로 돌아가기" disabled>
			<span aria-hidden="true">←</span><span>상위</span>
		</button>
		<button id="home-button" type="button" aria-label="전체 우주 보기">
			<span aria-hidden="true">⌂</span><span>전체</span>
		</button>
		<button id="labels-button" type="button" aria-label="천체 이름 표시" aria-pressed="true">
			<span aria-hidden="true">Aa</span><span>이름</span>
		</button>
		<button id="edges-button" type="button" aria-label="천체 관계 표시" aria-pressed="true">
			<span aria-hidden="true">⌁</span><span>관계</span>
		</button>
	</nav>

	<div class="legend" id="legend" aria-label="지식 계열 범례"></div>

	<section class="hint" id="interaction-hint" aria-label="조작 안내">
		<span>드래그 회전</span><span>휠 확대</span><span>노드 선택</span>
	</section>

	<aside id="selection-panel" class="selection-panel" aria-live="polite" hidden>
		<div class="selection-heading">
			<div>
				<p id="selection-kicker"></p>
				<h1 id="selection-title">선택한 천체</h1>
			</div>
			<button id="close-selection" type="button" aria-label="선택 정보 닫기">×</button>
		</div>
		<dl id="selection-facts"></dl>
		<button id="drill-button" class="primary-action" type="button" hidden>이 은하계로 진입</button>
	</aside>

	<div id="loading-state" class="loading-state" role="status" aria-live="assertive">
		<div class="loader-orbit" aria-hidden="true"><span></span></div>
		<strong id="loading-title">지식 우주를 구성하고 있습니다</strong>
		<span id="loading-detail">검증된 공간 타일을 불러오는 중</span>
	</div>

	<div id="error-state" class="error-state" role="alert" hidden>
		<strong id="error-title">우주를 열지 못했습니다</strong>
		<span id="error-detail"></span>
	</div>
</main>

<SupportDialog
	lang="kr"
	{links}
	{base}
	open={supportOpen}
	onClose={() => (supportOpen = false)}
/>
