// panel 셀 렌더 순수 헬퍼 · ui/web `analysis.$code.viewer.tsx` 1:1 포팅 (프레임워크 무관 TS).
// panel 셀 = raw DART XML (무손실, 대문자 정부 태그). 브라우저 렌더 위해 표준 html 로 정규화 + sanitize.

// ── DART 대문자 XML → 표준 html 태그 맵 ──
const DART_TAG_MAP: Record<string, string> = {
	'TABLE-GROUP': 'div',
	TABLE: 'table',
	THEAD: 'thead',
	TBODY: 'tbody',
	TR: 'tr',
	TH: 'th',
	TU: 'th',
	TE: 'td',
	TD: 'td',
	P: 'div',
	SPAN: 'span',
	TITLE: 'div',
	BR: 'br'
};

// DART USERMARK(폰트 size/볼드/색) → 구조 class. 원본은 절제목·소항목 헤딩을 USERMARK="F-NN B" 로 인코딩 ·
// F-14↑ = 소항목 헤딩(가/나/다, block+볼드+위 줄바꿈), 그 외 B = 인라인 볼드. 본문(F-10)·색상(0X)·폰트패밀리
// (F-GL/F-BT)는 손대지 않음(다크테마 가독성). standalone "B" 만 볼드로(F-BT/F-GL 의 B 오탐 차단).
export function userMarkClass(um: string): string {
	const sizeM = /F-(?:GL|BT)?(\d+)/.exec(um);
	const size = sizeM ? parseInt(sizeM[1], 10) : 0;
	const bold = /(?:^|\s)B(?:\s|$)/.test(um);
	if (size >= 14) return 'dm-h'; // 소항목 헤딩
	if (bold) return 'dm-b'; // 인라인 강조
	return '';
}

// ACODE/ACONTEXT 등 정부 메타 속성 제거, 표 구조 속성(colspan/rowspan/align) + 헤딩 구조 class 보존.
export function normalizeDartXml(value: string): string {
	if (!value || value.indexOf('<') < 0) return value;
	return value.replace(
		/<(\/?)([A-Za-z][\w-]*)((?:\s[^>]*)?)\s*\/?>/g,
		(_m, slash: string, tag: string, attrs: string) => {
			const upper = tag.toUpperCase();
			const name = DART_TAG_MAP[upper] ?? tag.toLowerCase();
			let keep = '';
			if (!slash && attrs) {
				const am = attrs.match(/\b(colspan|rowspan|align)\s*=\s*("[^"]*"|'[^']*'|\S+)/gi);
				if (am) keep = ' ' + am.join(' ');
				// 헤딩 구조 · TITLE(절 제목) + SPAN USERMARK(size/볼드). 원본 문서구조를 적당히 반영.
				let cls = '';
				if (upper === 'TITLE') cls = 'dm-title';
				else if (upper === 'SPAN') {
					const um = attrs.match(/USERMARK\s*=\s*"([^"]*)"/i);
					if (um) cls = userMarkClass(um[1]);
				}
				if (cls) keep += ` class="${cls}"`;
			}
			return `<${slash}${name}${keep}>`;
		}
	);
}

// DART 본문은 untrusted · DOMPurify 로 script/style/handler/iframe 제거 (CellContent.svelte 에서 적용).
export const SANITIZE_CONFIG = {
	ALLOWED_TAGS: ['table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'br', 'span', 'div', 'b', 'i', 'u', 'strong', 'em', 'sub', 'sup'],
	ALLOWED_ATTR: ['colspan', 'rowspan', 'class', 'align']
};

// HTML 본문에서 `<table>...</table>` block 추출 + 사이 텍스트 보존.
export function splitHtmlAndText(value: string): Array<['html' | 'text', string]> {
	const out: Array<['html' | 'text', string]> = [];
	const re = /<table[\s\S]*?<\/table>/gi;
	let last = 0;
	let m: RegExpExecArray | null;
	while ((m = re.exec(value)) !== null) {
		if (m.index > last) {
			const before = value.slice(last, m.index).trim();
			if (before) out.push(['text', before]);
		}
		out.push(['html', m[0]]);
		last = m.index + m[0].length;
	}
	if (last < value.length) {
		const tail = value.slice(last).trim();
		if (tail) out.push(['text', tail]);
	}
	return out;
}

const PERIOD_LABEL_RE = /^(?:당기|전기|당기말|전기말|당분기|전분기|당반기|전반기|당기누적|전기누적|3개월|누적|보고기간말)$/;
const UNIT_RE = /\(?\s*단위\s*[:：]?\s*[^)]+\)?/;
const PERIOD_DATE_RE = /^제\s*\d+\s*기/;

// HTML <table> 직전 paragraph 가 (단위 …)/회기일자/period label 패턴이면 표 caption/unit 흡수.
export function absorbCaptionUnitFromText(textBefore: string): { caption: string; unit: string; remaining: string } {
	const lines = textBefore.split('\n').map((l) => l.trim()).filter(Boolean);
	let caption = '';
	let unit = '';
	const remaining: string[] = [];
	for (const line of lines) {
		if (UNIT_RE.test(line) && line.length < 40) {
			if (!unit) unit = line.replace(/^\(|\)$/g, '');
			continue;
		}
		if (PERIOD_LABEL_RE.test(line)) {
			caption = caption ? `${caption} · ${line}` : line;
			continue;
		}
		if (PERIOD_DATE_RE.test(line) && line.length < 80) {
			caption = caption ? `${caption} · ${line}` : line;
			continue;
		}
		remaining.push(line);
	}
	return { caption, unit, remaining: remaining.join('\n') };
}

// 인라인 태그 strip (텍스트 조각의 caption/unit 패턴 매칭용). 블록 태그는 개행 보존.
export function stripInlineTags(s: string): string {
	return s
		.replace(/<\s*br\s*\/?>/gi, '\n')
		.replace(/<\/\s*(p|div|title|li|tr)\s*>/gi, '\n')
		.replace(/<[^>]+>/g, ' ')
		.replace(/[^\S\n]+/g, ' ')
		.replace(/[ \t]*\n[ \t]*/g, '\n')
		.replace(/\n{3,}/g, '\n\n')
		.trim();
}
