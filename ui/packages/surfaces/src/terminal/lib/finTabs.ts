// 재무 전체화면 탭 레지스트리 · finance 심화 카드(TerminalFinance.tabCards, 모드 토글 동작)
// + report·교차 카드(연 축 고정, 카드 제목에 '· 연' 표기). 데이터 규칙은 전부 runtime ReportPort
// 구현이 보장 · 본 모듈은 포트 출력 → FinCard 매핑만 한다 (집계·재계산 없음).
// 교차 카드(배당여력·생산성·인건비)는 finBundle.views.annual.statements 의 조 단위 값을
// report 연도와 union 축으로 정렬한다 (결측 = null → MiniFinChart pen-up).
import type { FinCard, Num, ReportPort, TerminalFinanceBundle } from '@dartlab/ui-contracts';

export interface TabCard {
	card: FinCard;
	periods: string[];
}
export interface FsTab {
	key: string;
	label: { kr: string; en: string };
	q?: string; // 탭이 답하는 질문 · 분석 내러티브 캡션 (body 상단)
	finKey?: 'profitability' | 'cashflow' | 'debt' | 'shareholder'; // terminalFinance.tabCards 키 (모드 토글 동작)
	load?: (code: string, bundle: TerminalFinanceBundle, report: ReportPort) => Promise<TabCard[]>; // report·교차 (연 축) · 포트는 호출측(FinFullscreen)이 runtime 컨텍스트에서 주입
	note?: string; // 탭 하단 정직성 캡션
}

const C = { rev: '#5b9bf0', op: '#ec4899', net: '#34d399', good: '#34d399', warn: '#fbbf24', purple: '#a78bfa', red: '#f0616f', blue: '#60a5fa', cyan: '#22d3ee', dim: '#64748b' };

const fyLabel = (year: string) => 'FY' + year.slice(2);
// 시리즈 전부 null 인 카드는 버린다 (빈 카드 노출 금지 · 신규 탭 공통 규칙)
const alive = (tc: TabCard): boolean => tc.card.series.some((s) => s.data.some((v) => v != null));

// finance annual statements 에서 계정 1행을 연도('2024') → 조 값 Map 으로
function annualMap(bundle: TerminalFinanceBundle, stmt: 'IS' | 'BS' | 'CF', key: string): Map<string, number> {
	const out = new Map<string, number>();
	const av = bundle.views.annual;
	if (!av) return out;
	const row = av.statements[stmt].find((r) => r.key === key);
	if (!row) return out;
	av.periods.forEach((p, i) => {
		const m = p.match(/^FY(\d{2})$/);
		const v = row.values[i];
		if (m && v != null) out.set('20' + m[1], v);
	});
	return out;
}

async function cashflowReport(code: string, _bundle: TerminalFinanceBundle, report: ReportPort): Promise<TabCard[]> {
	const inv = await report.investments(code);
	if (!inv || inv.trend.length < 2) return [];
	const years = inv.trend.map((t) => t.year);
	const tc: TabCard = {
		periods: years.map(fyLabel),
		card: {
			key: 'investedBook', title: '타법인출자 추이 · 연', unit: '조', series: [
				{ name: '출자 장부가', data: inv.trend.map((t) => (t.bookTotal != null ? +(t.bookTotal / 1e12).toFixed(3) : null)), color: C.blue, type: 'bar' },
				{ name: '출자사 수(개)', data: inv.trend.map((t) => t.count), color: C.warn, type: 'line', axis: 'r' }
			]
		}
	};
	return [tc].filter(alive);
}

async function shareholderReport(code: string, bundle: TerminalFinanceBundle, report: ReportPort): Promise<TabCard[]> {
	const [sr, own, dil] = await Promise.all([
		report.shareholderReturn(code),
		report.ownership(code),
		report.capitalChanges(code)
	]);
	const cards: TabCard[] = [];
	const ownBy = new Map((own ?? []).map((o) => [o.year, o]));
	if (sr && sr.length) {
		const srYears = sr.map((s) => s.year);
		const srP = srYears.map(fyLabel);
		const niBy = annualMap(bundle, 'IS', 'netIncome');
		// 배당수익률 · 공시값(DPS/주가) 단일 시리즈. 자사주 취득가치는 공시에 금액이 없어
		// 연평균종가 추정에 의존하므로(진짜 공시값 아님) 총주주환원·자사주수익률 추정 카드는 제외.
		cards.push({
			periods: srP,
			card: {
				key: 'divYield', title: '배당수익률 · 연', unit: '%', series: [
					{ name: '배당수익률', data: sr.map((s) => s.yieldPct), color: C.blue, type: 'line' }
				]
			}
		});
		// ③ 주당지표 · EPS·DPS + 주당 배당성향
		cards.push({
			periods: srP,
			card: {
				key: 'perShare', title: '주당지표 (EPS·DPS) · 연', unit: '원', series: [
					{ name: 'EPS', data: sr.map((s) => s.eps), color: C.cyan, type: 'bar' },
					{ name: 'DPS', data: sr.map((s) => s.dps), color: C.blue, type: 'bar' },
					{ name: 'DPS/EPS%', data: sr.map((s) => (s.eps != null && s.eps > 0 && s.dps != null ? +((s.dps / s.eps) * 100).toFixed(1) : null)), color: C.purple, type: 'line', axis: 'r' }
				]
			}
		});
		// 배당여력 · report 연도 ∪ finance annual 연도 union 축 (비12월 결산은 사업연도 기준 정렬)
		const cfoBy = annualMap(bundle, 'CF', 'cfOperating');
		const capexBy = annualMap(bundle, 'CF', 'capex');
		const years = [...new Set([...srYears, ...niBy.keys()])].sort();
		const srBy = new Map(sr.map((s) => [s.year, s]));
		cards.push({
			periods: years.map(fyLabel),
			card: {
				key: 'payoutCoverage', title: '배당여력 (배당 vs FCF vs 순이익) · 연', unit: '조', series: [
					{ name: '배당총액', data: years.map((y) => { const v = srBy.get(y)?.totalDividend; return v != null ? +(v / 1e12).toFixed(3) : null; }), color: C.blue, type: 'bar' },
					{ name: 'FCF', data: years.map((y) => { const op = cfoBy.get(y); return op != null ? +(op - (capexBy.get(y) ?? 0)).toFixed(3) : null; }), color: C.warn, type: 'bar' },
					{ name: '순이익', data: years.map((y) => niBy.get(y) ?? null), color: C.net, type: 'bar' },
					{ name: '배당성향%', data: years.map((y) => srBy.get(y)?.payoutPct ?? null), color: C.purple, type: 'line', axis: 'r' }
				]
			}
		});
	}
	// 희석 이력 · capitalChange 이벤트 연 합산 (양수 = 신주, 음수 = 감자·소각) + 발행주식수 추이
	{
		const dilYears = (dil?.years ?? []).map((d) => String(d.year));
		const stYears = (own ?? []).filter((o) => o.stockTotal != null).map((o) => o.year);
		const years = [...new Set([...dilYears, ...stYears])].sort();
		if (years.length) {
			const dilBy = new Map((dil?.years ?? []).map((d) => [String(d.year), d]));
			cards.push({
				periods: years.map(fyLabel),
				card: {
					key: 'dilution', title: '주식수 변동 (희석 이력) · 연', unit: '만주', stacked: true, signed: true, series: [
						{ name: '유상증자', data: years.map((y) => { const v = dilBy.get(y)?.paidIn; return v != null ? +(v / 1e4).toFixed(1) : null; }), color: C.red, type: 'bar' },
						{ name: '전환·행사', data: years.map((y) => { const v = dilBy.get(y)?.conversion; return v != null ? +(v / 1e4).toFixed(1) : null; }), color: C.warn, type: 'bar' },
						{ name: '감자·소각(−)', data: years.map((y) => { const v = dilBy.get(y)?.reduction; return v != null ? +(v / 1e4).toFixed(1) : null; }), color: C.blue, type: 'bar' },
						{ name: '발행주식수', data: years.map((y) => { const v = ownBy.get(y)?.stockTotal; return v != null ? +(v / 1e4).toFixed(0) : null; }), color: C.cyan, type: 'line', axis: 'r' }
					]
				}
			});
		}
	}
	// 자사주 수량 흐름 · 취득(+)·처분/소각(−) signed stack + 기말 보유 우축. dilution(증자·감자)과 소스·축 별개.
	// disposalQty/buybackCancel 은 양수 카운트 공시값이라 표시 시 명시 부호 반전.
	{
		const tq = (sr ?? []).filter((s) => s.buybackQty != null || s.disposalQty != null || s.buybackCancel != null || s.treasuryEnd != null);
		if (tq.length) {
			cards.push({
				periods: tq.map((s) => fyLabel(s.year)),
				card: {
					key: 'treasuryFlow', title: '자사주 수량 흐름 · 연', unit: '만주', stacked: true, signed: true, series: [
						{ name: '취득', data: tq.map((s) => (s.buybackQty != null ? +(s.buybackQty / 1e4).toFixed(1) : null)), color: C.good, type: 'bar' },
						{ name: '처분(−)', data: tq.map((s) => (s.disposalQty != null ? +(-s.disposalQty / 1e4).toFixed(1) : null)), color: C.warn, type: 'bar' },
						{ name: '소각(−)', data: tq.map((s) => (s.buybackCancel != null ? +(-s.buybackCancel / 1e4).toFixed(1) : null)), color: C.red, type: 'bar' },
						{ name: '기말 보유', data: tq.map((s) => (s.treasuryEnd != null ? +(s.treasuryEnd / 1e4).toFixed(0) : null)), color: C.cyan, type: 'line', axis: 'r' }
					]
				}
			});
		}
	}
	if (own && own.length) {
		cards.push({
			periods: own.map((o) => fyLabel(o.year)),
			card: {
				key: 'ownership', title: '소유구조 · 연', unit: '%', series: [
					{ name: '최대주주측', data: own.map((o) => o.majorPct), color: C.red, type: 'line' },
					{ name: '소액주주', data: own.map((o) => o.minorPct), color: C.blue, type: 'line' },
					{ name: '소액주주수(만명)', data: own.map((o) => (o.minorCount != null ? +(o.minorCount / 1e4).toFixed(2) : null)), color: C.dim, type: 'line', axis: 'r' }
				]
			}
		});
	}
	return cards.filter(alive);
}

async function peopleReport(code: string, bundle: TerminalFinanceBundle, report: ReportPort): Promise<TabCard[]> {
	const [wf, eb] = await Promise.all([report.workforce(code), report.execBoard(code)]);
	const cards: TabCard[] = [];
	if (wf && wf.length) {
		const wfYears = wf.map((w) => w.year);
		const wfP = wfYears.map(fyLabel);
		cards.push({
			periods: wfP,
			card: {
				key: 'headcount', title: '인원 구성 · 연', unit: '명', stacked: true, series: [
					{ name: '정규직', data: wf.map((w) => w.regular), color: C.blue, type: 'bar' },
					{ name: '계약직', data: wf.map((w) => w.contract), color: C.warn, type: 'bar' },
					{ name: '계약직 비중%', data: wf.map((w) => (w.regular != null && w.contract != null && w.regular + w.contract > 0 ? +((w.contract / (w.regular + w.contract)) * 100).toFixed(1) : null)), color: C.red, type: 'line', axis: 'r' }
				]
			}
		});
		// 남녀 인원 구성 · 우측 레일 스냅샷(남/여)의 시계열판. employee.parquet 성별합계 기집계, 추가 fetch 0.
		cards.push({
			periods: wfP,
			card: {
				key: 'genderMix', title: '남녀 인원 구성 · 연', unit: '명', stacked: true, series: [
					{ name: '남', data: wf.map((w) => w.male), color: C.blue, type: 'bar' },
					{ name: '여', data: wf.map((w) => w.female), color: C.purple, type: 'bar' },
					{ name: '여성 비중%', data: wf.map((w) => (w.male != null && w.female != null && w.male + w.female > 0 ? +((w.female / (w.male + w.female)) * 100).toFixed(1) : null)), color: C.cyan, type: 'line', axis: 'r' }
				]
			}
		});
		cards.push({
			periods: wfP,
			card: {
				key: 'payTenure', title: '급여·근속 · 연', unit: '백만원', series: [
					{ name: '1인평균급여', data: wf.map((w) => (w.avgSalary != null ? +(w.avgSalary / 1e6).toFixed(0) : null)), color: C.good, type: 'bar' },
					{ name: '근속연수(년)', data: wf.map((w) => w.tenure), color: C.purple, type: 'line', axis: 'r' }
				]
			}
		});
		// 생산성·인건비 · finance annual 교차 (조 → 억: ×1e4)
		const revBy = annualMap(bundle, 'IS', 'revenue');
		const opBy = annualMap(bundle, 'IS', 'operatingIncome');
		const wfBy = new Map(wf.map((w) => [w.year, w]));
		const years = [...new Set([...wfYears, ...revBy.keys()])].sort();
		const perEmp = (y: string, v: number | undefined): Num => {
			const t = wfBy.get(y)?.total;
			return v != null && t != null && t > 0 ? +((v * 1e4) / t).toFixed(1) : null;
		};
		cards.push({
			periods: years.map(fyLabel),
			card: {
				key: 'laborProductivity', title: '1인당 생산성 · 연', unit: '억', series: [
					{ name: '1인당 매출', data: years.map((y) => perEmp(y, revBy.get(y))), color: C.rev, type: 'bar' },
					{ name: '1인당 영업이익', data: years.map((y) => perEmp(y, opBy.get(y))), color: C.op, type: 'line' }
				]
			}
		});
		cards.push({
			periods: years.map(fyLabel),
			card: {
				key: 'laborShare', title: '인건비 부담 (직원 급여) · 연', unit: '조', series: [
					{ name: '급여총액', data: years.map((y) => { const v = wfBy.get(y)?.totalSalary; return v != null ? +(v / 1e12).toFixed(3) : null; }), color: C.blue, type: 'bar' },
					{ name: '급여/매출%', data: years.map((y) => { const v = wfBy.get(y)?.totalSalary; const r = revBy.get(y); return v != null && r != null && r > 0 ? +((v / 1e12 / r) * 100).toFixed(1) : null; }), color: C.warn, type: 'line', axis: 'r' },
					{ name: '급여/영업이익%', data: years.map((y) => { const v = wfBy.get(y)?.totalSalary; const o = opBy.get(y); return v != null && o != null && o > 0 ? +((v / 1e12 / o) * 100).toFixed(1) : null; }), color: C.red, type: 'line', axis: 'r' }
				]
			}
		});
		if (eb && eb.length) {
			cards.push({
				periods: eb.map((e) => fyLabel(e.year)),
				card: {
					key: 'execPay', title: '이사·감사 보수 · 연', unit: '억', series: [
						{ name: '1인평균 보수', data: eb.map((e) => (e.execAvgPay != null ? +(e.execAvgPay / 1e8).toFixed(2) : null)), color: C.op, type: 'bar' },
						{ name: '임원/직원 배율(배)', data: eb.map((e) => { const w = wfBy.get(e.year)?.avgSalary; return e.execAvgPay != null && w != null && w > 0 ? +(e.execAvgPay / w).toFixed(1) : null; }), color: C.purple, type: 'line', axis: 'r' }
					]
				}
			});
		}
	}
	if (eb && eb.length) {
		// 보수총액·인원 · execPay(1인평균)와 축이 다른 별개 정보 (사업보고서 4분기 확정값, 추가 fetch 0)
		cards.push({
			periods: eb.map((e) => fyLabel(e.year)),
			card: {
				key: 'execTotal', title: '이사·감사 보수총액·인원 · 연', unit: '억', series: [
					{ name: '보수총액', data: eb.map((e) => (e.execTotalPay != null ? +(e.execTotalPay / 1e8).toFixed(1) : null)), color: C.warn, type: 'bar' },
					{ name: '인원(명)', data: eb.map((e) => e.execCount), color: C.cyan, type: 'line', axis: 'r' }
				]
			}
		});
		cards.push({
			periods: eb.map((e) => fyLabel(e.year)),
			card: {
				key: 'board', title: '이사회 구성 · 연', unit: '명', stacked: true, series: [
					{ name: '사외이사', data: eb.map((e) => e.outsideDirectors), color: C.good, type: 'bar' },
					{ name: '사내이사', data: eb.map((e) => (e.directors != null && e.outsideDirectors != null ? e.directors - e.outsideDirectors : null)), color: C.dim, type: 'bar' },
					{ name: '사외이사 비율%', data: eb.map((e) => (e.directors != null && e.directors > 0 && e.outsideDirectors != null ? +((e.outsideDirectors / e.directors) * 100).toFixed(0) : null)), color: C.cyan, type: 'line', axis: 'r' }
				]
			}
		});
	}
	return cards.filter(alive);
}

async function debtReport(code: string, bundle: TerminalFinanceBundle, report: ReportPort): Promise<TabCard[]> {
	const [dp, af] = await Promise.all([report.debtProfile(code), report.auditFees(code)]);
	const cards: TabCard[] = [];
	// ⚠ 채무증권 발행 실적(debtSecurities) 카드는 기각 · 외화채 분기 환산 변동이 dedup 을 뚫어
	// 중복 합산(삼성 2015 Harman "26.74조" 허구)·인수 전 이력 유입·CP 차환 롤오버 지배 3중 오염 실측.
	// 감사보수·독립성 · 비감사/감사 보수 비율 = 감사인 독립성 고전 지표 (높을수록 적신호)
	const auditFeeCard: TabCard | null = af && af.length >= 2 ? {
		periods: af.map((a) => fyLabel(String(a.year))),
		card: {
			key: 'auditFees', title: '감사보수·독립성 · 연', unit: '억', series: [
				{ name: '감사보수', data: af.map((a) => (a.auditFee != null ? +(a.auditFee / 1e8).toFixed(1) : null)), color: C.blue, type: 'bar' },
				{ name: '비감사보수', data: af.map((a) => (a.nonAuditFee != null ? +(a.nonAuditFee / 1e8).toFixed(1) : null)), color: C.warn, type: 'bar' },
				{ name: '비감사/감사%', data: af.map((a) => (a.auditFee != null && a.auditFee > 0 && a.nonAuditFee != null ? +((a.nonAuditFee / a.auditFee) * 100).toFixed(1) : null)), color: C.red, type: 'line', axis: 'r' }
			]
		}
	} : null;
	const tail = [auditFeeCard].filter((c): c is TabCard => c != null);
	if (!dp || !dp.years.length) return [...tail].filter(alive); // 무사채 회사도 감사보수는 노출
	const dpr = dp.years;
	// 전방 만기 사다리 · 최신 연도 잔존만기 7버킷 (x축 = 만기 버킷). 점선 = 최신 연간 현금성자산.
	if (dp.ladder) {
		const cashBy = annualMap(bundle, 'BS', 'cash');
		const cashYears = [...cashBy.keys()].sort();
		const cashLatest = cashYears.length ? (cashBy.get(cashYears[cashYears.length - 1]) ?? null) : null;
		const L = dp.ladder;
		cards.push({
			periods: ['1년이하', '1~2년', '2~3년', '3~4년', '4~5년', '5~10년', '10년+'],
			card: {
				key: 'maturityLadder', title: `전방 만기 사다리 · ${fyLabel(L.year)}`, unit: '조', stacked: true,
				refLines: cashLatest != null ? [cashLatest] : undefined,
				series: [
					{ name: '회사채', data: L.buckets.map((v) => (v != null ? +(v / 1e12).toFixed(3) : null)), color: C.op, type: 'bar' },
					{ name: '전단채+CP(≤1y)', data: L.buckets.map((_, i) => (i === 0 && L.shortTerm != null ? +(L.shortTerm / 1e12).toFixed(3) : null)), color: C.cyan, type: 'bar' }
				]
			}
		});
	}
	const series: FinCard['series'] = [
		{ name: '1년이하', data: dpr.map((d) => (d.bond1y != null ? +(d.bond1y / 1e12).toFixed(3) : null)), color: C.red, type: 'bar' },
		{ name: '1~5년', data: dpr.map((d) => (d.bond1to5 != null ? +(d.bond1to5 / 1e12).toFixed(3) : null)), color: C.op, type: 'bar' },
		{ name: '5~10년', data: dpr.map((d) => (d.bond5to10 != null ? +(d.bond5to10 / 1e12).toFixed(3) : null)), color: C.blue, type: 'bar' },
		{ name: '10년초과', data: dpr.map((d) => (d.bond10plus != null ? +(d.bond10plus / 1e12).toFixed(3) : null)), color: C.purple, type: 'bar' }
	];
	// 초단기물(전단채+CP) · 보유율 ~5% 라 단독 카드 금지, 유효 연도가 있을 때만 조건부 시리즈
	if (dpr.some((d) => d.stb != null || d.cp != null)) {
		series.push({ name: '초단기물(전단채+CP)', data: dpr.map((d) => (d.stb != null || d.cp != null ? +(((d.stb ?? 0) + (d.cp ?? 0)) / 1e12).toFixed(3) : null)), color: C.cyan, type: 'line' });
	}
	cards.push({
		periods: dpr.map((d) => fyLabel(d.year)),
		card: { key: 'bondMaturity', title: '사채 잔액 추이 · 연', unit: '조', stacked: true, series }
	});
	return [...cards, ...tail].filter(alive); // 사다리 → 잔액 → 감사보수 순
}

export const FS_TABS: FsTab[] = [
	{
		key: 'profitability', label: { kr: '수익성', en: 'PROFIT' }, q: '얼마나 잘 버나', finKey: 'profitability',
		note: '포괄손익 격차 = CIS(포괄손익계산서) 직독. OCI = 환산차이·금융자산평가·확정급여 재측정 등 · 손익계산서 밖에서 자본으로 직행하는 손익.'
	},
	{ key: 'cashflow', label: { kr: '현금·투자', en: 'CASH' }, q: '이익이 현금인가, 어디에 쓰나', finKey: 'cashflow', load: cashflowReport },
	{
		key: 'debt', label: { kr: '재무체력', en: 'DEBT' }, q: '버틸 수 있나', finKey: 'debt', load: debtReport,
		note: '만기 사다리 = 액면 기준 미상환 잔액(report) · 장부가와 소폭 차이. 점선 = 최신 연간 현금성자산. 무사채 회사는 카드 비표시. 감사보수 = 감사용역 계약보수(연간 계약값), 비감사 = 같은 연도 용역 보수 합 · 비감사/감사 비율이 높을수록 감사인 독립성 적신호. 감사 이력 = 사업보고서 기준 (사업연도 = 접수연도−1).'
	},
	{
		key: 'shareholder', label: { kr: '주주환원·소유', en: 'RETURN' }, q: '주주에게 무엇을 주나', finKey: 'shareholder', load: shareholderReport,
		note: '자본변동 브리지 = 최신 연간 자본변동표(SCE) 합계 차원 · 기타 = 기말 대조 잔차(소유주거래·연결범위변동·주식보상 등). 배당·자사주 = 보통주 기준 공시값 · report. 배당여력의 FCF·순이익 = 연간 재무제표 교차. 자사주 가치 = 연평균종가 × 취득수량 추정. 희석 이력 = 증자·전환·감자 공시 이벤트 연 합산 (무상증자·분할 제외).'
	},
	{
		key: 'people', label: { kr: '인력·보수', en: 'PEOPLE' }, q: '사람과 보상', load: peopleReport,
		note: '급여 = 직원 급여만(임원·복리후생 제외), 사업보고서 연간 확정값. 보수 = 이사·감사 전체(등기 구분 미공시).'
	},
	// 가격↔기초체력 + PER·PBR 추이 · finKey/load 없는 메타 전용 탭. 카드는 FinFullscreen 이 candles·EPS·
	// 발행주식수와 buildPriceFundamentalCard / buildPerPbrCard 로 직접 빌드(특수 분기, lazy report).
	{
		key: 'price', label: { kr: '가격', en: 'PRICE' }, q: '주가가 기초체력과 함께, 그리고 합당한 값에 거래됐나',
		note: '시장가격을 펀더멘털에 비추는 탭. 위 = 주가·매출·자본을 =100 으로 리베이스(로그축)해 함께 갔는지, 아래 = PER·PBR 추이로 자기 이력 대비 밸류에이션 수준. 주가는 각 기간 공시 접수일 종가(미리보기 아님), PER·PBR 은 연 축. 어느 것도 적정주가 판정은 아니다 · 각 카드의 ! 로 해석 기준 참조.'
	}
];
