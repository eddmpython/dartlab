// IPO 발굴 · 워커 /ipo-filings 라이브 read-through(최근 85일, corp_cls=E + 지분증권 신고 C001) → 3조건
// 판별 미러 → 발행사 그룹핑(최신 FULL 신고서 + [발행조건확정] doc). 상장 전 발행사는 allFilings HF
// bake(Y/K 한정)에 없어 이 라이브 경로가 퍼블릭 유일 데이터원(베이크 0). 공개/로컬 공통배선(:8400 불요).
// 판별 정본 = src/dartlab/providers/dart/securitiesRegistration.classifyIpo. 아래 미러는 소비 필터일 뿐
// 정의를 소유하지 않는다(정본 변경 시 여기 동기화). 미배선/실패 = [] 정직 표기.
import type { IpoFiling } from '@dartlab/ui-contracts';
import type { DataCore } from '../../../data/fetch/request';
import { originConfigured } from '../../../data/origins/registry';

/** 워커 /ipo-filings 응답 행(list.json 필드 camelCase). */
export interface IpoWorkerRow {
	rceptNo?: string;
	rceptDate?: string;
	corpCode?: string;
	corpCls?: string;
	stockCode?: string;
	corpName?: string;
	reportNm?: string;
	filer?: string;
}

// classifyIpo 미러 · _SUBTYPES 앞 4자 매칭(정본 s[:4] in inner 과 동일 규칙).
const SUBTYPES = ['지분증권', '집합투자증권', '채무증권', '유동화증권', '투자계약증권', '파생결합증권'];

// 증권신고서 직후 *첫 괄호* = 정본 subtype (펀드명 속 '(지분증권)' 오매칭 차단 · 정본 _subtype 미러).
function subtypeOf(reportNm: string): string {
	const m = reportNm.match(/증권신고서\(([^)]+)\)/);
	const inner = m?.[1] ?? '';
	if (!inner) return '기타';
	for (const s of SUBTYPES) if (inner.includes(s.slice(0, 4))) return s;
	return inner;
}

// 스팩 식별 · report_nm 아니라 회사명(정본 AntiPatterns 동일).
const spacOf = (corpName: string): boolean => corpName.includes('스팩') || corpName.includes('기업인수목적');

/** 3조건 판별 미러(지분증권 subtype + corp_cls=E + 빈 stock_code) + prospectus/notice 분리. */
export function classifyIpoMeta(
	reportNm: string,
	corpCls: string,
	stockCode: string,
	corpName: string
): { isIpo: boolean; isSpac: boolean; kind: 'prospectus' | 'notice' } {
	const subtype = subtypeOf(reportNm);
	const kind = reportNm.startsWith('효력발생안내') || reportNm.includes('정정신고서제출요구') ? 'notice' : 'prospectus';
	return { isIpo: subtype === '지분증권' && corpCls === 'E' && stockCode.trim() === '', isSpac: spacOf(corpName), kind };
}

/** 발행사(corp_code) 그룹핑 · 최신 FULL 신고서(초판·기재정정, 발행조건확정 제외) + 최신 확정 doc. 순수(테스트 용이). */
export function groupIpoFilings(rows: IpoWorkerRow[]): IpoFiling[] {
	const byCorp = new Map<string, { full?: Required<Pick<IpoWorkerRow, 'rceptNo'>> & IpoWorkerRow; conf?: IpoWorkerRow }>();
	for (const r of rows) {
		const reportNm = String(r.reportNm ?? '').trim();
		const rceptNo = String(r.rceptNo ?? '').trim();
		const corpName = String(r.corpName ?? '').trim();
		const key = String(r.corpCode ?? '').trim() || corpName;
		if (!rceptNo || !key) continue;
		const c = classifyIpoMeta(reportNm, String(r.corpCls ?? '').trim(), String(r.stockCode ?? ''), corpName);
		if (!c.isIpo) continue; // 투자설명서·발행실적보고서·타 subtype = 비대상
		const slot = byCorp.get(key) ?? {};
		if (reportNm.includes('발행조건확정')) {
			// 확정공모가 doc(CORRECTION, 6섹션 없음) · 파싱 대상 아님, 리포트에 확정가 병합용.
			if (!slot.conf || rceptNo > String(slot.conf.rceptNo)) slot.conf = { ...r, rceptNo, reportNm };
		} else if (c.kind === 'prospectus') {
			if (!slot.full || rceptNo > slot.full.rceptNo) slot.full = { ...r, rceptNo, reportNm };
		}
		byCorp.set(key, slot);
	}
	const out: IpoFiling[] = [];
	for (const { full, conf } of byCorp.values()) {
		if (!full) continue; // FULL 신고서가 윈도우 밖(확정 doc 만 잔존) = 파싱 대상 없음 → 제외
		const corpName = String(full.corpName ?? '').trim();
		out.push({
			corpName,
			corpCode: String(full.corpCode ?? '').trim(),
			rceptNo: full.rceptNo,
			rceptDate: String(full.rceptDate ?? '').trim(),
			reportNm: String(full.reportNm ?? '').trim(),
			isSpac: spacOf(corpName),
			corrected: String(full.reportNm ?? '').includes('기재정정'),
			confirmationRceptNo: conf ? String(conf.rceptNo) : null,
			confirmationDate: conf ? String(conf.rceptDate ?? '').trim() || null : null,
			url: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${full.rceptNo}`
		});
	}
	out.sort((a, b) => b.rceptDate.localeCompare(a.rceptDate) || b.rceptNo.localeCompare(a.rceptNo));
	return out;
}

export async function loadIpoFilings(core: DataCore): Promise<IpoFiling[]> {
	if (!originConfigured('ipoFilingsWorker')) return []; // 워커 미배선 → 발굴 빈값(정직 floor)
	try {
		const j = await core.request<{ items?: IpoWorkerRow[] }>({
			origin: 'ipoFilingsWorker',
			path: '', // 쿼리 없는 고정 라우트
			cacheKey: 'ipoFilings.recent',
			cache: { scope: 'memory', ttlMs: 30 * 60_000, maxEntries: 1 }, // 워커 엣지 1800s 와 일치
			parse: (r) => (r.ok ? (r.json() as Promise<{ items?: IpoWorkerRow[] }>) : Promise.resolve({}))
		});
		return groupIpoFilings(Array.isArray(j.items) ? j.items : []);
	} catch {
		return [];
	}
}
