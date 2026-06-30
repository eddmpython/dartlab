// 표시 포맷 헬퍼 · 재무 값은 모두 조(兆) KRW 단위(StmtRow.values 계약). 단위는 표별 자동 스케일.
import type { Num } from '@dartlab/ui-contracts';
import { fmtKrwFromJo, pickKrwUnit } from '@dartlab/ui-format/krw';

/** 기간 라벨 → 4자리 연도 컬럼 ('FY23' → '2023'). 분기 라벨은 그대로. */
export function pYear(label: string): string {
	const m = /^FY(\d{2})$/.exec(label);
	if (m) return `20${m[1]}`;
	return label;
}

export function fmtPct(v: Num, digits = 1): string {
	if (v == null || !Number.isFinite(v)) return '-';
	return `${(v as number).toFixed(digits)}%`;
}

export function fmtPctSigned(v: Num, digits = 1): string {
	if (v == null || !Number.isFinite(v)) return '-';
	const n = v as number;
	return `${n > 0 ? '+' : ''}${n.toFixed(digits)}%`;
}

export function fmtMult(v: Num, digits = 2): string {
	if (v == null || !Number.isFinite(v)) return '-';
	return `${(v as number).toFixed(digits)}배`;
}

/** 단일 금액(조 단위 값) → 조/억 자연 단위. KPI·문장용. SSOT(@dartlab/ui-format) 위임 · 0.0조 차단. */
export function fmtAmt1(v: Num): string {
	if (v == null || !Number.isFinite(v)) return '-';
	return fmtKrwFromJo(v as number);
}

/** 조 단위 값 묶음 → 표 전체 단일 스케일(SSOT pickKrwUnit). "억이 지배하면 전부 억" · 매출(조)·
 *  영업이익(억)이 섞이면 다수인 억으로 통일해 혼합·"0.0조"를 함께 없앤다. 전부 조면 조 유지. */
export function scaleAmt(values: Num[]): { unit: string; scale: number } {
	const sc = pickKrwUnit(values, { from: '조' });
	return { unit: `${sc.unit}원`, scale: sc.scale };
}

export function fmtScaled(v: Num, scale: number): string {
	if (v == null || !Number.isFinite(v)) return '-';
	const x = (v as number) * scale;
	// 억으로 환산돼 커진 값(1,000+)은 정수 천단위 콤마, 조 단위(1,000 미만)는 1자리 소수(열 정렬).
	if (Math.abs(x) >= 1000) return Math.round(x).toLocaleString('en-US');
	return x.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

/** 주식수 · 억주/만주/주 자동. */
export function fmtShares(v: Num): string {
	if (v == null || !Number.isFinite(v)) return '-';
	const n = v as number;
	const a = Math.abs(n);
	if (a === 0) return '0';
	if (a >= 1e8) return `${(n / 1e8).toFixed(2)}억주`;
	if (a >= 1e4) return `${Math.round(n / 1e4).toLocaleString('en-US')}만주`;
	return `${Math.round(n).toLocaleString('en-US')}주`;
}

/** 원 금액 · 큰 값은 조/억, 작은 값(주당 등)은 원. */
export function fmtWon(v: Num): string {
	if (v == null || !Number.isFinite(v)) return '-';
	const n = v as number;
	const a = Math.abs(n);
	if (a >= 1e12) return `${(n / 1e12).toFixed(1)}조`;
	if (a >= 1e8) return `${Math.round(n / 1e8).toLocaleString('en-US')}억`;
	return `${Math.round(n).toLocaleString('en-US')}원`;
}

/** 보수·급여(원) · 억/만원/원. (fmtWon 은 DPS 등 소액에 원 유지가 필요해 별도.) */
export function fmtPay(v: Num): string {
	if (v == null || !Number.isFinite(v)) return '-';
	const n = v as number;
	const a = Math.abs(n);
	if (a >= 1e8) return `${(n / 1e8).toFixed(1)}억`;
	if (a >= 1e4) return `${Math.round(n / 1e4).toLocaleString('en-US')}만원`;
	return `${Math.round(n).toLocaleString('en-US')}원`;
}

/** 정수 카운트 + 접미사. */
export function fmtNum(v: Num, suffix = ''): string {
	if (v == null || !Number.isFinite(v)) return '-';
	return `${Math.round(v as number).toLocaleString('en-US')}${suffix}`;
}

/** lo~hi 범위를 단일 단위로 일관 표기(조 축의 억·조 혼용 방지). */
export function fmtRange(lo: Num, hi: Num, unit: '%' | '배' | '조'): string {
	if (lo == null || hi == null || !Number.isFinite(lo) || !Number.isFinite(hi)) return '-';
	if (unit === '%') return `${fmtPct(lo)} ~ ${fmtPct(hi)}`;
	if (unit === '배') return `${fmtMult(lo)} ~ ${fmtMult(hi)}`;
	// 조 · 두 값을 같은 단위로(둘 중 큰 절대값 기준)
	const maxAbs = Math.max(Math.abs(lo as number), Math.abs(hi as number));
	if (maxAbs >= 1) return `${(lo as number).toFixed(1)}조 ~ ${(hi as number).toFixed(1)}조`;
	return `${Math.round((lo as number) * 10000).toLocaleString('en-US')}억 ~ ${Math.round((hi as number) * 10000).toLocaleString('en-US')}억`;
}
