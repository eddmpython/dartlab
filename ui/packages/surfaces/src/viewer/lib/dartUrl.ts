// 공시 뷰어 "원본" URL 시장분기 · Python `companyApi._viewerUrlForFiling` 1:1 포팅.
//
// KR(DART): main.do?rcpNo={rceptNo}. US(EDGAR): SEC filing index.
// panel 만으로 충족 · panel 엔 cik 컬럼이 없지만 SEC accession(rceptNo) 의 앞 10자리가 filer CIK 라
// 거기서 추출(`0000320193-25-000079` → cik 0000320193 → Apple). 별도 데이터 불필요.

export type Market = 'KR' | 'US';

// 종목코드로 시장 판정 · KR=6자리 숫자, 그 외(ticker)=US.
export function marketForCode(code: string): Market {
	return /^\d{6}$/.test(code) ? 'KR' : 'US';
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
