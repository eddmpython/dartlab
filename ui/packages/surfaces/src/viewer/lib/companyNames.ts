// 회사 유니버스(code → 회사명) · panel 엔 회사명 컬럼이 없어 ecosystem(scan 과 동일 소스)에서 해석.
// module-level promise 캐시 · 검색·뷰어가 공유(중복 fetch 0).
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

export interface Co {
	code: string;
	name: string;
}

let cache: Promise<Co[]> | null = null;

export function loadCompanies(): Promise<Co[]> {
	if (!cache) {
		cache = loadJson<{ nodes?: Array<{ id?: string; stockCode?: string; label?: string }> }>('map/ecosystem.json', {
			fetchFn: fetch
		})
			.then((eco) =>
				(eco?.nodes ?? [])
					.map((n) => ({ code: String(n.id ?? n.stockCode ?? ''), name: String(n.label ?? '') }))
					.filter((c) => c.code)
			)
			.catch(() => [] as Co[]);
	}
	return cache;
}

// ── AI 크로스-회사 이동 · 질문 텍스트에서 "다른 회사" 결정론 감지 ──

export interface CompanyHit {
	code: string;
	name: string;
}

// 별칭/단축어 · 정식명에 안 나오는 식별성 높은 토막만. bounded 수동 큐레이션.
// searchIndex SYNONYMS·answerCompose 와 동일 규율 · PMI/자동발굴 금지(project_unified_search_table §8).
// "삼성"·"현대"·"LG" 같은 그룹명·흔출어는 등록 금지(오탐원). 끝없이 늘면 덕지덕지 신호.
const NAME_ALIAS: Record<string, string> = {
	하이닉스: '000660',
	sk하이닉스: '000660',
	삼전: '005930'
	// 운영자 수동 추가
};

/**
 * 질문 텍스트에서 "현재 회사가 아닌 다른 회사"를 결정론 사전매칭으로 감지.
 * 데이터셋 보유 회사만 후보(환각 출구 차단). LLM NER 아님.
 * @returns [] = 감지 없음(현재 회사로 답) · [1개] = 단일 이동 후보 · [≥2개] = 모호(후보 칩)
 */
export async function resolveCompanies(q: string, currentCode: string): Promise<CompanyHit[]> {
	const cos = await loadCompanies();
	// 어절(공백·구두점 분리) 단위 매칭 · 옛 공백제거 concatenation + includes 는 "하이닉스"에서 "이닉스" 같은
	// 접미/접요 부분일치 오감지를 냈다. 어절이 이름과 일치하거나 이름으로 시작(조사 흡수)할 때만 매칭.
	const words = q.toLowerCase().match(/[가-힣a-z0-9]+/g) ?? [];
	if (!words.length) return [];
	const wordHit = (s: string) => words.some((w) => w === s || w.startsWith(s));
	const out = new Map<string, CompanyHit>(); // code → hit (중복 제거)
	const lenByCode = new Map<string, number>(); // longest 정렬 가중(별칭은 999)

	// 1) 별칭 · 식별성 높은 토막 우선.
	for (const [alias, acode] of Object.entries(NAME_ALIAS)) {
		if (acode === currentCode) continue; // 현재 회사 무시
		if (wordHit(alias.toLowerCase())) {
			const c = cos.find((x) => x.code === acode);
			if (c) {
				out.set(c.code, { code: c.code, name: c.name });
				lenByCode.set(c.code, 999);
			}
		}
	}

	// 2) 정식 회사명 · 데이터셋에 있는 이름만(환각 차단). 2자 이하 제외(흔출어 충돌).
	for (const c of cos) {
		if (c.code === currentCode) continue; // 현재 회사 무시
		const nm = c.name.replace(/\s/g, '').toLowerCase();
		if (nm.length < 3) continue; // "LG"·"GS" 등 2자 차단
		if (wordHit(nm)) {
			out.set(c.code, { code: c.code, name: c.name });
			if (!lenByCode.has(c.code)) lenByCode.set(c.code, nm.length);
		}
	}

	const arr = [...out.values()];
	arr.sort((a, b) => (lenByCode.get(b.code) ?? 0) - (lenByCode.get(a.code) ?? 0));
	return arr.slice(0, 3); // 모호 시 상위 3 (UX 후보 칩 상한)
}
