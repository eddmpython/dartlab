// 캡션 패널 회사 배지 · 제품(무엇을 만드나) + 지주회사 라벨. 공유 이미지(슬라이드)엔 안 얹고
// 웹 리더(PostModal/FeedCard) 캡션 헤더 아래에만(시각 회귀·SNS 내보내기 오염 0). 시장구분(코스피/코스닥)은
// search-index 미포함이라 후속(Tier B) · 본 헬퍼는 런타임 직독 가능분(rt.company.products)만.
import type { DartLabRuntime } from '@dartlab/ui-contracts';

export interface CompanyBadges {
	/** 주요 제품/서비스 · rt.company.products(code).product. 미존재 undefined. */
	product?: string;
	/** 지주회사 여부 · 회사명 키워드 휴리스틱(SK·LG 등 키워드 없는 지주는 미검출, v1 한계). */
	isHolding: boolean;
}

/** 회사명으로 지주회사 판별(키워드 휴리스틱). 정식 플래그(credit 엔진 BS 투자비율)는 후속. */
export function isHoldingName(corpName: string): boolean {
	return /지주|홀딩스|holdings/i.test(corpName ?? '');
}

/** 캡션 배지 · 제품(rt.company.products 직독) + 지주 라벨. 미존재/throw 는 부분/빈으로 정직 폴백. */
export async function loadCompanyBadges(rt: DartLabRuntime, code: string, corpName: string): Promise<CompanyBadges> {
	const isHolding = isHoldingName(corpName);
	if (!code) return { isHolding };
	try {
		const p = await rt.company.products(code);
		return { product: p?.product || undefined, isHolding };
	} catch {
		return { isHolding };
	}
}
