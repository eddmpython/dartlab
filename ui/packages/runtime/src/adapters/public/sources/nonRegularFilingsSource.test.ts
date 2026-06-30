// 시장 공시 피드 source 단위 테스트 · fake DataCore(requestParquetWholeFile 주입)로 네트워크 없이
// 정규화 검증: dedup(rceptNo)·정기보고서 제외·필드 매핑·corpName·url·trim·bake 순서 보존.
import { describe, it, expect } from 'vitest';
import { loadMarketFeed } from './nonRegularFilingsSource';
import type { DataCore } from '../../../data/fetch/request';

// market_recent.parquet 한 행(메타 6컬럼) shape
function row(o: Partial<Record<string, unknown>>): Record<string, unknown> {
	return { stock_code: '', corp_name: '', rcept_dt: '', report_nm: '', rcept_no: '', flr_nm: '', ...o };
}

// rows 를 그대로 돌려주는 fake core · loadMarketFeed 는 requestParquetWholeFile 만 호출.
function fakeCore(rows: Record<string, unknown>[] | null): DataCore {
	return {
		requestParquetWholeFile: async () => rows
	} as unknown as DataCore;
}

describe('loadMarketFeed', () => {
	it('null(파일 미존재) → 빈 배열', async () => {
		expect(await loadMarketFeed(fakeCore(null))).toEqual([]);
	});

	it('필드 매핑·corpName·url·trim', async () => {
		const out = await loadMarketFeed(
			fakeCore([
				row({
					stock_code: '005930',
					corp_name: '삼성전자',
					rcept_dt: '20260612',
					report_nm: '  주식등의대량보유상황보고서  ',
					rcept_no: '20260612000123',
					flr_nm: '국민연금공단'
				})
			])
		);
		expect(out).toHaveLength(1);
		expect(out[0]).toEqual({
			rceptNo: '20260612000123',
			rceptDate: '2026-06-12',
			stockCode: '005930',
			corpName: '삼성전자',
			reportNm: '주식등의대량보유상황보고서',
			filer: '국민연금공단',
			url: 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260612000123'
		});
	});

	it('rceptNo 중복 제거(keep-first) + 정기보고서·빈 코드 제외, bake 순서 보존', async () => {
		const out = await loadMarketFeed(
			fakeCore([
				row({ stock_code: '000660', corp_name: 'SK하이닉스', rcept_dt: '20260610', report_nm: '최대주주변경', rcept_no: 'A' }),
				row({ stock_code: '000660', corp_name: 'SK하이닉스', rcept_dt: '20260610', report_nm: '최대주주변경(중복)', rcept_no: 'A' }), // dedup
				row({ stock_code: '005930', corp_name: '삼성전자', rcept_dt: '20260331', report_nm: '사업보고서', rcept_no: 'B' }), // 정기 제외
				row({ stock_code: '', corp_name: '', rcept_dt: '20260609', report_nm: '자기주식취득결정', rcept_no: 'C' }), // 빈 코드 제외
				row({ stock_code: '035420', corp_name: 'NAVER', rcept_dt: '20260608', report_nm: '단일판매ㆍ공급계약체결', rcept_no: 'D' })
			])
		);
		expect(out.map((f) => f.rceptNo)).toEqual(['A', 'D']); // 입력(bake rcept_dt desc) 순서 보존, 재정렬 없음
		expect(out[0]?.reportNm).toBe('최대주주변경'); // keep-first
	});
});
