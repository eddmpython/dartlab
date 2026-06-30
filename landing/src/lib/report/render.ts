// /report·/cards 공용 순수 렌더 헬퍼 · 기하/포맷/신호색. Svelte 비의존(window/document 없음)이라
// 단위테스트 가능하고 두 소비자가 같은 렌더 언어를 공유한다. report/+page.svelte 인라인에서 추출
// (명명함수 → 기계적 동치, vitest 가 중립색·verdict 합성 0 을 고정). 새 합성·LLM·신규 숫자 없음.

/** 마크다운 강조(**) 제거 + em/en 대시 제거(절 구분은 쉼표로). 표/카드/리포트 prose 공용 정리. */
export function clean(t: unknown): string {
	return String(t ?? '')
		.replace(/\*\*(.+?)\*\*/g, '$1')
		.replace(/\*\*/g, '')
		.replace(/\s*[·-]\s*/g, ', ') // em/en 대시 제거 → 쉼표(절 구분)
		.replace(/\s*,\s*,/g, ',') // 중복 쉼표 정리
		.replace(/\s{2,}/g, ' ')
		.replace(/^[\s,]+|[\s,]+$/g, ''); // 앞뒤 잔여 쉼표·공백
}

export const engineLabel: Record<string, string> = {
	analysis: '재무분석',
	credit: '신용평가',
	quant: '시장·기술',
	industry: '산업비교',
	macro: '거시',
	story: '종합서사'
};

/** 숫자 셀 신호색 · 음수(적)/양수(녹). 단위·기호를 걷어낸 코어로 판정. 같은 색으로 좋고/나쁨 주장 안 함. */
export function cellTone(v: unknown): string {
	const s = String(v ?? '').trim();
	if (!s || s === '-') return '';
	const core = s.replace(/[%조억원배일pP ,]/g, '');
	if (/^[-−△▼(]/.test(s) || /^-/.test(core)) return 'neg';
	if (/^[+▲]/.test(s)) return 'pos';
	return '';
}

// 판정 어휘 신호색 · 신용/건전성 점검표의 '양호/주의' 전용(적색=음수 SSOT와 분리해 주의=황갈).
export function verdictTone(v: unknown): string {
	const s = String(v ?? '').trim();
	if (s.startsWith('양호') || s === '안정' || s === '충족') return 'ok';
	if (s.startsWith('주의') || s === '경계' || s === '미달') return 'warn';
	return ''; // '산출 불가' 등 → 중립
}

// 비숫자 의미 컬럼(좌측 텍스트, cellTone 미적용) 화이트리스트
export const TXT_COLS = new Set(['최근 범위', '기준', '업종 내 위치']);

// 스파크라인 · 64×22 면적 채움 microchart. 색은 중립(accent): 같은 색으로 좋고/나쁨을
// 주장하지 않게(부채비율↓·매출↑ 모두 같은 색). 좋고 나쁨은 판정 컬럼·본문이 말한다.
export function spark(row: Record<string, string>, yearCols: string[]) {
	const pairs: { yr: number; n: number }[] = [];
	for (const yk of yearCols) {
		const yr = parseInt(yk, 10);
		if (!Number.isFinite(yr)) continue;
		const raw = String(row[yk] ?? '').replace(/[^0-9.\-]/g, '');
		const n = parseFloat(raw);
		pairs.push({ yr, n: Number.isFinite(n) ? n : NaN });
	}
	pairs.sort((a, b) => a.yr - b.yr);
	const nums: number[] = pairs.map((p) => p.n);
	const valid = nums.filter((n) => Number.isFinite(n));
	if (valid.length < 3) return null;
	// robust 도메인 · 단일 극단값(예: NAVER FY21 순이익률 241.7%)이 나머지를 1px 평지로
	// 깔아 추세를 거짓 전달하지 않게 median±3·IQR 로 *그리는 값만* 클램프(표 숫자는 불변).
	const sorted = [...valid].sort((a, b) => a - b);
	const q = (p: number) => sorted[Math.max(0, Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * p)))];
	const med = q(0.5);
	const iqr = q(0.75) - q(0.25) || Math.abs(med) || 1;
	const clipLo = med - 3 * iqr,
		clipHi = med + 3 * iqr;
	const plot = nums.map((n) => (Number.isFinite(n) ? Math.min(clipHi, Math.max(clipLo, n)) : NaN));
	const clipped = nums.map((n) => Number.isFinite(n) && (n > clipHi || n < clipLo));
	const pv = plot.filter((n) => Number.isFinite(n));
	let min = Math.min(...pv);
	let max = Math.max(...pv);
	const hasNeg = Math.min(...valid) < 0;
	if (hasNeg) {
		min = Math.min(min, 0);
		max = Math.max(max, 0);
	}
	const range = max - min || 1;
	const w = 64,
		h = 22,
		pad = 2;
	const ih = h - pad * 2;
	const step = w / (nums.length - 1);
	const xy = plot.map((n, i) =>
		Number.isFinite(n) ? { x: i * step, y: pad + (ih - ((n - min) / range) * ih), clip: clipped[i] } : null
	);
	const pts = xy.filter(Boolean) as { x: number; y: number; clip: boolean }[];
	if (pts.length < 2) return null;
	const points = pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
	const area = `${pts[0].x.toFixed(1)},${h} ` + points + ` ${pts[pts.length - 1].x.toFixed(1)},${h}`;
	const clipMarks = pts.filter((p) => p.clip).map((p) => ({ x: p.x.toFixed(1), y: p.y.toFixed(1) }));
	const lastP = pts[pts.length - 1];
	const zeroY = min < 0 && max > 0 ? (pad + (ih - ((0 - min) / range) * ih)).toFixed(1) : null;
	return { points, area, zeroY, clipMarks, lastX: lastP.x.toFixed(1), lastY: lastP.y.toFixed(1) };
}

export function isTimeSeries(cols: string[]): boolean {
	// 연도(2023) 또는 분기(25Q1) 라벨이 2열 이상이면 시계열 표 → 스파크라인.
	const ts = (s: string) => /^\d{4}$/.test(s) || /^\d{2}Q[1-4]$/.test(s);
	return cols.length >= 4 && ts(cols[1] ?? '');
}

export function chunk<T>(arr: T[], n: number): T[][] {
	const out: T[][] = [];
	for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n));
	return out;
}

// 표에 그릴 스파크라인이 하나라도 있나 · 전부 빈 칸이면 추이 컬럼 자체를 숨긴다(휑한 거터 방지).
export function tableHasSpark(data: Record<string, string>[], cols: string[]): boolean {
	return data.some((row) => spark(row, cols.slice(1)) != null);
}

// ── 라인 차트(주가 궤적) · series 정규화 + 면적 + 수평 마커 ──
export function lineGeo(series: number[], markers: { label: string; v: number }[] = []) {
	const v = series.filter((n) => Number.isFinite(n));
	if (v.length < 2) return null;
	const mv = markers.map((m) => m.v).filter((n) => Number.isFinite(n));
	const min = Math.min(...v, ...mv);
	const max = Math.max(...v, ...mv);
	const range = max - min || 1;
	const w = 100,
		h = 30;
	const step = w / (series.length - 1);
	const Y = (n: number) => (h - ((n - min) / range) * h).toFixed(2);
	const pts = series.map((n, i) => `${(i * step).toFixed(2)},${Y(n)}`).join(' ');
	const area = `0,${h} ` + pts + ` ${w},${h}`;
	const lastX = ((series.length - 1) * step).toFixed(2);
	const lastY = Y(series[series.length - 1]);
	const mk = markers.map((m) => ({ label: m.label, y: Y(m.v), top: (m.v - min) / range > 0.5 }));
	const up = series[series.length - 1] >= series[0];
	return { pts, area, lastX, lastY, mk, up };
}

export function wonLabel(v: number): string {
	return `${Math.round(v).toLocaleString('en-US')}원`;
}

export function splitTitle(t: string): { head: string; sub: string } {
	const s = String(t ?? '');
	const m = s.split(/\s*(?:--|·|·)\s*/);
	if (m.length >= 2) return { head: m[0].trim(), sub: m.slice(1).join(' · ').trim() };
	return { head: s.trim(), sub: '' };
}
