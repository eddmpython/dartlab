// 카드 투영 단위테스트 — projectBlock 8 변종 매핑·pending/skip 정직 카드·미매핑 fail-loud·
// narration 신규합성 0(모델값 그대로). fixture 만으로 런타임 비의존 검증.
import { describe, it, expect } from 'vitest';
import type { ReportModel, ReportBlock, ReportSection } from '$lib/report/model';
import type { NoteSeriesBundle, CompositionSeries } from '@dartlab/ui-contracts';
import type { CarouselCard } from './model';
import { projectBlock, projectReport, projectResult, compositionToCard, chapterAnchors } from './project';

function model(overrides: Partial<ReportModel> = {}): ReportModel {
	return {
		stockCode: '005930',
		corpName: '삼성전자',
		asOf: '2025-03-31',
		dataBasis: 'FY2024 (연간)',
		perspectiveKey: 'earningsPower',
		perspectiveLabel: '수익성',
		conclusion: '영업이익률이 회복 국면에 있다.',
		headlineKpis: [
			{ label: '매출', value: '300조' },
			{ label: '영업이익률', value: '12.3%' }
		],
		narrativeOverview: '개요',
		keyFindings: [],
		sections: [],
		closing: [{ label: '종합', engine: 'story', line: '구조적 회복이 관건이다.' }],
		provenance: { engines: {}, note: '' },
		assumptionsNote: '',
		qualityLabel: 'verified',
		focusQuestions: [],
		...overrides
	};
}

const HEAD = { heading: '재무분석', sub: '수익성' };

describe('projectBlock — 8 변종 명시 매핑', () => {
	it('line/bars/share/metrics/flags/table(시계열) → 카드', () => {
		expect(projectBlock({ type: 'line', series: [1, 2, 3] }, HEAD)?.kind).toBe('line');
		expect(projectBlock({ type: 'bars', rows: [{ label: 'a', value: 1, display: '1' }] }, HEAD)?.kind).toBe('bars');
		expect(
			projectBlock({ type: 'share', rows: [{ year: '2024', segs: [] }], legend: [] }, HEAD)?.kind
		).toBe('share');
		expect(projectBlock({ type: 'metrics', metrics: [{ label: 'a', value: '1' }] }, HEAD)?.kind).toBe('kpis');
		expect(projectBlock({ type: 'flags', kind: 'warning', flags: ['x'] }, HEAD)?.kind).toBe('flags');
		const ts: ReportBlock = { type: 'table', data: [{ 항목: '매출', '2022': '1', '2023': '2', '2024': '3' }] };
		expect(projectBlock(ts, HEAD)?.kind).toBe('table');
	});
	it('heading·짧은 text·비시계열 table → 명시 skip(null)', () => {
		expect(projectBlock({ type: 'heading', title: 'x' }, HEAD)).toBeNull();
		expect(projectBlock({ type: 'text', text: '짧음' }, HEAD)).toBeNull();
		expect(projectBlock({ type: 'table', data: [{ 항목: '매출', 값: '1' }] }, HEAD)).toBeNull();
	});
	it('충분히 긴 text → narrative', () => {
		const c = projectBlock({ type: 'text', text: '영업이익률이 3년 연속 개선되어 구조적 회복 신호로 읽힌다.' }, HEAD);
		expect(c?.kind).toBe('narrative');
	});
	it('미매핑 변종 → fail-loud(throw, silent drop 금지)', () => {
		expect(() => projectBlock({ type: 'bogus' } as unknown as ReportBlock, HEAD)).toThrow(/미매핑/);
	});
});

describe('projectBlock table — 4:5 카드 정규화(라벨 맨앞·기간 cap·요약열 드롭)', () => {
	it('라벨이 끝열인 표(연간추세)도 라벨을 cols[0] 로 정규화 — 열 어긋남 방지', () => {
		// 실제 케이스: ['2020'..'2025','연간 지표'] (라벨이 마지막). 라벨이 맨 앞으로 와야 함.
		const block: ReportBlock = {
			type: 'table',
			data: [{ '2020': '59.2', '2021': '69.9', '2022': '86.6', '2023': '99.8', '2024': '107.4', '2025': '114.1', '연간 지표': '매출액(조)' }]
		};
		const card = projectBlock(block, HEAD);
		expect(card?.kind).toBe('table');
		if (card?.kind !== 'table') throw new Error('table 아님');
		expect(card.cols[0]).toBe('연간 지표'); // 라벨 맨앞
		expect(card.cols.slice(1)).toEqual(['2020', '2021', '2022', '2023', '2024', '2025']); // 기간 순서 보존
	});
	it('기간 7+ · 요약열(YoY) → 라벨 + 최근 6기간만(요약열 드롭, 헤더 절단 해소)', () => {
		const periods: Record<string, string> = {};
		['23Q3', '23Q4', '24Q1', '24Q2', '24Q3', '24Q4', '25Q1'].forEach((q, i) => (periods[q] = String(i)));
		const block: ReportBlock = { type: 'table', data: [{ 항목: '매출', ...periods, YoY: '-5%' }] };
		const card = projectBlock(block, HEAD);
		if (card?.kind !== 'table') throw new Error('table 아님');
		expect(card.cols[0]).toBe('항목');
		expect(card.cols).not.toContain('YoY'); // 요약열 드롭
		expect(card.cols.slice(1)).toEqual(['23Q4', '24Q1', '24Q2', '24Q3', '24Q4', '25Q1']); // 최근 6기간(23Q3 탈락)
		expect(card.cols.length).toBeLessThanOrEqual(7); // 라벨+6 → 추이 포함해도 8열 ≤ 가독 한계
	});
});

describe('projectReport — 덱 구조 + 정직', () => {
	const sec: ReportSection = {
		key: 'profit',
		title: '재무분석 -- 수익성은 지속되는가',
		sourceEngine: 'analysis',
		blocks: [
			{ type: 'heading', title: '추세' },
			{ type: 'line', series: [10, 11, 12], xLabels: ['22', '24'] },
			{ type: 'flags', kind: 'opportunity', flags: ['신규 라인 가동'] }
		]
	};
	it('cover → kpis → finChart → 섹션카드(시각만 1장) — 자동 종합·산문·신호 없음', () => {
		const deck = projectReport(model({ sections: [sec] }), { heroUrls: ['https://x/h.webp'] });
		const kinds = deck.cards.map((c) => c.kind);
		expect(kinds[0]).toBe('cover');
		expect(kinds).toContain('kpis');
		expect(kinds).toContain('finChart');
		expect(kinds).toContain('line'); // 섹션은 차트(line) 1장만 — flags 는 같은 섹션이라 탈락(시각만)
		expect(kinds).not.toContain('flags');
		expect(kinds).not.toContain('closing'); // 자동 종합 제거 — 종합/서사는 수기 editorial 로
		expect(kinds).not.toContain('narrative'); // 자동 산문 제거
		expect(deck.cards.filter((c) => c.kind === 'line')[0]).toMatchObject({ heading: '재무분석', sub: '수익성은 지속되는가' });
	});
	it('cover 는 모델값 그대로(신규 숫자 합성 0)', () => {
		const deck = projectReport(model());
		const cover = deck.cards[0];
		expect(cover.kind === 'cover' && cover.conclusion).toBe('영업이익률이 회복 국면에 있다.');
		expect(cover.bg).toBeUndefined(); // hero 없으면 폴백(undefined)
	});
	it('hero 사진 전부를 슬라이드에 순환 배정(한 장도 안 빠짐)', () => {
		const deck = projectReport(model({ sections: [sec] }), { heroUrls: ['a', 'b', 'c'] });
		expect(deck.heroUrls).toEqual(['a', 'b', 'c']);
		const bgs = deck.cards.filter((c) => c.kind !== 'empty').map((c) => c.bg);
		expect(deck.cards[0].bg).toBe('a'); // 표지 = 첫 hero
		expect(new Set(bgs).size).toBeGreaterThan(1); // 여러 hero 가 실제로 쓰임(순환)
	});
	it('hero 부재 시에도 덱 렌더 가능(빈 화면 금지) — cover+finChart 최소', () => {
		const deck = projectReport(model({ headlineKpis: [], sections: [] }));
		expect(deck.cards.length).toBeGreaterThanOrEqual(2); // cover + finChart(+closing)
		expect(deck.cards.some((c) => c.kind === 'finChart')).toBe(true);
	});
	it('자동 핵심지표가 전부 결측이면 빈 KPI 카드를 붙이지 않는다', () => {
		const deck = projectReport(
			model({
				headlineKpis: [
					{ label: '매출', value: '-' },
					{ label: '영업이익률', value: '–' }
				]
			})
		);
		expect(deck.cards.some((c) => c.kind === 'kpis')).toBe(false);
	});
	it('편집자가 검증한 핵심지표가 있으면 자동 핵심지표보다 우선한다', () => {
		const lead: CarouselCard[] = [
			{ kind: 'editorial', line: '커버', chapter: '표지' },
			{ kind: 'kpis', heading: '핵심 지표', chapter: '핵심지표', metrics: [{ label: '매출', value: '13억8563만달러' }] }
		];
		const deck = projectReport(model(), { lead });
		const kpis = deck.cards.filter((c) => c.kind === 'kpis');
		expect(kpis).toHaveLength(1);
		expect(kpis[0]).toMatchObject({ metrics: [{ label: '매출', value: '13억8563만달러' }] });
	});
});

describe('큐레이션 오버레이(CarouselSpec) — notes/order', () => {
	const secA: ReportSection = {
		key: 'profit',
		title: '재무분석 -- 수익성',
		sourceEngine: 'analysis',
		blocks: [{ type: 'line', series: [1, 2, 3] }]
	};
	const secB: ReportSection = {
		key: 'debt',
		title: '신용 -- 부채',
		sourceEngine: 'credit',
		blocks: [{ type: 'bars', rows: [{ label: '부채', value: 1, display: '1' }] }]
	};
	it('notes[섹션key] → 섹션 첫 카드 note 주입', () => {
		const deck = projectReport(model({ sections: [secA] }), { spec: { notes: { profit: '본업 현금이 받친다' } } });
		const line = deck.cards.find((c) => c.kind === 'line');
		expect(line?.note).toBe('본업 현금이 받친다');
	});
	it('order → 섹션 필터/재정렬(미지정 key 제외)', () => {
		const deck = projectReport(model({ sections: [secA, secB] }), { spec: { order: ['debt'] } });
		// debt 만 남고 profit(line) 제외.
		expect(deck.cards.some((c) => c.kind === 'bars')).toBe(true);
		expect(deck.cards.some((c) => c.kind === 'line')).toBe(false);
	});
	it('spec 없으면 자동 투영 그대로(note 없음)', () => {
		const deck = projectReport(model({ sections: [secA] }));
		expect(deck.cards.find((c) => c.kind === 'line')?.note).toBeUndefined();
	});
});

// 주석 구성 시계열 fixture — 부문별매출/비용성격별(rt.report.noteSeries).
function comp(cats: string[]): CompositionSeries {
	return {
		categories: cats,
		points: [
			{ period: '2024Q4', year: '2024', quarter: '4분기', total: 1000, shares: cats.map((_, i) => (i === 0 ? 60 : 40 / (cats.length - 1 || 1))) },
			{ period: '2025Q1', year: '2025', quarter: '1분기', total: 1100, shares: cats.map((_, i) => (i === 0 ? 55 : 45 / (cats.length - 1 || 1))) }
		]
	};
}

describe('주석 구성 깊은 카드(compositionToCard) — 세로 스택+표·조건부·신규합성 0', () => {
	it('categories(최신 desc)·periods(최근6·shortPeriod)·shares·amounts, chapter=사업·운영', () => {
		const card = compositionToCard(comp(['반도체', '디스플레이']), '부문별 매출', '어디서 버나');
		expect(card?.kind).toBe('composition');
		if (card?.kind !== 'composition') throw new Error('composition 아님');
		expect(card.heading).toBe('부문별 매출');
		expect(card.sub).toBe('어디서 버나');
		expect(card.chapter).toBe('사업·운영');
		expect(card.categories).toEqual(['반도체', '디스플레이']); // 최신(55>45) 비중 desc
		expect(card.periods).toEqual(['24Q4', '25Q1']); // shortPeriod(20 제거)
		expect(card.shares[0][0]).toBe(60); // 기간0·카테고리0 비중 그대로(신규합성 0)
		expect(card.amounts[0]).toBeCloseTo((55 / 100) * 1100); // 최신 금액 = 비중×당기합
		expect(card.latestPeriod).toBe('25Q1');
	});
	it('null·빈·전부 잔여 → null(단일부문/미공시 = 조건부 skip, 핵심만)', () => {
		expect(compositionToCard(null, 'x', 'y')).toBeNull();
		expect(compositionToCard({ categories: [], points: [] }, 'x', 'y')).toBeNull();
		expect(compositionToCard({ categories: ['a'], points: [] }, 'x', 'y')).toBeNull();
		// 최신 비중이 전부 0(잔여)이면 null
		expect(compositionToCard({ categories: ['a', 'b'], points: [{ period: '2025Q1', year: '2025', quarter: '1분기', total: 0, shares: [0, 0] }] }, 'x', 'y')).toBeNull();
	});
	it('7기간+ → 최근 6컷만(카드 밀도)', () => {
		const many: CompositionSeries = {
			categories: ['a', 'b'],
			points: Array.from({ length: 8 }, (_, i) => ({ period: `2024Q${i}`, year: '2024', quarter: '4분기', total: 100, shares: [50, 50] }))
		};
		const card = compositionToCard(many, 'x', 'y');
		if (card?.kind !== 'composition') throw new Error('composition 아님');
		expect(card.periods.length).toBe(6);
		expect(card.shares.length).toBe(6);
	});
});

describe('챕터 점프 앵커(chapterAnchors) — 섹션 네비', () => {
	const tagged = (chapter?: string): CarouselCard => ({ kind: 'empty', reason: 'x', chapter }) as CarouselCard;
	it('distinct chapter 첫 index, 연속 dedup', () => {
		const cards = [tagged('표지'), tagged('핵심지표'), tagged('재무'), tagged('재무'), tagged('사업·운영')];
		expect(chapterAnchors(cards).map((a) => a.label)).toEqual(['표지', '핵심지표', '재무', '사업·운영']);
		expect(chapterAnchors(cards)[2]).toEqual({ label: '재무', index: 2 }); // 첫 '재무'
	});
	it('chapter 없는 카드 무시', () => {
		expect(chapterAnchors([tagged(undefined), tagged(undefined)])).toEqual([]);
	});
});

describe('projectReport — 깊은 카드 주입 + 챕터 태깅', () => {
	it('수익성 + noteSeries → 부문/비용 composition 2장(finChart 뒤)', () => {
		const ns: NoteSeriesBundle = { segment: comp(['반도체', 'DX']), cost: comp(['원재료', '인건비']) };
		const deck = projectReport(model(), { noteSeries: ns });
		const comps = deck.cards.filter((c) => c.kind === 'composition');
		expect(comps.map((c) => c.heading)).toEqual(['부문별 매출', '비용 체질']);
	});
	it('segment 만 있으면 1장(cost null → 조건부 skip)', () => {
		const ns: NoteSeriesBundle = { segment: comp(['a', 'b']), cost: null };
		const deck = projectReport(model(), { noteSeries: ns });
		expect(deck.cards.filter((c) => c.kind === 'composition').map((c) => c.heading)).toEqual(['부문별 매출']);
	});
	it('비-수익성 관점에는 미주입(5덱 비대화 방지)', () => {
		const ns: NoteSeriesBundle = { segment: comp(['a', 'b']), cost: comp(['c', 'd']) };
		const deck = projectReport(model({ perspectiveKey: 'liquidity', perspectiveLabel: '재무안정성' }), { noteSeries: ns });
		expect(deck.cards.some((c) => c.kind === 'composition')).toBe(false);
	});
	it('cover/kpis/finChart 챕터 태깅 — 네비 앵커 4종 성립', () => {
		const ns: NoteSeriesBundle = { segment: comp(['a', 'b']), cost: null };
		const deck = projectReport(model(), { noteSeries: ns });
		expect(deck.cards[0].chapter).toBe('표지');
		expect(deck.cards.find((c) => c.kind === 'kpis')?.chapter).toBe('핵심지표');
		expect(deck.cards.find((c) => c.kind === 'finChart')?.chapter).toBe('재무');
		expect(chapterAnchors(deck.cards).map((a) => a.label)).toEqual(['표지', '핵심지표', '재무', '사업·운영']);
	});
});

describe('pending/skip — 정직 빈 카드', () => {
	it('pending 관점 → empty 카드', () => {
		const deck = projectReport(model({ pending: true }));
		expect(deck.cards.map((c) => c.kind)).toEqual(['cover', 'empty']);
	});
	it('ReportSkipped → empty 카드(broken img 아님)', () => {
		const deck = projectResult({ skipped: true, stockCode: '999999', reason: '데이터 없음' }, '수익성');
		expect(deck.cards).toEqual([{ kind: 'empty', reason: '데이터 없음' }]);
	});
});
