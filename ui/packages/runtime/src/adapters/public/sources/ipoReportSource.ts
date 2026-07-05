// IPO 공모분석 리포트 · HF dart/ipo/reports.parquet 직독(rcept 키, reportJson 컬럼 = 전체 IpoReport).
// 왓치 cron 이 buildIpoReport 로 파싱해 구운 구조화 typed 산출을 터미널이 다른 데이터(finance·scan·
// market_recent)와 동일하게 whole-file 직독 + JSON.parse(reportSource 동형). 파서 재구현 0 · pyodide 0.
// 퍼블릭엔 이게 유일 report 경로(원문 파싱은 브라우저 불가). 로컬은 이걸 우선 쓰고 미베이크분만 /api 헤드룸.
import type { IpoReport } from '@dartlab/ui-contracts';
import type { DataCore } from '../../../data/fetch/request';

interface ReportRow extends Record<string, unknown> {
	rcept?: unknown;
	reportJson?: unknown;
}

/**
 * rcept 로 베이크된 리포트 1건 직독. 미베이크(다음 cron 전)·미배선·파싱실패는 null(정직 표기).
 * 파일이 소형(~30 발행사)이라 whole-file read + rcept 필터(정렬 무관). reportJson 은 전체 IpoReport JSON.
 */
export async function loadIpoReport(core: DataCore, rceptNo: string): Promise<IpoReport | null> {
	const rcept = String(rceptNo || '').trim();
	if (!rcept) return null;
	try {
		const rows = await core.requestParquetRows<ReportRow>({
			origin: 'hfRange',
			path: 'dart/ipo/reports.parquet',
			columns: ['rcept', 'reportJson'],
			filter: { rcept: { $eq: rcept } },
			cacheKey: `ipoReport:${rcept}`,
			cache: { scope: 'memory', ttlMs: 30 * 60_000, maxEntries: 64 } // 리포트는 rcept 단위 사실상 불변(정정 시 cron 갱신)
		});
		const raw = rows.find((r) => String(r.rcept ?? '').trim() === rcept)?.reportJson;
		if (raw == null) return null;
		const parsed = JSON.parse(String(raw)) as IpoReport;
		return parsed && typeof parsed === 'object' && Array.isArray(parsed.sections) ? parsed : null;
	} catch {
		return null;
	}
}
