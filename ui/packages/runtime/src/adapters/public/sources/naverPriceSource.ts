// 네이버 fchart 라이브 fresh-tail · gov(공공데이터포털, T+1 영업일 지연)가 아직 발행하지 않은
// 최신 거래일(예: 금요일치는 월요일 발행)을 표시용으로 채운다. 공개 HF 데이터셋(gov)은 그대로 두고
// 화면을 그릴 때만 네이버에서 가져와 mergeDedup 으로 tail 에 얹는다 · 재배포가 아니라 사용자 세션
// 표시용 fetch 이므로 저작권 안전. gov 와 네이버는 KRX 원천·원주가라 겹치는 날 값이 동일 → 점프 없음.
//   dev = /__naver 미들웨어(Node 서버측 fetch, 브라우저 CORS 우회).
//   프로덕션 = CF 프록시 네이버 라우트(예정) · 배선 전까진 미동작([] 반환).
// 옛 module Map 캐시 + 인라인 fetch 는 폐기 · fetch 코어가 read 레벨 캐시(10분 TTL)·dedup. dev/프록시
//   분기 + URL 조립은 origins 레지스트리(naverWorker)로 흡수.
import type { Candle } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';
import { originConfigured } from '../../../data/origins/registry';

const browser = typeof window !== 'undefined';

// loadNaverFresh 는 publicPricePort 경유로 core 를 받지만, core 미주입 경로(레거시)도 안전하게 폴백.
// (govPriceSource.govCore 동형 · 어댑터 주입 우선, 무주입만 모듈 폴백 lazy 생성.)
const naverCore = moduleFallbackCore();

interface NaverFreshFile {
	source: string;
	code: string;
	asOf: string;
	candles: Candle[];
}

/** gov 미발행 최신 거래일을 네이버에서 채우는 fresh tail (오름차순 Candle[]). [] = 미지원·실패·미배선. */
export function loadNaverFresh(code: string, core?: DataCore): Promise<Candle[]> {
	if (!browser) return Promise.resolve([]);
	if (!originConfigured('naverWorker')) return Promise.resolve([]); // 프록시 미설정 → EOD(전일 종가)까지만
	const c = code.trim();
	return naverCore(core)
		.request<NaverFreshFile>({
			origin: 'naverWorker',
			path: c,
			parse: (r) => (r.ok ? (r.json() as Promise<NaverFreshFile>) : Promise.resolve({ candles: [] } as unknown as NaverFreshFile))
		})
		.then((j) => (Array.isArray(j.candles) ? j.candles : []))
		.catch(() => []);
}
