<script lang="ts">
	// 로컬 공시 뷰어. surface ViewerStudio 마운트(단계-6-3). 패널/TOC/검색/비교/AskDrawer 는 HF parquet 직접 read
	// (@dartlab/ui-runtime/data/parquet/hfRange, 브라우저)로 landing 공개 뷰어와 동일 동작. 터미널 오버레이의 iframe 타깃
	// 이기도 하다(viewer.urlForCompany → ?terminalEmbed=1 → embedded 모드: 헤더·title 숨김·100% 높이).
	// 정량재무 다이얼로그(DuckDB-WASM)는 local 셸이 provideDuckDb 미주입 → 빈값 정직 강등(기존 로컬 터미널 재무 패리티).
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ViewerStudio } from '@dartlab/ui-surfaces/viewer';
	import { isKrStockCode, normalizeKrCode } from '@dartlab/ui-contracts';
	import { localLinks } from '$lib/shell/terminalShell';

	const code = $derived(page.params.code ?? ''); // [code] 라우트라 항상 존재. 타입 coerce.
	const vs = $derived(
		(page.url.searchParams.get('vs') ?? '')
			.split(',')
			.map((c) => normalizeKrCode(c))
			.filter(isKrStockCode)
	);
	const embedded = $derived(page.url.searchParams.get('terminalEmbed') === '1');

	// 회사 이동·비교 변경 → 같은 viewer 라우트 URL 로 되비춤(딥링크 보존). 라우팅 의존은 셸이 소유.
	function onNavigate(next: string, nextVs: string[]) {
		const q = nextVs.filter((c) => c && c !== next).join(',');
		return goto(`${base}/analysis/${encodeURIComponent(next)}/viewer${q ? `?vs=${q}` : ''}`, {
			invalidateAll: true
		});
	}

	function onAsk(stockCode: string) {
		return goto(`${base}/chat?code=${encodeURIComponent(stockCode)}`);
	}
</script>

<svelte:head><title>Viewer · {code} · dartlab local</title></svelte:head>

<!-- tier="local": 이 라우트는 local 셸 전용. Ask는 공용 Agent Runtime chat으로, export는 local 완전판으로 연결한다. -->
<ViewerStudio {code} {vs} {embedded} tier="local" {onNavigate} {onAsk} basePath={base} repoUrl={localLinks.repo} />
