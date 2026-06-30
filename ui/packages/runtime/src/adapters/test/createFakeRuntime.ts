// test adapter · 네트워크 0, 전 포트 fixture 구현 (02 §9.3).
// DartLabRuntime 타입을 통째로 구현하므로, tsc 가 "전 포트 required 메서드 구현 존재"를
// 기계 검사한다 (05 §2 conformance 의 컴파일 타임 절반 · 런타임 fixture 대조는 첫 surface 테스트와 동행).
import type {
	AiPort,
	Candle,
	CompanyPort,
	DartLabRuntime,
	ExportArtifact,
	ExportableTable,
	ExportBundleLike,
	ExportInput,
	ExportPort,
	FilingPort,
	FinancePort,
	IndexPort,
	MacroPort,
	MapPort,
	NavigationPort,
	NewsPort,
	PricePort,
	ReportPort,
	RuntimeEnvironment,
	RuntimeStorageKey,
	ScanPort,
	SearchPort,
	StoragePort,
	ViewerPort
} from '@dartlab/ui-contracts';
import { INDEX_PRESETS } from '@dartlab/ui-contracts';
import { createServiceRegistry } from '../../services/serviceRegistry';
import { listExportableTables } from '../export/exportShared';

const FIXTURE_CODE = '005930';

function fixtureCandles(): Candle[] {
	// 5영업일 고정 fixture · 시각 회귀·렌더 검증용 (난수·현재시각 금지: 결정론).
	return [
		{ t: '20260601', o: 100, h: 110, l: 95, c: 105, v: 1000 },
		{ t: '20260602', o: 105, h: 115, l: 100, c: 110, v: 1200 },
		{ t: '20260603', o: 110, h: 112, l: 101, c: 102, v: 900 },
		{ t: '20260604', o: 102, h: 108, l: 99, c: 107, v: 1100 },
		{ t: '20260605', o: 107, h: 120, l: 106, c: 118, v: 1500 }
	];
}

function fakeCompany(): CompanyPort {
	return {
		async products(code) {
			if (code !== FIXTURE_CODE) return null;
			return { product: '메모리 반도체', productRaw: 'DRAM·NAND', latestPeriod: '2026Q1', industry: '반도체' };
		},
		async productIndex() {
			return { [FIXTURE_CODE]: { product: '메모리 반도체', productRaw: 'DRAM·NAND', latestPeriod: '2026Q1' } };
		},
		async relations(code) {
			if (code !== FIXTURE_CODE) return null;
			return { suppliers: [], customers: [], peers: [], neighborCount: 0, blog: null };
		},
		async reportFacts() {
			return [];
		},
		async industryProfitPool() {
			return null;
		}
	};
}

function fakePrice(): PricePort {
	const candles = fixtureCandles();
	return {
		async initial(code) {
			if (code !== FIXTURE_CODE) return null;
			return { candles, oldestYear: 2026 };
		},
		async older() {
			return [];
		},
		loaded(code) {
			return code === FIXTURE_CODE ? candles : [];
		},
		async govCandles(code) {
			return code === FIXTURE_CODE ? candles : null;
		},
		async govRecent() {
			return { [FIXTURE_CODE]: candles };
		}
	};
}

function fakeIndex(): IndexPort {
	// 결정론 fixture · KR 코스피(OHLCV) + US SP500(degenerate o=h=l=c·v=0). 그 외 null. 난수·현재시각 금지.
	const krCandles: Candle[] = [
		{ t: '20260601', o: 2700, h: 2720, l: 2690, c: 2710, v: 500_000 },
		{ t: '20260602', o: 2710, h: 2735, l: 2705, c: 2730, v: 520_000 },
		{ t: '20260603', o: 2730, h: 2740, l: 2715, c: 2725, v: 480_000 }
	];
	const usCandles: Candle[] = [
		{ t: '20260601', o: 5300, h: 5300, l: 5300, c: 5300, v: 0 },
		{ t: '20260602', o: 5320, h: 5320, l: 5320, c: 5320, v: 0 },
		{ t: '20260603', o: 5310, h: 5310, l: 5310, c: 5310, v: 0 }
	];
	return {
		async catalog() {
			return INDEX_PRESETS;
		},
		async search(query) {
			const q = query.trim();
			return q ? INDEX_PRESETS.filter((r) => r.name.includes(q)) : [];
		},
		async series(ref) {
			if (ref.code === 'idx:KOSPI/코스피') return krCandles;
			if (ref.code === 'idx:US/SP500') return usCandles;
			return null;
		}
	};
}

function fakeFiling(): FilingPort {
	return {
		async regular(code) {
			if (code !== FIXTURE_CODE) return [];
			return [
				{
					rceptNo: '20260331000001',
					rceptDate: '2026-03-31',
					reportType: '사업보고서',
					year: '2025',
					url: 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260331000001'
				}
			];
		},
		async nonRegular() {
			return [];
		},
		async recentForCodes() {
			return {};
		},
		async marketFeed() {
			return [];
		},
		async panelToc(code) {
			if (code !== FIXTURE_CODE) return null;
			return {
				stockCode: code,
				corpName: '픽스처전자',
				chapters: [
					{
						chapter: 'I. 회사의 개요',
						sections: [
							{
								sectionLeaf: '1. 회사의 개요',
								sectionKey: 'I. 회사의 개요␟1. 회사의 개요',
								blocks: [{ blockLeaf: '개요', leafType: 'narrative', disclosureKey: null }]
							}
						]
					}
				],
				periods: ['2025']
			};
		},
		async panelInit(code) {
			const toc = await this.panelToc(code);
			const grid = await this.panelGrid(code, 'I. 회사의 개요␟1. 회사의 개요');
			if (!toc || !grid) return null;
			return {
				stockCode: code,
				corpName: toc.corpName,
				toc,
				firstChapter: 'I. 회사의 개요',
				firstSectionKey: 'I. 회사의 개요␟1. 회사의 개요',
				grid
			};
		},
		async panelGrid(code, sectionKey) {
			if (code !== FIXTURE_CODE) return null;
			return {
				stockCode: code,
				corpName: '픽스처전자',
				chapter: 'I. 회사의 개요',
				sectionLeaf: '1. 회사의 개요',
				sectionKey,
				periods: ['2025'],
				rows: [
					{
						chapter: 'I. 회사의 개요',
						sectionLeaf: '1. 회사의 개요',
						blockLeaf: '개요',
						leafType: 'narrative',
						disclosureKey: null,
						scope: null,
						blockType: 'text',
						cells: { '2025': '<p>픽스처 본문</p>' }
					}
				]
			};
		}
	};
}

function fakeNews(): NewsPort {
	return {
		async forCompany(code) {
			if (code !== FIXTURE_CODE) return [];
			return [
				{ date: '2026-06-05', title: '픽스처전자, 신제품 공개', source: '한경', url: 'https://example.com/n1', description: '결정론 fixture 뉴스 스니펫.', track: 'naver' },
				{ date: '2026-06-03', title: '픽스처전자 실적 호조', source: '매경', url: 'https://example.com/n2', description: '', track: 'naver' },
				{ date: '2021-04-02', title: '픽스처전자 과거 기사', source: 'reuters.com', url: 'https://example.com/g1', description: '', track: 'gdelt' }
			];
		},
		async market() {
			return [
				{ date: '2026-06-12', title: '코스피, 외국인 순매수에 강세 마감', source: '연합뉴스', url: 'https://example.com/m1' },
				{ date: '2026-06-11', title: '반도체 수출 회복…2분기 실적 기대', source: '한경', url: 'https://example.com/m2' }
			];
		}
	};
}

function fakeFinance(): FinancePort {
	return {
		async bundle(code, scope) {
			if (code !== FIXTURE_CODE) return null;
			return {
				currency: 'KRW',
				scope: scope ?? 'CFS',
				availScopes: ['CFS', 'OFS'],
				modes: ['annual'],
				views: {
					annual: {
						periods: ['FY24', 'FY25'],
						freq: 'annual',
						cards: [],
						tabCards: { profitability: [], cashflow: [], debt: [], shareholder: [] },
						revYoy: [null, 10],
						opYoy: [null, 12],
						cashQuality: [1.1, 1.2],
						statements: { IS: [], BS: [], CF: [] },
						ratios: []
					},
					quarter: null,
					ttm: null
				},
				defaultMode: 'annual',
				filedDates: {}
			};
		}
	};
}

function fakeMacro(): MacroPort {
	const def = { id: 'USDKRW', src: 'ecos' as const, kr: '원/달러 환율', en: 'USD/KRW', unit: '원' };
	return {
		async listSeries() {
			return [def];
		},
		async getSeries(id) {
			if (id !== 'USDKRW') return null;
			return [
				{ d: '20260601', v: 1350 },
				{ d: '20260602', v: 1355 }
			];
		},
		async getSeriesRaw(id) {
			return id === 'USDKRW' ? [{ d: '20260601', v: 1350 }, { d: '20260602', v: 1355 }] : null;
		},
		async getLatest() {
			return [{ def, v: 1355, d: '20260602', chg: 5, spark: [1350, 1355] }];
		},
		async getTransmission(query = {}) {
			const sectorKey = query.sectorKey ?? 'semiconductor';
			return {
				version: 'test',
				market: query.market ?? 'KR',
				sectorKey,
				asOf: '2026-06-02',
				drivers: [
					{
						id: 'USDKRW',
						labelKr: '원/달러 환율',
						source: 'ECOS',
						sourceSeriesId: 'USDKRW',
						market: 'KR',
						unit: '원',
						group: 'FX',
						transform: 'level_and_mom_1m',
						directionSemantics: '상승은 원화 약세다.',
						defaultLagMonths: [0, 3],
						sourceLineage: {
							source: 'ECOS',
							sourceSeriesId: 'USDKRW',
							date: '2026-06-02',
							value: 1355,
							unit: '원',
							artifactPath: 'macro/ecos/observations.parquet',
							asOfPolicy: 'observation_date <= price_as_of',
							status: 'observed'
						}
					}
				],
				edges: [
					{
						id: 'fx-export-revenue',
						driverId: 'USDKRW',
						market: 'KR',
						sectorKeys: [sectorKey],
						channel: 'revenue',
						financialLine: '매출 성장률 / 환산손익',
						valuationLever: 'growth',
						sign: 'mixed',
						lagMonths: [0, 3],
						evidenceLevel: 'sectorPrior',
						confidence: 'low',
						requiredCompanyEvidence: ['해외 매출 비중', 'FX 손익 주석'],
						falsifiers: ['달러 원가 비중이 상쇄'],
						sourceRefs: ['driver:USDKRW', 'macro.transmission:test'],
						sourceRef: 'macro.transmission:edge:fx-export-revenue',
						evidenceLabel: 'PRIOR'
					}
				],
				regimeEvidence: [],
				aliases: {},
				sourceRefs: ['dartlab://macro/transmission'],
				missing: []
			};
		}
	};
}

function fakeReport(): ReportPort {
	return {
		async valuationSnapshot() {
			return null;
		},
		async noteSeries() {
			return null;
		},
		async shareholders() {
			return null;
		},
		async shareholderPeriods() {
			return null;
		},
		async workforce(code) {
			if (code !== FIXTURE_CODE) return null;
			return [
				{
					year: '2025',
					total: 1000,
					male: 600,
					female: 400,
					regular: 950,
					contract: 50,
					avgSalary: 80_000_000,
					totalSalary: 80_000_000_000,
					tenure: 10
				}
			];
		},
		async investments() {
			return null;
		},
		async shareholderReturn() {
			return null;
		},
		async ownership() {
			return null;
		},
		async execBoard() {
			return null;
		},
		async debtProfile() {
			return null;
		},
		async capitalChanges() {
			return null;
		},
		async auditTrail() {
			return null;
		},
		async topExecPay() {
			return null;
		},
		async auditFees() {
			return null;
		}
	};
}

function fakeScan(): ScanPort {
	return {
		async changes() {
			return [];
		},
		async listTableSources() {
			return [{ id: 'financeLite', label: '재무 라이트', url: 'fixture://financeLite.parquet', kind: 'parquet' }];
		},
		async getPresets() {
			return [];
		},
		async savePreset() {
			// fixture · no-op
		}
	};
}

function fakeMap(): MapPort {
	return {
		async listIndustries() {
			return [{ id: 'semis', name: '반도체' }];
		},
		async getIndustryMap(id) {
			if (id !== 'semis') return null;
			return { id, payload: {} };
		}
	};
}

function fakeSearch(): SearchPort {
	const universe = [{ stockCode: FIXTURE_CODE, corpName: '픽스처전자', industry: '반도체', revenue: 100 }];
	return {
		async universe() {
			return universe;
		},
		async query(input) {
			const hits = universe.filter((r) => r.corpName.includes(input.text) || r.stockCode === input.text);
			return { hits, total: hits.length };
		},
		async queryFilings(input) {
			const t = (input.text ?? '').trim();
			if (!t) return [];
			return [
				{
					rceptNo: '20260612900600',
					corpName: '픽스처전자',
					stockCode: FIXTURE_CODE,
					reportNm: '주요사항보고서',
					rceptDt: '20260612',
					snippet: `${t} 관련 픽스처 공시 본문`,
					source: 'allFilings',
					sourceRef: 'dart:allFilings:20260612900600#section=0',
					score: 1
				}
			];
		},
		async indexBuiltAt() {
			return '2026-06-18T00:00:00';
		}
	};
}

function fakeViewer(): ViewerPort {
	return {
		mode: 'component',
		urlForCompany(code) {
			return `/viewer/company/${code}`;
		},
		async openCompany() {
			// fixture · host 앱이 onNavigate 로 검증
		},
		async openFiling() {
			// fixture · no-op
		}
	};
}

function fakeAi(): AiPort {
	return {
		async capabilities() {
			return {
				tier: 'deterministic',
				streaming: false,
				toolCalling: false,
				localWorkspace: false,
				deterministicAnswers: true,
				upgradeHint: '로컬 설치 시 고급 분석 엔진 사용 가능'
			};
		},
		async ask(input) {
			return { text: `fixture 답변: ${input.prompt}`, refs: [] };
		},
		async *streamAsk(input) {
			yield { type: 'TEXT_MESSAGE_CONTENT', messageId: 'm1', delta: `fixture: ${input.prompt}` };
			yield { type: 'RUN_FINISHED', runId: 'r1', status: 'ok', refs: [], suggestedQuestions: [] };
		},
		async runTool(input) {
			return { status: 'done', summary: `fixture tool: ${input.toolName}`, refs: [], error: null };
		},
		async explainEvidence() {
			return { text: 'fixture 근거 설명', refs: [] };
		},
		async listModes() {
			return [
				{ id: 'chat', label: '챗', description: '일반 질의', available: true },
				{ id: 'terminal', label: '터미널', description: '운영 화면', available: true }
			];
		},
		async setMode() {
			// fixture · no-op
		},
		async getMode() {
			return 'chat';
		}
	};
}

function fakeNavigation(calls: string[]): NavigationPort {
	return {
		async toTerminal(code) {
			calls.push(`terminal:${code}`);
		},
		async toViewer(code) {
			calls.push(`viewer:${code}`);
		},
		async toCompany(code) {
			calls.push(`company:${code}`);
		},
		async toAsk() {
			calls.push('ask');
		},
		href(route) {
			return `/${route.kind}`;
		}
	};
}

function fakeExport(): ExportPort {
	return {
		listExportableTables(bundle: ExportBundleLike): ExportableTable[] {
			return listExportableTables(bundle);
		},
		async listTemplates() {
			return [];
		},
		async saveTemplate(template) {
			return template.templateId || 't_fixture';
		},
		async deleteTemplate() {
			return true;
		},
		async generate(input: ExportInput): Promise<ExportArtifact> {
			// fixture · 결정론 빈 .xlsx 자리표시자 Blob(실 writer 는 surfaces/엔진).
			return {
				filename: `${input.code}_공시표.xlsx`,
				mime: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
				blob: new Blob([], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
			};
		}
	};
}

function fakeStorage(): StoragePort {
	const store = new Map<string, unknown>();
	const subs = new Map<string, Set<(v: unknown) => void>>();
	return {
		async get<T>(key: RuntimeStorageKey) {
			return (store.get(key) as T | undefined) ?? null;
		},
		async set<T>(key: RuntimeStorageKey, value: T) {
			store.set(key, value);
			subs.get(key)?.forEach((cb) => cb(value));
		},
		async remove(key) {
			store.delete(key);
			subs.get(key)?.forEach((cb) => cb(null));
		},
		subscribe<T>(key: RuntimeStorageKey, cb: (value: T | null) => void) {
			const set = subs.get(key) ?? new Set();
			set.add(cb as (v: unknown) => void);
			subs.set(key, set);
			return () => set.delete(cb as (v: unknown) => void);
		}
	};
}

export interface FakeRuntimeOptions {
	env?: Partial<RuntimeEnvironment>;
}

/** 호스트 앱 없이 surface 를 렌더·검증하기 위한 결정론 fixture runtime. */
export function createFakeRuntime(options: FakeRuntimeOptions = {}): DartLabRuntime & { navigationCalls: string[] } {
	const navigationCalls: string[] = [];
	const runtime: DartLabRuntime = {
		env: {
			kind: 'test',
			basePath: '',
			locale: 'ko',
			marketDefault: 'KR',
			buildVersion: 'test',
			readonly: false,
			...options.env
		},
		company: fakeCompany(),
		price: fakePrice(),
		index: fakeIndex(),
		filing: fakeFiling(),
		news: fakeNews(),
		finance: fakeFinance(),
		viewer: fakeViewer(),
		macro: fakeMacro(),
		report: fakeReport(),
		scan: fakeScan(),
		map: fakeMap(),
		search: fakeSearch(),
		ai: fakeAi(),
		services: createServiceRegistry([]),
		export: fakeExport(),
		navigation: fakeNavigation(navigationCalls),
		storage: fakeStorage(),
		telemetry: { event() {} },
		featureFlags: { isEnabled: () => false }
	};
	return Object.assign(runtime, { navigationCalls });
}
