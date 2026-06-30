import { describe, it, expect } from 'vitest';
import { resolveMarket } from '@dartlab/ui-contracts';

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
});
