// 시장 라우팅 SSOT. 식별자(KR 종목코드 / US 티커·CIK) → 시장 분류 단일 진입점.
//
// 라이브러리(Python) 라우팅은 provider *priority* 기반이라(예: EDGAR canHandle 은 6자리
// 숫자도 True 를 반환하고 dart<edgar priority 로 분기) 프론트가 식별자 *모양*만으로 베끼면
// 6자리 KR 코드(005930)와 6자리 US CIK(Apple=320193)를 못 가른다. 따라서 프론트 규칙은
// **명시 market override 1순위 + 모호 신호**로 비대칭 설계한다.
//
// 이 함수는 산재된 `/^\d{6}$/ ? 'KR' : 'US'`(viewer/dartUrl · finance/annual · compare/targets)
// 를 대체할 정본이다. market 미지정 기본값은 'KR'(무회귀 불변식. CLAUDE.md).

/** 단일 시장 리터럴. indexPort/macro 의 'KR'|'US' 와 동형. */
export type Market = 'KR' | 'US';

/** resolveMarket 결과. 시장 + 이중키(KR=code · US=ticker/cik). */
export interface MarketRef {
	market: Market;
	/** KR 6자리 종목코드 (market='KR'). 영숫자 코드의 영문은 대문자 정규화. */
	code?: string;
	/** US 티커 (대문자, ticker 입력 시). */
	ticker?: string;
	/** US CIK (숫자 입력 + market='US' override, 또는 비-6자리 숫자 자동판정). zero-pad 는 소비자(edgar/tickers)에서. */
	cik?: string;
	/** 입력이 6자리 *순수 숫자* 라 KR코드 ∩ US CIK 모양 충돌. 자동판정은 KR 로 떨어뜨림. US CIK 면 {market:'US'} 명시 필요. */
	ambiguous?: boolean;
}

// KRX 단축코드 6자리. 첫 자리는 항상 숫자, 나머지는 영숫자다.
// 순수 6자리 숫자(005930)가 다수지만 신형 발행분은 영문을 섞는다(에스엔시스 0008Z0 ·
// 삼성에피스홀딩스 0126Z0 · SK우 03473K). 2026-07 기준 상장 2,873 종목 중 79 종목이 영숫자다.
// 옛 `/^\d{6}$/` 는 이들을 전부 US 티커로 오분류해 edgar/ 경로로 보내 404 를 냈다.
// US 티커는 숫자로 시작하지 않으므로 "숫자 선두 + 6자" 규칙은 티커와 충돌하지 않는다.
const RE_KR_CODE = /^\d[0-9A-Z]{5}$/;
/** 6자리 *순수* 숫자. US CIK 와 모양이 겹치는 부분집합(모호 플래그 판정용). */
const RE_KR_NUMERIC_CODE = /^\d{6}$/;
const RE_NUMERIC = /^\d+$/;
const RE_HAS_ALPHA = /[A-Za-z]/;

/**
 * 식별자를 시장으로 분류한다(priority-비대칭, 이중키).
 *
 * 규칙 ① 명시 `opts.market` override 1순위 ② 자동판정: KRX 단축코드 모양(숫자 선두 6자
 * 영숫자)→KR(순수 6자리 숫자일 때만 모호 플래그), 비-6자리 숫자→US CIK, 영문 포함→US 티커,
 * 그 외/빈→KR 기본(무회귀).
 *
 * 6자리 *순수 숫자* CIK 는 KR 코드와 모양이 충돌하므로(Apple=320193) US 로 라우팅하려면
 * `{market:'US'}` 를 명시해야 한다. 영숫자 KR 코드(0008Z0)는 CIK 가 될 수 없어 모호하지 않다.
 *
 * @example resolveMarket('005930') // { market:'KR', code:'005930', ambiguous:true }
 * @example resolveMarket('0008Z0') // { market:'KR', code:'0008Z0' }  에스엔시스(코스닥)
 * @example resolveMarket('AAPL')   // { market:'US', ticker:'AAPL' }
 * @example resolveMarket('320193', { market:'US' }) // { market:'US', cik:'320193' }
 */
export function resolveMarket(id: string, opts?: { market?: Market }): MarketRef {
	const raw = String(id ?? '').trim();
	const override = opts?.market;

	// ① 명시 market override 1순위
	if (override === 'US') {
		return RE_NUMERIC.test(raw)
			? { market: 'US', cik: raw }
			: { market: 'US', ticker: raw.toUpperCase() };
	}
	if (override === 'KR') {
		return { market: 'KR', code: normalizeKrCode(raw) };
	}

	// ② 자동판정 (override 없음)
	const kr = normalizeKrCode(raw);
	if (RE_KR_CODE.test(kr)) {
		// 순수 6자리 숫자만 US CIK 와 모양이 겹친다 → 모호 플래그(US 면 명시 필요).
		// 영숫자 코드(0008Z0)는 CIK 모양이 아니라 확정 KR.
		return RE_KR_NUMERIC_CODE.test(kr)
			? { market: 'KR', code: kr, ambiguous: true }
			: { market: 'KR', code: kr };
	}
	if (RE_NUMERIC.test(raw)) {
		// 비-6자리 순수 숫자(예: 10자리 CIK 0000320193) → US CIK (KR 코드는 6자리뿐).
		return { market: 'US', cik: raw };
	}
	if (RE_HAS_ALPHA.test(raw)) {
		return { market: 'US', ticker: raw.toUpperCase() };
	}
	// 빈 문자열·기타 → KR 기본(무회귀).
	return { market: 'KR', code: raw };
}

/**
 * KR 종목코드 표기 정규화. KRX 영숫자 코드의 영문은 항상 대문자다(0008z0 → 0008Z0).
 * 숫자만인 코드는 그대로 통과하므로 기존 6자리 경로에 영향이 없다.
 */
export function normalizeKrCode(code: string): string {
	return String(code ?? '')
		.trim()
		.toUpperCase();
}

/**
 * KRX 단축코드 모양인지 판정한다. HF `dart/` 정적 자산(panel·filings·finance)의
 * 보유 여부 가드로 쓰는 술어. 산재하던 `/^\d{6}$/.test(code)` 를 대체한다.
 *
 * 오버로드 2 종인 이유: 인자가 이미 `string` 인데 타입 술어(`code is string`)를 태우면
 * 거짓 분기가 `never` 로 좁혀져 `else` 쪽 문자열 연산이 컴파일 에러가 난다.
 * 따라서 string 입력은 평범한 boolean, unknown 입력(localStorage·JSON 파싱분)만 술어로 받는다.
 */
export function isKrStockCode(code: string): boolean;
export function isKrStockCode(code: unknown): code is string;
export function isKrStockCode(code: unknown): boolean {
	return typeof code === 'string' && RE_KR_CODE.test(normalizeKrCode(code));
}
