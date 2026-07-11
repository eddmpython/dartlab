import { describe, it, expect } from 'vitest';
import { resolveEndpoint, renderLiveTable, type LiveResult } from './liveData';

describe('resolveEndpoint (계약 검증)', () => {
	it('계약 축을 정규 /pyapi 경로로', () => {
		expect(resolveEndpoint('company/005930/panel/IS')).toBe('/pyapi/company/005930/panel/IS');
		expect(resolveEndpoint('scan/growth')).toBe('/pyapi/scan/growth');
		expect(resolveEndpoint('company/005930/analysis/financial/수익성')).toBe(
			'/pyapi/company/005930/analysis/financial/수익성'
		);
		expect(resolveEndpoint('company/005930/industry')).toBe('/pyapi/company/005930/industry');
	});

	it('선행 슬래시·pyapi 접두 정규화', () => {
		expect(resolveEndpoint('/pyapi/scan/growth')).toBe('/pyapi/scan/growth');
		expect(resolveEndpoint('/scan/growth')).toBe('/pyapi/scan/growth');
	});

	it('허용 쿼리 키(fields·freq·scope)는 통과', () => {
		expect(resolveEndpoint('company/005930/select/IS?fields=매출액,영업이익')).toBe(
			'/pyapi/company/005930/select/IS?fields=매출액,영업이익'
		);
		expect(resolveEndpoint('company/005930/panel/IS?freq=Y')).toBe('/pyapi/company/005930/panel/IS?freq=Y');
	});

	it('계약 밖은 null (임의 verb·경로 이탈 차단)', () => {
		expect(resolveEndpoint('company/005930/foo/IS')).toBeNull();
		expect(resolveEndpoint('company/005930/audit')).toBeNull();
		expect(resolveEndpoint('secret/../etc')).toBeNull();
		expect(resolveEndpoint('company/005930/panel/IS/../../hack')).toBeNull();
		expect(resolveEndpoint('')).toBeNull();
	});

	it('허용 안 된 쿼리 키는 null', () => {
		expect(resolveEndpoint('scan/growth?evil=1')).toBeNull();
	});
});

describe('renderLiveTable (안전 렌더)', () => {
	const table: LiveResult = {
		ok: true,
		status: 200,
		tier: 'browser',
		data: { columns: ['항목', '값'], shape: [1, 2], rows: [{ 항목: '매출', 값: '<script>' }], truncated: false },
	};

	it('셀의 HTML 을 이스케이프한다(신뢰경계)', () => {
		const html = renderLiveTable(table);
		expect(html).toContain('&lt;script&gt;');
		expect(html).not.toContain('<script>');
	});

	it('tier 배지를 낸다', () => {
		expect(renderLiveTable(table)).toContain('ld-tier-browser');
	});

	it('오류는 오류 박스로', () => {
		const err: LiveResult = { ok: false, status: 503, tier: 'browser', error: '엔진 미준비' };
		const html = renderLiveTable(err);
		expect(html).toContain('ld-err');
		expect(html).toContain('엔진 미준비');
	});
});
