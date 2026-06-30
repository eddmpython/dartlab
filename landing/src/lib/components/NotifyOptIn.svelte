<script lang="ts">
	// 알림 켜기 · 2단 게이트(소프트 프롬프트 → 클릭 시에만 OS 권한). 콜드 자동 팝업 금지(1회 거부=영구 차단).
	// iOS 16.4+ 는 홈화면 설치(standalone) 안에서만 푸시 가능 → 미설치 Safari 는 숨김(InstallPrompt 가 설치유도).
	// 설계: mainPlan/watcher-notify-platform/07-p1-client-receiving.md §2.
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { isStandalone, isIosSafari } from '$lib/pwa/platform';
	import {
		VAPID_PUBLIC_KEY,
		DEFAULT_TOPICS,
		subscribePush,
		serializeSubscription,
		postSubscribe,
		postUnsubscribe
	} from '$lib/notify/subscription';

	let { topics = DEFAULT_TOPICS }: { topics?: string[] } = $props();

	const DISMISS_KEY = 'dl-notify-dismissed';
	type Phase = 'hidden' | 'soft' | 'subscribing' | 'on' | 'blocked';
	let phase = $state<Phase>('hidden');

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
			/* 프라이빗 모드 · 무시 */
		}
	}

	async function subscribeAndPost() {
		phase = 'subscribing';
		try {
			const reg = await navigator.serviceWorker.ready;
			const sub = await subscribePush(reg, VAPID_PUBLIC_KEY);
			await postSubscribe(serializeSubscription(sub, topics));
			phase = 'on';
		} catch {
			phase = 'soft'; // 실패 → 소프트 복귀(재시도 가능)
		}
	}

	// '알림 켜기' 클릭(제스처) · OS 권한 팝업은 오직 여기. requestPermission 을 먼저(ready await 가 제스처 끊는 것 회피).
	async function enable() {
		let perm: NotificationPermission;
		try {
			perm = await Notification.requestPermission();
		} catch {
			perm = Notification.permission;
		}
		if (perm === 'granted') await subscribeAndPost();
		else if (perm === 'denied') {
			phase = 'blocked';
			remember();
		} else phase = 'soft';
	}

	async function disable() {
		try {
			const reg = await navigator.serviceWorker.ready;
			const sub = await reg.pushManager.getSubscription();
			if (sub) {
				await postUnsubscribe(sub.endpoint);
				await sub.unsubscribe();
			}
		} catch {
			/* 무시 · 서버 purge 가 결국 정리 */
		}
		phase = 'soft';
	}

	function close() {
		phase = 'hidden';
		remember();
	}

	onMount(async () => {
		// 가드 순서 · 하나라도 걸리면 requestPermission 미호출(콜드 팝업 0).
		if (typeof Notification === 'undefined' || !('serviceWorker' in navigator) || !('PushManager' in window)) return; // ① 미지원
		if (!VAPID_PUBLIC_KEY) return; // ② 키 미주입 = 기능 off(graceful)
		if (!isStandalone() && isIosSafari()) return; // ③ iOS 미설치 = InstallPrompt 가 설치유도(중복 안내 0)
		if (dismissed()) return; // ④ 이미 닫음
		const perm = Notification.permission;
		if (perm === 'denied') {
			phase = 'blocked'; // ⑤ 영구 차단 안내만(재요청 버튼 0)
			return;
		}
		if (perm === 'granted') {
			// ⑥ 이미 허용 · 기존 구독 있으면 on, 없으면 구독
			try {
				const reg = await navigator.serviceWorker.ready;
				const existing = await reg.pushManager.getSubscription();
				if (existing) phase = 'on';
				else await subscribeAndPost();
			} catch {
				phase = 'soft';
			}
			return;
		}
		phase = 'soft'; // ⑦ 소프트 프롬프트만
	});
</script>

{#if phase !== 'hidden' && phase !== 'on'}
	<div class="notifyBar" role="dialog" aria-label="DartLab 알림 설정">
		<img class="nIcon" src="{base}/icon-192.png" alt="" width="30" height="30" />
		<div class="nText">
			{#if phase === 'blocked'}
				<b>알림 차단됨</b>
				<span>브라우저 설정에서 알림을 허용하세요</span>
			{:else}
				<b>새 글·신규상장 알림 받기</b>
				<span>새 글·카드 + IPO·수주 이벤트를 기기로</span>
			{/if}
		</div>
		{#if phase === 'soft'}
			<button class="nEnable" onclick={enable}>알림 켜기</button>
		{:else if phase === 'subscribing'}
			<button class="nEnable" disabled>등록 중…</button>
		{/if}
		<button class="nClose" onclick={close} aria-label="닫기">✕</button>
	</div>
{:else if phase === 'on'}
	<div class="notifyBar notifyOn" role="status">
		<span class="nOnLabel">🔔 알림 켜짐</span>
		<button class="nOff" onclick={disable}>끄기</button>
	</div>
{/if}

<style>
	/* InstallPrompt 미러 · 단 더 위(70px)에 두어 두 바 시각 겹침 방지(07 §6). */
	.notifyBar {
		position: fixed;
		left: 50%;
		bottom: calc(70px + env(safe-area-inset-bottom, 0px));
		transform: translateX(-50%);
		z-index: 79;
		display: flex;
		align-items: center;
		gap: 11px;
		width: min(380px, calc(100vw - 24px));
		padding: 10px 12px;
		border-radius: 14px;
		background: rgba(13, 17, 25, 0.96);
		border: 1px solid rgba(var(--dl-accent-rgb), 0.4);
		box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(8px);
		color: #e8eef6;
		animation: nIn 0.28s cubic-bezier(0.2, 0.9, 0.3, 1);
	}
	.notifyOn {
		width: auto;
		gap: 8px;
		padding: 8px 12px;
	}
	@keyframes nIn {
		from {
			opacity: 0;
			transform: translate(-50%, 14px);
		}
		to {
			opacity: 1;
			transform: translate(-50%, 0);
		}
	}
	.nIcon {
		flex: 0 0 auto;
		border-radius: 8px;
	}
	.nText {
		display: flex;
		flex-direction: column;
		gap: 1px;
		flex: 1 1 auto;
		min-width: 0;
		line-height: 1.3;
		overflow-wrap: normal;
		word-break: keep-all;
	}
	.nText b {
		font-size: 13px;
		font-weight: 700;
		color: #f5f8fc;
		white-space: nowrap;
	}
	.nText span {
		font-size: 11px;
		color: #9aa7bc;
	}
	.nEnable {
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
	.nEnable:hover:not(:disabled) {
		filter: brightness(1.08);
	}
	.nEnable:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.nOnLabel {
		font-size: 12.5px;
		font-weight: 700;
		color: #cbd5e1;
	}
	.nOff {
		flex: 0 0 auto;
		padding: 5px 11px;
		border: 1px solid rgba(255, 255, 255, 0.14);
		border-radius: 8px;
		background: transparent;
		color: #9aa7bc;
		font-size: 11.5px;
		cursor: pointer;
	}
	.nOff:hover {
		color: #e8eef6;
		background: rgba(255, 255, 255, 0.06);
	}
	.nClose {
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
	.nClose:hover {
		color: #cbd5e1;
		background: rgba(255, 255, 255, 0.06);
	}
</style>
