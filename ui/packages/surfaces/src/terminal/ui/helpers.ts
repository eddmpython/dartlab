// DartLab Terminal · 공유 UI 헬퍼 (bilingual 해석 · tone 클래스 · 포맷).
import type { Bilingual, Lang, Tone } from '../lib/types';

type MaybeBilingual = Bilingual | { kr?: string; en?: string } | string | null | undefined;

export function tx(obj: MaybeBilingual, lang: Lang): string {
	if (obj == null) return '';
	if (typeof obj === 'string') return obj;
	return obj[lang] || obj.kr || obj.en || '';
}
// compact 라벨 · 현재 언어 1개만 (dense)
export function txc(obj: MaybeBilingual, lang: Lang): string {
	if (obj == null) return '';
	if (typeof obj === 'string') return obj;
	return lang === 'en' ? obj.en || obj.kr || '' : obj.kr || obj.en || '';
}

export function toneClass(t: Tone | string | undefined): string {
	return (
		{ up: 'tUp', down: 'tDn', good: 'tGood', warn: 'tWarn', neutral: 'tNeu' } as Record<string, string>
	)[t || 'neutral'] || 'tNeu';
}
export function chgClass(n: number | null | undefined): string {
	return n != null && n > 0 ? 'tUp' : n != null && n < 0 ? 'tDn' : 'tNeu';
}

export function fmtNum(n: number | null | undefined, d = 0): string {
	if (n == null || Number.isNaN(n)) return '·';
	return n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
}
export function fmtAbbr(n: number | null | undefined): string {
	if (n == null || Number.isNaN(n)) return '·';
	const a = Math.abs(n);
	if (a >= 1e12) return (n / 1e12).toFixed(2) + 'T';
	if (a >= 1e9) return (n / 1e9).toFixed(2) + 'B';
	if (a >= 1e6) return (n / 1e6).toFixed(1) + 'M';
	if (a >= 1e3) return (n / 1e3).toFixed(0) + 'K';
	return '' + n;
}
export function sign(n: number | null | undefined, d = 2): string {
	if (n == null || Number.isNaN(n)) return '·';
	return (n > 0 ? '+' : '') + fmtNum(n, d);
}
// 미니 스파크라인 polyline points (min-max 정규화) · 티커 스트립·KPI·좌측 레일 공유
export function sparkPts(s: number[], w = 34, h = 11): string {
	const lo = Math.min(...s);
	const hi = Math.max(...s);
	const rng = hi - lo || 1;
	return s.map((v, i) => `${((i / (s.length - 1)) * w).toFixed(1)},${(h - ((v - lo) / rng) * (h - 1.5) - 0.75).toFixed(1)}`).join(' ');
}

// heat color for sector/change cells (zip 팔레트: 상승=초록, 하락=빨강)
export function heat(v: number, max = 1): string {
	const t = Math.max(-1, Math.min(1, v / max));
	if (t >= 0) return `rgba(52, 211, 153, ${0.06 + t * 0.45})`;
	return `rgba(240, 97, 111, ${0.06 + -t * 0.45})`;
}

// 'LIVE' 라벨 금지 · 모든 소스가 EOD·일배치·분기공시 캐시(실시간 아님). 실데이터/파생만 구분.
export const PROV: Record<string, { kr: string; en: string; cls: string; t: Bilingual }> = {
	real: { kr: '실데이터', en: 'REAL', cls: 'pReal', t: { kr: '공시·시세 원천 실데이터 (EOD·일배치)', en: 'real source data (EOD · daily batch)' } },
	derived: { kr: '파생', en: 'DERIVED', cls: 'pDeriv', t: { kr: '실데이터에서 계산 (엔진출력 아님)', en: 'computed from real data' } },
	wire: { kr: '재구성', en: 'RECON', cls: 'pWire', t: { kr: '실 지표 기반 재구성', en: 'reconstructed from real metrics' } }
};
