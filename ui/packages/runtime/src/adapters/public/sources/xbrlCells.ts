// panel contentRaw 의 정부 XBRL <TE ACODE ACONTEXT> 셀 직독 · 엔진 providers/dart/panel/build/cell.py 동형(런타임 포팅).
// panel 본문엔 정부가 태깅한 셀이 무손실 보존돼 있어, 런타임이 이미 받는 contentRaw 에서 직접 읽는다(별도 bake 0).
// 표 *레이아웃* 정규식 파싱이 아니라 정부 *택소노미 태그*(ACODE=개념·ACONTEXT=기간/축) 직독 · 노이즈·이름변경·총계에 강건.
// 결정론 문자열 분해(lxml/엔진 무관, 순수). 비용=acode, 부문=axisPath 멤버. ACONTEXT 양식 = 2025-03 사업보고서+.

export interface XbrlCell {
	acode: string; // 'ifrs-full_Revenue' / 'ifrs-full_RawMaterialsAndConsumablesUsed' / 'dart_*'
	label: string; // 같은 TR 첫 ACODE-없는 TE 한글 라벨
	value: number; // 원 환산 (단위 배율 적용)
	ctxYear: number; // 실연도
	ctxFlow: string; // 'd'(흐름) | 'e'(시점)
	ctxQuarter: number; // 1~4 (4=연간/사업보고서)
	ctxMode: string; // 'Y'(연간) | 'A'(누적YTD) | 'Q'(단독) | 'P'(시점)
	axisPath: string; // 축 멤버 '|' join (부문=세그먼트 멤버 운반)
}

// ACONTEXT period 토큰: (당기/전기/전전기)FY{연도}{흐름}{marker}. marker=FY(연간)/FQ(1)/HY(2)/TQ(3) + A(누적)·Q(단독)·∅(시점).
const PERIOD_RE = /^(BP|P|C)FY(\d{4})([de])(FY|FQA|FQQ|FQ|HYA|HYQ|HY|TQA|TQQ|TQ)$/;
const MARKER_QUARTER: Record<string, number> = { FY: 4, FQ: 1, HY: 2, TQ: 3 };
const AXIS_PREFIXES = new Set(['ifrs-full', 'dart']);
const UNIT_RE = /단위\s*[:：]\s*(백만원|천원|원)/;
const UNIT_SCALE: Record<string, number> = { 백만원: 1e6, 천원: 1e3, 원: 1 };
const NUM_RE = /^[△▲\-(]?\s*[\d,]+\.?\d*\s*\)?$/;
const NOTE_RE = /^\(?주[\s\d,]/;

function markerToQuarterMode(marker: string): [number, string] {
	if (marker === 'FY') return [4, 'Y'];
	const base = marker.slice(0, 2); // FQ/HY/TQ
	const suffix = marker.slice(2); // ''|'A'|'Q'
	const mode = suffix === 'A' || suffix === 'Q' ? suffix : 'P';
	return [MARKER_QUARTER[base] ?? 4, mode];
}

// ACONTEXT 의 axis 토큰 list → Member 로 끝나는 토큰만(축 드롭, 멤버 보존). ifrs-full_/dart_ prefix 는 벗김, entity 보존.
function axisMembers(segs: string[]): string[] {
	const tokens: string[] = [];
	let buf: string[] = [];
	for (const s of segs) {
		if (AXIS_PREFIXES.has(s) || s.startsWith('entity')) {
			if (buf.length) tokens.push(buf.join('_'));
			buf = [s];
		} else {
			buf.push(s);
		}
	}
	if (buf.length) tokens.push(buf.join('_'));
	return tokens
		.filter((t) => t.endsWith('Member'))
		.map((m) => (m.startsWith('ifrs-full_') ? m.slice('ifrs-full_'.length) : m.startsWith('dart_') ? m.slice('dart_'.length) : m));
}

/** ACONTEXT attribute → (ctxYear, ctxFlow, ctxQuarter, ctxMode, axisPath). period 토큰 미매칭 시 null. */
export function decodeAcontext(ctx: string): { ctxYear: number; ctxFlow: string; ctxQuarter: number; ctxMode: string; axisPath: string } | null {
	if (!ctx) return null;
	const parts = ctx.split('_');
	const m = PERIOD_RE.exec(parts[0] ?? '');
	if (!m) return null;
	const [q, mode] = markerToQuarterMode(m[4]!);
	return { ctxYear: Number(m[2]), ctxFlow: m[3]!, ctxQuarter: q, ctxMode: mode, axisPath: axisMembers(parts.slice(1)).join('|') };
}

const stripTags = (s: string): string => (s || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();

/** 금액 텍스트 → 원 환산 값. △/▲/(괄호) 음수, 콤마 strip. (주N)·비숫자는 null. */
function parseAmount(text: string, mult: number): number | null {
	const t = (text || '').trim();
	if (!t || NOTE_RE.test(t) || !NUM_RE.test(t)) return null;
	const neg = t[0] === '△' || t[0] === '▲' || t[0] === '-' || (t.startsWith('(') && t.endsWith(')'));
	const digits = t.replace(/[^\d.]/g, '');
	if (!digits || digits === '.') return null;
	const v = Number(digits);
	if (!Number.isFinite(v)) return null;
	return (neg ? -v : v) * mult;
}

/** 본문 '단위 : 백만원|천원|원' → 원 배율. 미발견 백만원(기본). */
export function detectUnit(text: string): number {
	const m = UNIT_RE.exec(text || '');
	return m ? (UNIT_SCALE[m[1]!] ?? 1e6) : 1e6;
}

/** panel contentRaw(표 XML) → XBRL <TE ACODE ACONTEXT> 셀 직독. ACONTEXT 없으면(옛 양식) 빈 배열(최근만).
 * TR 별 첫 ACODE-없는 TE = 한글 라벨, ACODE+ACONTEXT TE = value 셀. mult = 호출측 단위 배율. */
export function xbrlCellsFromContent(contentRaw: string, mult: number): XbrlCell[] {
	const out: XbrlCell[] = [];
	if (!contentRaw || contentRaw.indexOf('ACONTEXT') < 0) return out;
	const trs = contentRaw.match(/<TR[^>]*>[\s\S]*?<\/TR>/gi);
	if (!trs) return out;
	for (const tr of trs) {
		const tes = [...tr.matchAll(/<TE([^>]*)>([\s\S]*?)<\/TE>/gi)];
		if (!tes.length) continue;
		// 라벨 = 첫 ACODE-없는 TE
		let label = '';
		for (const te of tes) {
			if (!/ACODE\s*=\s*"[^"]+"/i.test(te[1]!)) {
				const txt = stripTags(te[2]!);
				if (txt) {
					label = txt;
					break;
				}
			}
		}
		for (const te of tes) {
			const attrs = te[1]!;
			const acodeM = /ACODE\s*=\s*"([^"]*)"/i.exec(attrs);
			const actxM = /ACONTEXT\s*=\s*"([^"]*)"/i.exec(attrs);
			if (!acodeM || !actxM || !acodeM[1] || !actxM[1]) continue;
			const decoded = decodeAcontext(actxM[1]);
			if (!decoded) continue;
			const value = parseAmount(stripTags(te[2]!), mult);
			if (value == null) continue;
			out.push({ acode: acodeM[1], label, value, ...decoded });
		}
	}
	return out;
}
