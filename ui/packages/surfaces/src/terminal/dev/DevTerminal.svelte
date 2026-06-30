<script lang="ts">
	// 격리 개발 작업대 셸 · /lab/terminal-dev 전용 WIP 조립 지점 (viewer 의 dev/ 선례).
	// 규약(무중단 · feedback_ui_rules #10):
	//   1. 본진(/terminal 라우트 + TerminalSurface 본 경로)은 이 dev/ 폴더를 절대 import 하지 않는다
	//      · landing/scripts/checkDevIsolation.js 가 빌드에서 기계 강제. 본진은 @dartlab/ui-surfaces/terminal,
	//      dev 는 @dartlab/ui-surfaces/terminal/dev 로 export 경로 자체가 분리(단계-4b). dev/ 의 어떤 WIP 가
	//      어떤 푸시에 실려 나가도 본진 번들에 포함될 수 없다.
	//   2. 신규 컴포넌트 WIP 는 이 폴더에 두고 여기서 조립·검증한다. 검증 완료 후 본 경로로
	//      이동+배선을 한 커밋으로 승격 (스크린샷 눈검수 게이트 통과 후).
	//   3. 기존 본 컴포넌트 수정은 로컬 미커밋 상태로 dev 서버(5173)에서 검증 · 미커밋 = 타 세션
	//      push 에 실리지 않는 격리 경계. 검증 즉시 커밋·푸시로 창을 닫는다.
	import type { ComponentProps } from 'svelte';
	import TerminalSurface from '../TerminalSurface.svelte';

	let { eng, runtime, hosts, links, initial = '005930' }: ComponentProps<typeof TerminalSurface> = $props();
</script>

<div class="devBanner mono">DEV 작업대 · 본진은 /terminal · 본 라우트는 noindex · WIP 는 surfaces terminal/dev/</div>
<TerminalSurface {eng} {runtime} {hosts} {links} {initial} />

<style>
	.devBanner {
		position: sticky;
		top: 0;
		z-index: 60;
		background: rgba(var(--amber-rgb), 0.12);
		color: var(--amber);
		border-bottom: 1px solid rgba(var(--amber-rgb), 0.4);
		font-size: 11px;
		padding: 3px 12px;
		letter-spacing: 0.3px;
	}
</style>
