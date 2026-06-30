/**
 * ChartSpec JSON loader · viz SSOT 통일 회로의 진입점.
 *
 * Python `dartlab.viz` 가 빌드 타임에 dump 한 ChartSpec JSON 을 fetch.
 * 위치: `landing/static/charts/{stockCode}/manifest.json` + section JSON.
 * 빌드: `landing/_scripts/buildCompanyCharts.py`.
 */

import { base } from '$app/paths';

export interface ChartSpec {
	chartType: string;
	title?: string;
	series?: Array<Record<string, unknown>>;
	categories?: string[];
	options?: Record<string, unknown>;
	meta?: Record<string, unknown>;
	purpose?: string;
	evidenceIds?: string[];
	evidenceBinding?: ChartEvidenceBinding;
	vizType?: string;
}

export interface ChartEvidenceBinding {
	tableRef: string;
	source: string;
	stockCode: string;
	topic: string;
	periodKind?: string;
	periods?: string[];
	[key: string]: unknown;
}

export interface ChartManifestEntry {
	section: 'narrative' | 'hero' | 'statement' | 'peer';
	key: string;
	path: string;
	chartType: string;
	title: string;
	purpose?: string;
	evidenceBinding?: ChartEvidenceBinding;
	evidenceIds?: string[];
}

export interface ChartManifest {
	version: string;
	stockCode: string;
	corpName: string;
	generatedAt: string;
	charts: ChartManifestEntry[];
	skipped?: string[];
}

export type ChartFetch = typeof fetch;

function chartsRoot(stockCode: string): string {
	return `${base}/charts/${stockCode}`;
}

async function fetchJson<T>(url: string, fetchFn: ChartFetch): Promise<T | null> {
	try {
		const resp = await fetchFn(url);
		if (!resp.ok) return null;
		return (await resp.json()) as T;
	} catch {
		return null;
	}
}

/** 종목의 ChartSpec 매니페스트 로드. 없으면 null. */
export async function loadChartManifest(
	stockCode: string,
	fetchFn: ChartFetch = fetch
): Promise<ChartManifest | null> {
	if (!stockCode) return null;
	return fetchJson<ChartManifest>(`${chartsRoot(stockCode)}/manifest.json`, fetchFn);
}

/** 매니페스트의 단일 entry → ChartSpec dict. */
export async function loadChartSpec(
	stockCode: string,
	entry: ChartManifestEntry,
	fetchFn: ChartFetch = fetch
): Promise<ChartSpec | null> {
	if (!stockCode || !entry?.path) return null;
	return fetchJson<ChartSpec>(`${chartsRoot(stockCode)}/${entry.path}`, fetchFn);
}

/** 매니페스트의 모든 ChartSpec 을 한 번에 로드 (병렬). */
export async function loadAllChartSpecs(
	stockCode: string,
	manifest: ChartManifest,
	fetchFn: ChartFetch = fetch
): Promise<Map<string, ChartSpec>> {
	const entries = manifest.charts ?? [];
	const specs = await Promise.all(entries.map((e) => loadChartSpec(stockCode, e, fetchFn)));
	const result = new Map<string, ChartSpec>();
	entries.forEach((e, i) => {
		const s = specs[i];
		if (s) result.set(e.key, s);
	});
	return result;
}

/** section 으로 grouping. */
export function groupBySection(manifest: ChartManifest): Record<string, ChartManifestEntry[]> {
	const groups: Record<string, ChartManifestEntry[]> = {};
	for (const entry of manifest.charts ?? []) {
		const s = entry.section ?? 'narrative';
		(groups[s] ??= []).push(entry);
	}
	return groups;
}

/**
 * EvidencePanel drill-back 회로의 진입점 schema.
 * ChartRenderer 의 onPointClick 콜백이 받는 객체.
 */
export interface ChartPointRef {
	period?: string;
	valueRef?: string;
	rcept_no?: string;
	filingUrl?: string;
	pdfPage?: number;
	name?: string;
	value?: number | string;
	[key: string]: unknown;
}
