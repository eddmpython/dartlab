<script lang="ts">
	// 은근한 PWA 설치 안내 · 설치 가능할 때만 1회, 하단 작은 바. 3겹 가드로 *이미 설치한 사람에겐 안 뜸*:
	//  ① standalone 실행(홈화면 아이콘으로 연 앱)이면 숨김  ② 안드/데스크톱은 beforeinstallprompt(설치 안 됨일 때만
	//     발생)로만 노출 + appinstalled 즉시 숨김  ③ iOS Safari 탭만 수동 힌트 1회(설치여부 감지 불가 · show-once).
	// 닫으면 localStorage 로 다시 안 뜸. 라우트 무관(루트 레이아웃 마운트).
	import { base } from '$app/paths';
	import { onMount } from 'svelte';

	const DISMISS_KEY = 'dl-install-dismissed';

	interface BipEvent extends Event {
		prompt: () => void;
		userChoice: Promise<{ outcome: string }>;
	}

	let visible = $state(false);
	let mode = $state<'button' | 'ios'>('button');
	let deferred: BipEvent | null = null;

	function isStandalone(): boolean {
		return (
			window.matchMedia('(display-mode: standalone)').matches ||
			(navigator as unknown as { standalone?: boolean }).standalone === true
		);
	}
	function dismissed(): boolean {
		try {
			return localStorage.getItem(DISMISS_KEY) === '1';
		} catch {
			return false;
		}
	}
	function remember() {
		try {
			localStorage.setItem(DISMISS_KEY, '1');
		} catch {
			/* 프라이빗 모드 등 · 무시 */
		}
	}
	function isIosSafari(): boolean {
		const ua = navigator.userAgent;
		return /iphone|ipad|ipod/i.test(ua) && /safari/i.test(ua) && !/crios|fxios|edgios/i.test(ua);
	}

	function close() {
		visible = false;
		remember();
	}
	async function install() {
		if (!deferred) return;
		deferred.prompt();
		try {
			await deferred.userChoice;
		} catch {
			/* 무시 */
		}
		deferred = null;
		visible = false;
		remember(); // 설치하든 거절하든 다시 안 띄움
	}

	onMount(() => {
		if (isStandalone() || dismissed()) return; // 가드① + 이미 닫음

		// 가드② · 안드/데스크톱: 설치 가능할 때만 이벤트가 온다(이미 설치면 안 옴).
		const onBip = (e: Event) => {
			e.preventDefault();
			deferred = e as BipEvent;
			mode = 'button';
			visible = true;
		};
		const onInstalled = () => {
			visible = false;
			remember();
		};
		window.addEventListener('beforeinstallprompt', onBip);
		window.addEventListener('appinstalled', onInstalled);

		// 가드③ · iOS Safari 탭: beforeinstallprompt 없음 → 콘텐츠 잠깐 본 뒤 수동 힌트 1회.
		let iosTimer: ReturnType<typeof setTimeout> | null = null;
		if (isIosSafari()) {
			iosTimer = setTimeout(() => {
				if (!isStandalone() && !dismissed()) {
					mode = 'ios';
					visible = true;
				}
			}, 3500);
		}

		return () => {
			window.removeEventListener('beforeinstallprompt', onBip);
			window.removeEventListener('appinstalled', onInstalled);
			if (iosTimer) clearTimeout(iosTimer);
		};
	});
</script>

{#if visible}
	<div class="installBar" role="dialog" aria-label="DartLab 앱 설치 안내">
		<img class="ipIcon" src="{base}/icon-192.png" alt="" width="32" height="32" />
		<div class="ipText">
			{#if mode === 'ios'}
				<b>홈 화면에 추가</b>
				<span
					>공유 <svg class="ipShare" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v13" /><path d="m8 7 4-4 4 4" /><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7" /></svg> →
					'홈 화면에 추가'</span
				>
			{:else}
				<b>DartLab 앱 설치</b>
				<span>주소창 없이 앱처럼 빠르게</span>
			{/if}
		</div>
		{#if mode === 'button'}
			<button class="ipInstall" onclick={install}>설치</button>
		{/if}
		<button class="ipClose" onclick={close} aria-label="닫기">✕</button>
	</div>
{/if}

<style>
	.installBar {
		position: fixed;
		left: 50%;
		bottom: calc(14px + env(safe-area-inset-bottom, 0px));
		transform: translateX(-50%);
		z-index: 80;
		display: flex;
		align-items: center;
		gap: 11px;
		/* 명시 width · 없으면 fixed+flex 가 콘텐츠 최소폭으로 쪼그라들고, 전역 overflow-wrap:anywhere 가
		   글자단위로 끊어 세로로 깨진다. 고정폭 + 아래 텍스트 keep-all 로 정상 줄바꿈. */
		width: min(380px, calc(100vw - 24px));
		padding: 10px 12px;
		border-radius: 14px;
		background: rgba(13, 17, 25, 0.96);
		border: 1px solid rgba(var(--dl-accent-rgb), 0.4);
		box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(8px);
		color: #e8eef6;
		animation: ipIn 0.28s cubic-bezier(0.2, 0.9, 0.3, 1);
	}
	@keyframes ipIn {
		from {
			opacity: 0;
			transform: translate(-50%, 14px);
		}
		to {
			opacity: 1;
			transform: translate(-50%, 0);
		}
	}
	.ipIcon {
		flex: 0 0 auto;
		border-radius: 8px;
	}
	.ipText {
		display: flex;
		flex-direction: column;
		gap: 1px;
		flex: 1 1 auto;
		min-width: 0;
		line-height: 1.3;
		/* 전역 overflow-wrap:anywhere 해제 · 한글 어절 단위(keep-all)로만 줄바꿈(글자단위 깨짐 차단). */
		overflow-wrap: normal;
		word-break: keep-all;
	}
	.ipText b {
		font-size: 13px;
		font-weight: 700;
		color: #f5f8fc;
		white-space: nowrap;
	}
	.ipText span {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		font-size: 11px;
		color: #9aa7bc;
	}
	.ipShare {
		color: var(--dl-accent);
		vertical-align: middle;
	}
	.ipInstall {
		flex: 0 0 auto;
		padding: 7px 14px;
		border: none;
		border-radius: 9px;
		background: var(--dl-accent);
		color: #06080d;
		font-size: 12.5px;
		font-weight: 800;
		cursor: pointer;
		transition: filter 0.15s;
	}
	.ipInstall:hover {
		filter: brightness(1.08);
	}
	.ipClose {
		flex: 0 0 auto;
		width: 26px;
		height: 26px;
		border: none;
		border-radius: 7px;
		background: transparent;
		color: #6b7688;
		font-size: 13px;
		cursor: pointer;
	}
	.ipClose:hover {
		color: #cbd5e1;
		background: rgba(255, 255, 255, 0.06);
	}
</style>
