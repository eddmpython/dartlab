// 로컬 어댑터 공용 · 미배선 트립와이어.
// (옛 getJson 은 로컬 provider 게이트 adapters/local/api/localApi.ts 로 이관 · /api 호출 단일 집결, 02 §5.)

export function notWiredYet(what: string, stage: string): never {
	throw new Error(`[local adapter] ${what} 는 ${stage}에서 구현된다 · 이 호출이 보이면 배선 순서 위반이다.`);
}
