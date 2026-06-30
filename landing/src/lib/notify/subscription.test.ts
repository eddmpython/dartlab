import { describe, it, expect } from 'vitest';
import { urlBase64ToUint8Array, serializeSubscription, DEFAULT_TOPICS } from './subscription';

describe('urlBase64ToUint8Array — VAPID 키 디코드', () => {
	it('padding 없는 base64url 복원', () => {
		// "Man" → "TWFu" (padding 0). 길이 3 기대.
		expect(Array.from(urlBase64ToUint8Array('TWFu'))).toEqual([77, 97, 110]);
	});
	it('- _ → + / 매핑 + padding 복원', () => {
		// 바이트 [251,255,191] → b64 "+/+/" → b64url "-_-_"
		expect(Array.from(urlBase64ToUint8Array('-_-_'))).toEqual([251, 255, 191]);
	});
	it('uncompressed VAPID 공개키(65B) 디코드', () => {
		// 0x04 || 32B x || 32B y 형태의 길이만 검증(임의 65B base64url).
		const raw = new Uint8Array(65).fill(7);
		raw[0] = 4;
		let bin = '';
		for (const b of raw) bin += String.fromCharCode(b);
		const b64url = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
		const out = urlBase64ToUint8Array(b64url);
		expect(out.length).toBe(65);
		expect(out[0]).toBe(4);
	});
});

describe('serializeSubscription — 허브 /subscribe body', () => {
	const endpoint = 'https://fcm.googleapis.com/fcm/send/abc123';
	const fakeSub = {
		endpoint,
		toJSON() {
			return { endpoint, keys: { p256dh: 'BPxxPUBKEY', auth: 'AUTHsecret' } };
		}
	} as unknown as PushSubscription;

	it('endpoint·keys·topics 직렬화', () => {
		const payload = serializeSubscription(fakeSub, ['blogPublish']);
		expect(payload.endpoint).toBe('https://fcm.googleapis.com/fcm/send/abc123');
		expect(payload.keys.p256dh).toBe('BPxxPUBKEY');
		expect(payload.keys.auth).toBe('AUTHsecret');
		expect(payload.topics).toEqual(['blogPublish']);
	});

	it('DEFAULT_TOPICS = 전 공개 토픽(허브 TOPIC_ALLOWLIST 와 일치)', () => {
		expect(DEFAULT_TOPICS).toEqual(['blogPublish', 'cardPublish', 'newIpo', 'newOrders']);
	});
});
