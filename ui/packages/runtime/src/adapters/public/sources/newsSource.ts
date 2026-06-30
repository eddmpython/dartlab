// 종목 뉴스 헤드라인 로더 · 네이버 검색 API archive(private, 언론사 저작권)를 CF 워커가 read 토큰으로
// 서버사이드 read 해 반환(라이브 표시 = 의도된 용도, 공개 벌크 재배포 아님). 브라우저는 private 직독 불가라
// 워커 경유가 유일 경로 · 공개·로컬 동일(price·macro 와 같은 "공통 배선": 워커/HF 단일 소스).
//   모든 환경 = CF 워커 /news 라우트(origins newsWorker). 미설정 시 [] (정직한 미배선).
// (옛 dev /__news 미들웨어 분기는 구현된 적 없어 로컬을 빈 상태로 만들었다 · newsWorker 게이트로 통일.)
// 옛 module Map 캐시 + 인라인 fetch 는 폐기 · fetch 코어가 read 레벨 캐시(10분 TTL)·dedup. env 게이트 +
//   워커 URL 조립은 origins 레지스트리(newsWorker)로 흡수.
import type { NewsItem } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';
import { originConfigured } from '../../../data/origins/registry';

const browser = typeof window !== 'undefined';

// publicNewsPort() 는 ui/web 레거시·로컬/퍼블릭 어댑터가 core 없이 호출하므로 core 미주입 경로 전용 모듈
// 폴백 코어를 lazy 생성한다(govPriceSource.govCore 동형). 어댑터가 core 를 주입하면 그걸 쓴다.
const newsCore = moduleFallbackCore();

interface NewsFile {
	code: string;
	asOf?: string;
	items?: NewsItem[];
}

/** 종목별 최근 뉴스 (date 내림차순). [] = 미지원·실패·미배선·해당없음.
 *  name(회사명) 주입 시 워커가 네이버 검색 라이브 헤드라인을 byCompany 아카이브 위에 머지(조회시점 최신). */
export function loadCompanyNews(code: string, core?: DataCore, name?: string): Promise<NewsItem[]> {
	if (!browser) return Promise.resolve([]);
	if (!originConfigured('newsWorker')) return Promise.resolve([]); // 프록시 미설정 → 빈 섹션(코어 호출 생략)
	const c = code.trim();
	const nm = (name ?? '').trim();
	const spec = nm ? `${c}\t${nm}` : c; // newsWorkerUrl 이 \t 로 code|회사명 분리(라이브 RSS q)
	return newsCore(core)
		.request<NewsFile>({
			origin: 'newsWorker',
			path: spec,
			parse: (r) => (r.ok ? (r.json() as Promise<NewsFile>) : Promise.resolve({ code: c } as NewsFile))
		})
		.then((j) => (Array.isArray(j.items) ? j.items : []))
		.catch(() => []);
}
