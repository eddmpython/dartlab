import type { FetchLike } from '@dartlab/ui-runtime/data/dartlabData';
import type {
	UniverseChangeSet,
	UniverseEvidenceQuery,
	UniverseEvidenceResolution,
	UniverseObservationPoint,
	UniverseObservationRange,
	UniverseRouteSeed
} from '@dartlab/ui-contracts';

export interface DartlabBrowserOptions {
	fetchFn: FetchLike;
}

export interface MarketMapBundle {
	ecosystem: any;
	atlas: any;
	industryStats: any;
	meta: any;
	movers: any;
	timeline: any;
}

export interface ScanBundle {
	ecosystem: any;
	meta: any;
	markets: Record<string, string>;
}

export interface UniverseBrowser {
	seed(): Promise<UniverseRouteSeed>;
	industry(industryId: string): Promise<unknown>;
	company(stockCode: string): Promise<unknown>;
	observations(entityId: string, metricId: string, range?: UniverseObservationRange): Promise<UniverseObservationPoint[]>;
	changes(maxMarks?: number): Promise<UniverseChangeSet>;
	resolveEvidence(query: UniverseEvidenceQuery): Promise<UniverseEvidenceResolution>;
}

export interface DashboardBundle {
	stockCode: string;
	ecosystem: any;
	finance: any;
	quarters: any;
	meta: any;
	macro: any;
	companyMeta: any;
	industryMeta: any;
	industryId: string | null;
	version: string;
}

export type BrowserShowTopic = 'IS' | 'BS' | 'CF' | 'ratios' | 'businessOverview';
export type BrowserShowFreq = 'Y' | 'Q';

export interface BrowserShowOptions {
	freq?: BrowserShowFreq;
}

export interface BrowserTableRow {
	key: string;
	label: string;
	unit: string;
	values: Array<number | string | null>;
}

export interface BrowserTable {
	kind: 'table';
	topic: BrowserShowTopic;
	stockCode: string;
	unit: string;
	columns: string[];
	rows: BrowserTableRow[];
	source: string;
}

export interface BrowserText {
	kind: 'text';
	topic: BrowserShowTopic;
	stockCode: string;
	title: string;
	text: string;
	source: string;
}

export type BrowserShowResult = BrowserTable | BrowserText;
