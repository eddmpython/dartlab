// Runtime 최상위 계약 — mainPlan/02 §2. 의존 0 (타입 전용 패키지).
// 빈값 규약: `[]` = 조회 성공·해당 없음 / `null` = 데이터셋 자체 미존재·미공시. 어댑터는 이 의미를 섞지 않는다.
import type { CompanyPort } from './company';
import type { PricePort } from './price';
import type { IndexPort } from './indexPort';
import type { FilingPort } from './filing';
import type { NewsPort } from './news';
import type { FinancePort } from './finance';
import type { ViewerPort } from './viewer';
import type { MacroPort } from './macro';
import type { ReportPort } from './report';
import type { ScanPort } from './scan';
import type { IpoPort } from './ipo';
import type { MapPort } from './map';
import type { SearchPort } from './search';
import type { AiPort } from './ai';
import type { ServicesPort } from './services';
import type { ExportPort } from './export';
import type { NavigationPort } from './navigation';
import type { StoragePort } from './storage';

/** 단일 정의 — 옛 landing 코드의 3중 재정의(types.ts·terminalFinance.ts·reportSeries.ts)를 수렴. */
export type Num = number | null;

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export type RuntimeKind = 'public' | 'local' | 'test';

export interface RuntimeEnvironment {
	kind: RuntimeKind;
	basePath: string;
	locale: 'ko' | 'en';
	marketDefault: 'KR' | 'US';
	buildVersion: string;
	readonly: boolean;
}

export interface DataProvenance {
	source: string; // 예: 'gov/prices' · 'dart/panel' · 'local-cache'
	asOf?: string; // YYYYMMDD 또는 ISO
}

export interface DataCoverage {
	from?: string;
	to?: string;
	note?: string;
}

/** 어댑터 반환 metadata 봉투 — stale 데이터를 최신처럼 표시하지 않기 위한 계약 (02 §3.6). */
export interface RuntimeDataEnvelope<T> {
	data: T;
	provenance: DataProvenance[];
	asOf: string;
	stale: boolean;
	coverage: DataCoverage;
}

export interface TelemetryPort {
	/** public = 무PII 집계만, local = 옵트인 로컬 로그. */
	event(name: string, props?: Record<string, string | number>): void;
}

/** flag 식별자 — 목록은 단계-2 구현에서 union으로 좁힌다(잠정 string). */
export type DartLabFeatureFlag = string;

export interface FeatureFlagPort {
	isEnabled(flag: DartLabFeatureFlag): boolean;
}

/**
 * Port 메서드는 전부 required — optional 메서드(`x?:`) + 조용한 fallback 금지 (02 §3).
 * 미지원 기능은 null/빈값 + RuntimeDataEnvelope.stale/provenance 로 정직하게 드러낸다.
 */
export interface DartLabRuntime {
	env: RuntimeEnvironment;
	company: CompanyPort;
	price: PricePort;
	index: IndexPort;
	filing: FilingPort;
	news: NewsPort;
	finance: FinancePort;
	viewer: ViewerPort;
	macro: MacroPort;
	report: ReportPort;
	scan: ScanPort;
	ipo: IpoPort;
	map: MapPort;
	search: SearchPort;
	ai: AiPort;
	services: ServicesPort;
	export: ExportPort;
	navigation: NavigationPort;
	storage: StoragePort;
	telemetry: TelemetryPort;
	featureFlags: FeatureFlagPort;
}
