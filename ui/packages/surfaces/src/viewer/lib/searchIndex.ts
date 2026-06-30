// 공시뷰어 인-페이지 검색 · gridBySection(브라우저 보유) 위 BM25 역인덱스. 서버·임베딩·LLM 0.
//
// 설계: 한국어 음절 bigram(조사 변형 흡수, 형태소 0) + BM25 + 큐레이션 동의어확장. 표(blockType='table')는
// 라벨만 인덱싱(거대표 13MB 본문 폭주 차단 · 표는 라벨/섹션으로 찾음). 빌드는 타임슬라이싱(메인스레드 비차단).
// 실측 검증: tests/_attempts/viewerSearch/ (삼성·SK·카카오 진짜 panel, 빌드 0.76s·쿼리 0.3ms). README 참조.

import type { PanelBundle, PanelRow } from './types';

const HANGUL = /[가-힣]+/g;
const ASCII = /[A-Za-z]{2,20}/g;
const TAG = /<[^>]+>/g;
const ENT = /&[a-zA-Z#0-9]+;/g;
const WS = /\s+/g;

// 한국어 음절 bigram + ascii 단어 (숫자 제외 = vocab 오염 차단). 가-힣 은 BMP 라 surrogate 무관.
export function tokenizeBigram(text: string): string[] {
	const out: string[] = [];
	const hg = text.match(HANGUL);
	if (hg) {
		for (const run of hg) {
			if (run.length === 1) out.push(run);
			else for (let i = 0; i < run.length - 1; i++) out.push(run.slice(i, i + 2));
		}
	}
	const ac = text.match(ASCII);
	if (ac) for (const w of ac) out.push(w.toLowerCase());
	return out;
}

// 검색용 경량 평문화 · 태그·엔티티→공백, 공백 1회 정규화. (cell.ts stripInlineTags 는 캡션파싱용 6패스라
// 대량 인덱싱엔 과함 · 실측 2배 느림. 인덱싱은 단일라인 평문이면 충분.)
export function plainText(raw: string): string {
	return raw.replace(TAG, ' ').replace(ENT, ' ').replace(WS, ' ').trim();
}

// ── 금액 추출 (원 단위) · "100억 이상" 같은 숫자/조건 검색용. tests/_attempts/viewerSearch/constraintFacet.py
// 검증판 1:1. 명시단위 조/억만, "조" 다의어(兆 vs 條 법조항) 2중 차단: 앞 '제' 배제 + 조는 뒤 원/억 동반시만. ──
const AMT_KR = /(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s?(조|억)(?=\s*원|[\s,.)\]]|$)/g;
const UNIT_MULT: Record<string, number> = { 조: 1e12, 억: 1e8 };
// 셀 1개(text)→최대 금액(원). 행 전체 join 호출 = 행 max, 단일 셀 호출 = per-period 금액(diff.ts 재사용).
export function maxAmountKrw(text: string): number {
	let max = 0;
	AMT_KR.lastIndex = 0;
	let m: RegExpExecArray | null;
	while ((m = AMT_KR.exec(text)) !== null) {
		if (text.slice(Math.max(0, m.index - 2), m.index).includes('제')) continue; // 제N조 = 법조항(條)
		if (m[2] === '조') {
			const tail = text.slice(m.index + m[0].length, m.index + m[0].length + 14);
			if (!/^\s*원/.test(tail) && !/^\s*[\d,]+\s*억/.test(tail)) continue; // 兆(금액)은 뒤 원/억 동반시만
		}
		const v = parseFloat(m[1].replace(/,/g, '')) * UNIT_MULT[m[2]];
		if (v > max) max = v;
	}
	return max;
}

// 큐레이션 동의어 · dartlab `ngramIndex._L0_INFORMAL`(43키) + 공시 도메인 상식 시드. 운영자 수동 관리.
// PMI/공기행렬 자동발굴 금지(단일회사 코퍼스 동어반복 인공물 · project_unified_search_table §8 격하).
const SYNONYMS: Record<string, string[]> = {
	부채: ['차입금', '사채', '우발부채', '지급보증', '리스부채'],
	차입금: ['사채', '단기차입', '장기차입', 'borrowings'],
	위험: ['리스크', '불확실성', '위험요인'],
	소송: ['계류', '손해배상', '분쟁', '피소', '제소'],
	배당: ['배당금', '현금배당', '현물배당', '배당성향'],
	자사주: ['자기주식', '자기주식취득', '자기주식소각'],
	스톡옵션: ['주식매수선택권', '주식기준보상'],
	감사인: ['감사의견', '감사보고서', '내부회계관리', '외부감사'],
	특수관계자: ['특수관계', '이해관계자', '관계기업', '종속기업'],
	손상: ['손상차손', '영업권', '회수가능액'],
	합병: ['인수', '사업결합', '분할'],
	증자: ['유상증자', '무상증자', '신주발행'],
	전환사채: ['전환사채', '신주인수권부사채', '교환사채'],
	리스: ['리스부채', '사용권자산', '운용리스', '금융리스'],
	충당부채: ['충당부채', '우발부채', '복구충당', '판매보증'],
	파생: ['파생상품', '선도', '스왑', '헤지']
};

export interface IndexedRow {
	sectionKey: string;
	rowIndex: number; // gridBySection.get(sectionKey) 내 index (PanelMatrix 행 i 와 정렬 → glow 타깃)
	chapter: string;
	section: string;
	block: string;
	scope: string;
	blockType: 'text' | 'table';
	cells: Record<string, string>; // period → 평문 셀 (스니펫·hit period 용)
	tf: Map<string, number>;
	len: number;
	maxAmount: number; // 행 본문 최대 금액(원) · "100억 이상" 조건검색 필터용. 없으면 0.
}

export interface SearchIndex {
	rows: IndexedRow[];
	postings: Map<string, number[]>;
	df: Map<string, number>;
	avgdl: number;
	vocab: number;
	periods: string[]; // bundle.periods (최신좌측 timeline SSOT) · 근거 기간선택·recency 랭킹의 정본
}

export interface SearchHit {
	sectionKey: string;
	rowIndex: number;
	chapter: string;
	section: string;
	block: string;
	scope: string;
	period: string;
	score: number;
	snippet: string;
	matchKind: 'text' | 'table' | 'amount';
	matchedTerms: string[];
	stale: boolean; // 근거 셀이 이 행의 더 최신 셀보다 옛것 = "이 항목의 최근 언급은 과거" (UX 정직 표기)
}

export interface BuildOpts {
	/** 표 행 본문도 토큰화할지. 기본 false = 표는 라벨만(거대표 폭주 차단, 표는 라벨로 찾음). */
	tableBody?: boolean;
	/** 셀당 토큰화 상한 글자수(거대 텍스트셀 방어). 기본 4000. */
	cellCap?: number;
}

interface Acc {
	rows: IndexedRow[];
	postings: Map<string, number[]>;
	df: Map<string, number>;
	totalLen: number;
}

// 한 행(PanelRow) → acc 누적. buildIndex/buildIndexChunked 공용 (parity 보장).
function indexRow(acc: Acc, sectionKey: string, rowIndex: number, r: PanelRow, opts: Required<BuildOpts>): void {
	const cells: Record<string, string> = {};
	for (const [p, raw] of Object.entries(r.cells)) {
		if (raw) cells[p] = plainText(raw);
	}
	if (Object.keys(cells).length === 0) return;
	const label = `${r.chapter} ${r.sectionLeaf} ${r.blockLeaf}`;
	const skipBody = !opts.tableBody && r.blockType === 'table';
	const bodyText = skipBody
		? ''
		: Object.values(cells)
				.map((c) => (c.length > opts.cellCap ? c.slice(0, opts.cellCap) : c))
				.join(' ');
	const toks = tokenizeBigram(label + ' ' + bodyText);
	const tf = new Map<string, number>();
	for (const t of toks) tf.set(t, (tf.get(t) ?? 0) + 1);
	const idx = acc.rows.length;
	for (const t of tf.keys()) {
		let lst = acc.postings.get(t);
		if (!lst) acc.postings.set(t, (lst = []));
		lst.push(idx);
		acc.df.set(t, (acc.df.get(t) ?? 0) + 1);
	}
	const len = toks.length || 1;
	acc.totalLen += len;
	acc.rows.push({
		sectionKey,
		rowIndex,
		chapter: r.chapter,
		section: r.sectionLeaf,
		block: r.blockLeaf,
		scope: r.scope ?? '',
		blockType: r.blockType,
		cells,
		tf,
		len,
		maxAmount: maxAmountKrw(Object.values(cells).join(' '))
	});
}

function finalize(acc: Acc, bundle: PanelBundle): SearchIndex {
	return {
		rows: acc.rows,
		postings: acc.postings,
		df: acc.df,
		avgdl: acc.totalLen / Math.max(1, acc.rows.length),
		vocab: acc.df.size,
		periods: bundle.periods // SSOT(최신좌측) 보존 · 호출 시 cells 키 재정렬 금지(과거기간 근거 버그 근본차단)
	};
}

function defaults(opts: BuildOpts): Required<BuildOpts> {
	return { tableBody: opts.tableBody ?? false, cellCap: opts.cellCap ?? 4000 };
}

/** 동기 빌드 · 작은 회사·테스트용. 큰 회사는 buildIndexChunked 권장. */
export function buildIndex(bundle: PanelBundle, opts: BuildOpts = {}): SearchIndex {
	const o = defaults(opts);
	const acc: Acc = { rows: [], postings: new Map(), df: new Map(), totalLen: 0 };
	for (const [sectionKey, prows] of bundle.gridBySection) {
		for (let i = 0; i < prows.length; i++) indexRow(acc, sectionKey, i, prows[i], o);
	}
	return finalize(acc, bundle);
}

// MessageChannel 기반 yield-to-main (setTimeout 4ms clamp 회피, 진짜 macrotask 양보 = 렌더 비차단).
function yieldToMain(): Promise<void> {
	return new Promise((resolve) => {
		const ch = new MessageChannel();
		ch.port1.onmessage = () => resolve();
		ch.port2.postMessage(null);
	});
}

/**
 * 타임슬라이싱 빌드 · 섹션 묶음마다 메인스레드에 양보(잼 0). 결과는 buildIndex 와 동일(parity).
 * 거대표 회사(카카오 1.4s)도 16ms 프레임 안 넘게 끊어 빌드.
 */
export async function buildIndexChunked(bundle: PanelBundle, opts: BuildOpts = {}, chunkSections = 8): Promise<SearchIndex> {
	const o = defaults(opts);
	const acc: Acc = { rows: [], postings: new Map(), df: new Map(), totalLen: 0 };
	let since = 0;
	for (const [sectionKey, prows] of bundle.gridBySection) {
		for (let i = 0; i < prows.length; i++) indexRow(acc, sectionKey, i, prows[i], o);
		if (++since >= chunkSections) {
			since = 0;
			await yieldToMain();
		}
	}
	return finalize(acc, bundle);
}

const K1 = 1.5;
const B = 0.75;
// 공시 Q&A 는 기본 최신우선 · 근거의 최신 needle 셀이 오래될수록 점수 감쇠(1/(1+λ·rank)). λ=0.08 →
// 5기간전 ×0.71, 40기간전 ×0.24. 강한 relevance 는 살리되 옛 근거를 최신 위로 못 올린다(불만2 "과거기간" 직격).
const RECENCY_LAMBDA = 0.08;
const RERANK_POOL = 50; // BM25 상위 풀만 recency 재랭킹(비용 bound, topK ≪ pool)
const RRF_K = 60; // Reciprocal Rank Fusion 상수(표준) · plain BM25 ⊕ 섹션scoping 융합 시 1/(K+rank) 합
const SCORE_CUT_RATIO = 0.25; // top1 대비 미만 곁가지 컷(불만1 "안맞는 근거" 완화, 최소 1건 보장)
// 텍스트 행인데 표면어가 어느 셀에도 없음 = bigram 유령매칭(예 "영업이익" 질의에 이익잉여금 행 · 영업·이익 조각만
// 맞고 문구는 없음). 감점해 진짜 문구 든 행을 올린다. 표(table) 행은 라벨매칭이 본가치라 제외(표라벨 정답 보존).
const SURFACELESS_PENALTY = 0.5;

function recencyWeight(rank: number): number {
	return 1 / (1 + RECENCY_LAMBDA * rank);
}

/** 쿼리 → bigram 가중치 + 적용된 동의어 목록(칩 노출용). */
export function expandQuery(query: string, expand = true): { weights: Map<string, number>; added: string[] } {
	const weights = new Map<string, number>();
	for (const t of tokenizeBigram(query)) weights.set(t, 1.0);
	const added: string[] = [];
	if (expand) {
		// 동의어 발화 = *어절 경계* 매칭 (옛 query.replace(공백) substring 은 "확정급여부채"→부채, "리스크"→리스 등
		// 단어경계 넘은 오발화 다수 · 곁가지 동의어를 끌어왔다). 어절이 key 와 일치 또는 key 로 시작할 때만.
		const words = query.toLowerCase().match(/[가-힣a-z0-9]{2,}/g) ?? [];
		for (const [key, syns] of Object.entries(SYNONYMS)) {
			const k = key.toLowerCase();
			if (words.some((w) => w === k || w.startsWith(k))) {
				for (const syn of syns) {
					for (const bg of tokenizeBigram(syn)) weights.set(bg, Math.max(weights.get(bg) ?? 0, 0.5));
					added.push(syn);
				}
			}
		}
	}
	return { weights, added };
}

// ── 숫자/조건 쿼리 파싱 · 기존 검색창이 "100억 이상", "1조 초과", "50억 이하"를 이해(새 UI 0). ──
// 작은 bounded 집합(조/억 × 이상·초과·넘는·넘게=gte / 이하·미만·미달=lte). 패턴이 끝없이 늘면 = 덕지덕지 신호.
const AMOUNT_Q = /(\d[\d,]*(?:\.\d+)?)\s*(조|억)\s*(?:원\s*)?(이상|초과|넘는|넘게|이하|미만|미달)/;
export interface AmtConstraint {
	min?: number;
	max?: number;
}
export function parseConstraint(query: string): { c: AmtConstraint | null; residual: string } {
	const m = query.match(AMOUNT_Q);
	if (!m || m.index === undefined) return { c: null, residual: query };
	const v = parseFloat(m[1].replace(/,/g, '')) * UNIT_MULT[m[2]];
	const gte = m[3] === '이상' || m[3] === '초과' || m[3] === '넘는' || m[3] === '넘게';
	const residual = (query.slice(0, m.index) + ' ' + query.slice(m.index + m[0].length)).replace(/\s+/g, ' ').trim();
	return { c: gte ? { min: v } : { max: v }, residual };
}
export function amtOk(amt: number, c: AmtConstraint): boolean {
	return amt > 0 && (c.min === undefined || amt >= c.min) && (c.max === undefined || amt <= c.max);
}

function surfaceNeedles(query: string, added: string[]): string[] {
	const needles = new Set<string>();
	for (const source of [query, ...added]) {
		for (const m of source.matchAll(/[가-힣A-Za-z0-9]{2,}/g)) {
			const v = m[0].trim();
			if (v.length >= 2) needles.add(v);
		}
	}
	return [...needles].sort((a, b) => b.length - a.length);
}

interface EvPeriod { period: string; rank: number; hasNeedle: boolean; stale: boolean }

// 근거 기간 선택 · SSOT periods(최신좌측) 순회: needle 든 *최신* 셀. 없으면 최신 비어있지 않은 셀
// (옛 fallback 은 가장 오래된 셀로 추락했음 · 2015Q4 소송 같은 헛근거 근본차단). needlesLc = 소문자 needle.
// stale = needle 셀이 이 행의 더 최신 비어있지 않은 셀보다 옛것 = "이 항목의 최근 언급은 과거".
function evidencePeriod(cells: Record<string, string>, periods: string[], needlesLc: string[]): EvPeriod {
	let firstNonEmpty = -1;
	for (let i = 0; i < periods.length; i++) {
		const cell = cells[periods[i]];
		if (!cell) continue;
		if (firstNonEmpty < 0) firstNonEmpty = i;
		const lc = cell.toLowerCase();
		for (const needle of needlesLc) {
			if (lc.includes(needle)) {
				return { period: periods[i], rank: i, hasNeedle: true, stale: i > firstNonEmpty };
			}
		}
	}
	const idx = firstNonEmpty >= 0 ? firstNonEmpty : 0;
	return { period: periods[idx] ?? '', rank: idx, hasNeedle: false, stale: false };
}

// 선택된 셀에서 스니펫 + 매칭어. (period 선택은 evidencePeriod 가 담당 · 셀/period 항상 정합.)
function snippetAt(cell: string, needles: string[]): { snippet: string; matchedTerms: string[] } {
	const lc = cell.toLowerCase();
	let bestAt = Number.POSITIVE_INFINITY;
	const matched: string[] = [];
	for (const needle of needles) {
		const at = lc.indexOf(needle.toLowerCase());
		if (at >= 0) {
			bestAt = Math.min(bestAt, at);
			matched.push(needle);
		}
	}
	if (matched.length) {
		const start = Math.max(0, bestAt - 34);
		const end = Math.min(cell.length, bestAt + 92);
		return { snippet: cell.slice(start, end), matchedTerms: matched.slice(0, 8) };
	}
	return { snippet: cell.slice(0, 96), matchedTerms: [] };
}

export function search(
	idx: SearchIndex,
	query: string,
	opts: { expand?: boolean; topK?: number; dedupe?: boolean; scopeSections?: string[]; scopeTerms?: string[] } = {}
): { hits: SearchHit[]; added: string[] } {
	// 조건("100억 이상")이 있으면 떼어내고, 남은 표면어로 BM25 + 금액 필터.
	const { c, residual } = parseConstraint(query);
	const lexQuery = c ? residual : query;
	const { weights, added } = expandQuery(lexQuery, opts.expand ?? true);
	const n = idx.rows.length;
	if (n === 0) return { hits: [], added };
	const scores = new Map<number, number>();
	for (const [term, qw] of weights) {
		const d = idx.df.get(term) ?? 0;
		if (d <= 0) continue;
		const idf = Math.log((n - d + 0.5) / (d + 0.5) + 1.0);
		const postings = idx.postings.get(term);
		if (!postings) continue;
		for (const pos of postings) {
			const row = idx.rows[pos];
			const tf = row.tf.get(term) ?? 0;
			const denom = tf + K1 * (1 - B + B * (row.len / idx.avgdl));
			if (denom > 0) scores.set(pos, (scores.get(pos) ?? 0) + (qw * idf * (tf * (K1 + 1))) / denom);
		}
	}

	// 근거 기간/스니펫에 쓸 표면어. evidencePeriod 재계산을 행당 1회로 메모.
	const needles = surfaceNeedles(lexQuery, added);
	const needlesLc = needles.map((s) => s.toLowerCase());
	const epCache = new Map<number, EvPeriod>();
	const epOf = (pos: number): EvPeriod => {
		let e = epCache.get(pos);
		if (!e) {
			e = evidencePeriod(idx.rows[pos].cells, idx.periods, needlesLc);
			epCache.set(pos, e);
		}
		return e;
	};

	// 2차 신호 · 섹션scoping(scopeSections). RRF 융합용. 없으면 순수 BM25.
	// scoped 레인 = (질의 ∪ 예측 intent canon=scopeTerms) BM25 를 *예측 target 섹션 행*에만 누적. canon 이 구어질의↔본문
	// 어휘 간극 흡수("돌아가"→"가동률"), 섹션 제약이 곁가지 차단. 라우팅 틀려도 plain 보존 → always-safe.
	// 5업종 held-out top-6 섹션도달 56~71%→92~98%(pipeline.py verify). 재계산 비용 = scope 행만 순회.
	let secondary: Map<number, number> | undefined;
	if (opts.scopeSections && opts.scopeSections.length) {
		const scope = opts.scopeSections;
		const inScope = (pos: number): boolean => {
			const r = idx.rows[pos];
			return scope.some((sec) => (r.chapter + ' ' + r.section).includes(sec));
		};
		const sw = new Map<string, number>(weights);
		if (opts.scopeTerms) for (const t of tokenizeBigram(opts.scopeTerms.join(' '))) if (!sw.has(t)) sw.set(t, 0.5);
		secondary = new Map<number, number>();
		for (const [term, qw] of sw) {
			const d = idx.df.get(term) ?? 0;
			if (d <= 0) continue;
			const idf = Math.log((n - d + 0.5) / (d + 0.5) + 1.0);
			const postings = idx.postings.get(term);
			if (!postings) continue;
			for (const pos of postings) {
				if (!inScope(pos)) continue;
				const row = idx.rows[pos];
				const tf = row.tf.get(term) ?? 0;
				const denom = tf + K1 * (1 - B + B * (row.len / idx.avgdl));
				if (denom > 0) secondary.set(pos, (secondary.get(pos) ?? 0) + (qw * idf * (tf * (K1 + 1))) / denom);
			}
		}
	}
	// 후보 랭킹 · 표면어 BM25 있으면: 상위 풀만 recency 재랭킹(최신우선) → 상대컷(곁가지 제거).
	// 순수 조건("100억 이상")이면 조건 만족 행을 금액 내림차순. 둘 다 없으면 빈 결과.
	const hasSecond = !!secondary && secondary.size > 0;
	let ranked: Array<[number, number]>;
	if (scores.size > 0 || hasSecond) {
		const bmSorted = [...scores.entries()].sort((a, b) => b[1] - a[1]);
		const bmRank = new Map<number, number>();
		bmSorted.forEach(([pos], i) => bmRank.set(pos, i));

		let candidates: number[];
		let baseScore: (pos: number) => number;
		if (hasSecond) {
			// 융합 = plain BM25(어휘) ⊕ 섹션scoping RRF. 후보 = 양쪽 상위 풀 union(라우팅 틀려도 plain 보존).
			const dnSorted = [...secondary!.entries()].sort((a, b) => b[1] - a[1]);
			const dnRank = new Map<number, number>();
			dnSorted.forEach(([pos], i) => dnRank.set(pos, i));
			const pool = new Set<number>();
			for (const [pos] of bmSorted.slice(0, RERANK_POOL)) pool.add(pos);
			for (const [pos] of dnSorted.slice(0, RERANK_POOL)) pool.add(pos);
			candidates = [...pool];
			baseScore = (pos) =>
				(bmRank.has(pos) ? 1 / (RRF_K + bmRank.get(pos)!) : 0) + (dnRank.has(pos) ? 1 / (RRF_K + dnRank.get(pos)!) : 0);
		} else {
			candidates = bmSorted.slice(0, RERANK_POOL).map(([pos]) => pos);
			baseScore = (pos) => scores.get(pos) ?? 0;
		}
		if (c) candidates = candidates.filter((pos) => amtOk(idx.rows[pos].maxAmount, c));

		const reranked = candidates
			.map((pos): [number, number] => {
				const ep = epOf(pos);
				let s = baseScore(pos) * recencyWeight(ep.rank);
				// 표면어 없는 텍스트행 감점은 *plain BM25 단독*에서만(bigram 유령매칭 교정). 섹션scoping 모드선 canon 보강어 매칭이 정상이라 제외.
				if (!hasSecond && idx.rows[pos].blockType === 'text' && !ep.hasNeedle) s *= SURFACELESS_PENALTY;
				return [pos, s];
			})
			.sort((a, b) => b[1] - a[1]);
		const cut = (reranked[0]?.[1] ?? 0) * SCORE_CUT_RATIO;
		ranked = reranked.filter(([, s]) => s >= cut);
		if (!ranked.length && reranked.length) ranked = [reranked[0]]; // 최소 1건 보장
	} else if (c) {
		ranked = idx.rows
			.map((r, i): [number, number] => [i, r.maxAmount])
			.filter(([, amt]) => amtOk(amt, c))
			.sort((a, b) => b[1] - a[1])
			.slice(0, RERANK_POOL);
	} else {
		return { hits: [], added };
	}

	// 결과 dedupe · 같은 (섹션,블록)의 scope(연결/별도)·leafSeq 변형을 하나로 접어 top-K 가 서로 다른 항목이
	// 되게(출시 후 감사: 쿼리당 평균 1.2~1.6 중복 = "같은 항목 4번" 제거). 첫 등장(최고 랭킹)만 유지.
	const topK = opts.topK ?? 8;
	const seenLabel = new Set<string>();
	const top: Array<[number, number]> = [];
	for (const entry of ranked) {
		const r = idx.rows[entry[0]];
		const label = r.sectionKey + '␟' + r.block;
		if (opts.dedupe ?? true) {
			if (seenLabel.has(label)) continue;
			seenLabel.add(label);
		}
		top.push(entry);
		if (top.length >= topK) break;
	}
	const hits: SearchHit[] = top.map(([pos, sc]) => {
		const row = idx.rows[pos];
		const ep = epOf(pos);
		const { snippet, matchedTerms } = snippetAt(row.cells[ep.period] ?? '', needles);
		return {
			sectionKey: row.sectionKey,
			rowIndex: row.rowIndex,
			chapter: row.chapter,
			section: row.section,
			block: row.block,
			scope: row.scope,
			period: ep.period,
			score: sc,
			snippet,
			matchKind: c && amtOk(row.maxAmount, c) ? 'amount' : row.blockType === 'table' ? 'table' : 'text',
			matchedTerms,
			stale: ep.stale
		};
	});
	return { hits, added };
}
