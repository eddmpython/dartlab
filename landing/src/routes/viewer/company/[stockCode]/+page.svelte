<script lang="ts">
	// 공시뷰어 라우트 · URL ↔ ViewerStudio 어댑터(한몸두입구의 라우트 입구).
	// 본체는 @dartlab/ui-surfaces/viewer 의 ViewerStudio(surface). 여기는 params/?vs= 를 props 로,
	// 스튜디오의 회사 이동·비교 변경(onNavigate)을 goto URL 로만 되비춘다(딥링크·뒤로가기 보존).
	// 공개 셸이 surface 에 SvelteKit 결합을 주입: basePath(에셋)·repoUrl(이슈 링크)·header(사이트 Header 스니펫).
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import Header from '$lib/components/sections/Header.svelte';
	import { ViewerStudio } from '@dartlab/ui-surfaces/viewer';

	let { data }: { data: { code: string; vs?: string[]; vsRejected?: Array<{ code: string; reason: string }> } } = $props();

	// invalidateAll: 같은 경로 + ?vs= 쿼리만 바뀌는 goto 가 load 를 다시 안 돌리는 케이스 방지.
	function onNavigate(code: string, vs: string[]) {
		const q = vs.filter((c) => c && c !== code).join(',');
		return goto(`${base}/viewer/company/${code}${q ? `?vs=${q}` : ''}`, { invalidateAll: true });
	}
</script>

{#snippet header()}
	<Header context="landing" />
{/snippet}

<ViewerStudio code={data.code} vs={data.vs ?? []} {onNavigate} basePath={base} repoUrl={brand.repo} {header} />
