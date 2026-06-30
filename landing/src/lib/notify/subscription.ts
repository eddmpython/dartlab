// Web Push 구독 공유 모듈 — service-worker 와 NotifyOptIn 이 함께 import(직렬화 형태·URL·토픽 1 SSOT).
// 허브 계약: mainPlan/watcher-notify-platform/06-p1-hub-worker.md §2.

const HUB_BASE = (import.meta.env.VITE_PUSHHUB_URL ?? '').replace(/\/+$/, '');
export const SUBSCRIBE_URL = HUB_BASE + '/subscribe';
export const VAPID_PUBLIC_KEY: string = import.meta.env.VITE_VAPID_PUBLIC_KEY ?? '';

// 단일 opt-in = 전 공개 토픽 구독(발행 + 시장 이벤트). 허브 TOPIC_ALLOWLIST 와 일치. 토픽별 cap·조용한시간은
// 러너가 처리(허브 thin). 토픽별 개별 on/off 는 P3 알림센터(per-topic 미세조정). 노이즈 가드 = 러너 rate-limit.
export const DEFAULT_TOPICS = ['blogPublish', 'cardPublish', 'newIpo', 'newOrders'];

export interface SubscribePayload {
	endpoint: string;
	keys: { p256dh: string; auth: string };
	topics: string[];
}

/** base64url(VAPID 공개키) → Uint8Array(applicationServerKey). padding 복원 후 atob. */
export function urlBase64ToUint8Array(b64: string): Uint8Array {
	const padding = '='.repeat((4 - (b64.length % 4)) % 4);
	const base64 = (b64 + padding).replace(/-/g, '+').replace(/_/g, '/');
	const raw = atob(base64);
	const out = new Uint8Array(raw.length);
	for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
	return out;
}

/** PushSubscription → 허브 /subscribe body. sub.toJSON().keys 는 padding 포함 base64url 가능(허브가 허용). */
export function serializeSubscription(sub: PushSubscription, topics: string[]): SubscribePayload {
	const json = sub.toJSON();
	return {
		endpoint: sub.endpoint,
		keys: { p256dh: json.keys?.p256dh ?? '', auth: json.keys?.auth ?? '' },
		topics
	};
}

/** 기존 구독 있으면 재사용, 없으면 신규 구독(userVisibleOnly 강제 — silent push 불가). */
export async function subscribePush(reg: ServiceWorkerRegistration, vapidPublicKey: string): Promise<PushSubscription> {
	const existing = await reg.pushManager.getSubscription();
	if (existing) return existing;
	return reg.pushManager.subscribe({
		userVisibleOnly: true,
		applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) as BufferSource
	});
}

/** 구독 등록 POST. 실패는 throw(호출자가 phase 복구). */
export async function postSubscribe(payload: SubscribePayload): Promise<void> {
	const res = await fetch(SUBSCRIBE_URL, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload)
	});
	if (!res.ok) throw new Error(`subscribe failed: ${res.status}`);
}

/** 구독 해지 — 전체 또는 부분(topics). pushManager.unsubscribe 와 동시 호출. */
export async function postUnsubscribe(endpoint: string, topics?: string[]): Promise<void> {
	await fetch(SUBSCRIBE_URL, {
		method: 'DELETE',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(topics ? { endpoint, topics } : { endpoint })
	});
}
