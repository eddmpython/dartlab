/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

/**
 * dartlab Service Worker — 설치형 PWA(앱 셸 오프라인) + 데이터 무간섭.
 *
 * - 앱 셸(build/files: 해시 불변 JS·CSS·정적 자산)은 install 시 프리캐시 → cache-first.
 * - 내비게이션(HTML)은 network-first → 성공분 캐시 → 오프라인이면 캐시 폴백.
 * - ⛔ 크로스오리진(HF parquet·프록시 /media·/news 등 데이터)은 SW 가 절대 가로채지 않는다. hyparquet/DuckDB
 *   의 Range 요청을 네트워크에 그대로 맡겨야 첫 방문자의 저장소·메모리를 불리지 않는다(설계 불변).
 */
import { build, files, version } from '$service-worker';
import {
	SUBSCRIBE_URL,
	VAPID_PUBLIC_KEY,
	DEFAULT_TOPICS,
	serializeSubscription,
	urlBase64ToUint8Array
} from '$lib/notify/subscription';
import { sanitizeNotificationText, safeSelfRoute } from '$lib/notify/sanitize';

declare const self: ServiceWorkerGlobalScope;

const SHELL = `dartlab-shell-${version}`;
const SHELL_ASSETS = [...build, ...files];
const ASSET_SET = new Set(SHELL_ASSETS);

self.addEventListener('install', (event) => {
	event.waitUntil(
		(async () => {
			const cache = await caches.open(SHELL);
			await cache.addAll(SHELL_ASSETS);
			await self.skipWaiting();
		})()
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		(async () => {
			// 이전 버전 셸 캐시 + 옛 HF parquet full-body 캐시(dartlab-scan-*) 제거.
			const keys = await caches.keys();
			await Promise.all(
				keys
					.filter((k) => k.startsWith('dartlab-scan-') || (k.startsWith('dartlab-shell-') && k !== SHELL))
					.map((k) => caches.delete(k))
			);
			await self.clients.claim();
		})()
	);
});

self.addEventListener('fetch', (event) => {
	const req = event.request;
	if (req.method !== 'GET') return;
	const url = new URL(req.url);

	// ⛔ 크로스오리진(HF·프록시·뉴스 등 데이터) — SW 무간섭. 네트워크 그대로.
	if (url.origin !== self.location.origin) return;

	// 앱 셸 자산(해시 불변) — 캐시 우선.
	if (ASSET_SET.has(url.pathname)) {
		event.respondWith(
			(async () => {
				const cached = await caches.match(req);
				return cached ?? fetch(req);
			})()
		);
		return;
	}

	// 내비게이션(HTML) — 네트워크 우선, 성공분 캐시, 오프라인이면 캐시 폴백.
	if (req.mode === 'navigate') {
		event.respondWith(
			(async () => {
				try {
					const res = await fetch(req);
					const cache = await caches.open(SHELL);
					cache.put(req, res.clone());
					return res;
				} catch {
					const cached = await caches.match(req);
					return (
						cached ??
						new Response('오프라인 — 연결을 확인하세요.', {
							status: 503,
							headers: { 'Content-Type': 'text/html; charset=utf-8' }
						})
					);
				}
			})()
		);
		return;
	}

	// 그 외 same-origin GET — 기본 네트워크(가로채지 않음).
});

// ── Web Push 수신 3 리스너 (P1) — 기존 셸 캐시 동작과 독립 ──────────────
// 설계: mainPlan/watcher-notify-platform/07-p1-client-receiving.md
const ICON = `${import.meta.env.BASE_URL}icon-192.png`; // BASE_URL='/dartlab/' (절대경로 404 가드)

interface PushPayload {
	title?: string;
	body?: string;
	url?: string;
	tag?: string;
}

// push — aes128gcm 복호된 payload(notification 서브객체) 렌더. 항상 showNotification(미표시=userVisibleOnly 위반).
self.addEventListener('push', (event) => {
	event.waitUntil(
		(async () => {
			let payload: PushPayload = {};
			try {
				payload = (event.data?.json() as PushPayload) ?? {};
			} catch {
				payload = {};
			}
			const title = sanitizeNotificationText(payload.title || 'DartLab', 80) || 'DartLab';
			const body = sanitizeNotificationText(payload.body || '새 업데이트가 있습니다.', 120);
			// payload.url = app-path(base 없음) → SW 가 한 곳에서 BASE 접두 + same-origin 검증(피싱 차단).
			const url = safeSelfRoute(payload.url, import.meta.env.BASE_URL, self.location.origin);
			const tag = typeof payload.tag === 'string' ? payload.tag : undefined;
			await self.registration.showNotification(title, { body, tag, icon: ICON, badge: ICON, data: { url } });
		})()
	);
});

// notificationclick — same-origin 창 있으면 focus+navigate, 없으면 openWindow. 목적지=검증된 상대경로.
self.addEventListener('notificationclick', (event) => {
	event.notification.close();
	const dest = (event.notification.data?.url as string) || `${import.meta.env.BASE_URL}`;
	event.waitUntil(
		(async () => {
			const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
			for (const c of all) {
				if (new URL(c.url).origin === self.location.origin) {
					await c.focus();
					if ('navigate' in c) await (c as WindowClient).navigate(dest);
					return;
				}
			}
			await self.clients.openWindow(dest);
		})()
	);
});

// pushsubscriptionchange — 만료/회전 시 재구독 + /subscribe 재등록. 구 endpoint 는 /send 404/410 자가청소.
interface PushSubscriptionChangeEvent extends ExtendableEvent {
	newSubscription: PushSubscription | null;
	oldSubscription: PushSubscription | null;
}
self.addEventListener('pushsubscriptionchange', ((event: PushSubscriptionChangeEvent) => {
	event.waitUntil(
		(async () => {
			let sub = event.newSubscription;
			if (!sub) {
				// oldSubscription.options 가 원래 applicationServerKey 보존 → 재구독 시 VAPID 키 플러밍 거의 불요.
				const opts =
					event.oldSubscription?.options ??
					(VAPID_PUBLIC_KEY
						? { userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY) }
						: null);
				if (!opts || !opts.applicationServerKey) return; // 키 없음 → skip(graceful)
				sub = await self.registration.pushManager.subscribe(opts as PushSubscriptionOptionsInit);
			}
			await fetch(SUBSCRIBE_URL, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(serializeSubscription(sub, DEFAULT_TOPICS))
			});
		})()
	);
}) as EventListener);

export {};
