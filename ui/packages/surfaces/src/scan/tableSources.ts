/**
 * DataExplorer 모달의 9 탭 정의.
 *
 * 각 source 별 데이터 fetch 패턴:
 *   - 'memory'  : page.svelte 의 in-memory state (priceMap/valuationMap/changesMap/ecosystem nodes)
 *   - 'parquet' : DuckDB-WASM 으로 HF parquet `SELECT * FROM view LIMIT 1000` lazy fetch
 *   - 'notebook': SQL Notebook (별도 컴포넌트, table list 적용 X)
 *
 * 큰 테이블 (KRX prices, changes) 은 'parquet' source + 검색 시 SQL re-query.
 */

import {
	Building2,
	TrendingUp,
	Wallet,
	FileEdit,
	BarChart3,
	Banknote,
	Vault,
	Users,
	Notebook,
	SlidersHorizontal,
	type Icon as LucideIcon
} from 'lucide-svelte';

export interface TableSource {
	id: string;
	label: string;
	icon?: typeof LucideIcon;
	source: 'screen' | 'memory' | 'parquet' | 'notebook';
	hfPath?: string;
	viewName?: string;
	defaultLimit?: number;
	searchableColumns?: string[];
	desc: string;
}

export const TABLE_SOURCES: TableSource[] = [
	{
		id: 'screen',
		label: 'screen',
		icon: SlidersHorizontal,
		source: 'screen',
		desc: '조건형 스크리닝 · 필드 검색, 조건 조합, 그리드 필터 적용'
	},
	{
		id: 'ecosystem',
		label: 'ecosystem',
		icon: Building2,
		source: 'memory',
		desc: '회사 노드 · 41 필드 (id/label/industry + scan 등급 8종 + 정량·변화 + 거버넌스)'
	},
	{
		id: 'prices',
		label: 'prices (KRX)',
		icon: TrendingUp,
		source: 'parquet',
		hfPath: 'gov/prices/date/{year}.parquet',
		viewName: 'krxPricesAll',
		defaultLimit: 1000,
		searchableColumns: ['ISU_CD'],
		desc: 'KRX 일별 OHLCV · 회사×일자 long-form (~67만 row)'
	},
	{
		id: 'valuation',
		label: 'valuation',
		icon: Wallet,
		source: 'parquet',
		hfPath: 'dart/scan/valuation.parquet',
		viewName: 'valuation',
		defaultLimit: 5000,
		searchableColumns: ['stockCode'],
		desc: 'PER/PBR/배당수익률/시총 (Naver API)'
	},
	{
		id: 'changes',
		label: 'changes',
		icon: FileEdit,
		source: 'parquet',
		hfPath: 'dart/scan/changes.parquet',
		viewName: 'changes',
		defaultLimit: 1000,
		searchableColumns: ['stockCode', 'sectionTitle'],
		desc: '공시 변경 raw · 회사×기간×섹션'
	},
	{
		id: 'finance_lite',
		label: 'finance_lite',
		icon: BarChart3,
		source: 'parquet',
		hfPath: 'dart/scan/finance-lite.parquet',
		viewName: 'finance_lite',
		defaultLimit: 1000,
		searchableColumns: ['stockCode', 'account_id'],
		desc: '재무 long-form · 회사×분기×계정 (30+ 계정)'
	},
	{
		id: 'dividend',
		label: 'dividend',
		icon: Banknote,
		source: 'parquet',
		hfPath: 'dart/scan/report/dividend.parquet',
		viewName: 'dividend',
		defaultLimit: 5000,
		searchableColumns: ['stockCode'],
		desc: '배당 보고 · 결산월·주당배당금·배당수익률'
	},
	{
		id: 'treasuryStock',
		label: 'treasuryStock',
		icon: Vault,
		source: 'parquet',
		hfPath: 'dart/scan/report/treasuryStock.parquet',
		viewName: 'treasuryStock',
		defaultLimit: 5000,
		searchableColumns: ['stockCode'],
		desc: '자사주 · 매입액·매입주식수·보유주식수'
	},
	{
		id: 'executive',
		label: 'executive',
		icon: Users,
		source: 'parquet',
		hfPath: 'dart/scan/report/executive.parquet',
		viewName: 'executive',
		defaultLimit: 1000,
		searchableColumns: ['stockCode'],
		desc: '임원 · 임원명·직위·급여·상여·퇴직금'
	},
	{
		id: 'notebook',
		label: 'SQL Notebook',
		icon: Notebook,
		source: 'notebook',
		desc: 'motherduck-style · CodeMirror SQL 셀 + Markdown + 셀 간 reference + autocomplete'
	}
];

export const TABLE_SOURCES_BY_ID = new Map(TABLE_SOURCES.map((t) => [t.id, t]));

/** parquet path 의 {year} 치환. KRX prices 처럼 연도별 parquet 용. */
export function resolveHfPath(path: string): string {
	const year = new Date().getFullYear();
	return path.replace('{year}', String(year));
}
