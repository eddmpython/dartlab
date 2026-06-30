// 이벤트 레일 분류 taxonomy · 주가차트 하단 "이벤트 레일"(공시 dot)의 카테고리 필터 SSOT.
// 지금은 DART 공시(정기 + 비정기 그룹)만. 향후 뉴스·실적·매크로 등 다른 이벤트 타입을 같은 레일에 채울 수 있게
// key 레지스트리로 설계한다 · 레일 item 은 generic `category` 한 필드만 들고, 새 타입은 여기 EVENT_CATS 에 키만 추가.
// 비정기 공시는 DART 공식 공시그룹 필드가 (현 데이터 계약에) 없어, 공시 원문명(reportNm) 키워드로 *근사* 매핑한다.

export interface EventCat {
	key: string;
	kr: string;
	en: string;
}

// 표시 순서 = 드롭다운·우선순위. regular 는 RegularFiling(kind='regular')에서 직접 부여, 나머지는 classifyFiling 근사.
export const EVENT_CATS: EventCat[] = [
	{ key: 'regular', kr: '정기공시', en: 'Periodic' },
	{ key: 'major', kr: '주요사항', en: 'Major' },
	{ key: 'equity', kr: '지분공시', en: 'Ownership' },
	{ key: 'issue', kr: '발행공시', en: 'Issuance' },
	{ key: 'exchange', kr: '거래소공시', en: 'Exchange' },
	{ key: 'audit', kr: '감사', en: 'Audit' },
	{ key: 'news', kr: '뉴스', en: 'News' }, // 네이버 헤드라인(공시 아님) · item.kind='news', url=원문. 공시와 색 구분.
	{ key: 'etc', kr: '기타', en: 'Other' }
	// 향후 확장 예: { key: 'earnings', kr: '실적', en: 'Earnings' } …
	// (레일 item.category 에 해당 key 를 실어 보내고, 분류기/수집기만 추가하면 필터 UI 는 자동 반영)
];

export const EVENT_CAT_KEYS: string[] = EVENT_CATS.map((c) => c.key);
export const EVENT_CAT_LABEL: Record<string, { kr: string; en: string }> = Object.fromEntries(
	EVENT_CATS.map((c) => [c.key, { kr: c.kr, en: c.en }])
);

// 지분공시(소유) 패턴 · 차트 이벤트레일(classifyFiling 'equity')과 시장피드(marketFeedCategory
// 'ownership')가 *공유*하는 단일 SSOT 리터럴. 복붙 금지 · 양쪽이 이 const 를 import 한다.
export const RX_OWNERSHIP = /대량보유|특정증권|의결권|주식등의|임원[ㆍ·]?주요주주/;

/**
 * 비정기 공시 원문명(reportNm) → 공시그룹 키워드 근사 분류. 순서 = 우선순위(첫 매치 채택).
 * 공식 DART 카테고리 필드 부재로 키워드 휴리스틱 · 모호하면 'etc'. 정기보고서는 kind 로 이미 'regular'.
 */
export function classifyFiling(reportNm: string): string {
	const s = reportNm || '';
	if (RX_OWNERSHIP.test(s)) return 'equity';
	if (/증권신고서|투자설명서|발행조건|발행실적|일괄신고|증권발행/.test(s)) return 'issue';
	if (/감사보고서|외부감사|회계감사/.test(s)) return 'audit';
	if (/주요사항|유[ㆍ·]?무상증자|유상증자|무상증자|전환사채|신주인수권|교환사채|자기주식|영업[ 양]?양[수도]|합병|분할|감자|주식소각|주식교환|주식이전|해산|부도|회생|파산|채권은행|관리절차|유형자산양수|타법인주식/.test(s)) return 'major';
	if (/수시|조회공시|자율공시|공정공시|풍문|해명|공급계약|단일판매|취득결정|처분결정|배당|임원변경|최대주주|주주총회|경영사항|손익구조|매출액|기재정정|정정신고|투자판단/.test(s)) return 'exchange';
	return 'etc';
}
