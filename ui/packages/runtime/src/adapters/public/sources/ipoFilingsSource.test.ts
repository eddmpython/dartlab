// ipoFilingsSource · classifyIpo 3조건 미러 + 발행사 그룹핑 회귀. 케이스는 워커 /ipo-filings 실측
// (2026-07, corp_cls=E + C001 92일 29행)에서 나온 report_nm 형태 그대로.
import { describe, expect, it } from 'vitest';
import { classifyIpoMeta, groupIpoFilings, type IpoWorkerRow } from './ipoFilingsSource';

describe('classifyIpoMeta (정본 classifyIpo 미러)', () => {
	it('3조건 동시 = IPO', () => {
		expect(classifyIpoMeta('증권신고서(지분증권)', 'E', '', '기도산업').isIpo).toBe(true);
		expect(classifyIpoMeta('[기재정정]증권신고서(지분증권)', 'E', '', '레메디').isIpo).toBe(true);
	});
	it('펀드명 속 (지분증권) 오매칭 차단 · 첫 괄호 subtype', () => {
		expect(classifyIpoMeta('증권신고서(집합투자증권-회사형)(존속기한(지분증권))', 'E', '', '운용사').isIpo).toBe(false);
	});
	it('상장사 유상증자(Y/K·stock_code 보유) = 비-IPO', () => {
		expect(classifyIpoMeta('증권신고서(지분증권)', 'Y', '005930', '삼성전자').isIpo).toBe(false);
		expect(classifyIpoMeta('증권신고서(지분증권)', 'E', '123456', '어딘가').isIpo).toBe(false);
	});
	it('투자설명서·발행실적보고서(신고서 아님) = 비대상', () => {
		expect(classifyIpoMeta('[기재정정]투자설명서', 'E', '', '레메디').isIpo).toBe(false);
		expect(classifyIpoMeta('증권발행실적보고서', 'E', '', '레몬헬스케어').isIpo).toBe(false);
	});
	it('스팩은 corpName 으로 · notice 분리', () => {
		expect(classifyIpoMeta('증권신고서(지분증권)', 'E', '', '한국제나인호기업인수목적').isSpac).toBe(true);
		expect(classifyIpoMeta('효력발생안내( 2026.6.26. 지분증권)', 'E', '', '기도산업').kind).toBe('notice');
	});
});

const row = (rceptNo: string, rceptDate: string, corpCode: string, corpName: string, reportNm: string): IpoWorkerRow => ({
	rceptNo,
	rceptDate,
	corpCode,
	corpCls: 'E',
	stockCode: '',
	corpName,
	reportNm
});

describe('groupIpoFilings (발행사별 최신 FULL + 확정 doc)', () => {
	it('기재정정 여러 판 중 최신 FULL 1건 + 발행조건확정 병합 rcept', () => {
		const rows: IpoWorkerRow[] = [
			row('20260618000100', '2026-06-18', 'C1', '레몬헬스케어', '투자설명서'),
			row('20260623000200', '2026-06-23', 'C1', '레몬헬스케어', '[발행조건확정]증권신고서(지분증권)'),
			row('20260612000300', '2026-06-12', 'C1', '레몬헬스케어', '[기재정정]증권신고서(지분증권)'),
			row('20260508000400', '2026-05-08', 'C1', '레몬헬스케어', '증권신고서(지분증권)'),
			row('20260626000500', '2026-06-26', 'C2', '기도산업', '증권신고서(지분증권)')
		];
		const out = groupIpoFilings(rows);
		expect(out).toHaveLength(2);
		const lemon = out.find((f) => f.corpCode === 'C1');
		expect(lemon?.rceptNo).toBe('20260612000300'); // 확정 doc 아닌 최신 FULL
		expect(lemon?.corrected).toBe(true);
		expect(lemon?.confirmationRceptNo).toBe('20260623000200');
		const kido = out.find((f) => f.corpCode === 'C2');
		expect(kido?.confirmationRceptNo).toBeNull();
		expect(kido?.url).toContain('20260626000500');
	});
	it('FULL 이 윈도우 밖(확정 doc 만 잔존)이면 발행사 제외 · 정렬 = 접수일 desc', () => {
		const rows: IpoWorkerRow[] = [
			row('20260623000200', '2026-06-23', 'C1', '레몬헬스케어', '[발행조건확정]증권신고서(지분증권)'),
			row('20260624000100', '2026-06-24', 'C3', '딜리셔스', '증권신고서(지분증권)'),
			row('20260626000500', '2026-06-26', 'C2', '기도산업', '증권신고서(지분증권)')
		];
		const out = groupIpoFilings(rows);
		expect(out.map((f) => f.corpName)).toEqual(['기도산업', '딜리셔스']);
	});
});
