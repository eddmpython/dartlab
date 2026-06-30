// 회사 선택 시 1 회 · 무거운 소스(주가·재무·제품맵)를 포트 경유로 병렬 워밍업 (fire-and-forget).
// 어댑터 로더들의 in-flight dedup 덕에 패널의 같은 호출과 다운로드를 공유한다(중복 fetch 0).
// 포트 호출만 쓰므로 public(landing)·local(ui/web 브리지) 어느 runtime 에서도 동작.
import type { DartLabRuntime } from '@dartlab/ui-contracts';

export function warmCompany(runtime: DartLabRuntime, code: string): void {
	void runtime.price.govCandles(code); // 회사별 gov 캐시 · dev: 라이브 fetch+HF 저장, prod: 캐시 읽기
	void runtime.price.govRecent(); // 최근 거래일 tail · 전 종목 공유 1파일, 세션 1회
	void runtime.finance.bundle(code);
	void runtime.company.productIndex();
}
