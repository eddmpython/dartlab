// 공시 뷰어 "원본" URL 시장분기 · Python `companyApi._viewerUrlForFiling` 1:1 포팅.
//
// KR(DART): main.do?rcpNo={rceptNo}. US(EDGAR): SEC filing index.
// panel 만으로 충족 · panel 엔 cik 컬럼이 없지만 SEC accession(rceptNo) 의 앞 10자리가 filer CIK 라
// 거기서 추출(`0000320193-25-000079` → cik 0000320193 → Apple). 별도 데이터 불필요.

import { resolveMarket, type Market } from '@dartlab/ui-contracts';

export type { Market };

// 종목코드로 시장 판정. 판정 규칙은 resolveMarket(contracts) 정본에 위임한다.
// 손수 `/^\d{6}$/` 를 쓰면 KRX 영숫자 코드(에스엔시스 0008Z0)를 US 로 오분류해
// edgar/ 경로 404 를 낸다.
export function marketForCode(code: string): Market {
	return resolveMarket(code).market;
}

export function viewerUrl(market: Market, rceptNo: string | null | undefined): string | null {
	if (!rceptNo) return null;
	if (market !== 'US') {
		return `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${rceptNo}`;
	}
	// EDGAR: rceptNo = SEC accession (0000320193-25-000079). cik = 앞 10자리(filer) leading-zero strip.
	const cik = (rceptNo.split('-')[0] ?? '').replace(/^0+/, '');
	if (!cik) return null;
	const accDash = rceptNo.replace(/-/g, '');
	return `https://www.sec.gov/Archives/edgar/data/${cik}/${accDash}/${rceptNo}-index.htm`;
}
