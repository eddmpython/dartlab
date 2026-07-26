// ipoReportSource · HF dart/ipo/reports.parquet 직독(rcept 필터 + reportJson JSON.parse) 회귀.
// DataCore.requestParquetRows 를 스텁해 순수 매핑(round-trip·미존재 null·손상 null)만 검증.
import { describe, expect, it } from 'vitest';
import { loadIpoReport } from './ipoReportSource';
import type { DataCore } from '../../../data/fetch/request';

const REPORT = {
	title: '기도산업 공모분석',
	summary: { priceBand: [24800, 28400], peerPer: 10.01 },
	sections: [{ title: '공모 개요', badge: '✓ 검증', rows: [['희망공모가', '24,800원 ~ 28,400원']] }],
	markdown: '# 기도산업 공모분석'
};

function fakeCore(rows: Record<string, unknown>[]): DataCore {
	return {
		requestParquetRows: async () => rows
	} as unknown as DataCore;
}

describe('loadIpoReport', () => {
	it('rcept 매칭 행의 reportJson 을 IpoReport 로 파싱', async () => {
		const core = fakeCore([{ rcept: '20260626000715', reportJson: JSON.stringify(REPORT) }]);
		const r = await loadIpoReport(core, '20260626000715');
		expect(r?.title).toBe('기도산업 공모분석');
		expect(r?.sections[0]?.title).toBe('공모 개요');
		expect(r?.summary?.priceBand).toEqual([24800, 28400]);
	});

	it('미베이크(행 없음) = null', async () => {
		const core = fakeCore([]);
		expect(await loadIpoReport(core, '99999999')).toBeNull();
	});

	it('빈 rcept = null (read 생략)', async () => {
		const core = fakeCore([{ rcept: 'x', reportJson: JSON.stringify(REPORT) }]);
		expect(await loadIpoReport(core, '  ')).toBeNull();
	});

	it('손상 JSON = null (throw 아님)', async () => {
		const core = fakeCore([{ rcept: '20260626000715', reportJson: '{broken' }]);
		expect(await loadIpoReport(core, '20260626000715')).toBeNull();
	});

	it('read 실패(throw) = null', async () => {
		const core = {
			requestParquetRows: async () => {
				throw new Error('network');
			}
		} as unknown as DataCore;
		expect(await loadIpoReport(core, '20260626000715')).toBeNull();
	});
});
