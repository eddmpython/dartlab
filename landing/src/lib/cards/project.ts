// ReportModel → CarouselDeck 순수 투영 — 굽지 않음·런타임 비의존(fixture 로 단위테스트 가능).
// 핵심 정직장치: projectBlock 이 ReportBlock 8 변종을 *명시* 매핑하고 default 에서 assertNever 로
// 컴파일/런타임 fail-loud → 새 ReportBlock 추가 시 "여기 매핑 안 하면 의도적 비-캐러셀"을 강제 선언.
// silent drop 금지. pending/skip 은 broken img 가 아니라 정직 empty 카드로.
import type { ReportBlock, ReportModel, ReportResult, OverviewModel } from '$lib/report/model';
import { isSkipped } from '$lib/report/model';
import { clean, splitTitle, isTimeSeries } from '$lib/report/render';
import type { NoteSeriesBundle, CompositionSeries } from '@dartlab/ui-contracts';
import type { CarouselCard, CarouselDeck, CarouselSpec } from './model';

// 챕터 라벨 SSOT — 캡션 패널 섹션 점프 네비(chapterAnchors)가 이 순서대로 앵커를 만든다.
const CH_COVER = '표지';
const CH_KPIS = '핵심지표';
const CH_FIN = '재무';
const CH_BIZ = '사업·운영';

interface HeadCtx {
	heading?: string;
	sub?: string;
	engine?: ReportModel['sections'][number]['sourceEngine'];
}

function assertNever(x: never): never {
	throw new Error(`projectBlock: 미매핑 ReportBlock 변종 — ${JSON.stringify(x)}`);
}

function isFilledMetricValue(value: string | null | undefined): boolean {
	const v = String(value ?? '').trim();
	return !!v && v !== '-' && v !== '–' && v.toLowerCase() !== 'n/a';
}

/** 카드용 초단문 — 첫 문장(마침표까지)만, 길면 자른다. 캐러셀은 리포트가 아니라 한 줄 후킹(기존 SNS 카피 톤). */
function hook(text: string, max = 80): string {
	const t = clean(text).trim();
	const dot = t.search(/[.!?]\s|다\.\s|입니다\.\s/);
	let s = dot > 0 && dot < max + 12 ? t.slice(0, t.indexOf('. ', dot - 1) + 1 || dot + 1) : t;
	if (s.length > max) s = s.slice(0, max).trim() + '…';
	return s.trim();
}

// ── 주석 구성 시계열(부문별매출·비용성격별) → share 카드 ──
// 카테고리명 정제는 터미널 NotesDashboardDialog.niceName 동형(원어 truth 보존·표시만 다듬음). 최근 6기간.
const SHARE_PERIODS = 6;
function niceCat(n: string): string {
	if (n === '기타') return '기타';
	const t = n.replace(/\s*및\s*/g, '·').replace(/(매입액|사용액|비용|비$)/g, '').trim();
	if (/^[A-Za-z]{1,4}$/.test(t)) return t.toUpperCase();
	return t.replace(/([a-z])([A-Z])/g, '$1 $2').slice(0, 16) || n;
}
const shortPeriod = (p: string): string => p.replace(/^20/, '');

/** 주석 구성(`rt.report.noteSeries` 의 segment/cost) → 시간축 100% 세로 스택 + 구성표 카드(터미널 동형).
 *  단일부문/미공시(null·빈·전부 잔여)면 null → 조건부 skip(데이터 있을 때만 = 핵심만 정체성). 신규 숫자 합성 0.
 *  카테고리는 최신 비중 desc 정렬 + 잔여(<0.05%, 태그 변경 사족) 제거 — 색 index 가 적층·표·범례 SSOT. */
export function compositionToCard(
	series: CompositionSeries | null | undefined,
	heading: string,
	sub: string
): CarouselCard | null {
	if (!series?.points?.length || !series.categories.length) return null;
	const pts = series.points.slice(-SHARE_PERIODS);
	const last = pts[pts.length - 1]!;
	const order = series.categories
		.map((_, i) => i)
		.filter((i) => (last.shares[i] ?? 0) > 0.05)
		.sort((a, b) => (last.shares[b] ?? 0) - (last.shares[a] ?? 0));
	if (!order.length) return null;
	return {
		kind: 'composition',
		heading,
		sub,
		chapter: CH_BIZ,
		categories: order.map((i) => niceCat(series.categories[i])),
		periods: pts.map((p) => shortPeriod(p.period)),
		shares: pts.map((p) => order.map((i) => p.shares[i] ?? 0)),
		amounts: order.map((i) => ((last.shares[i] ?? 0) / 100) * last.total),
		latestTotal: last.total,
		latestPeriod: shortPeriod(last.period)
	};
}

/** 덱 카드 → 챕터 점프 앵커(각 distinct chapter 의 첫 카드 index). 캡션 패널 섹션 네비용 —
 *  20장+ 익명 닷을 보완. 챕터는 projectReport 가 순서대로 태깅(표지→지표→재무→사업·운영)하므로 연속 dedup. */
export function chapterAnchors(cards: CarouselCard[]): { label: string; index: number }[] {
	const out: { label: string; index: number }[] = [];
	let last = '';
	cards.forEach((c, i) => {
		if (c.chapter && c.chapter !== last) {
			out.push({ label: c.chapter, index: i });
			last = c.chapter;
		}
	});
	return out;
}

/** ReportBlock 1개 → 슬라이드 카드 또는 null(명시 skip). 모든 변종을 다뤄야 컴파일됨(exhaustive). */
export function projectBlock(block: ReportBlock, head: HeadCtx): CarouselCard | null {
	switch (block.type) {
		case 'heading':
			return null; // 헤딩은 다음 카드의 head 로 접힘 — 독립 슬라이드 아님(명시 skip)
		case 'text': {
			const t = clean(block.text).trim();
			return t.length >= 24 ? { ...head, kind: 'narrative', text: hook(t, 130) } : null; // 첫 문장만(벽 금지)
		}
		case 'metrics':
			return block.metrics.length ? { ...head, kind: 'kpis', metrics: block.metrics } : null;
		case 'flags':
			return block.flags.length ? { ...head, kind: 'flags', tone: block.kind, items: block.flags } : null;
		case 'bars':
			return block.rows.length ? { ...head, kind: 'bars', rows: block.rows } : null;
		case 'line':
			return block.series.filter((n) => Number.isFinite(n)).length >= 2
				? { ...head, kind: 'line', series: block.series, xLabels: block.xLabels, markers: block.markers, valueFmt: block.valueFmt }
				: null;
		case 'share':
			return block.rows.length ? { ...head, kind: 'share', rows: block.rows, legend: block.legend } : null;
		case 'table': {
			const raw = block.data.length ? Object.keys(block.data[0]) : [];
			// 시계열 표만 캐러셀(스파크라인) — 비시계열 dense 표는 슬라이드에 안 맞아 명시 skip.
			if (!isTimeSeries(raw)) return null;
			// 4:5 카드는 좁다 → 라벨(기간 아닌 첫 열) + 최근 6기간만. 라벨이 끝열인 표(연간추세=
			// [2020..2025, '연간 지표'])도 맨 앞으로 정규화해 열 어긋남 방지, 요약열(YoY/TTM)은 드롭
			// (추이 스파크라인이 흐름 전달). 9~10열을 8열 이하로 줄여 헤더 절단('24…')도 해소.
			const isPd = (c: string) => /^\d{4}$/.test(c) || /^\d{2}Q[1-4]$/.test(c);
			const periods = raw.filter(isPd);
			const label = raw.find((c) => !isPd(c)) ?? raw[0];
			const cols = [label, ...periods.slice(-6)];
			return { ...head, kind: 'table', cols, data: block.data, unit: block.unit };
		}
		case 'thesis':
		case 'exhibit':
		case 'callout':
		case 'verdict':
		case 'scenario':
		case 'valuationBridge':
		case 'peerScatter':
		case 'driverTree':
		case 'excerpt':
		case 'transition':
			return null; // 전문 리포트 pro 블록 — /report 전용, 캐러셀 슬라이드 아님(명시 skip)
		default:
			return assertNever(block);
	}
}

/** 관점 보고서 → 슬라이드 덱. cover → KPIs → finChart 백본 → 섹션 블록 → closing.
 *  hero 사진 전부를 슬라이드 배경으로 순환 배정(인스타 에디토리얼). opts.spec(blog frontmatter
 *  `carousel:`)이 있으면 큐레이션 오버레이 — order 로 섹션 필터/재정렬, notes[key] 로 손글 caption. */
export function projectReport(
	model: ReportModel,
	opts: { heroUrls?: string[]; spec?: CarouselSpec; lead?: CarouselCard[]; noteSeries?: NoteSeriesBundle | null } = {}
): CarouselDeck {
	const spec = opts.spec;
	const heroUrls = opts.heroUrls ?? [];
	const lead = opts.lead ?? [];
	const base = {
		stockCode: model.stockCode,
		corpName: model.corpName,
		perspectiveKey: model.perspectiveKey,
		perspectiveLabel: model.perspectiveLabel,
		asOf: model.asOf,
		heroUrls
	};
	// lead(편집 계약 슬라이드)가 있으면 그것이 표지·서사 — 자동 cover 생략. 없으면 자동 cover.
	const cards: CarouselCard[] = lead.length
		? [...lead]
		: [
				{
					kind: 'cover',
					corpName: model.corpName,
					stockCode: model.stockCode,
					perspectiveLabel: model.perspectiveLabel,
					conclusion: hook(model.conclusion, 70), // 표지는 한 줄 후킹(리포트 결론 문단 전체 금지)
					dataBasis: model.dataBasis,
					chapter: CH_COVER
				}
			];
	// 편집 lead 표지도 첫 카드를 표지 챕터로(네비 첫 앵커) — 이미 chapter 있으면 보존.
	if (cards[0] && !cards[0].chapter) cards[0].chapter = CH_COVER;

	// 미구현 관점 → 정직 빈 카드(broken img 아님). lead 가 있으면 편집 슬라이드는 보존.
	if (model.pending) {
		if (!lead.length) cards.push({ kind: 'empty', reason: `${model.perspectiveLabel} 관점은 다음 사이클에 추가됩니다.` });
		assignHeroes(cards, heroUrls);
		return { ...base, cards };
	}

	const hasLeadKpis = cards.some((c) => c.kind === 'kpis');
	const headlineKpis = model.headlineKpis.filter((m) => isFilledMetricValue(m.value));
	if (!hasLeadKpis && headlineKpis.length) cards.push({ kind: 'kpis', heading: '핵심 지표', chapter: CH_KPIS, metrics: headlineKpis });
	// 재무 백본 = 터미널 중간패널 재무 그리드를 **보는 관점 순서** 그대로 한 장씩(각 장 = MiniFinChart 그래프
	// + 표 한 세트). 손익→현금→효율→체력. cardKey 로 번들 카드 선택. 스파크라인(table) 금지.
	for (const p of FIN_PERSPECTIVES) cards.push({ kind: 'finChart', heading: p.heading, sub: p.sub, chapter: CH_FIN, stockCode: model.stockCode, cardKey: p.key });

	// 사업·운영 깊은 카드 — 주석 구성(부문별매출·비용성격별)을 수익성 관점에만 주입(맥락 적합·5덱 비대화 방지).
	// rt.report.noteSeries 직독(별도 bake 0). 단일부문/미공시면 compositionToShare 가 null → 조건부 skip(핵심만).
	if (model.perspectiveKey === 'earningsPower' && opts.noteSeries) {
		const seg = compositionToCard(opts.noteSeries.segment, '부문별 매출', '어디서 버나');
		const cost = compositionToCard(opts.noteSeries.cost, '비용 체질', '돈을 뭐에 쓰나');
		if (seg) cards.push(seg);
		if (cost) cards.push(cost);
	}

	// 큐레이션 order: 섹션 key 화이트리스트로 필터/재정렬(없으면 원순서). 미지정 key 는 무시(누락 surface 는 audit).
	let sections = model.sections;
	if (spec?.order?.length) {
		const rank = new Map(spec.order.map((k, i) => [k, i]));
		sections = model.sections.filter((s) => rank.has(s.key)).sort((a, b) => rank.get(a.key)! - rank.get(b.key)!);
	}

	for (const sec of sections) {
		const { head, sub } = splitTitle(sec.title);
		const headCtx: HeadCtx = { heading: head, sub, engine: sec.sourceEngine };
		const card = pickSectionCard(sec.blocks, headCtx); // 섹션당 1장(시각 우선) — 텍스트 도배·과다 슬라이드 방지
		if (card) {
			const note = spec?.notes?.[sec.key];
			if (note) card.note = note;
			card.chapter = CH_BIZ;
			cards.push(card);
		}
	}

	// 종합(closing)·자동 산문 제거 — 자동은 표·그래프만. 종합/서사는 수기 editorial 슬라이드(carousel: 블록)로.

	assignHeroes(cards, heroUrls);
	return { ...base, cards };
}

// 재무 백본 관점 카드 — 터미널 중간패널 재무 그리드(financeSource) 키를 보는 순서대로(손익→현금→효율→체력).
// 각 키가 MiniFinChart 한 장으로 렌더된다(그래프+표 세트). 관점 대표 카드 하나씩.
const FIN_PERSPECTIVES: { key: string; heading: string; sub: string }[] = [
	// 손익 — 얼마나 버나
	{ key: 'incomeBreakdown', heading: '손익구조', sub: '매출에서 이익까지' },
	{ key: 'costStructure', heading: '비용구조', sub: '원가·판관비가 매출을 먹는 정도' },
	{ key: 'marginTrend', heading: '이익률', sub: '매출총이익률·영업이익률·순이익률 추이' },
	// 현금 — 이익이 진짜인가
	{ key: 'cashflowSigned', heading: '현금흐름', sub: '영업·투자·재무 현금' },
	{ key: 'cashConversion', heading: '이익의 현금화', sub: '순이익이 진짜 현금인가' },
	{ key: 'fcfTrend', heading: '잉여현금흐름', sub: '쓰고 남는 현금' },
	// 효율 — 자본을 잘 굴리나
	{ key: 'returnTrend', heading: '자본수익', sub: '자기자본·자산 수익률' },
	{ key: 'dupont', heading: '자기자본수익률 분해', sub: '마진·회전·레버리지' },
	// 체력 — 버틸 수 있나
	{ key: 'assetComposition', heading: '자산구조', sub: '무엇으로 구성됐나' },
	{ key: 'leverageTrend', heading: '레버리지·유동', sub: '버틸 수 있나' }
];

// 자동 섹션 슬라이드 = **시각 그래프만**(line/bars/share). 표(table)는 스파크라인이 손익구조를 못 보여줘
// 금지 — 재무는 위 FIN_PERSPECTIVES(MiniFinChart)로 그린다. 산문·신호·지표 자동 생성도 금지(수기 editorial).
const AUTO_VISUAL = new Set(['line', 'bars', 'share']);
const KIND_RANK: Record<string, number> = { line: 0, bars: 0, share: 1 };
function pickSectionCard(blocks: ReportBlock[], head: HeadCtx): CarouselCard | null {
	const cards = blocks
		.map((b) => projectBlock(b, head))
		.filter((c): c is CarouselCard => c !== null && AUTO_VISUAL.has(c.kind));
	if (!cards.length) return null;
	return cards.sort((a, b) => (KIND_RANK[a.kind] ?? 9) - (KIND_RANK[b.kind] ?? 9))[0];
}

/** hero 사진 전부를 슬라이드에 순환 배정 — 한 장도 안 빠지게. 이미 bg 있는 카드(편집 계약 image)는 보존. */
function assignHeroes(cards: CarouselCard[], heroUrls: string[]): void {
	if (!heroUrls.length) return;
	cards.forEach((c, i) => {
		if (c.kind !== 'empty' && !c.bg) c.bg = heroUrls[i % heroUrls.length];
	});
}

/** buildReport 결과(또는 skip) → 덱. skip 도 정직 카드로 렌더(빈 화면 금지). */
export function projectResult(
	result: ReportResult,
	perspectiveLabel: string,
	opts: { heroUrls?: string[]; spec?: CarouselSpec; lead?: CarouselCard[]; noteSeries?: NoteSeriesBundle | null } = {}
): CarouselDeck {
	if (isSkipped(result)) {
		// 데이터 skip 이어도 편집 계약 슬라이드(lead)는 그대로 보여준다(굽지 않은 손글). 없으면 정직 빈 카드.
		const cards = opts.lead?.length ? [...opts.lead] : [{ kind: 'empty' as const, reason: result.reason }];
		return {
			stockCode: result.stockCode,
			corpName: result.stockCode,
			perspectiveKey: '',
			perspectiveLabel,
			asOf: '',
			heroUrls: opts.heroUrls ?? [],
			cards
		};
	}
	return projectReport(result, opts);
}

/** 5관점 통합 thesis → 덱 머리에 붙일 closing 카드(있으면). LLM·신규합성 0(overview.thesis 그대로). */
export function overviewClosingCard(overview: OverviewModel | null): CarouselCard | null {
	const t = clean(overview?.thesis ?? '').trim();
	return t ? { kind: 'closing', heading: '5관점 통합', thesis: t } : null;
}
