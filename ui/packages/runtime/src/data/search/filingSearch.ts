// 전역 공시 본문 검색 · 질의어 postings + top-k meta 만 HTTP range fetch(서버리스·exact BM25).
// 공통배선: 퍼블릭·로컬 동일 코어(DataCore)·동일 경로(hf 통파일 / hfRange 조각). 인덱스 sidecar는
// fieldIndex.saveShardedSegment 산출(postings/terms/docLengths/meta.bin + main_stems.json + search_meta.json).
// 검증(_attempts/filingPostingsFetch): byte-range fetch BM25 = full BM25 overlap 1.0000(exact).
// 회사 인덱스(universe/query)는 별개 feature(census A-11) · 본 포트는 queryFilings(공시 코퍼스)만 구현.
//
// ★배포 layout: 인덱스 파일은 flat 경로가 아니라 run-scoped staging 에 있고, flat `manifest.json` 이
// 안정 pointer(`fileSources`: 파일명→staging 경로)다(publishIndex.manifestPointer 모델). 그래서 항상
// manifest 를 먼저 읽어 fileSources 로 각 파일을 resolve 한다 · CI 가 새 빌드를 publish 하면 pointer 만
// 갈아끼워도 다음 세션이 자동 추종(공통배선이 publish SSOT 와 일치). fileSources 부재 시 flat fallback.
import type { DataCore } from '../fetch/request';
import type { SearchPort, FilingHit, FilingSearchQuery } from '@dartlab/ui-contracts';

const K1 = 1.5;
const B = 0.75;
const HANGUL = /[가-힣]+/g;
const ASCII = /[A-Za-z]{2,20}/g;

// searchIndex.ts/tokenizeContent 와 byte-parity: 한글 음절 bigram + 영문 소문자(숫자 제외).
function tokenizeBigram(text: string): string[] {
	if (!text) return [];
	const out: string[] = [];
	for (const m of text.matchAll(HANGUL)) {
		const run = m[0];
		if (run.length === 1) out.push(run);
		else for (let i = 0; i < run.length - 1; i++) out.push(run.slice(i, i + 2));
	}
	for (const m of text.matchAll(ASCII)) out.push(m[0].toLowerCase());
	return out;
}

// LEB128 unsigned varint · count 개 디코드(값 < 2^31 보장: docId<~5M, tf 소). 반환 (값, 다음 pos).
function readVarints(bytes: Uint8Array, pos: number, count: number): number[] {
	const vals = new Array<number>(count);
	for (let n = 0; n < count; n++) {
		let shift = 0;
		let val = 0;
		let byte: number;
		do {
			byte = bytes[pos++] ?? 0;
			val |= (byte & 0x7f) << shift;
			shift += 7;
		} while (byte & 0x80);
		vals[n] = val >>> 0;
	}
	return vals;
}

interface MetaCard {
	rcept_no?: string;
	corp_name?: string;
	stock_code?: string;
	report_nm?: string;
	rcept_dt?: string;
	source?: string;
	sourceRef?: string;
	snippet?: string;
}

interface SearchStats {
	stemDict: Record<string, number>;
	terms: Uint32Array; // stemId 별 (byteStart, gapLen, tfLen, df)
	docLengths: Uint32Array;
	// doc 별 meta.bin byte offset (nDocs+1·~3.7MB). scoring 엔 불필요(hydration 직전에만) → Promise 로 지연:
	// 콜드 임계경로서 제외하고 postings range-fetch+BM25 와 다운로드를 겹친다(첫 질의 latency↓·질의당 회귀 0).
	metaOffsetsP: Promise<BigUint64Array>;
	nDocs: number;
	avgDocLength: number;
	postingsPath: string; // resolve 된 postings.bin 경로(range fetch)
	metaPath: string; // resolve 된 meta.bin 경로(range fetch)
}

export interface FilingSearchOptions {
	/** 인덱스 tier. 기본 ``full``(flat ``dart/contentIndex/`` · 전체 코퍼스, range-fetch 라 클라 비용 동일).
	 *  그 외 tier 는 ``dart/contentIndex/{tier}/`` 서브디렉터리(예 lite). 둘 다 manifest pointer 경유. */
	tier?: string;
}

export function createSearchPort(core: DataCore, opts: FilingSearchOptions = {}): SearchPort {
	const tier = opts.tier ?? 'full';
	const prefix = tier === 'full' ? 'dart/contentIndex' : `dart/contentIndex/${tier}`;
	const manifestPath = `${prefix}/manifest.json`;
	let statsP: Promise<SearchStats> | null = null;
	let manifestP: Promise<{ resolve: (name: string) => string; builtAt: string | null }> | null = null;

	// flat `manifest.json`(pointer)을 *1회* 읽어 fileSources(파일명→staging 경로) resolve + builtAt(인덱스
	// 빌드시점, as-of 라벨용) 캐시. 부재 시 flat fallback. core.request 가 캐시하므로 stats(~10MB)와 무관하게
	// 경량(manifest 만)으로 builtAt 만 떼올 수 있다 · indexBuiltAt 는 콜드 stats 로드를 강제하지 않는다.
	function loadManifest(): Promise<{ resolve: (name: string) => string; builtAt: string | null }> {
		return (manifestP ??= (async () => {
			let fileSources: Record<string, string> = {};
			let builtAt: string | null = null;
			try {
				const manifest = await core.request<{ fileSources?: Record<string, string>; builtAt?: string }>({
					origin: 'hf',
					path: manifestPath,
					parse: (r) => r.json()
				});
				if (manifest && typeof manifest.fileSources === 'object' && manifest.fileSources) fileSources = manifest.fileSources;
				if (manifest && typeof manifest.builtAt === 'string') builtAt = manifest.builtAt;
			} catch {
				// manifest 부재(404)·파싱 실패 → flat fallback(전환기/직접배포 호환). 파일 fetch 가 정직히 실패한다.
			}
			return { resolve: (name: string) => fileSources[name] ?? `${prefix}/${name}`, builtAt };
		})());
	}

	// 단일 main 세그먼트(compact-only · delta 폐기). stats blob = 콜드 1회 캐시. 통파일 hf(프록시), 조각 hfRange.
	async function loadStats(): Promise<SearchStats> {
		const { resolve } = await loadManifest();
		const ab = (name: string) => core.request<ArrayBuffer>({ origin: 'hf', path: resolve(name), parse: (r) => r.arrayBuffer() });
		// metaOffsets(~3.7MB)는 hydration(최종 top-k meta fetch) 전까지 불필요 → fetch 만 킥오프하고 콜드
		// 임계경로(scoring)서 블로킹 안 함. core 가 캐시·dedup. 결과 0(early return) 시 await 안 될 수 있어
		// unhandledRejection 가드(실 소비처 await 는 정상 throw → queryFilings catch).
		const metaOffsetsP = ab('main.metaOffsets.bin').then((b) => new BigUint64Array(b));
		metaOffsetsP.catch(() => {});
		const [stemDict, termsBuf, dlBuf, meta] = await Promise.all([
			core.request<Record<string, number>>({ origin: 'hf', path: resolve('main_stems.json'), parse: (r) => r.json() }),
			ab('main.terms.bin'),
			ab('main.docLengths.bin'),
			core.request<{ nDocs: number; avgDocLength: number }>({ origin: 'hf', path: resolve('main.search_meta.json'), parse: (r) => r.json() })
		]);
		return {
			stemDict,
			terms: new Uint32Array(termsBuf),
			docLengths: new Uint32Array(dlBuf),
			metaOffsetsP,
			nDocs: meta.nDocs,
			avgDocLength: Math.max(meta.avgDocLength, 1),
			postingsPath: resolve('main.postings.bin'),
			metaPath: resolve('main.meta.bin')
		};
	}

	async function queryFilings(input: FilingSearchQuery): Promise<FilingHit[]> {
		const text = (input.text ?? '').trim();
		if (!text) return [];
		const tokens = tokenizeBigram(text);
		if (!tokens.length) return [];
		const stats = await (statsP ??= loadStats());
		const limit = Math.max(1, input.limit ?? 10);

		const seen = new Set<string>();
		const sids: number[] = [];
		for (const tok of tokens) {
			if (seen.has(tok)) continue;
			seen.add(tok);
			const sid = stats.stemDict[tok];
			if (sid !== undefined) sids.push(sid);
		}
		if (!sids.length) return [];

		// 질의어 term postings 조각만 병렬 range fetch(1 RTT wave) → exact BM25 누적.
		const scores = new Map<number, number>();
		await Promise.all(
			sids.map(async (sid) => {
				const byteStart = stats.terms[sid * 4] ?? 0;
				const gapLen = stats.terms[sid * 4 + 1] ?? 0;
				const tfLen = stats.terms[sid * 4 + 2] ?? 0;
				const df = stats.terms[sid * 4 + 3] ?? 0;
				if (!df) return;
				const buf = await core.requestBytes({ path: stats.postingsPath, start: byteStart, len: gapLen + tfLen });
				const u8 = new Uint8Array(buf);
				const gaps = readVarints(u8, 0, df);
				const tfs = readVarints(u8, gapLen, df);
				const idf = Math.log((stats.nDocs - df + 0.5) / (df + 0.5) + 1.0);
				let docId = 0;
				for (let i = 0; i < df; i++) {
					docId += gaps[i] ?? 0; // 첫 gap=절대 docId, 이후 delta → cumsum
					const tf = tfs[i] ?? 0;
					const dl = stats.docLengths[docId] || stats.avgDocLength;
					const norm = (tf * (K1 + 1)) / (tf + K1 * (1 - B + (B * dl) / stats.avgDocLength));
					scores.set(docId, (scores.get(docId) ?? 0) + idf * norm);
				}
			})
		);
		if (!scores.size) return [];

		const top = [...scores.entries()].sort((a, b) => b[1] - a[1]).slice(0, limit);

		// hydration · metaOffsets 합류(scoring 동안 병렬 다운로드돼 보통 이미 완료). top-k doc meta 만 range fetch.
		const metaOffsets = await stats.metaOffsetsP;
		return Promise.all(
			top.map(async ([docId, score]) => {
				const o0 = Number(metaOffsets[docId]);
				const o1 = Number(metaOffsets[docId + 1]);
				const buf = await core.requestBytes({ path: stats.metaPath, start: o0, len: o1 - o0 });
				const card = JSON.parse(new TextDecoder().decode(buf)) as MetaCard;
				return {
					rceptNo: card.rcept_no ?? '',
					corpName: card.corp_name ?? '',
					stockCode: card.stock_code ?? '',
					reportNm: (card.report_nm ?? '').trim(),
					rceptDt: card.rcept_dt ?? '',
					snippet: card.snippet ?? '',
					source: card.source ?? '',
					sourceRef: card.sourceRef ?? '',
					score
				} satisfies FilingHit;
			})
		);
	}

	// 인덱스 빌드시점(as-of 라벨) · manifest 만 읽어 builtAt 반환(콜드 stats ~10MB 강제 안 함). 부재 시 null.
	async function indexBuiltAt(): Promise<string | null> {
		return (await loadManifest()).builtAt;
	}

	const companyIndexUnwired = (): never => {
		throw new Error('[search] universe/query(회사 인덱스)는 별도 feature(census A-11) · 이 경로는 미배선. queryFilings(공시 본문)만 구현됨.');
	};
	return { universe: companyIndexUnwired, query: companyIndexUnwired, queryFilings, indexBuiltAt };
}
