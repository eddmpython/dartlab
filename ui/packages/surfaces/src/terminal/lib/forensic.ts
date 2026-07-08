// 포렌식 적신호 · 풀스크린 재무탭(finTabs)에 묻힌 결정론 위험지표를 우측 패널 한눈 프리뷰로 승격(신규 데이터 0,
// auditFees·debtProfile = 기존 ReportPort). 임계를 *넘은* 신호만 산출 · 정상치는 표시하지 않는다(완결성 주장
// 회피: "이상 없음" 같은 전역 단정 금지 · 빈 결과면 소비처가 패널 자체를 숨긴다). 값은 이미 공시된 사실의 비율.
import type { AuditFeeYear, DebtProfileBundle } from '@dartlab/ui-contracts';

export type ForensicLevel = 'red' | 'amber';
export interface ForensicSignal {
	id: 'auditIndependence' | 'debtWall';
	level: ForensicLevel;
	kr: string;
	en: string;
	val: string; // 핵심 수치 (공시된 사실) · 글랜스 detail
	// 통합된 리스크 경고등 다이얼로그에서 이 신호를 설명하기 위한 카탈로그 필드(riskRules.RiskRule 와 동형).
	whatKr: string;
	whatEn: string;
	thresholdKr: string;
	thresholdEn: string;
	source: string;
}

const jo = (won: number): string => (won / 1e12).toFixed(2);

/** 감사인 독립성 · 최신연도 비감사/감사 보수 비율. 비감사가 감사보수에 근접·초과하면 독립성 적신호(회계 고전 지표). */
function auditIndependence(af: AuditFeeYear[] | null): ForensicSignal | null {
	if (!af || !af.length) return null;
	const last = af[af.length - 1];
	if (last.auditFee == null || last.auditFee <= 0 || last.nonAuditFee == null) return null;
	const ratio = last.nonAuditFee / last.auditFee;
	if (ratio < 0.5) return null; // 임계 미만 = 정상(미표시)
	return {
		id: 'auditIndependence',
		level: ratio >= 1 ? 'red' : 'amber',
		kr: '감사인 독립성',
		en: 'Auditor independence',
		val: `비감사/감사 ${Math.round(ratio * 100)}% · ${last.year}`,
		whatKr: '감사인이 컨설팅 수입에 휘둘리지 않는가 · 비감사/감사 보수 비율',
		whatEn: 'Is the auditor free of consulting-revenue capture · non-audit / audit fee ratio',
		thresholdKr: '비감사/감사 ≥ 100% → red · 50~100% → yellow',
		thresholdEn: 'non-audit/audit ≥ 100% → red · 50-100% → yellow',
		source: '정기보고서 감사·비감사 보수 (ReportPort.auditFees)'
	};
}

/** 단기 상환벽 · 최신연도 1년이하 사채+단기사채+CP vs 현금성자산(원 단위). 단기상환액이 현금에 근접·초과하면 유동성 적신호. */
function debtWall(dp: DebtProfileBundle | null, cashLatestWon: number | null): ForensicSignal | null {
	if (!dp || !dp.years.length || cashLatestWon == null || cashLatestWon <= 0) return null;
	const last = dp.years[dp.years.length - 1];
	const shortTerm = (last.bond1y ?? 0) + (last.stb ?? 0) + (last.cp ?? 0);
	if (shortTerm <= 0) return null;
	const ratio = shortTerm / cashLatestWon;
	if (ratio < 0.7) return null;
	return {
		id: 'debtWall',
		level: ratio >= 1 ? 'red' : 'amber',
		kr: '단기 상환벽',
		en: 'Near-term debt wall',
		val: `1년내 ${jo(shortTerm)}조 / 현금 ${jo(cashLatestWon)}조`,
		whatKr: '1년 내 갚을 사채를 현금으로 덮는가 · 단기사채+CP vs 현금성자산',
		whatEn: 'Do near-term bonds fit within cash · short-term bonds+CP vs cash',
		thresholdKr: '단기상환액/현금 ≥ 100% → red · 70~100% → yellow',
		thresholdEn: 'short-term repayment/cash ≥ 100% → red · 70-100% → yellow',
		source: '정기보고서 사채 잔존만기 · 현금성자산 (ReportPort.debtProfile)'
	};
}

/** 임계 초과 적신호 목록 · 비면 소비처가 패널을 숨긴다(정상=무표시, 완결성 단정 금지). */
export function forensicSignals(input: {
	auditFees: AuditFeeYear[] | null;
	debtProfile: DebtProfileBundle | null;
	cashLatestWon: number | null;
}): ForensicSignal[] {
	return [auditIndependence(input.auditFees), debtWall(input.debtProfile, input.cashLatestWon)].filter(
		(s): s is ForensicSignal => s != null
	);
}
