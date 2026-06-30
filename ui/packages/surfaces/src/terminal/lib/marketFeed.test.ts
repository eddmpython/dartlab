// 시장 공시 피드 분류기 골든 · 실측 상위 제목(최근3개월) 기준.
// ① marketFeedCategory 6키 매핑 ② classifyFiling 회귀 0(이벤트레일 SSOT 불변) ③ isInstitutionalFiler.
import { describe, it, expect } from 'vitest';
import { marketFeedCategory, isInstitutionalFiler, MARKET_FEED_CATS } from './marketFeed';
import { classifyFiling } from './eventRail';

describe('marketFeedCategory · 주가영향 6탭', () => {
	const cases: [string, string][] = [
		['자기주식취득결정', 'treasury'],
		['자기주식처분결정', 'treasury'],
		['주요사항보고서(자기주식취득결정)', 'treasury'], // 래핑돼도 자기주식 우선
		['유상증자결정', 'capital'],
		['주요사항보고서(전환사채권발행결정)', 'capital'],
		['신주인수권부사채권발행결정', 'capital'],
		['최대주주변경', 'control'],
		['최대주주등소유주식변동신고서', 'control'], // 최대주주 → control(ownership 보다 우선)
		['회사합병결정', 'control'],
		['주식등의대량보유상황보고서(일반)', 'ownership'],
		['임원ㆍ주요주주특정증권등소유상황보고서', 'ownership'],
		['연결재무제표기준영업(잠정)실적(공정공시)', 'earnings'],
		['단일판매ㆍ공급계약체결', 'earnings'],
		['기업설명회(IR)개최(안내공시)', 'etc'], // 약신호 행정 → 전체탭에만
		['사외이사의선임ㆍ해임또는중도퇴임에관한신고', 'etc']
	];
	for (const [nm, key] of cases) {
		it(`${nm} → ${key}`, () => expect(marketFeedCategory(nm)).toBe(key));
	}
	it('탭 = 전체 + 5 카테고리(etc 별탭 없음)', () => {
		expect(MARKET_FEED_CATS.map((c) => c.key)).toEqual(['all', 'ownership', 'treasury', 'capital', 'control', 'earnings']);
	});
});

describe('classifyFiling 회귀 0 · 이벤트레일 SSOT 불변(RX_OWNERSHIP 추출 후에도 동일)', () => {
	it('대량보유 → equity', () => expect(classifyFiling('주식등의대량보유상황보고서')).toBe('equity'));
	it('임원주요주주 → equity', () => expect(classifyFiling('임원ㆍ주요주주특정증권등소유상황보고서')).toBe('equity'));
	it('자기주식 → major (기존대로 묶임)', () => expect(classifyFiling('자기주식취득결정')).toBe('major'));
	it('단일판매 → exchange', () => expect(classifyFiling('단일판매ㆍ공급계약체결')).toBe('exchange'));
	it('감사보고서 → audit', () => expect(classifyFiling('감사보고서제출')).toBe('audit'));
});

describe('isInstitutionalFiler · flr_nm 보조칩(실측 샘플)', () => {
	for (const f of ['국민연금공단', '미래에셋자산운용', 'BlackRockFundAdvisors', 'NorgesBank', '한국증권금융', '케이비증권'])
		it(`${f} → 기관`, () => expect(isInstitutionalFiler(f)).toBe(true));
	for (const f of ['오세영', '박정원', '정해린', '진양곤'])
		it(`${f} → 개인(비기관)`, () => expect(isInstitutionalFiler(f)).toBe(false));
});
