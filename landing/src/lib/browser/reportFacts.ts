// 보고서 비재무 fact 매퍼 · 정기보고서 parquet row → LiveCompanyReportFact. companyLive 에서 격리(순수 row-shaper).
// 타입 import 는 erased(런타임 circular 무해) · 값 의존은 companyLive→reportFacts 단방향.
import type { LiveCompanyReportFact } from './companyLive';

// 정기보고서 parquet row 의 부분 스키마(DART 필드코드) · 매퍼가 읽는 필드만 선언.
// 값은 문자열 셀로 다룬다(value/detail 가 string). readReportFactRows 가 any[] 를 주므로 caller 무영향(경계 격리).
export interface PeriodicReportRow {
	year?: string | null;
	// 도시에 스파인 · 출처 공시 접수번호(↗원문) + 결산 기준일(as-of)
	rcept_no?: string | null;
	stlm_dt?: string | null;
	// 배당
	thstrm?: string | null;
	se?: string | null;
	// 자사주
	trmend_qy?: string | null;
	stock_knd?: string | null;
	change_qy_acqs?: string | null;
	// 임원
	nm?: string | null;
	ofcps?: string | null;
	// 감사
	adt_opinion?: string | null;
	adtor?: string | null;
	emphs_matter?: string | null;
	core_adt_matter?: string | null;
	// 주요주주
	mxmm_shrholdr_nm?: string | null;
	qota_rt?: string | null;
	change_cause?: string | null;
	// 회사채
	facvalu_totamt?: string | null;
	scrits_knd_nm?: string | null;
	intrt?: string | null;
	evl_grad_instt?: string | null;
}

// 도시에 스파인 · 출처 공시(rcept_no) + 결산기준일(stlm_dt)을 fact 에 부착(↗원문·as-of). 모든 매퍼 공유.
function srcOf(row: PeriodicReportRow | null | undefined): { rceptNo: string | null; stlmDt: string | null } {
	const rc = row?.rcept_no?.trim();
	const sd = row?.stlm_dt?.trim();
	return { rceptNo: rc && rc !== '-' ? rc : null, stlmDt: sd && sd !== '-' ? sd : null };
}

export function toDividendFact(row: PeriodicReportRow | null | undefined): LiveCompanyReportFact | null {
	if (!row) return null;
	return {
		key: 'dividend',
		label: '배당',
		value: row.thstrm ?? row.se ?? '확인',
		detail: [row.year, row.stlm_dt].filter(Boolean).join(' · '),
		source: '정기보고서 배당',
		...srcOf(row)
	};
}

export function toTreasuryFact(row: PeriodicReportRow | null | undefined): LiveCompanyReportFact | null {
	if (!row) return null;
	return {
		key: 'treasuryStock',
		label: '자사주',
		value: row.trmend_qy ?? '확인',
		detail: [row.year, row.stock_knd, row.change_qy_acqs ? `취득 ${row.change_qy_acqs}` : null]
			.filter(Boolean)
			.join(' · '),
		source: '정기보고서 자사주',
		...srcOf(row)
	};
}

export function toExecutiveFact(rows: PeriodicReportRow[]): LiveCompanyReportFact | null {
	if (!rows.length) return null;
	return {
		key: 'executive',
		label: '임원',
		value: `${rows.length}명`,
		detail: rows.map((r) => [r.nm, r.ofcps].filter(Boolean).join(' ')).join(' · '),
		source: '정기보고서 임원',
		...srcOf(rows[0])
	};
}

export function toAuditFact(row: PeriodicReportRow | null | undefined): LiveCompanyReportFact | null {
	if (!row) return null;
	return {
		key: 'auditOpinion',
		label: '감사의견',
		value: row.adt_opinion ?? '확인',
		detail: [row.year, row.adtor, row.emphs_matter || row.core_adt_matter].filter(Boolean).join(' · '),
		source: '정기보고서 감사',
		...srcOf(row)
	};
}

export function toMajorHolderFact(row: PeriodicReportRow | null | undefined): LiveCompanyReportFact | null {
	if (!row) return null;
	return {
		key: 'majorHolder',
		label: '주요주주',
		value: row.mxmm_shrholdr_nm ?? '확인',
		detail: [row.year, row.qota_rt ? `${row.qota_rt}%` : null, row.change_cause].filter(Boolean).join(' · '),
		source: '정기보고서 주주',
		...srcOf(row)
	};
}

export function toCorporateBondFact(row: PeriodicReportRow | null | undefined): LiveCompanyReportFact | null {
	if (!row) return null;
	return {
		key: 'corporateBond',
		label: '회사채',
		value: row.facvalu_totamt ?? row.scrits_knd_nm ?? '확인',
		detail: [row.year, row.scrits_knd_nm, row.intrt, row.evl_grad_instt].filter(Boolean).join(' · '),
		source: '정기보고서 회사채',
		...srcOf(row)
	};
}
