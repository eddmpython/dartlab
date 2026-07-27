import { describe, it, expect } from 'vitest';
import { isKrStockCode, normalizeKrCode, resolveMarket } from '@dartlab/ui-contracts';

// S1-L2.1 게이트 · priority-비대칭 식별자 라우팅. 핵심: 6자리 숫자는 KR코드 ∩ US CIK
// 모양 충돌이라 자동판정은 KR(모호 플래그), US CIK 는 명시 market 필요.
describe('resolveMarket', () => {
	it('KR 6자리 종목코드 → KR(모호 플래그)', () => {
		expect(resolveMarket('005930')).toMatchObject({ market: 'KR', code: '005930', ambiguous: true });
	});

	it('US 티커 → US (대문자 정규화)', () => {
		expect(resolveMarket('aapl')).toMatchObject({ market: 'US', ticker: 'AAPL' });
	});

	it('6자리 숫자 CIK(320193) 자동판정은 KR · US 는 명시 필요', () => {
		const auto = resolveMarket('320193');
		expect(auto.market).toBe('KR');
		expect(auto.ambiguous).toBe(true);
		expect(resolveMarket('320193', { market: 'US' })).toMatchObject({ market: 'US', cik: '320193' });
	});

	it('비-6자리 숫자(10자리 CIK) → US CIK (KR 코드는 6자리뿐)', () => {
		expect(resolveMarket('0000320193')).toMatchObject({ market: 'US', cik: '0000320193' });
	});

	it('명시 market override 1순위', () => {
		expect(resolveMarket('AAPL', { market: 'US' })).toMatchObject({ market: 'US', ticker: 'AAPL' });
		expect(resolveMarket('005930', { market: 'KR' })).toMatchObject({ market: 'KR', code: '005930' });
		// override='KR' 은 모호 플래그 없음(명시했으므로)
		expect(resolveMarket('005930', { market: 'KR' }).ambiguous).toBeUndefined();
	});

	it('클래스 접미 티커(BRK.B) → US', () => {
		expect(resolveMarket('BRK.B')).toMatchObject({ market: 'US', ticker: 'BRK.B' });
	});

	it('market 미지정 빈/공백 → KR 기본(무회귀 불변식)', () => {
		expect(resolveMarket('').market).toBe('KR');
		expect(resolveMarket('   ').market).toBe('KR');
	});

	// 회귀 가드: KRX 영숫자 단축코드. 옛 `/^\d{6}$/` 는 이들을 US 티커로 오분류해
	// 공시뷰어가 edgar/panel/{code}.parquet 404 로 죽었다(에스엔시스 0008Z0).
	it('KRX 영숫자 코드 → KR (모호 아님)', () => {
		expect(resolveMarket('0008Z0')).toMatchObject({ market: 'KR', code: '0008Z0' }); // 에스엔시스(코스닥)
		expect(resolveMarket('0008Z0').ambiguous).toBeUndefined();
		expect(resolveMarket('0126Z0').market).toBe('KR'); // 삼성에피스홀딩스
		expect(resolveMarket('03473K').market).toBe('KR'); // SK우
		expect(resolveMarket('00104K').market).toBe('KR'); // CJ4우(전환)
	});

	it('영숫자 코드 소문자 입력 → 대문자 정규화', () => {
		expect(resolveMarket('0008z0')).toMatchObject({ market: 'KR', code: '0008Z0' });
	});

	it('US 티커는 숫자로 시작하지 않아 KRX 코드 모양과 충돌하지 않는다', () => {
		expect(resolveMarket('AAPL').market).toBe('US');
		expect(resolveMarket('GOOGL').market).toBe('US'); // 5자 티커
		expect(resolveMarket('BRK.B').market).toBe('US');
	});
});

describe('isKrStockCode', () => {
	it('KRX 단축코드 모양만 참', () => {
		expect(isKrStockCode('005930')).toBe(true);
		expect(isKrStockCode('0008Z0')).toBe(true);
		expect(isKrStockCode('0008z0')).toBe(true); // 대소문자 무관
		expect(isKrStockCode('AAPL')).toBe(false);
		expect(isKrStockCode('Z00080')).toBe(false); // 첫 자리는 숫자여야 한다
		expect(isKrStockCode('00593')).toBe(false); // 5자
		expect(isKrStockCode('0059300')).toBe(false); // 7자
		expect(isKrStockCode(undefined)).toBe(false);
	});
});

describe('normalizeKrCode', () => {
	it('공백 제거 + 대문자 · 숫자 코드는 무변', () => {
		expect(normalizeKrCode(' 0008z0 ')).toBe('0008Z0');
		expect(normalizeKrCode('005930')).toBe('005930');
	});
});
