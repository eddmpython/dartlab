// 로컬 company 포트 · 전부 공개 HF 자산 공통배선(corpList·relations·profit-pool). 로컬 :8400 불요
// (macro·finance·price 와 동일 "로컬이 깃헙페이지 자산을 공유"). relations 도 공개 HF(map ego) 직독 ·
// 옛 /api meta 체크 후 빈 관계 반환 스텁 폐기(실관계 노출). reportFacts(라이브 duckdb)는 셸 주입 영역이라 로컬 [].
import type { CompanyPort, ProductIndexItem } from '@dartlab/ui-contracts';
import { loadHfProductIndexMap } from '../../public/sources/productIndexSource';
import { loadIndustryProfitPool } from '../../public/sources/industryPoolSource';
import { loadCompanyRelations } from '../../public/sources/relationsSource';

// 전 종목 product/회사정보 인덱스 = 공개 HF 소스를 Record(JSON-safe 계약)로 1 회 변환·공유 (공개 어댑터와 동일).
let productIndexPromise: Promise<Record<string, ProductIndexItem> | null> | null = null;
function loadProductIndexRecord(): Promise<Record<string, ProductIndexItem> | null> {
	productIndexPromise ??= (async () => {
		try {
			return Object.fromEntries(await loadHfProductIndexMap());
		} catch {
			return null;
		}
	})();
	return productIndexPromise;
}

export function localCompanyPort(): CompanyPort {
	return {
		// 단일 회사 제품/프로필 = 공개 HF 인덱스 조회 (ceo/결산/상장/본사/홈페이지 포함).
		async products(code) {
			const rec = await loadProductIndexRecord();
			return rec?.[code.trim()] ?? null;
		},
		productIndex: loadProductIndexRecord,
		// 공급망 관계 = 공개 HF(map ego) 직독 · 공개 어댑터와 동일.
		relations: loadCompanyRelations,
		// 라이브 보고서 팩트 · 셸 주입(duckdb-wasm) 영역. 로컬 미배선 = [].
		async reportFacts() {
			return [];
		},
		// 산업 profit-pool = 공개 정적 자산(map/industries/{id}.json) 공유.
		industryProfitPool: loadIndustryProfitPool
	};
}
