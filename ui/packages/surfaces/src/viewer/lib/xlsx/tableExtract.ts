// table-export 정합 정규화 · 엔진 `dartXmlNormalize.coerceCell` + `detectUnit` 의 1:1 TS 포팅.
// 순수 함수 (DOM 0, fetch 0). 엔진과 같은 골든 규칙으로 같은 *.grid.json 픽스처를 양쪽 검증한다.
//
// 규칙 (엔진 `providers/dart/parse/dartXmlNormalize.py` 와 정확히 동일):
//   - 숫자 `^-?[\d,]+(\.\d+)?$` (콤마 제거 후) → Number. "1,234" → 1234, "23.7" → 23.7.
//   - 한국식 음수: "(1,234)" → -1234 ; "△1,234"/"▲1234"(줄바꿈 포함 "△\n5") → -1234.
//   - 빈/공백뿐 → null (honest-gap · 결손을 절대 0 으로 만들지 않는다).
//   - 그 외(한글·혼합·"5,000원"·"2024.12.31") → 원본 문자열(trim). 단위 접미 벗기기 금지.
//   - detectUnit 은 라벨만 · 값 스케일 환산 0 (xml-native-truth).

const NUMERIC_RE = /^-?[\d,]+(\.\d+)?$/;
// 한국식 음수 래퍼: (1,234) 괄호음수 ; △ / ▲ 삼각형 접두 (줄바꿈·공백 흡수 \s*).
const PAREN_NEG_RE = /^\(\s*([\d,]+(?:\.\d+)?)\s*\)$/;
const TRIANGLE_NEG_RE = /^[△▲]\s*([\d,]+(?:\.\d+)?)$/;

// 콤마 제거 숫자 토큰을 정수(점 없음) 또는 실수(점 있음)로 파싱.
function toNumber(digits: string): number {
	return Number(digits.replace(/,/g, ''));
}

/**
 * 표 셀 문자열을 타입값으로 정합 정규화 · 엔진 `coerceCell` 포팅.
 *
 * @param text raw 셀 텍스트.
 * @returns number | string | null. 결손은 null (절대 0 아님 · honest-gap).
 *
 * @example
 * coerceCell('1,234');        // 1234
 * coerceCell('(1,234)');      // -1234
 * coerceCell('△5');           // -5
 * coerceCell('△\n5');         // -5
 * coerceCell('');             // null
 * coerceCell('삼성');         // '삼성'
 * coerceCell('5,000원');      // '5,000원' (단위 접미 → 문자열 유지)
 * coerceCell('2024.12.31');   // '2024.12.31' (점 2개 → 문자열)
 */
export function coerceCell(text: string | null | undefined): number | string | null {
	if (text == null) return null;
	const s = text.trim();
	if (!s) return null;

	// 한국식 괄호음수: (1,234) → -1234
	const pm = PAREN_NEG_RE.exec(s);
	if (pm) return -toNumber(pm[1]);

	// 한국식 삼각형음수: △1,234 / ▲1234 → -1234 (줄바꿈 포함)
	const tm = TRIANGLE_NEG_RE.exec(s);
	if (tm) return -toNumber(tm[1]);

	// 평문 숫자 (선행 "-" 포함).
	if (NUMERIC_RE.test(s)) {
		// 가드: 단독 "-" / "," / "." 는 숫자 아님 → 문자열 유지.
		if (s.replace(/[-,. ]/g, '') === '') return s;
		return toNumber(s);
	}

	// 비숫자 텍스트 → 문자열 유지.
	return s;
}

// ── 단위 감지 (감지만, 환산 0 · xml-native-truth) ──
// "(단위: 백만원)" / "단위 : 천원" / "(단위:원)" 등. 콜론 뒤 단위 토큰 캡처.
const UNIT_RE = /단위\s*[:：]?\s*([^)\]\n]+)/;
// 알려진 한국 회계 단위 토큰 · 검증용. 미지 토큰 → "" (추측 0).
const KNOWN_UNITS: Record<string, string> = {
	원: '원',
	천원: '천원',
	백만원: '백만원',
	십억원: '십억원',
	억원: '억원',
	조원: '조원',
	주: '주',
	'%': '%',
	달러: '달러',
	천달러: '천달러',
	백만달러: '백만달러',
	usd: 'USD',
	천usd: '천USD',
	백만usd: '백만USD'
};

/**
 * 단위 캡션("(단위: 백만원)") 감지 → canonical 단위 토큰 반환, 값 환산 0 · 엔진 `detectUnit` 포팅.
 *
 * @param caption "(단위: …)" 조각을 포함할 수 있는 임의 텍스트.
 * @returns canonical 단위 토큰(예 "백만원", "원", "%") 또는 인식 실패 시 "".
 *
 * @example
 * detectUnit('(단위: 백만원)'); // '백만원'
 * detectUnit('매출 추이');      // ''
 */
export function detectUnit(caption: string | null | undefined): string {
	if (!caption) return '';
	const m = UNIT_RE.exec(caption);
	if (!m) return '';
	// 후행 ")"/"]"·공백 제거.
	const raw = m[1].trim().replace(/[)\]\s]+$/, '').trim();
	const key = raw.toLowerCase();
	if (key in KNOWN_UNITS) return KNOWN_UNITS[key];
	// "백만원, 주" 식 다중 단위 · 접두 매칭으로 첫 알려진 토큰.
	for (const token of Object.keys(KNOWN_UNITS)) {
		if (raw.startsWith(token)) return KNOWN_UNITS[token];
	}
	return ''; // 미지 단위 → 빈칸, 추측 0
}
