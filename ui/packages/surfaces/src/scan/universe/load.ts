// 유니버스 패널 로더 · gov/prices/universe-monthly.parquet(floor, HF SSOT) → UniverseRow[].
// scan DuckDB-wasm 인프라(registerHfParquet) 재사용. 브라우저 전용(node 단위테스트는 engine.test 가 합성으로).
// 실측 11.91MB·443,422행 단일파일 · 1회 로드 후 ym 윈도 SELECT.

import type { DartDb } from '../duckSql';
import type { DelistReason, UniverseRow } from './types';

const VALID_REASON = new Set<DelistReason>(['none', 'merger', 'unknown', 'codeChange']);

/** 패널 전체(또는 ym 윈도)를 UniverseRow[] 로. 엔진(runUniverse)이 소비. */
export async function loadUniversePanel(db: DartDb, windowFrom: string, windowTo: string): Promise<UniverseRow[]> {
	await db.registerHfParquet('universeMonthly', 'gov/prices/universe-monthly.parquet');
	const raw = await db.query<{
		ym: string;
		stockCode: string;
		close: number;
		mktcap: number;
		turnover: number;
		momMonthly: number | null;
		volMonthly6m: number | null;
		high52wProx: number | null;
		retFwd1m: number | null;
		retFwd3m: number | null;
		delistReason: string;
	}>(
		`SELECT ym, stockCode, close, mktcap, turnover, momMonthly, volMonthly6m, high52wProx, retFwd1m, retFwd3m, delistReason
		 FROM universeMonthly
		 WHERE ym >= '${windowFrom}' AND ym <= '${windowTo}'
		 ORDER BY ym, stockCode`
	);
	return raw.map((r) => ({
		ym: String(r.ym),
		stockCode: String(r.stockCode),
		close: Number(r.close),
		mktcap: Number(r.mktcap),
		turnover: Number(r.turnover),
		momMonthly: r.momMonthly == null ? null : Number(r.momMonthly),
		volMonthly6m: r.volMonthly6m == null ? null : Number(r.volMonthly6m),
		high52wProx: r.high52wProx == null ? null : Number(r.high52wProx),
		retFwd1m: r.retFwd1m == null ? null : Number(r.retFwd1m),
		retFwd3m: r.retFwd3m == null ? null : Number(r.retFwd3m),
		delistReason: VALID_REASON.has(r.delistReason as DelistReason) ? (r.delistReason as DelistReason) : 'none'
	}));
}

/** 패널 가용 ym 범위(윈도 컨트롤 초기값). */
export async function loadUniverseYmRange(db: DartDb): Promise<{ min: string; max: string } | null> {
	await db.registerHfParquet('universeMonthly', 'gov/prices/universe-monthly.parquet');
	const r = await db.query<{ mn: string; mx: string }>(`SELECT MIN(ym) AS mn, MAX(ym) AS mx FROM universeMonthly`);
	if (!r.length || !r[0].mn) return null;
	return { min: String(r[0].mn), max: String(r[0].mx) };
}
