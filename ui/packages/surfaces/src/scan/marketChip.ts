/**
 * 거래시장 칩 (KOSPI / KOSDAQ / KONEX / US) · 색·라벨 lookup.
 *
 * KR 노드의 market 은 ecosystem.json (빌드 시 KRX join), US 노드는 edgarNodes 로더가
 * market='US' 를 명시한다. 1급 시장 차원(KR/US)은 marketScope.ts 가 따로 다룬다.
 * 여기는 화면 칩 표기 전용이다.
 */

export type Market = 'KOSPI' | 'KOSDAQ' | 'KONEX' | 'US' | 'UNKNOWN';

export const MARKET_INFO: Record<Market, { color: string; label: string }> = {
	KOSPI: { color: '#3b82f6', label: 'KOSPI' },
	KOSDAQ: { color: '#fbbf24', label: 'KOSDAQ' },
	KONEX: { color: '#94a3b8', label: 'KONEX' },
	// EDGAR. 하위시장(NYSE/NASDAQ)은 아직 원천에 없어 단일 칩으로 둔다.
	US: { color: '#34d399', label: 'US' },
	UNKNOWN: { color: '#475569', label: '·' }
};

/** 노드의 market 필드를 정규화. 등록되지 않은 표기는 'UNKNOWN'.
 *
 * KRX 가 'KOSDAQ GLOBAL' 같은 sub-segment 라벨도 쓰므로 substring 매칭 사용.
 */
export function normalizeMarket(raw: unknown): Market {
	if (typeof raw !== 'string') return 'UNKNOWN';
	const upper = raw.toUpperCase();
	if (upper === 'US' || upper === 'NYSE' || upper === 'NASDAQ' || upper === 'AMEX') return 'US';
	if (upper.includes('KONEX') || upper.includes('코넥스') || upper === 'KNX') return 'KONEX';
	if (upper.includes('KOSDAQ') || upper.includes('코스닥') || upper === 'KSQ') return 'KOSDAQ';
	if (upper.includes('KOSPI') || upper.includes('유가증권') || upper === 'STK') return 'KOSPI';
	return 'UNKNOWN';
}

export function marketColor(raw: unknown): string {
	return MARKET_INFO[normalizeMarket(raw)].color;
}

export function marketLabel(raw: unknown): string {
	return MARKET_INFO[normalizeMarket(raw)].label;
}
