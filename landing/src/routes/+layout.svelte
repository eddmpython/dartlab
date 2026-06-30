<script lang="ts">
	import '../app.css';
	import '@dartlab/ui-design/styles/v2-tokens.css';
	import '@dartlab/ui-design/styles/tokens.css';
	import '@dartlab/ui-design/styles/typography.css';
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { themePref, applyTheme } from '$lib/theme';
	import { setStaticBase } from '@dartlab/ui-runtime/data/dartlabData';
	import { loadFinanceRows } from '@dartlab/ui-runtime/data/financeRows';
	import { loadDartDb } from '$lib/data/duckdb';
	import { provideFinanceRows } from '@dartlab/ui-surfaces/viewer';
	import { provideScanDuckDb } from '@dartlab/ui-surfaces/scan';
	import type { Snippet } from 'svelte';

	// runtime/data 의 static 경로 base 주입 (과도기 — 4a-2 에서 RuntimeEnvironment.basePath 로 정식화)
	setStaticBase(base);
	// 정량재무제표 표(viewer FinanceDialog)는 DuckDB-WASM 대신 hyparquet raw 행으로 JS 집계 — 차트(bundle)와
	// 같은 rowsCache 공유라 회사당 1회 다운로드·엔진 콜드스타트 0. scan 은 여전히 DuckDB-WASM(duckSql) — 전역 주입.
	provideFinanceRows(loadFinanceRows);
	provideScanDuckDb(loadDartDb);
	import CloudflareWebAnalytics from '$lib/components/CloudflareWebAnalytics.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import InstallPrompt from '$lib/components/InstallPrompt.svelte';
	import NotifyOptIn from '$lib/components/NotifyOptIn.svelte';

	let { children }: { children: Snippet } = $props();

	// 라우트별 테마 적용 — 콘텐츠 표면은 사용자 선호(라이트 가능), 도구 표면은 강제 다크. 네비게이션마다 재평가.
	$effect(() => {
		applyTheme($themePref, page.url.pathname, base);
	});
</script>

<CloudflareWebAnalytics />
<CommandPalette />
<InstallPrompt />
<NotifyOptIn />
{@render children()}

<style>
	/* 전역 모바일 보호 — viewport 가로 스크롤 차단
	   app.css에 두면 Tailwind v4 빌드에서 누락되므로 svelte global로 강제 */
	:global(html) {
		max-width: 100vw;
		overflow-x: clip;
	}
	:global(body) {
		max-width: 100vw;
		overflow-x: clip;
		word-break: keep-all;
		overflow-wrap: anywhere;
	}
	:global(img),
	:global(svg),
	:global(video),
	:global(canvas),
	:global(iframe) {
		max-width: 100%;
		height: auto;
	}
	:global(body > div) {
		max-width: 100vw;
	}

	/* dartlab 다크 톤 scrollbar 통일 — 모든 element 의 native scrollbar.
	   WebKit 기반 (Chrome/Safari/Edge) + Firefox scrollbar-color. */
	:global(*::-webkit-scrollbar) {
		width: 10px;
		height: 10px;
	}
	:global(*::-webkit-scrollbar-track) {
		background: transparent;
	}
	:global(*::-webkit-scrollbar-thumb) {
		background: #334155;
		border-radius: 5px;
		border: 2px solid transparent;
		background-clip: padding-box;
	}
	:global(*::-webkit-scrollbar-thumb:hover) {
		background: #475569;
		background-clip: padding-box;
		border: 2px solid transparent;
	}
	:global(*::-webkit-scrollbar-corner) {
		background: transparent;
	}
	:global(html) {
		scrollbar-color: #334155 transparent;
		scrollbar-width: thin;
	}
</style>
