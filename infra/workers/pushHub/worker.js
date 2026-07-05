// dartlab Push Hub Worker — 구독 저장 + Web Push 발송만 한다(저장+발송, 크롤·판정 0).
//
// 원칙(런타임-SSOT 정합):
// - 감지 지능은 dartlab(gather·scan SSOT)에 산다. 허브는 구독 보관 + VAPID 서명 + push 발송뿐.
// - 라우트 3개: POST/DELETE /subscribe(무인증 공개) · POST /send(러너 전용 Bearer+nonce).
// - 개인조건·종목·user_id 컬럼 영구 0(endpoint+종목=재식별 surface). 개인화는 로컬 소유.
// - 암호화 = 순수 WebCrypto(RFC 8291 aes128gcm + RFC 8292 VAPID ES256). npm 의존 0.
// 설계 정본: mainPlan/watcher-notify-platform/06-p1-hub-worker.md

// ── 상수 ───────────────────────────────────────────────────────────
// 발행(blog·card) + 공개 왓처 토픽(IPO 신규상장·신규수주). 개인조건 0 — 전부 무차별 브로드캐스트.
const TOPIC_ALLOWLIST = new Set(['blogPublish', 'cardPublish', 'newIpo', 'newOrders']);
const PUSH_HOSTS = ['fcm.googleapis.com', 'web.push.apple.com']; // + *.push.services.mozilla.com (suffix)
const MOZILLA_SUFFIX = '.push.services.mozilla.com';
const B64URL_RE = /^[A-Za-z0-9_-]+={0,2}$/; // padding 허용(일부 브라우저 키가 padding 포함)
const NONCE_WINDOW_S = 300;
const JWT_TTL_S = 12 * 3600;
const PUSH_TTL_S = 4 * 24 * 3600;
const SEND_CHUNK = 20; // Promise.allSettled fan-out 청크(직렬 금지 — Worker wall-clock 한도)

// ── base64url ──────────────────────────────────────────────────────
const enc = new TextEncoder();

function b64urlToBytes(s) {
	const pad = s.length % 4 === 0 ? '' : '='.repeat(4 - (s.length % 4));
	const b64 = (s + pad).replace(/-/g, '+').replace(/_/g, '/');
	const bin = atob(b64);
	const out = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
	return out;
}

function bytesToB64url(bytes) {
	let bin = '';
	const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
	for (let i = 0; i < arr.length; i++) bin += String.fromCharCode(arr[i]);
	return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlJson(obj) {
	return bytesToB64url(enc.encode(JSON.stringify(obj)));
}

function nowSec() {
	return Math.floor(Date.now() / 1000);
}

// 상수시간 문자열 비교(Bearer 토큰 타이밍 누설 차단).
function timingSafeEqual(a, b) {
	const ba = enc.encode(String(a ?? ''));
	const bb = enc.encode(String(b ?? ''));
	if (ba.length !== bb.length) return false;
	let diff = 0;
	for (let i = 0; i < ba.length; i++) diff |= ba[i] ^ bb[i];
	return diff === 0;
}

// ── CORS (siteSignals 형판) ────────────────────────────────────────
function allowedOrigins(env) {
	return String(env.ALLOW_ORIGIN || '')
		.split(',')
		.map((o) => o.trim())
		.filter(Boolean);
}

function corsHeaders(req, env) {
	const origins = allowedOrigins(env);
	const origin = req.headers.get('Origin');
	const allow = origins.length && origin && origins.includes(origin) ? origin : origins[0] || '*';
	return {
		'Access-Control-Allow-Origin': allow,
		'Access-Control-Allow-Methods': 'POST, DELETE, OPTIONS',
		'Access-Control-Allow-Headers': 'Content-Type',
		Vary: 'Origin'
	};
}

function isEndpointAllowed(endpoint) {
	let host;
	try {
		host = new URL(endpoint).host;
	} catch {
		return false;
	}
	return PUSH_HOSTS.includes(host) || host.endsWith(MOZILLA_SUFFIX);
}

function isoNow() {
	return new Date().toISOString();
}

// ── VAPID JWT (RFC 8292, ES256 — crypto.subtle, npm 0) ─────────────
// 비밀키 = pkcs8 DER 의 base64url. 서명 = ECDSA P-256/SHA-256 → IEEE P1363 raw 64B = JWS ES256 그대로(DER 변환 0).
async function importVapidPrivKey(env) {
	const der = b64urlToBytes(env.VAPID_PRIVATE_KEY);
	return crypto.subtle.importKey('pkcs8', der, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
}

async function makeVapidJwt(audOrigin, privKey, env) {
	const header = b64urlJson({ typ: 'JWT', alg: 'ES256' });
	const payload = b64urlJson({ aud: audOrigin, exp: nowSec() + JWT_TTL_S, sub: env.VAPID_SUBJECT });
	const input = `${header}.${payload}`;
	const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, privKey, enc.encode(input));
	return `${input}.${bytesToB64url(sig)}`;
}

// ── aes128gcm 본문 암호화 (RFC 8291 §3.4, 2단 HKDF — 참고구현 web-push encrypt 포팅) ──
async function hmacSha256(keyBytes, msgBytes) {
	const key = await crypto.subtle.importKey('raw', keyBytes, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
	return new Uint8Array(await crypto.subtle.sign('HMAC', key, msgBytes));
}

function concatBytes(...parts) {
	const total = parts.reduce((n, p) => n + p.length, 0);
	const out = new Uint8Array(total);
	let off = 0;
	for (const p of parts) {
		out.set(p, off);
		off += p.length;
	}
	return out;
}

// plaintext(Uint8Array), uaPub(p256dh raw 65B), authSecret(auth 16B) → aes128gcm body(Uint8Array).
async function encryptPayload(plaintext, uaPub, authSecret) {
	const asKeys = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
	const uaKey = await crypto.subtle.importKey('raw', uaPub, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
	const ecdh = new Uint8Array(await crypto.subtle.deriveBits({ name: 'ECDH', public: uaKey }, asKeys.privateKey, 256));
	const asPub = new Uint8Array(await crypto.subtle.exportKey('raw', asKeys.publicKey)); // 65B
	const salt = crypto.getRandomValues(new Uint8Array(16));

	// 1단계: ECDH + auth → IKM (RFC 8291)
	const prkKey = await hmacSha256(authSecret, ecdh);
	const keyInfo = concatBytes(enc.encode('WebPush: info'), new Uint8Array([0]), uaPub, asPub);
	const ikm = (await hmacSha256(prkKey, concatBytes(keyInfo, new Uint8Array([1])))).slice(0, 32);

	// 2단계: salt → CEK·NONCE (RFC 8188 aes128gcm)
	const prk = await hmacSha256(salt, ikm);
	const cek = (await hmacSha256(prk, concatBytes(enc.encode('Content-Encoding: aes128gcm'), new Uint8Array([0, 1])))).slice(0, 16);
	const nonce = (await hmacSha256(prk, concatBytes(enc.encode('Content-Encoding: nonce'), new Uint8Array([0, 1])))).slice(0, 12);

	const cekKey = await crypto.subtle.importKey('raw', cek, { name: 'AES-GCM' }, false, ['encrypt']);
	const record = concatBytes(plaintext, new Uint8Array([2])); // 0x02 = 단일·마지막 record delimiter
	const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce, tagLength: 128 }, cekKey, record));

	// RFC 8188 헤더: salt(16) | rs(4=4096) | idlen(1=65) | keyid(as_pub 65) | ciphertext
	const rs = new Uint8Array([0, 0, 0x10, 0]); // uint32 big-endian 4096
	return concatBytes(salt, rs, new Uint8Array([65]), asPub, ct);
}

// ── /subscribe ─────────────────────────────────────────────────────
async function handleSubscribe(req, env, cors) {
	let body;
	try {
		body = await req.json();
	} catch {
		return new Response('bad json', { status: 400, headers: cors });
	}
	const endpoint = String(body?.endpoint ?? '');
	const p256dh = String(body?.keys?.p256dh ?? '');
	const auth = String(body?.keys?.auth ?? '');
	const topics = Array.isArray(body?.topics) ? body.topics.map(String) : [];

	if (!isEndpointAllowed(endpoint)) return new Response('endpoint not allowed', { status: 422, headers: cors });
	if (!B64URL_RE.test(p256dh) || !B64URL_RE.test(auth)) return new Response('bad keys', { status: 422, headers: cors });
	const topicSet = [...new Set(topics)].filter((t) => TOPIC_ALLOWLIST.has(t));
	if (!topicSet.length) return new Response('no valid topic', { status: 422, headers: cors });

	const ts = isoNow();
	const stmts = [
		env.PUSHHUB_DB.prepare(
			`INSERT INTO subscriptions (endpoint, p256dh, auth, uaClass, createdAt, lastSeenAt)
			 VALUES (?, ?, ?, 'other', ?, ?)
			 ON CONFLICT(endpoint) DO UPDATE SET p256dh=excluded.p256dh, auth=excluded.auth, lastSeenAt=excluded.lastSeenAt`
		).bind(endpoint, p256dh, auth, ts, ts),
		// 토픽 전량 교체(차집합 동기화) — 멱등.
		env.PUSHHUB_DB.prepare(`DELETE FROM topicSubs WHERE endpoint=?`).bind(endpoint),
		...topicSet.map((t) =>
			env.PUSHHUB_DB.prepare(`INSERT OR IGNORE INTO topicSubs (endpoint, topic, subscribedAt) VALUES (?, ?, ?)`).bind(endpoint, t, ts)
		)
	];
	try {
		await env.PUSHHUB_DB.batch(stmts);
	} catch {
		return new Response('db error', { status: 502, headers: cors });
	}
	return new Response(JSON.stringify({ ok: true, topics: topicSet }), {
		headers: { ...cors, 'Content-Type': 'application/json' }
	});
}

// ── DELETE /subscribe ──────────────────────────────────────────────
async function handleUnsubscribe(req, env, cors) {
	let body;
	try {
		body = await req.json();
	} catch {
		return new Response('bad json', { status: 400, headers: cors });
	}
	const endpoint = String(body?.endpoint ?? '');
	if (!endpoint) return new Response('no endpoint', { status: 422, headers: cors });
	const topics = Array.isArray(body?.topics) ? body.topics.map(String) : null;

	try {
		if (topics && topics.length) {
			// 부분해지 — 지정 토픽만. 남은 토픽 0이면 정리 위해 구독행도 삭제.
			await env.PUSHHUB_DB.batch(topics.map((t) => env.PUSHHUB_DB.prepare(`DELETE FROM topicSubs WHERE endpoint=? AND topic=?`).bind(endpoint, t)));
			const left = await env.PUSHHUB_DB.prepare(`SELECT COUNT(*) AS n FROM topicSubs WHERE endpoint=?`).bind(endpoint).first();
			if (!left || left.n === 0) {
				await env.PUSHHUB_DB.prepare(`DELETE FROM subscriptions WHERE endpoint=?`).bind(endpoint).run(); // CASCADE topicSubs
			}
		} else {
			// 전체삭제 — subscriptions 1행(FK ON DELETE CASCADE 가 topicSubs 정리).
			await env.PUSHHUB_DB.prepare(`DELETE FROM subscriptions WHERE endpoint=?`).bind(endpoint).run();
		}
	} catch {
		return new Response('db error', { status: 502, headers: cors });
	}
	return new Response(JSON.stringify({ ok: true }), { headers: { ...cors, 'Content-Type': 'application/json' } });
}

// ── /send (러너 전용 — Bearer + nonce, CORS 없음) ──────────────────
async function handleSend(req, env) {
	const auth = req.headers.get('Authorization') || '';
	const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
	if (!env.PUSHHUB_SEND_TOKEN || !timingSafeEqual(token, env.PUSHHUB_SEND_TOKEN)) {
		return new Response('unauthorized', { status: 401 });
	}
	const ts = parseInt(req.headers.get('X-DL-Ts') || '0', 10);
	const nonce = req.headers.get('X-DL-Nonce') || '';
	if (!nonce || !Number.isFinite(ts) || Math.abs(nowSec() - ts) > NONCE_WINDOW_S) {
		return new Response('stale or missing nonce', { status: 401 });
	}
	// nonce 멱등 — 같은 (topic,slug) 재발송은 409(중복 거절). sentNonce = 동시에 last-seen 커서.
	let inserted;
	try {
		inserted = await env.PUSHHUB_DB.prepare(`INSERT OR IGNORE INTO sentNonce (nonce, ts) VALUES (?, ?)`).bind(nonce, ts).run();
	} catch {
		return new Response('db error', { status: 502 });
	}
	if (!inserted?.meta?.changes) return new Response('replay', { status: 409 });

	let body;
	try {
		body = await req.json();
	} catch {
		return new Response('bad json', { status: 400 });
	}
	const notification = body?.notification;
	if (!notification || typeof notification !== 'object') return new Response('no notification', { status: 422 });

	// 대상 조회 — topic 브로드캐스트(JOIN 1회) 또는 endpoints[] 타겟.
	let subs;
	try {
		if (Array.isArray(body?.endpoints) && body.endpoints.length) {
			const marks = body.endpoints.map(() => '?').join(',');
			subs = (await env.PUSHHUB_DB.prepare(`SELECT endpoint, p256dh, auth FROM subscriptions WHERE endpoint IN (${marks})`).bind(...body.endpoints).all()).results;
		} else {
			const topic = String(body?.topic ?? '');
			if (!TOPIC_ALLOWLIST.has(topic)) return new Response('bad topic', { status: 422 });
			subs = (
				await env.PUSHHUB_DB.prepare(
					`SELECT s.endpoint, s.p256dh, s.auth FROM topicSubs t JOIN subscriptions s ON s.endpoint=t.endpoint WHERE t.topic=?`
				)
					.bind(topic)
					.all()
			).results;
		}
	} catch {
		return new Response('db error', { status: 502 });
	}

	if (!subs.length) {
		// 구독자 0 = 아직 아무도 못 받음. nonce 롤백해 이후 구독자가 in-window 매치를 받게 한다(영구 소실 방지).
		try { await env.PUSHHUB_DB.prepare(`DELETE FROM sentNonce WHERE nonce=?`).bind(nonce).run(); } catch {}
		return new Response(JSON.stringify({ sent: 0, pruned: 0, failed: 0 }), { headers: { 'Content-Type': 'application/json' } });
	}

	const plaintext = enc.encode(JSON.stringify(notification)); // 평문 = notification 서브객체만(봉투 아님)
	const privKey = await importVapidPrivKey(env);
	const jwtByOrigin = {};
	const vapidK = env.VAPID_PUBLIC_KEY;

	async function sendOne(sub) {
		const audOrigin = new URL(sub.endpoint).origin;
		if (!jwtByOrigin[audOrigin]) jwtByOrigin[audOrigin] = await makeVapidJwt(audOrigin, privKey, env);
		const cipher = await encryptPayload(plaintext, b64urlToBytes(sub.p256dh), b64urlToBytes(sub.auth));
		const res = await fetch(sub.endpoint, {
			method: 'POST',
			headers: {
				'Content-Encoding': 'aes128gcm',
				'Content-Type': 'application/octet-stream',
				TTL: String(PUSH_TTL_S),
				Urgency: 'normal',
				Authorization: `vapid t=${jwtByOrigin[audOrigin]}, k=${vapidK}`
			},
			body: cipher
		});
		return { endpoint: sub.endpoint, status: res.status };
	}

	let sent = 0;
	let failed = 0;
	const toPurge = [];
	for (let i = 0; i < subs.length; i += SEND_CHUNK) {
		const chunk = subs.slice(i, i + SEND_CHUNK);
		const settled = await Promise.allSettled(chunk.map((s) => sendOne(s)));
		for (let j = 0; j < settled.length; j++) {
			const r = settled[j];
			if (r.status === 'fulfilled') {
				const st = r.value.status;
				if (st >= 200 && st < 300) sent++;
				else if (st === 404 || st === 410) toPurge.push(r.value.endpoint);
				else failed++; // 429/5xx 보존(재시도 가능)
			} else {
				failed++;
			}
		}
	}

	let pruned = 0;
	if (toPurge.length) {
		try {
			const marks = toPurge.map(() => '?').join(',');
			await env.PUSHHUB_DB.prepare(`DELETE FROM subscriptions WHERE endpoint IN (${marks})`).bind(...toPurge).run(); // CASCADE topicSubs
			pruned = toPurge.length; // 의미 = purge 한 endpoint 수(meta.changes 는 CASCADE 행까지 세므로 부정확)
		} catch {
			/* purge 실패는 비치명 — 다음 발송에서 재시도 */
		}
	}

	// 전건 실패(sent==0 && failed>0) = 일시 장애(FCM 5xx/429). nonce 롤백해 다음 cron 재시도(영구 미배송 방지).
	// 부분 성공(sent>0)은 nonce 유지(배송된 구독자 재발송 스팸 방지). failed 는 body 로 러너에 노출.
	if (sent === 0 && failed > 0) {
		try { await env.PUSHHUB_DB.prepare(`DELETE FROM sentNonce WHERE nonce=?`).bind(nonce).run(); } catch {}
	}
	return new Response(JSON.stringify({ sent, pruned, failed }), { headers: { 'Content-Type': 'application/json' } });
}

// ── 디스패치 ───────────────────────────────────────────────────────
export default {
	async fetch(req, env) {
		const url = new URL(req.url);
		const path = url.pathname;

		if (path === '/send') {
			if (req.method !== 'POST') return new Response('method not allowed', { status: 405 });
			if (!env.PUSHHUB_DB) return new Response('db not configured', { status: 503 });
			return handleSend(req, env);
		}

		if (path === '/subscribe') {
			const cors = corsHeaders(req, env);
			if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
			if (!env.PUSHHUB_DB) return new Response('db not configured', { status: 503, headers: cors });
			if (req.method === 'POST') return handleSubscribe(req, env, cors);
			if (req.method === 'DELETE') return handleUnsubscribe(req, env, cors);
			return new Response('method not allowed', { status: 405, headers: cors });
		}

		return new Response('not found', { status: 404 });
	}
};

// 테스트 하네스(vitest-pool-workers)에서 순수 헬퍼 단위검증용 — 발송 경로 외 부수효과 0.
export const __test = { b64urlToBytes, bytesToB64url, isEndpointAllowed, timingSafeEqual, encryptPayload, makeVapidJwt, importVapidPrivKey };
