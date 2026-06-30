// 재무 유형 라벨 SSOT · 좌측 레일·상세검색(ScreenerModal)·유형 범례(FinTypeLegendDialog) 3소비처 공유.
// 기준·코드·문서가 이 파일 하나에서 나와 드리프트가 구조적으로 불가능하다 (분기 임계 재보정도 여기 한 곳).
//
// 결정론 규칙 · 고정 임계값 기계 판정. 추정·예측·점수화 아님. 결측(null·빈 문자열) = 그 라벨 미부여(fail-safe).
// 복수 충족 시 배열 순서가 우선순위 체인: 주의형 > 회복형 > 성장형 > 수익형 > 우량형 (첫 매치 1개만 표시 ·
// 하방 신호 은폐 비용이 비대칭적으로 커서 주의형 최우선, 상태변화(회복) > 정적 라벨).
//
// ⛔ 기준식 사용 금지 필드 (씨데이터 전수 실측): EcoNode.debtRatio·auditRisk·px.beta·px.foreignPct = 전수 null,
//    revenueYoyPct = 빈티지 오염(YTD/연간 혼합). 부채비율은 반드시 finance.json ratios 에서 읽는다.
// ⚠ JS 코어션 함정: null >= -5 는 true · 모든 수치 비교는 `v != null && v >= 임계` 형태 강제.
import type { EcoNode, FinanceCompany, PriceRow } from './types';

export interface FinTypeDef {
	name: string;
	tone: 'down' | 'up' | 'good' | 'neutral' | 'warn';
	criteriaKr: string; // 데이터 출처 모달에 그대로 노출되는 한 줄 기준 · 임계값 포함
	criteriaEn: string;
}

// 배열 순서 = 우선순위 체인 (하방 신호 최우선 · 은폐 비용 비대칭).
// 주가 라벨 2종(고변동·신고가)은 px 미전달 호출처에서 자연 미부여 · fail-safe 일관.
export const FIN_TYPES: FinTypeDef[] = [
	{
		name: '주의형',
		tone: 'down',
		criteriaKr: '수익성 적자 · 유동성 등급 주의/위험 · 현금흐름 현금위기형 · 3개 신호 중 2개 이상 동시 충족 (결측 신호는 미충족으로 계산)',
		criteriaEn: 'At least 2 of 3 signals: loss-making · liquidity grade caution/risk · cash-crisis CF pattern'
	},
	{
		name: '회복형',
		tone: 'up',
		criteriaKr: 'ROE ≥ 2% 이고 ROE 증감 ≥ +5%p 이며 전기 ROE(= 당기 ROE − 증감) < 0 · 적자에서 흑자로 전환',
		criteriaEn: 'ROE ≥ 2%, ROE delta ≥ +5%p, prior ROE (= ROE − delta) < 0 · loss-to-profit turnaround'
	},
	{
		name: '역성장',
		tone: 'down',
		criteriaKr: '매출 3년 CAGR ≤ −15% · 외형이 추세적으로 줄어드는 회사 (회복형이 위 순위라 갓 턴어라운드한 회사는 여기 안 걸림)',
		criteriaEn: '3Y revenue CAGR ≤ −15% · secular revenue decline (turnarounds caught by 회복형 first)'
	},
	{
		name: '고변동',
		tone: 'warn',
		criteriaKr: '주가 1년 변동성 ≥ 85% (연환산, 유니버스 상위 ~10%) · 좋고 나쁨이 아니라 진폭 경고',
		criteriaEn: '1Y annualized price volatility ≥ 85% (top ~10% of universe) · amplitude flag, not a verdict'
	},
	{
		name: '대장주',
		tone: 'good',
		criteriaKr: '동종업종 매출 1위 이고 업종 종목 수 ≥ 5 (소형 업종의 무의미한 1위 제외)',
		criteriaEn: 'Industry revenue rank #1 with ≥ 5 peers in the industry'
	},
	{
		name: '성장형',
		tone: 'good',
		criteriaKr: '매출 3년 CAGR ≥ 20% 이고 수익성 등급이 적자가 아님',
		criteriaEn: '3Y revenue CAGR ≥ 20% and profitability grade not loss-making'
	},
	{
		name: '개선형',
		tone: 'up',
		criteriaKr: '영업이익률 증감 ≥ +3%p 이고 영업이익률 > 0 이고 ROE > 0 · 이미 흑자인데 마진이 확장 중 (부호 전환은 회복형 소관)',
		criteriaEn: 'OP margin delta ≥ +3%p with positive OP margin and ROE · margin expansion while already profitable'
	},
	{
		name: '수익형',
		tone: 'good',
		criteriaKr: '영업이익률 ≥ 12% 이고 ROE ≥ 0%',
		criteriaEn: 'Operating margin ≥ 12% and ROE ≥ 0%'
	},
	{
		name: '현금부자',
		tone: 'good',
		criteriaKr: '순현금(현금성자산 − 차입금·사채) ≥ 총자산의 20% (최신 연간 재무제표)',
		criteriaEn: 'Net cash (cash − borrowings/bonds) ≥ 20% of total assets (latest annual statements)'
	},
	{
		name: '신고가',
		tone: 'up',
		criteriaKr: '현재가가 52주 최고가의 95% 이상 이고 1년 수익률 > 0 · 고점 부근 주행 중',
		criteriaEn: 'Price ≥ 95% of 52-week high with positive 1Y return'
	},
	{
		name: '우량형',
		tone: 'neutral',
		criteriaKr: '부채비율 ≤ 50% (최신 연간 재무제표) 이고 유동성 등급 우수·양호 이고 수익성 등급 보통 이상',
		criteriaEn: 'Debt ratio ≤ 50% (latest annual statements), liquidity grade good+, profitability grade fair+'
	}
];
const T = Object.fromEntries(FIN_TYPES.map((t) => [t.name, t])) as Record<string, FinTypeDef>;

function lastNonNull(arr?: (number | null)[]): number | null {
	if (!arr) return null;
	for (let i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return arr[i];
	return null;
}

export interface FinTypeResult {
	primary: FinTypeDef | null; // 우선순위 체인 첫 매치 · 모든 화면이 이것만 표시 (화면 간 불일치 금지)
	all: FinTypeDef[]; // 전체 만족 집합 · hover title 등 보조 노출용
}

export function finTypeOf(n: EcoNode, fin?: FinanceCompany, px?: PriceRow): FinTypeResult {
	const hits: FinTypeDef[] = [];
	// 주의형 · 2-of-3 합의 (단독 신호 오탐 차단: 현금위기형 단독은 양호 기업도 걸린다)
	const signals = [n.profGrade === '적자', n.liqGrade === '주의' || n.liqGrade === '위험', n.cfPattern === '현금위기형'];
	if (signals.filter(Boolean).length >= 2) hits.push(T['주의형']);
	// 회복형 · 전기 ROE 를 roe−roeDelta 로 결정론 복원해 부호 전환(적자→흑자)을 요구
	if (n.roe != null && n.roeDelta != null && n.roe >= 2 && n.roeDelta >= 5 && n.roe - n.roeDelta < 0) hits.push(T['회복형']);
	// 역성장 · revCagr 는 3년 CAGR 라 빈티지 안전 (revenueYoyPct 는 YTD/연간 혼합 오염으로 금지)
	if (n.revCagr != null && n.revCagr <= -15) hits.push(T['역성장']);
	// 고변동 · 85 ≈ 유니버스 p90 (p50=53 실측). 판정이 아니라 진폭 경고라 warn tone.
	if (px?.volatility1y != null && px.volatility1y >= 85) hits.push(T['고변동']);
	// 대장주 · 업종 5개사 미만의 1위는 무의미해 제외
	if (n.industryRank === 1 && n.industryPeerCount != null && n.industryPeerCount >= 5) hits.push(T['대장주']);
	// 성장형 · 적자 가드 (부실 외형성장 차단)
	if (n.revCagr != null && n.revCagr >= 20 && !!n.profGrade && n.profGrade !== '적자') hits.push(T['성장형']);
	// 개선형 · 이미 흑자에서 마진 확장 (부호 전환=회복형이 위 순위라 의미 중복 없음)
	if (n.opMarginDelta != null && n.opMargin != null && n.roe != null && n.opMarginDelta >= 3 && n.opMargin > 0 && n.roe > 0) hits.push(T['개선형']);
	// 수익형 · opMargin 12 = 유니버스 상위 ~15-18% 컷
	if (n.opMargin != null && n.roe != null && n.opMargin >= 12 && n.roe >= 0) hits.push(T['수익형']);
	// 현금부자 · finance.json bs 최신 비결측. 차입 계정 결측은 0(무차입) 취급 · cash 가 있어야만 판정
	const cash = lastNonNull(fin?.bs?.assets?.cash);
	const ta = lastNonNull(fin?.bs?.totals?.totalAsset);
	if (cash != null && ta != null && ta > 0) {
		const debtSum = (lastNonNull(fin?.bs?.liab?.shortDebt) ?? 0) + (lastNonNull(fin?.bs?.liab?.longDebt) ?? 0) + (lastNonNull(fin?.bs?.liab?.bonds) ?? 0);
		if ((cash - debtSum) / ta >= 0.2) hits.push(T['현금부자']);
	}
	// 신고가 · 1년 수익률 양수 가드 (저점 반등 중 고점 닿는 노이즈 차단)
	if (px?.week52High != null && px.currentPrice != null && px.currentPrice >= px.week52High * 0.95 && (px.return1y ?? 0) > 0) hits.push(T['신고가']);
	// 우량형 · 부채비율은 finance.json ratios 최신 비결측 (EcoNode.debtRatio 는 전수 null)
	const d = lastNonNull(fin?.ratios?.debtRatio);
	if (
		d != null && d <= 50 &&
		(n.liqGrade === '우수' || n.liqGrade === '양호') &&
		(n.profGrade === '우수' || n.profGrade === '양호' || n.profGrade === '보통')
	) hits.push(T['우량형']);
	return { primary: hits[0] ?? null, all: hits };
}

// 좌측 레일 2칩 표시 · 음(down/warn)축 첫 매치 + 양(up/good/neutral)축 첫 매치.
// primary 정의는 불변(전 화면 일관) · 본 함수는 primary 의 상위집합 공개라 모순 없음.
export function displayPair(res: FinTypeResult): FinTypeDef[] {
	const neg = res.all.find((t) => t.tone === 'down' || t.tone === 'warn') ?? null;
	const pos = res.all.find((t) => t.tone === 'up' || t.tone === 'good' || t.tone === 'neutral') ?? null;
	return [neg, pos].filter((t): t is FinTypeDef => t != null);
}
