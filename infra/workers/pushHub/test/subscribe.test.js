// /subscribe · DELETE /subscribe — 검증·UPSERT 멱등·CASCADE 삭제.
import { env, createExecutionContext, waitOnExecutionContext } from 'cloudflare:test';
import { beforeEach, describe, expect, it } from 'vitest';
import worker from '../worker.js';

const ORIGIN = 'https://eddmpython.github.io';
const FCM = 'https://fcm.googleapis.com/fcm/send/abc123';
const P256DH = 'BAmvbhdzey9IoM0H2SS7dv71mf1xzQwkYPwv2LlP05971sn0PFAlPdUe0cQVCP_Ppv8jNGp-tNcaTY0Wc72nt6I';
const AUTH = 'vzLGSTnMeNJpr6n6O12Ykw';

async function call(method, body) {
	const ctx = createExecutionContext();
	const req = new Request('https://hub.example/subscribe', {
		method,
		headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
		body: body ? JSON.stringify(body) : undefined
	});
	const res = await worker.fetch(req, env, ctx);
	await waitOnExecutionContext(ctx);
	return res;
}

beforeEach(async () => {
	await env.PUSHHUB_DB.exec('DELETE FROM topicSubs');
	await env.PUSHHUB_DB.exec('DELETE FROM subscriptions');
	await env.PUSHHUB_DB.exec('DELETE FROM sentNonce');
});

describe('POST /subscribe', () => {
	it('유효 구독 → 200 + 행 생성', async () => {
		const res = await call('POST', { endpoint: FCM, keys: { p256dh: P256DH, auth: AUTH }, topics: ['blogPublish'] });
		expect(res.status).toBe(200);
		const sub = await env.PUSHHUB_DB.prepare('SELECT * FROM subscriptions WHERE endpoint=?').bind(FCM).first();
		expect(sub.p256dh).toBe(P256DH);
		const ts = await env.PUSHHUB_DB.prepare('SELECT topic FROM topicSubs WHERE endpoint=?').bind(FCM).all();
		expect(ts.results.map((r) => r.topic)).toEqual(['blogPublish']);
	});

	it('임의 endpoint host → 422 (SSRF 차단)', async () => {
		const res = await call('POST', { endpoint: 'https://evil.example.com/x', keys: { p256dh: P256DH, auth: AUTH }, topics: ['blogPublish'] });
		expect(res.status).toBe(422);
	});

	it('비-base64url 키 → 422', async () => {
		const res = await call('POST', { endpoint: FCM, keys: { p256dh: 'has space!', auth: AUTH }, topics: ['blogPublish'] });
		expect(res.status).toBe(422);
	});

	it('allowlist 외 토픽만 → 422', async () => {
		const res = await call('POST', { endpoint: FCM, keys: { p256dh: P256DH, auth: AUTH }, topics: ['hackTopic'] });
		expect(res.status).toBe(422);
	});

	it('공개 왓처 토픽(newIpo·newOrders) 수용 → 200', async () => {
		const res = await call('POST', { endpoint: FCM, keys: { p256dh: P256DH, auth: AUTH }, topics: ['newIpo', 'newOrders', 'hackTopic'] });
		expect(res.status).toBe(200);
		const ts = await env.PUSHHUB_DB.prepare('SELECT topic FROM topicSubs WHERE endpoint=? ORDER BY topic').bind(FCM).all();
		expect(ts.results.map((r) => r.topic)).toEqual(['newIpo', 'newOrders']); // hackTopic 은 필터됨
	});

	it('재구독 UPSERT 멱등 → 단일 행', async () => {
		await call('POST', { endpoint: FCM, keys: { p256dh: P256DH, auth: AUTH }, topics: ['blogPublish'] });
		await call('POST', { endpoint: FCM, keys: { p256dh: P256DH, auth: AUTH }, topics: ['blogPublish', 'cardPublish'] });
		const n = await env.PUSHHUB_DB.prepare('SELECT COUNT(*) AS c FROM subscriptions').first();
		expect(n.c).toBe(1);
		const ts = await env.PUSHHUB_DB.prepare('SELECT topic FROM topicSubs WHERE endpoint=? ORDER BY topic').bind(FCM).all();
		expect(ts.results.map((r) => r.topic)).toEqual(['blogPublish', 'cardPublish']); // 전량 교체
	});
});

describe('DELETE /subscribe', () => {
	it('전체 삭제 → subscriptions·topicSubs 동시 제거(CASCADE)', async () => {
		await call('POST', { endpoint: FCM, keys: { p256dh: P256DH, auth: AUTH }, topics: ['blogPublish', 'cardPublish'] });
		const res = await call('DELETE', { endpoint: FCM });
		expect(res.status).toBe(200);
		const n = await env.PUSHHUB_DB.prepare('SELECT COUNT(*) AS c FROM subscriptions').first();
		const t = await env.PUSHHUB_DB.prepare('SELECT COUNT(*) AS c FROM topicSubs').first();
		expect(n.c).toBe(0);
		expect(t.c).toBe(0);
	});

	it('부분 해지(topics) → 해당 토픽만 제거', async () => {
		await call('POST', { endpoint: FCM, keys: { p256dh: P256DH, auth: AUTH }, topics: ['blogPublish', 'cardPublish'] });
		await call('DELETE', { endpoint: FCM, topics: ['blogPublish'] });
		const ts = await env.PUSHHUB_DB.prepare('SELECT topic FROM topicSubs WHERE endpoint=?').bind(FCM).all();
		expect(ts.results.map((r) => r.topic)).toEqual(['cardPublish']);
	});
});

describe('OPTIONS /subscribe', () => {
	it('preflight → 204', async () => {
		const res = await call('OPTIONS');
		expect(res.status).toBe(204);
	});
});
