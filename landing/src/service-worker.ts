/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

/**
 * dartlab Service Worker · 설치형 PWA(앱 셸 오프라인) + 데이터 무간섭.
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

/**
 * 노트북 런타임 캐시. pyodide 커널(CDN 휠 ~32MB)과 dartlab wheel(~21MB)은 노트북을 여는 순간
 * 매번 다시 받는다(실측: 같은 프로필 재방문도 12.2초 -> 11.2초로 거의 그대로. HF wheel 은 서명된
 * xet CDN 으로 302 되어 URL 이 매번 달라 HTTP 캐시가 안 먹는다). 그래서 노트북을 실제로 연 사용자만
 * 이 캐시를 채운다. 크로스오리진 무간섭이라는 SW 설계 불변은 그대로 두고, 아래 좁은 허용목록만 예외다.
 * panel/parquet 같은 데이터 Range 요청은 여전히 절대 가로채지 않는다(경로에 /pyodide/ 가 없다).
 */
const PYODIDE_CACHE = 'dartlab-pyodide-v1';

/** 버전이 URL 에 박혀 불변인 것(cache-first). */
function isImmutableRuntimeAsset(url: URL): boolean {
	return (
		(url.hostname === 'cdn.jsdelivr.net' && url.pathname.startsWith('/pyodide/')) ||
		url.hostname === 'files.pythonhosted.org'
	);
}

/**
 * dartlab wheel(stale-while-revalidate). 파일명에 버전이 있지만 같은 버전으로 재발행하는 운영이 있어
 * cache-first 로 굳히면 옛 wheel 이 영구 고착된다. 캐시를 즉시 주고 뒤에서 갱신한다.
 */
function isDartlabWheel(url: URL): boolean {
	return url.hostname === 'huggingface.co' && url.pathname.includes('/pyodide/') && url.pathname.endsWith('.whl');
}

/**
 * 노트북 데이터 캐시. pyodide 는 parquet 을 통째로 받아 FS 에 쓴다(005930 panel 보드 12.8MB, 실측 약 5.2초).
 * Range 요청(hyparquet 의 부분 읽기)은 여기서 절대 다루지 않는다. 부분 응답을 캐시-우선으로 돌려주면
 * 리더가 깨지고, 첫 방문자의 저장소를 불리지 않겠다는 SW 설계 불변도 그 Range 경로를 두고 한 말이다.
 * 그래서 Range 헤더가 없는 whole-file GET 만, 그것도 dart 데이터 경로만 캐시한다.
 */
const NB_DATA_CACHE = 'dartlab-nbdata-v1';
const NB_DATA_MAX_ENTRIES = 12; // 회사 몇 곳 분량. 넘으면 가장 오래된 항목부터 버린다.
const NB_DATA_MAX_BYTES = 32 * 1024 * 1024;

function isNotebookDataWholeGet(url: URL, req: Request): boolean {
	return (
		url.hostname === 'huggingface.co' &&
		url.pathname.includes('/resolve/main/dart/') &&
		url.pathname.endsWith('.parquet') &&
		!req.headers.has('range')
	);
}

/**
 * Cache.put 은 `redirected: true` 응답을 TypeError 로 거부한다. HF(huggingface.co)는 서명된 xet CDN 으로
 * 302 하므로 wheel·parquet 응답이 전부 redirected 다. 그대로 넣으면 조용히 실패해 캐시가 안 찬다.
 * 본문은 그대로 두고 리다이렉트 표식만 벗긴 사본을 만든다.
 */
function cacheable(res: Response): Response {
	if (!res.redirected) return res;
	return new Response(res.body, { status: res.status, statusText: res.statusText, headers: res.headers });
}

async function putBounded(cache: Cache, req: Request, res: Response): Promise<void> {
	const len = Number(res.headers.get('content-length') || 0);
	if (len > NB_DATA_MAX_BYTES) return;
	await cache.put(req, cacheable(res));
	const keys = await cache.keys();
	if (keys.length > NB_DATA_MAX_ENTRIES) await cache.delete(keys[0]);
}

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
					.filter(
						(k) =>
							k.startsWith('dartlab-scan-') ||
							(k.startsWith('dartlab-shell-') && k !== SHELL) ||
							(k.startsWith('dartlab-pyodide-') && k !== PYODIDE_CACHE) ||
							(k.startsWith('dartlab-nbdata-') && k !== NB_DATA_CACHE)
					)
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

	// 노트북 런타임(pyodide 커널 휠 + dartlab wheel)만 크로스오리진 예외. 데이터(parquet Range)는 제외.
	if (isImmutableRuntimeAsset(url)) {
		event.respondWith(
			(async () => {
				const cache = await caches.open(PYODIDE_CACHE);
				const hit = await cache.match(req);
				if (hit) return hit;
				const res = await fetch(req);
				if (res.ok) event.waitUntil(cache.put(req, cacheable(res.clone())));
				return res;
			})()
		);
		return;
	}
	if (isDartlabWheel(url)) {
		event.respondWith(
			(async () => {
				const cache = await caches.open(PYODIDE_CACHE);
				const hit = await cache.match(req);
				const fresh = fetch(req)
					.then((res) => {
						if (res.ok) cache.put(req, cacheable(res.clone()));
						return res;
					})
					.catch(() => undefined);
				if (hit) {
					event.waitUntil(fresh); // 뒤에서 갱신(같은 버전 재발행 대응)
					return hit;
				}
				const res = await fresh;
				return res ?? Response.error();
			})()
		);
		return;
	}

	if (isNotebookDataWholeGet(url, req)) {
		event.respondWith(
			(async () => {
				const cache = await caches.open(NB_DATA_CACHE);
				const hit = await cache.match(req);
				if (hit) return hit;
				const res = await fetch(req);
				if (res.ok) event.waitUntil(putBounded(cache, req, res.clone()));
				return res;
			})()
		);
		return;
	}

	// ⛔ 그 외 크로스오리진(HF parquet Range·프록시·뉴스 등 데이터) · SW 무간섭. 네트워크 그대로.
	if (url.origin !== self.location.origin) return;

	// 앱 셸 자산(해시 불변) · 캐시 우선.
	if (ASSET_SET.has(url.pathname)) {
		event.respondWith(
			(async () => {
				const cached = await caches.match(req);
				return cached ?? fetch(req);
			})()
		);
		return;
	}

	// 내비게이션(HTML) · 네트워크 우선, 성공분 캐시, 오프라인이면 캐시 폴백.
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
						new Response('오프라인 · 연결을 확인하세요.', {
							status: 503,
							headers: { 'Content-Type': 'text/html; charset=utf-8' }
						})
					);
				}
			})()
		);
		return;
	}

	// 그 외 same-origin GET · 기본 네트워크(가로채지 않음).
});

// ── Web Push 수신 3 리스너 (P1) · 기존 셸 캐시 동작과 독립 ──────────────
// 설계: mainPlan/watcher-notify-platform/07-p1-client-receiving.md
const ICON = `${import.meta.env.BASE_URL}icon-192.png`; // BASE_URL='/dartlab/' (절대경로 404 가드)

interface PushPayload {
	title?: string;
	body?: string;
	url?: string;
	tag?: string;
}

// push · aes128gcm 복호된 payload(notification 서브객체) 렌더. 항상 showNotification(미표시=userVisibleOnly 위반).
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

// notificationclick · same-origin 창 있으면 focus+navigate, 없으면 openWindow. 목적지=검증된 상대경로.
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

// pushsubscriptionchange · 만료/회전 시 재구독 + /subscribe 재등록. 구 endpoint 는 /send 404/410 자가청소.
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
