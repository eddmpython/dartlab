// 공유 터미널 localStorage 헬퍼 · dlTerm.* 네임스페이스 단일 진입점. drawStore·templateStore·lastSymbol 이
// 각자 구현하던 raw 패턴(browser 가드·try/catch quota 무해·JSON)을 한 곳으로 수렴(공유). 새 저장 수요는
// 본 헬퍼를 쓴다. runtime.storage 는 public 어댑터에서 throw(notWiredYet · 단계-4a-3)라 정적 퍼블릭 플로어에서
// 크래시 → 의존하지 않는다. StoragePort 로의 일괄 이관은 ui-platform-refactor 단계-4a-3 소관(기존 4 키 + 본
// 헬퍼 동시 이관 예정). 영속 보장 아님(기기로컬·시크릿/캐시삭제·Safari ITP 소실 가능) · 소비처가 정직 라벨로 노출.
const browser = typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';

export type TermStoreKey = `dlTerm.${string}`;

/** 키 로드 · 부재·손상·파싱실패는 fallback (무해). */
export function readStore<T>(key: TermStoreKey, fallback: T): T {
	if (!browser) return fallback;
	try {
		const raw = window.localStorage.getItem(key);
		if (raw == null) return fallback;
		return JSON.parse(raw) as T;
	} catch {
		return fallback;
	}
}

/** 키 저장 · null/undefined 는 키 제거(쓰레기 키 방지), quota 초과는 무해 무시. */
export function writeStore<T>(key: TermStoreKey, value: T | null | undefined): void {
	if (!browser) return;
	try {
		if (value == null) window.localStorage.removeItem(key);
		else window.localStorage.setItem(key, JSON.stringify(value));
	} catch {
		/* quota · 무해 */
	}
}
