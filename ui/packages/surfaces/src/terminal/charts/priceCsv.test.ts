import { describe, it, expect } from 'vitest';
import { barYmd, priceBarsToRows, priceCsvFilename, PRICE_CSV_COLUMNS } from './priceCsv';
import { toCsv } from '../../scan/csvExport';

describe('priceCsv · render 진실 직렬화', () => {
	it('barYmd: ms-epoch(Date.UTC) 를 TZ off-by-one 없이 YYYYMMDD 로 되돌린다', () => {
		expect(barYmd(Date.UTC(2026, 3, 1))).toBe('20260401');
		expect(barYmd(Date.UTC(2010, 0, 4))).toBe('20100104');
		expect(barYmd(Date.UTC(2020, 11, 31))).toBe('20201231');
	});

	it('컬럼 t,o,h,l,c,v 를 봉에서 그대로 정형', () => {
		const rows = priceBarsToRows([
			{ timestamp: Date.UTC(2010, 0, 4), open: 1, high: 2, low: 0.5, close: 1.5, volume: 100 }
		]);
		expect(rows[0]).toEqual({ t: '20100104', o: 1, h: 2, l: 0.5, c: 1.5, v: 100 });
		expect([...PRICE_CSV_COLUMNS]).toEqual(['t', 'o', 'h', 'l', 'c', 'v']);
	});

	it('함정 5: turnover 를 봉이 들고 있어도 컬럼에 새지 않는다', () => {
		const rows = priceBarsToRows([
			{ timestamp: Date.UTC(2020, 0, 1), open: 1, high: 1, low: 1, close: 1, volume: 1, turnover: 123 } as never
		]);
		expect(Object.keys(rows[0])).toEqual(['t', 'o', 'h', 'l', 'c', 'v']);
	});

	it('결손 volume=빈셀(0 금지), 진짜 0(거래정지)은 보존', () => {
		const rows = priceBarsToRows([
			{ timestamp: Date.UTC(2020, 0, 1), open: 1, high: 1, low: 1, close: 1 }, // volume 결손
			{ timestamp: Date.UTC(2020, 0, 2), open: 1, high: 1, low: 1, close: 1, volume: 0 } // 진짜 정지
		]);
		expect(rows[0].v).toBeNull();
		expect(rows[1].v).toBe(0);
		const lines = toCsv([...PRICE_CSV_COLUMNS] as string[], rows as unknown as Array<Record<string, unknown>>)
			.replace(/^﻿/, '')
			.split('\n');
		expect(lines[1].endsWith(',')).toBe(true); // 결손 -> 빈셀
		expect(lines[2].endsWith(',0')).toBe(true); // 진짜 0 -> 0
	});

	it('함정 2: 파일명 날짜는 마지막 봉(render 진실)에서 도출 + tf/_adj 인코딩', () => {
		const rows = priceBarsToRows([
			{ timestamp: Date.UTC(2023, 3, 1), open: 1, high: 1, low: 1, close: 1, volume: 1 },
			{ timestamp: Date.UTC(2026, 5, 30), open: 1, high: 1, low: 1, close: 1, volume: 1 } // 백필로 더 최신 봉
		]);
		expect(priceCsvFilename('000660', rows, 'D', false)).toBe('dartlab_000660_20260630_D.csv');
		expect(priceCsvFilename('000660', rows, 'W', true)).toBe('dartlab_000660_20260630_W_adj.csv');
	});
});
