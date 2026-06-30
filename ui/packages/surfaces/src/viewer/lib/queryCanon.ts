// 질문→intent 라우팅 + 결정론 섹션 scoping (브라우저). 모델 무게 0·매퍼 0·dense 0.
//
// 들어온 질문 → intentModel(오프라인 curated 384질문에서 뽑은 압축 모델 ~27KB) 로 intent 라우팅(IDF 가중 bigram,
// generic 어휘 깎음) → 그 intent 의 *실제 섹션 target* 으로 검색 범위를 좁힌다(searchIndex.search {scopeSections}).
// searchIndex 가 plain BM25 ⊕ 섹션scoping 을 RRF 융합 · 라우팅 틀려도 plain 보존(안 깨짐), 맞으면 정답 섹션 끌어올림.
//
// 검증(tests/_attempts/viewerDenseEvidence/buildVerify.py): 5개 업종 end-to-end top-6 섹션도달 plain 56~71% →
// 섹션scoping 83~90%. 라우팅 LOO 71%(IDF). dense(30MB)·fuzzy canon(옛) 둘 다 능가하며 무게 0.
//
// dev 단계: 모델을 번들 import(네트워크 0, HF 연결 전 self-contained 테스트). 이관 시 HF fetch + 사용자질문 누적 재도출.

import intentModelJson from './intentModel.json';
import { hfUrl } from '@dartlab/ui-runtime/data/parquet/hfRange';
import { tokenizeBigram } from './searchIndex';

export interface IntentEntry {
	sections: string[]; // 결정론 섹션 target (intentSpec · 실제 DART chapter>sectionLeaf taxonomy)
	canon: string[]; // scope 검색 보강어(코퍼스 어휘) · 구어질의↔본문 간극 흡수("돌아가"→"가동률")
	route: Record<string, number>; // 라우팅 bigram → IDF 가중치(count·idf/dl 사전계산, top-K bounded)
	n: number; // 이 intent 큐레이션 질문 수(진단)
}
export interface IntentModel {
	v: number;
	intents: Record<string, IntentEntry>;
}

const BUNDLED: IntentModel = intentModelJson as IntentModel; // 빌드 동결본 · HF 실패 시 fallback(항상 동작)
const MODEL_PATH = 'dart/queries/intentModel.json'; // 파이프라인(.github/scripts/queries)이 HF 로 자동 업로드하는 경로

let modelP: Promise<IntentModel | null> | null = null;

// 1회 로드 · HF 의 *라이브* 모델 우선(파이프라인 재학습이 프론트 재배포 0 으로 반영), 실패 시 번들 fallback.
// 모듈 캐시(modelP)로 회사 이동 재마운트에도 1회. 시그니처 불변(호출부 무수정).
export function loadIntentModel(fetchFn: typeof fetch = fetch): Promise<IntentModel | null> {
	if (modelP) return modelP;
	modelP = (async () => {
		try {
			const resp = await fetchFn(hfUrl(MODEL_PATH));
			if (resp.ok) {
				const j = (await resp.json()) as IntentModel;
				if (j?.v === 2 && j.intents) return j; // schema 가드 · drift 시 번들로
			}
		} catch {
			/* 네트워크/CORS 실패 → 번들 fallback */
		}
		return BUNDLED;
	})();
	return modelP;
}

// 질문 → intent 점수(route 가중합). score(intent)=Σ qcount(bigram)·route[intent][bigram]. 0 이면 미라우팅.
function scoreIntents(model: IntentModel, query: string): Array<[string, number]> {
	const qc = new Map<string, number>();
	for (const b of tokenizeBigram(query)) qc.set(b, (qc.get(b) ?? 0) + 1);
	const scored: Array<[string, number]> = [];
	for (const [intent, e] of Object.entries(model.intents)) {
		let s = 0;
		for (const [b, c] of qc) s += c * (e.route[b] ?? 0);
		if (s > 0) scored.push([intent, s]);
	}
	scored.sort((a, b) => b[1] - a[1]);
	return scored;
}

// 상위 intent (라우팅 진단·디버그용).
export function predictIntents(model: IntentModel, query: string, topK = 2): string[] {
	return scoreIntents(model, query)
		.slice(0, topK)
		.map(([it]) => it);
}

// 질문 → 검색 scope = 상위 intent 의 target 섹션 + canon 보강어. searchIndex.search(q, {scopeSections, scopeTerms}) 에 넘긴다.
// RRF 융합이라 라우팅 틀려도 plain BM25 보존 → always-safe. topK=1 이 측정상 최적(top-2 는 noise).
// canon 이 구어질의↔본문 어휘 간극 흡수 → held-out top-6 섹션도달 80%→96~98%(selfProbe arm E).
export function queryScope(model: IntentModel | null, query: string, topK = 1): { sections: string[]; terms: string[] } {
	if (!model) return { sections: [], terms: [] };
	const sections = new Set<string>();
	const terms = new Set<string>();
	for (const it of predictIntents(model, query, topK)) {
		const e = model.intents[it];
		if (!e) continue;
		for (const s of e.sections) sections.add(s);
		for (const t of e.canon) terms.add(t);
	}
	return { sections: [...sections], terms: [...terms] };
}
