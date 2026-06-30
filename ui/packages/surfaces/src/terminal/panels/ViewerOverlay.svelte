<script lang="ts">
	// 공시뷰어 인터미널 오버레이 · ViewerStudio 를 fixed 전체화면에 lazy 마운트(한몸두입구의 터미널 입구).
	// ⛔ 정적 import 금지: 터미널 초기 청크에 viewer 가 실리면 평소 비용 0 원칙이 깨진다. 셸 주입 lazy
	// 로더(hosts.viewerStudio · 동적 import 리터럴은 셸 소유)로 청크 분리 유지 · ⤢ 클릭 전엔 1바이트도
	// 안 내려온다. 회사 이동·비교는 내부 state(URL 불변).
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import type { TerminalHosts } from '../lib/hosts';

	let {
		code,
		studio,
		repoUrl = '',
		onclose
	}: {
		code: string;
		studio: TerminalHosts['viewerStudio'];
		repoUrl?: string; // 셸 brand repo URL · 컴포넌트 임베드 ViewerStudio 의 이슈 링크용(미주입 시 깨진 /issues/new 방지).
		onclose: () => void;
	} = $props();
	const rt = useDartLabRuntime();

	// 내부 항해 전엔 터미널 종목을 따라가고(prop 반응), 뷰어 안에서 이동하면 그때부터 내부 state 가 잡는다.
	let nav = $state<{ code: string; vs: string[] } | null>(null);
	const view = $derived(nav ?? { code, vs: [] as string[] });
	function onNavigate(c: string, v: string[]) {
		nav = { code: c, vs: v };
	}

	// viewer port: URL 반환(ui/web 로컬) = iframe / null(landing 공개) = ViewerStudio 컴포넌트 임베드
	const viewerUrl = $derived(rt.viewer.urlForCompany(view.code, { vs: view.vs }));
	const mod = $derived(viewerUrl || !studio ? null : studio());

	// ESC 닫기 · 입력 필드(검색·질문) 안의 Esc 는 그 위젯 몫(팝오버 닫기)이라 오버레이는 무시.
	$effect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key !== 'Escape') return;
			const t = e.target as HTMLElement | null;
			if (t?.closest('input, textarea, [contenteditable]')) return;
			onclose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<div class="dlViewerFs">
	{#if viewerUrl}
		<iframe class="dlViewerFrame" src={viewerUrl} title="DartLab local viewer"></iframe>
	{:else if mod}
		{#await mod}
			<div class="dlViewerLoad"><span class="dlViewerSpin"></span>공시뷰어 여는 중…</div>
		{:then m}
			{@const Studio = m.default}
			<Studio code={view.code} vs={view.vs} embedded basePath={rt.env.basePath} {repoUrl} tier={rt.env.kind === 'local' ? 'local' : 'public'} {onNavigate} {onclose} />
		{:catch}
			<div class="dlViewerLoad">뷰어 모듈 로드 실패 · 네트워크 확인 후 다시 열어주세요.</div>
		{/await}
	{:else}
		<!-- 셸이 URL·임베드 어느 쪽도 제공하지 않음 · 열화 안내 (정상 셸에선 도달 불가) -->
		<div class="dlViewerLoad">이 셸에선 공시뷰어 임베드를 지원하지 않습니다.</div>
	{/if}
</div>

<style>
	.dlViewerFrame {
		width: 100%;
		height: 100%;
		border: 0;
		background: #05070b;
	}
</style>
