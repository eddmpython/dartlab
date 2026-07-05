// /send — Bearer 인증·nonce replay·발송 fan-out·404/410 purge. push fetch 는 fetchMock 으로 차단.
import { env, createExecutionContext, waitOnExecutionContext, fetchMock } from 'cloudflare:test';
import { afterEach, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import worker from '../worker.js';

const TOKEN = 'test-send-token';
const FCM_ORIGIN = 'https://fcm.googleapis.com';
const FCM_PATH = '/fcm/send/sub1';
const FCM = FCM_ORIGIN + FCM_PATH;
const P256DH = 'BAmvbhdzey9IoM0H2SS7dv71mf1xzQwkYPwv2LlP05971sn0PFAlPdUe0cQVCP_Ppv8jNGp-tNcaTY0Wc72nt6I';
const AUTH = 'vzLGSTnMeNJpr6n6O12Ykw';

function nowSec() {
	return Math.floor(Date.now() / 1000);
}

async function send({ token = TOKEN, ts = nowSec(), nonce = 'nonce-' + Math.random(), body = null } = {}) {
	const ctx = createExecutionContext();
	const headers = { 'Content-Type': 'application/json' };
	if (token !== null) headers['Authorization'] = `Bearer ${token}`;
	if (ts !== null) headers['X-DL-Ts'] = String(ts);
	if (nonce !== null) headers['X-DL-Nonce'] = nonce;
	const req = new Request('https://hub.example/send', { method: 'POST', headers, body: body ? JSON.stringify(body) : '{}' });
	const res = await worker.fetch(req, env, ctx);
	await waitOnExecutionContext(ctx);
	return res;
}

async function seedSub(endpoint = FCM, topic = 'blogPublish') {
	const now = new Date().toISOString();
	await env.PUSHHUB_DB.prepare('INSERT OR REPLACE INTO subscriptions (endpoint,p256dh,auth,uaClass,createdAt,lastSeenAt) VALUES (?,?,?,?,?,?)')
		.bind(endpoint, P256DH, AUTH, 'other', now, now)
		.run();
	await env.PUSHHUB_DB.prepare('INSERT OR IGNORE INTO topicSubs (endpoint,topic,subscribedAt) VALUES (?,?,?)').bind(endpoint, topic, now).run();
}

const NOTIF = { topic: 'blogPublish', notification: { title: '[새 글] 제목', body: '요약', url: '/blog/foo', tag: 'blog:foo' } };
const ORDERS_NOTIF = { title: '[신규수주] 테스트조선 백로그 확대', body: 'book-to-bill 2.10', url: '/terminal?sym=111111', tag: 'orders:111111' };

async function active({ token = TOKEN, ts = nowSec(), body = null } = {}) {
	const ctx = createExecutionContext();
	const headers = { 'Content-Type': 'application/json' };
	if (token !== null) headers['Authorization'] = `Bearer ${token}`;
	if (ts !== null) headers['X-DL-Ts'] = String(ts);
	const req = new Request('https://hub.example/active', { method: 'POST', headers, body: body ? JSON.stringify(body) : '{}' });
	const res = await worker.fetch(req, env, ctx);
	await waitOnExecutionContext(ctx);
	return res;
}

beforeAll(() => fetchMock.activate());
beforeEach(async () => {
	await env.PUSHHUB_DB.exec('DELETE FROM topicSubs');
	await env.PUSHHUB_DB.exec('DELETE FROM subscriptions');
	await env.PUSHHUB_DB.exec('DELETE FROM sentNonce');
	await env.PUSHHUB_DB.exec('DELETE FROM topicActive');
});
afterEach(() => fetchMock.assertNoPendingInterceptors());

describe('/send 인증', () => {
	it('Bearer 누락 → 401', async () => {
		expect((await send({ token: null, body: NOTIF })).status).toBe(401);
	});
	it('Bearer 오류 → 401', async () => {
		expect((await send({ token: 'wrong', body: NOTIF })).status).toBe(401);
	});
	it('ts 윈도 초과(±300s) → 401', async () => {
		expect((await send({ ts: nowSec() - 999, body: NOTIF })).status).toBe(401);
	});
	it('nonce replay → 409', async () => {
		await seedSub();
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		const first = await send({ nonce: 'fixed-nonce', body: NOTIF });
		expect(first.status).toBe(200);
		const replay = await send({ nonce: 'fixed-nonce', body: NOTIF });
		expect(replay.status).toBe(409); // 멱등 — 같은 nonce 재발송 거절
	});
});

describe('/send 발송', () => {
	it('알 수 없는 토픽 → 422', async () => {
		expect((await send({ body: { topic: 'unknownTopic', notification: NOTIF.notification } })).status).toBe(422);
	});
	it('구독 0 → {sent:0} (no-op)', async () => {
		const res = await send({ body: NOTIF });
		expect(res.status).toBe(200);
		expect((await res.json()).sent).toBe(0);
	});
	it('브로드캐스트 성공(201) → sent:1', async () => {
		await seedSub();
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		const res = await send({ body: NOTIF });
		expect(res.status).toBe(200);
		expect((await res.json()).sent).toBe(1);
	});
	it('410 응답 → purge(구독 삭제)', async () => {
		await seedSub();
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(410, '');
		const res = await send({ body: NOTIF });
		const j = await res.json();
		expect(j.pruned).toBe(1);
		const n = await env.PUSHHUB_DB.prepare('SELECT COUNT(*) AS c FROM subscriptions').first();
		expect(n.c).toBe(0);
	});
	it('구독 0 → nonce 롤백(이후 구독자 배송 가능)', async () => {
		const first = await send({ nonce: 'nce-0sub', body: NOTIF });
		expect((await first.json()).sent).toBe(0);
		// 이후 구독자 생김 → 같은 nonce 재-POST 가 409 아니라 배송돼야(nonce 롤백됨).
		await seedSub();
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		const second = await send({ nonce: 'nce-0sub', body: NOTIF });
		expect(second.status).toBe(200);
		expect((await second.json()).sent).toBe(1);
	});
	it('전건 발송 실패(5xx) → nonce 롤백(다음 cron 재시도)', async () => {
		await seedSub();
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(500, '');
		const first = await send({ nonce: 'nce-fail', body: NOTIF });
		const j1 = await first.json();
		expect(j1.sent).toBe(0);
		expect(j1.failed).toBe(1);
		// nonce 롤백됐으니 재-POST 는 409 아님. 이번엔 201 로 배송 성공.
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		const retry = await send({ nonce: 'nce-fail', body: NOTIF });
		expect(retry.status).toBe(200);
		expect((await retry.json()).sent).toBe(1);
	});
});

describe('/active threshold_cross 커서', () => {
	it('Bearer 누락 → 401', async () => {
		expect((await active({ token: null, body: { topic: 'newOrders', matches: [] } })).status).toBe(401);
	});
	it('알 수 없는 토픽 → 422', async () => {
		expect((await active({ body: { topic: 'nope', matches: [] } })).status).toBe(422);
	});
	it('신규 진입(entered)만 발화', async () => {
		await seedSub(FCM, 'newOrders');
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		const j = await (await active({ body: { topic: 'newOrders', matches: [{ key: 'A', notification: ORDERS_NOTIF }] } })).json();
		expect(j.entered).toBe(1);
		expect(j.sent).toBe(1);
	});
	it('지속 활성은 재발화 안 함(entered 0, fetch 없음)', async () => {
		await seedSub(FCM, 'newOrders');
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		await active({ body: { topic: 'newOrders', matches: [{ key: 'A', notification: ORDERS_NOTIF }] } });
		const j2 = await (await active({ body: { topic: 'newOrders', matches: [{ key: 'A', notification: ORDERS_NOTIF }] } })).json();
		expect(j2.entered).toBe(0); // 이미 활성 → 재발화 없음(fetch 인터셉터 미소비)
		expect(j2.sent).toBe(0);
	});
	it('재크로싱(하락 후 재상승)은 재발화', async () => {
		await seedSub(FCM, 'newOrders');
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		await active({ body: { topic: 'newOrders', matches: [{ key: 'A', notification: ORDERS_NOTIF }] } }); // 최초 진입
		await active({ body: { topic: 'newOrders', matches: [] } }); // A 하락(이탈) → 활성 set 에서 제거
		fetchMock.get(FCM_ORIGIN).intercept({ method: 'POST', path: FCM_PATH }).reply(201, '');
		const j3 = await (await active({ body: { topic: 'newOrders', matches: [{ key: 'A', notification: ORDERS_NOTIF }] } })).json(); // 재크로싱
		expect(j3.entered).toBe(1); // 재진입 발화(sentNonce 영구 dedup 이었다면 미발화였을 것)
		expect(j3.sent).toBe(1);
	});
});
