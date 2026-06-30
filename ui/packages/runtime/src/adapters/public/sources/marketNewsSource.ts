// 시장 전체(cross) 뉴스 피드 · public rss 아카이브(news/public/rss/{market}/{YYYY-MM-DD}.parquet,
// Google News RSS·재배포 가능)의 최근 N일 shard 를 통째로 읽어 합친다. 종목별(loadCompanyNews, naver
// 워커 라이브 read)과 *경로 분리*: 이건 전 시장이라 stock_code 필터 없이 일별 공개 parquet 직독.
//   bake(통합 recent 파일)는 의도적으로 안 만든다 · 시장 뉴스는 매일 조밀해 최근 며칠 shard 면 충분하고,
//   기존 일별 cron 산출물(gather writeDailyParquet)을 그대로 직독하는 게 별도빌드 0 의 정공법. 오늘(UTC)
//   shard 는 cron(어제까지) 직후라 보통 미존재이므로 어제부터 역순으로 읽어 불필요한 404 를 피한다.
//   미존재일(404)은 requestParquetWholeFile 이 null + 음성캐시 → 반복 GET 0.
//   ★라이브 오버레이: cron(일 2회)이 못 채우는 사이 갭은 marketNewsWorker(네이버 검색 라이브)가 메운다.
//   HF 누적 shard + 라이브 헤드라인을 url-dedup 머지 → 넓이(HF) + 10분급 신선도(라이브). 워커 미배선/실패 시 HF base 만.
// 제목+원문링크만(스니펫 없음) · 클릭=외부 기사 이동. rss 는 스키마상 description 이 null 이라 본디 제목만.
import type { MarketNews } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';
import { originConfigured } from '../../../data/origins/registry';

interface NewsRow extends Record<string, unknown> {
	date?: unknown;
	title?: unknown;
	url?: unknown;
	source?: unknown;
}

const COLS = ['date', 'title', 'url', 'source'];
const DAYS = 3; // 최근 N UTC 일 shard (오늘 포함 역순) · 오늘 shard 가 가장 신선(cron 이 UTC-runner-today 적재).
//                일 shard ~300~580KB·mount preload 라 3일 OK. 오늘 미존재(첫 run 전)면 404 음성캐시→어제/그제 커버.
const CAP = 300; // 렌더 상한 · 최근 윈도우라 무한스크롤 불필요

// core 미주입 경로(레거시/어댑터 무인자 호출) 전용 lazy 폴백 · loadCompanyNews(newsSource) 동형.
const marketCore = moduleFallbackCore();

// pl.Date 컬럼은 hyparquet 가 JS Date 로 준다 · Date/문자열/epoch-days 모두 YYYY-MM-DD 로 정규화.
function toIsoDate(v: unknown): string {
	if (v instanceof Date) return v.toISOString().slice(0, 10);
	const s = String(v ?? '').trim();
	if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
	const n = Number(s);
	if (Number.isFinite(n) && n > 10_000 && n < 100_000) return new Date(n * 86_400_000).toISOString().slice(0, 10);
	return s;
}

// 오늘(UTC)부터 N일 역순 · [오늘, 어제, 그제]. cron(UTC 08:00/16:00)이 UTC-runner-today 로 shard 를
// 적재하므로 오늘 shard 가 가장 신선하다. 첫 run 전이면 오늘은 404(음성캐시) → 어제/그제가 커버.
function recentDays(now: Date, days: number): string[] {
	const out: string[] = [];
	for (let i = 0; i < days; i++) {
		const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - i));
		out.push(d.toISOString().slice(0, 10));
	}
	return out;
}

/** 행 정규화 · 제목·url 필수, url dedup, date 내림차순, CAP. 순수 함수(테스트 대상). */
export function normalizeMarketNews(rows: NewsRow[]): MarketNews[] {
	const seen = new Set<string>();
	const out: MarketNews[] = [];
	for (const r of rows) {
		const url = String(r.url ?? '').trim();
		const title = String(r.title ?? '').trim();
		if (!url || !title || seen.has(url)) continue;
		seen.add(url);
		out.push({ date: toIsoDate(r.date), title, source: String(r.source ?? '').trim(), url });
	}
	out.sort((a, b) => b.date.localeCompare(a.date));
	return out.slice(0, CAP);
}

interface LiveNewsFile extends Record<string, unknown> {
	market?: string;
	items?: NewsRow[];
}

/** marketNewsWorker 라이브 RSS 헤드라인 · 미배선/실패는 []. 워커 응답 {market,asOf,items:[{date,title,source,url}]}. */
function loadLiveMarketNews(c: DataCore, market: string): Promise<NewsRow[]> {
	if (!originConfigured('marketNewsWorker')) return Promise.resolve([]); // 워커 미배선 → HF base 만(코어 호출 생략)
	return c
		.request<LiveNewsFile>({
			origin: 'marketNewsWorker',
			path: market, // marketNewsWorkerUrl 이 ?market= 로 조립
			parse: (r) => (r.ok ? (r.json() as Promise<LiveNewsFile>) : Promise.resolve({} as LiveNewsFile))
		})
		.then((j) => (Array.isArray(j.items) ? j.items : []))
		.catch(() => []);
}

/** 시장 전체 최근 뉴스 · HF 공개 rss 아카이브 최근 N일 shard + 라이브 RSS 오버레이 머지. 실패/미배선은 []. */
export async function loadMarketNews(core?: DataCore, market = 'KR', now: Date = new Date()): Promise<MarketNews[]> {
	const c = marketCore(core);
	const days = recentDays(now, DAYS);
	try {
		// HF 누적 shard(넓이) + 라이브 헤드라인(신선도) 동시 fetch · 둘 다 실패해도 normalizeMarketNews 가 [] 안전.
		const [perDay, live] = await Promise.all([
			Promise.all(
				days.map((day) =>
					c
						.requestParquetWholeFile<NewsRow>({
							origin: 'hf',
							path: `news/public/rss/${market}/${day}.parquet`,
							columns: COLS,
							cacheKey: `news.market:${market}:${day}`,
							cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 8 } // 신선도 · 짧은 TTL
						})
						.catch(() => null)
				)
			),
			loadLiveMarketNews(c, market)
		]);
		// live 를 앞에 · url-dedup keep-first 에서 라이브분 우선(동일 기사면 내용 동일이라 무관, 의미상 자연).
		return normalizeMarketNews([...live, ...perDay.flatMap((r) => r ?? [])]);
	} catch {
		return [];
	}
}
