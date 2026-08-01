import type { AsyncBuffer, FileMetaData, ParquetQueryFilter } from 'hyparquet';
import { HF_RESOLVE, hfRangeUrl } from '../origins/hf';

export type FetchLike = typeof fetch;

export interface HfObjectRef {
	path: string;
	url: string;
	size: number;
	etag: string | null;
	commit: string | null;
	acceptRanges: boolean;
	contentType: string | null;
}

export interface RangeRequestStat {
	url: string;
	range: string | null;
	status: number;
	bytes: number;
	durationMs: number;
}

export interface ParquetRangeSession {
	ref: HfObjectRef;
	file: AsyncBuffer;
	requests: RangeRequestStat[];
}

export interface ParquetMetadataSummary {
	path: string;
	size: number;
	rows: number;
	rowGroups: number;
	columns: string[];
	requests: RangeRequestStat[];
}

export interface ParquetRowsResult<T extends Record<string, unknown> = Record<string, unknown>> {
	rows: T[];
	requests: RangeRequestStat[];
}

export function hfUrl(path: string): string {
	return `${HF_RESOLVE}/${path.replace(/^\/+/, '')}`;
}

// HTTP 상태를 실어 나르는 읽기 실패. 호출측이 "미존재(404)"와 "일시 장애(5xx/네트워크)"를
// 구분해야 안내 문구가 갈린다 (404 를 "로드 실패" 로 뭉뚱그리면 우리 버그로 읽힌다).
// message 포맷은 기존 그대로 유지 (로그·기존 문자열 소비처 하위호환).
export class HfReadError extends Error {
	readonly status: number;
	readonly path: string;
	constructor(path: string, status: number, phase: string) {
		super(`${path} ${phase}: ${status}`);
		this.name = 'HfReadError';
		this.status = status;
		this.path = path;
	}
}

/** 미존재(404) 읽기 실패인지. 다른 에러·타입은 모두 false. */
export function isHfNotFound(e: unknown): boolean {
	return e instanceof HfReadError && e.status === 404;
}

// 동일 파일의 HEAD(범위 probe)는 세션 내 1 회만 · 반복 readParquetRows·lazy 좌측 팬의
// 불필요한 RTT 제거. 파일은 세션 중 불변이므로 ref(size/etag) 캐시 안전.
// 커스텀 fetchFn(측정/프록시 주입)은 캐시하지 않음.
const refCache = new Map<string, Promise<HfObjectRef>>();

export function headHfObject(path: string, fetchFn: FetchLike = fetch): Promise<HfObjectRef> {
	if (fetchFn !== fetch) return headHfObjectFresh(path, fetchFn);
	const hit = refCache.get(path);
	if (hit) return hit;
	const p = headHfObjectFresh(path, fetchFn).catch((e) => {
		refCache.delete(path);
		throw e;
	});
	refCache.set(path, p);
	return p;
}

async function headHfObjectFresh(path: string, fetchFn: FetchLike): Promise<HfObjectRef> {
	// range probe·세션은 HF 직결(hfRangeUrl) · 프록시 206 은 엣지캐시 불가라 7~9배 느림(origin.ts 참조).
	const url = hfRangeUrl(path);
	const resp = await fetchResilient(fetchFn, url, { headers: { Range: 'bytes=0-0' } });
	if (!resp.ok && resp.status !== 206) throw new HfReadError(path, resp.status, 'range probe 실패');
	const linkedSize = Number(resp.headers.get('x-linked-size'));
	const contentLength = Number(resp.headers.get('content-length'));
	const contentRange = resp.headers.get('content-range');
	const rangeSize = contentRange ? Number(contentRange.match(/\/(\d+)$/)?.[1]) : NaN;
	const size =
		Number.isFinite(linkedSize) && linkedSize > 0
			? linkedSize
			: Number.isFinite(rangeSize) && rangeSize > 0
				? rangeSize
				: contentLength;
	if (!Number.isFinite(size) || size <= 0) throw new Error(`${path} 크기 확인 실패`);
	await resp.arrayBuffer();
	return {
		path,
		// 안정 resolve URL 보관(서명된 cas-bridge 리다이렉트 URL 아님) · refCache 가 세션 내내 ref 를 재사용하므로
		// 서명 URL 캐시 시 만료 후 range 읽기가 깨진다. 매 요청이 stable URL 로 재해석된다(직결 redirect 비용은 측정 ~0.38s 에 포함).
		url,
		size,
		etag: resp.headers.get('etag') ?? resp.headers.get('x-linked-etag'),
		commit: resp.headers.get('x-repo-commit'),
		acceptRanges: resp.status === 206 || (resp.headers.get('accept-ranges') ?? '').toLowerCase() === 'bytes',
		contentType: resp.headers.get('content-type')
	};
}

export async function probeHfRange(
	path: string,
	range = 'bytes=0-15',
	fetchFn: FetchLike = fetch
): Promise<{ ref: HfObjectRef; status: number; contentRange: string | null; bytes: number }> {
	const ref = await headHfObject(path, fetchFn);
	const resp = await fetchFn(ref.url, { headers: { Range: range } });
	const bytes = (await resp.arrayBuffer()).byteLength;
	return {
		ref,
		status: resp.status,
		contentRange: resp.headers.get('content-range'),
		bytes
	};
}

// 범위요청 + 브라우저 HTTP 캐시 충돌(net::ERR_CACHE_OPERATION_NOT_SUPPORTED 등 · Range 응답이 캐시와 어긋날 때
// Chrome 이 던짐) → 캐시 우회(reload)로 1회 재시도. 잦은 "로드 실패" 가드.
export async function fetchResilient(fetchFn: FetchLike, input: Parameters<FetchLike>[0], init?: RequestInit): Promise<Response> {
	// 전이적 CDN 전파(갓 업로드/콜드 캐시)는 403/429/5xx 로 반환되거나 네트워크 throw → 짧은 백오프 재시도.
	// (lazy 이력 로드 시 콜드 parquet 의 transient 403 이 hyparquet throw → unhandled 로 새던 것 차단.)
	//
	// ⚠ Range 요청(206 Partial)은 프록시가 `Cache-Control: public` 을 줄 때 브라우저 HTTP 캐시가 부분응답을
	// 저장하려다 net::ERR_CACHE_OPERATION_NOT_SUPPORTED 로 throw 한다 → hyparquet range read 실패 → 회사별
	// parquet(정기공시·우측패널 등) 빈값. 과거 폴백 cache:'reload' 는 여전히 캐시에 WRITE 하므로 같은 에러가
	// 재발했다. 캐시를 읽지도 쓰지도 않는 'no-store' 만이 회피한다. 그래서 Range 요청은 처음부터 no-store,
	// 그 외(통파일 GET 등)는 캐시 이득을 살리되 실패 시 no-store 로 폴백한다.
	const LAST = 3;
	const rangeReq = !!new Headers(init?.headers).get('range');
	const noStore: RequestInit = { ...init, cache: 'no-store' };
	for (let attempt = 0; attempt <= LAST; attempt++) {
		try {
			const resp = await fetchFn(input, attempt === 0 && !rangeReq ? init : noStore);
			if (resp.ok || resp.status === 206) return resp;
			if (attempt < LAST && (resp.status === 403 || resp.status === 429 || resp.status >= 500)) {
				await new Promise((r) => setTimeout(r, 200 + 280 * attempt));
				continue;
			}
			return resp; // 최종 비-OK(404 등)는 그대로 · 호출측이 처리
		} catch {
			if (attempt < LAST) {
				await new Promise((r) => setTimeout(r, 200 + 280 * attempt));
				continue;
			}
			return await fetchFn(input, noStore);
		}
	}
	return await fetchFn(input, noStore);
}

// 소형 파일 통파일 임계 · 이하면 range 세션(직렬 메타데이터 왕복 수 회) 대신 1 회 GET.
// 회사별 gov 주가(~100KB)·소형 report parquet 가 8요청/~2s → 1요청/수백 ms 로 줄어든다.
// 큰 monolith(3~15MB report·date 파티션)는 projection/필터 range 가 여전히 유리 · 제외.
const WHOLE_FILE_MAX_BYTES = 1536 * 1024;

export async function openHfParquet(
	path: string,
	fetchFn: FetchLike = fetch
): Promise<ParquetRangeSession> {
	const [{ asyncBufferFromUrl }, ref] = await Promise.all([import('hyparquet'), headHfObject(path, fetchFn)]);
	const requests: RangeRequestStat[] = [];
	if (ref.size <= WHOLE_FILE_MAX_BYTES) {
		// 소형 통파일(Range 없는 GET)은 프록시(hfUrl) · 엣지캐시(cross-user)·per-file cache-control(recent=600s
		// 신선도)·403 흡수 이득이 살아있다. range(>임계)만 직결로 갔다(ref.url=hfRangeUrl). 책임경계 분리.
		const wholeUrl = hfUrl(path);
		const t0 = performance.now();
		const resp = await fetchResilient(fetchFn, wholeUrl);
		if (!resp.ok && resp.status !== 206) throw new HfReadError(path, resp.status, '전체 읽기 실패');
		const buf = await resp.arrayBuffer();
		requests.push({ url: wholeUrl, range: null, status: resp.status, bytes: buf.byteLength, durationMs: performance.now() - t0 });
		const file: AsyncBuffer = { byteLength: buf.byteLength, slice: (start: number, end?: number) => buf.slice(start, end ?? buf.byteLength) };
		return { ref, file, requests };
	}
	const measuredFetch: FetchLike = async (input, init) => {
		const t0 = performance.now();
		const resp = await fetchResilient(fetchFn, input, init);
		const cloned = resp.clone();
		const bytes = Number(resp.headers.get('content-length')) || 0;
		requests.push({
			url: typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url,
			range: new Headers(init?.headers).get('range'),
			status: resp.status,
			bytes,
			durationMs: performance.now() - t0
		});
		return cloned;
	};
	const file = await asyncBufferFromUrl({ url: ref.url, byteLength: ref.size, fetch: measuredFetch });
	return { ref, file, requests };
}

export async function readParquetMetadata(
	path: string,
	fetchFn: FetchLike = fetch
): Promise<ParquetMetadataSummary> {
	const [{ parquetMetadataAsync, parquetSchema }, session] = await Promise.all([
		import('hyparquet'),
		openHfParquet(path, fetchFn)
	]);
	const metadata = (await parquetMetadataAsync(session.file)) as FileMetaData;
	const schema = parquetSchema(metadata);
	return {
		path,
		size: session.ref.size,
		rows: Number(metadata.num_rows),
		rowGroups: metadata.row_groups?.length ?? 0,
		columns: schema.children.map((child) => child.element.name),
		requests: session.requests
	};
}

// 소형 단일 파일 직독 · HEAD probe 생략, GET 1 회로 전체 버퍼 → 파싱. 미존재(404)는 null.
// gov 회사별 주가처럼 "작고 통째로 읽는" 핫패스 전용 (요청 2→1, 콜드 RTT 1회 제거).
export async function readParquetWholeFile<T extends Record<string, unknown> = Record<string, unknown>>(
	path: string,
	options: { columns?: string[]; fetchFn?: FetchLike } = {}
): Promise<T[] | null> {
	const fetchFn = options.fetchFn ?? fetch;
	const [{ parquetReadObjects }, { compressors }, resp] = await Promise.all([
		import('hyparquet'),
		import('hyparquet-compressors'),
		fetchResilient(fetchFn, hfUrl(path))
	]);
	if (resp.status === 404) return null;
	if (!resp.ok && resp.status !== 206) throw new HfReadError(path, resp.status, '전체 읽기 실패');
	const buf = await resp.arrayBuffer();
	const file: AsyncBuffer = { byteLength: buf.byteLength, slice: (start: number, end?: number) => buf.slice(start, end ?? buf.byteLength) };
	return (await parquetReadObjects({ file, compressors, columns: options.columns })) as T[];
}

export async function readParquetRows<T extends Record<string, unknown> = Record<string, unknown>>(
	path: string,
	options: {
		columns?: string[];
		rowStart?: number;
		rowEnd?: number;
		filter?: ParquetQueryFilter;
		filterStrict?: boolean;
		fetchFn?: FetchLike;
	} = {}
): Promise<ParquetRowsResult<T>> {
	const [{ parquetReadObjects }, { compressors }, session] = await Promise.all([
		import('hyparquet'),
		import('hyparquet-compressors'),
		openHfParquet(path, options.fetchFn ?? fetch)
	]);
	const rows = (await parquetReadObjects({
		file: session.file,
		compressors,
		columns: options.columns,
		rowStart: options.rowStart,
		rowEnd: options.rowEnd,
		filter: options.filter,
		filterStrict: options.filterStrict,
		rowFormat: options.filter ? 'object' : undefined
	})) as T[];
	return { rows, requests: session.requests };
}
