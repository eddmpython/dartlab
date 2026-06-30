// 시장 공시 피드 전용 분류 · 좌측 '시장 공시 피드'(전상장사 수시공시)의 주가영향 6탭 taxonomy.
// 차트 이벤트레일의 classifyFiling(eventRail.ts) 과 *형제* 함수다. classifyFiling 은 reportNm 만으로
// equity/issue/major/exchange/etc 6분류라 자기주식이 major 에, 최대주주·공급계약·실적이 exchange 에,
// 임원소유와 5%대량보유가 한 equity 에 묻혀 주가영향 신호가 가려진다. 시장피드는 그걸 주가영향
// 카테고리로 *재투영*한다(etc 를 줄이는 만능분류기 아님 · 강신호를 위로 올리는 필터).
//
// ⛔ classifyFiling 을 개조·복제하지 않는다. 공유 패턴(지분=ownership)은 eventRail.RX_OWNERSHIP 를
//    import 재사용한다(단일 SSOT). 나머지(자기주식·증자사채·경영권·실적계약)는 classifyFiling 이 묶음
//    안에 가진 적 없는 *더 세밀한* 패턴이라 신규 리터럴이다(복붙 아님).
import { RX_OWNERSHIP } from './eventRail';

export interface MarketFeedCat {
	key: string;
	kr: string;
}

// 탭 = '전체' + 5 주가영향 카테고리. 'etc'(기타 수시)는 탭으로 승격하지 않는다 · '전체'에만 섞인다
// (PRD: etc 는 IR·지배구조·기준일 등 약신호 행정공시라 별탭 승격 금지·분류정확도에 공력 쓰지 않음).
export const MARKET_FEED_CATS: MarketFeedCat[] = [
	{ key: 'all', kr: '전체' },
	{ key: 'ownership', kr: '지분·내부자' },
	{ key: 'treasury', kr: '자기주식' },
	{ key: 'capital', kr: '증자·사채' },
	{ key: 'control', kr: '최대주주·경영권' },
	{ key: 'earnings', kr: '실적·계약' }
];
export const MARKET_FEED_CAT_LABEL: Record<string, string> = Object.fromEntries(
	MARKET_FEED_CATS.map((c) => [c.key, c.kr])
);

// 자기주식(취득·처분·소각·신탁) · classifyFiling 은 major 에 합병·증자와 섞음. 시장피드는 독립.
const RX_TREASURY = /자기주식/;
// 증자·사채(희석·자본조달) · 유·무상증자, 메자닌(CB/BW/EB), 감자. '결정' 공시 중심.
const RX_CAPITAL = /유[ㆍ·]?무상증자|유상증자|무상증자|전환사채|신주인수권|교환사채|감자/;
// 최대주주·경영권 · 지배권 이동·구조변화. (최대주주 키워드는 ownership 보다 우선해 control 로.)
const RX_CONTROL = /최대주주|합병|분할|영업[ 양]?양[수도]|주식교환|주식이전/;
// 실적·계약 · 펀더 서프라이즈. 잠정실적 공정공시·단일판매/공급계약.
const RX_EARNINGS = /손익구조|매출액|공정공시|단일판매|공급계약/;

/**
 * 시장 공시 원문명(reportNm) → 주가영향 6탭 카테고리. 첫 매치 채택(우선순위 = 신호 특이성 순):
 * treasury(자기주식) → capital(증자·사채) → control(최대주주·경영권) → ownership(지분·내부자)
 * → earnings(실적·계약) → etc. content_raw 없는 메타 분류라 방향(호재/악재) 판정 0 · 그룹명만.
 */
export function marketFeedCategory(reportNm: string): string {
	const s = reportNm || '';
	if (RX_TREASURY.test(s)) return 'treasury';
	if (RX_CAPITAL.test(s)) return 'capital';
	if (RX_CONTROL.test(s)) return 'control';
	if (RX_OWNERSHIP.test(s)) return 'ownership';
	if (RX_EARNINGS.test(s)) return 'earnings';
	return 'etc';
}

// ── 기관·연금 식별(보조 [기관] 필터칩 전용) ──
// ★정직 한계: report_nm 제목엔 '연금' 0건 · 제출자명(flr_nm)으로만 식별 가능하고 그게 지분 행의
// 약 9.5%만 잡힌다(개인 오너와 섞임). 지배적 오류는 '개인→기관 오분류(거의 0)'가 아니라 '기관→누락'
// (J.P.MORGAN 도 점 때문에 사전 누락). 그래서 칩은 '제출자=기관(부분식별·약10%)' 정직 라벨로만 쓰고,
// 독립 1급 탭으로 승격하지 않는다(전상장사 ~90% 침묵=커버 위반). flr_nm 원문은 행 툴팁에 노출(검증 가능).
const RX_INSTITUTION =
	/자산운용|국민연금|연금공단|공무원연금|사학연금|투자신탁|투자자문|캐피탈|은행|증권|보험|상호금융|새마을금고|신용협동|BlackRock|Norges|Vanguard|Fidelity|Capital|Asset|Advisor|Invest|Fund|Holdings|JPMorgan|Morgan|Goldman|Citadel|StateStreet/i;

/**
 * 제출자명(flr_nm)이 기관·연금 시그널인가 · 보조 [기관] 칩 필터 전용. 광의 사전(국내 기관 한글명 +
 * 외국 기관 영문 토큰). 휴리스틱이라 '근사'(약 10% 식별·미식별 다수) · 단정·impute 금지, 라벨로 정직 표기.
 */
export function isInstitutionalFiler(filer: string): boolean {
	return RX_INSTITUTION.test(filer || '');
}
