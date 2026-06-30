// 공시 Q&A 세션 상태 · AskDrawer 외부의 모듈 싱글턴. 회사 이동(viewer +page 가 bundle 재로드 시 잠깐
// bundle=null → studio 언마운트)로 AskDrawer 가 언마운트돼도 대화·모델·Ollama 상태가 생존해야 "AI 화면
// 그대로(크로스-회사 대화 유지)" 요구가 성립한다. 컴포넌트 내부 $state 는 언마운트 시 소실되므로 여기로 올린다.
// 초기화 시점 = 전체 새로고침(F5)뿐. (탭당 뷰어 1개 · 싱글턴 오염 없음. 대화는 회사 배지로 구분된다.)
import type { SearchHit } from './searchIndex';
import { DEFAULT_MODEL_ID, isKnownModel } from './webllm';

// 선택 WebLLM 모델 영속(localStorage) · 저장값이 카탈로그에 없으면(버전 변경·오염) 기본으로 폴백. SSR 가드.
function initialModel(): string {
	try {
		const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('dartlab.viewer.webllmModel') : null;
		return saved && isKnownModel(saved) ? saved : DEFAULT_MODEL_ID;
	} catch {
		return DEFAULT_MODEL_ID;
	}
}

export interface EvRef {
	n: number;
	period: string;
	path: string;
	text: string;
	stale: boolean;
}
export interface NavOption {
	code: string;
	name: string;
}
export interface Turn {
	q: string;
	companyName: string; // 이 답을 만든 회사명 (history 태그·배지·전환 divider)
	nav: NavOption[]; // 이동 칩(타 회사 감지 시). [] 면 일반 답 turn
	det: string;
	citedLabel: string | null;
	evItems: EvRef[];
	evHits: SearchHit[];
	ai: string;
	aiRunning: boolean;
	aiErr: string | null;
	tr: string; // 결정론 답(det) 번역 · Chrome Translator 온디바이스
	trLang: string; // 번역 대상 언어 코드(빈값=미번역)
	trBusy: boolean;
	trErr: string | null;
}
// 'cached' = 가중치가 브라우저 Cache 에 이미 있음(받기 아님, GPU 적재만 수 초). 'idle' = 한 번도 안 받음(~705MB).
export type ModelState = 'checking' | 'unsupported' | 'idle' | 'cached' | 'loading' | 'ready' | 'error';
export type OllamaState = 'hidden' | 'probing' | 'ready' | 'no-model' | 'blocked';
// blocked 의 세부 원인 · 같은 상태로 합치되 카피만 정확히(설치확인 vs 허용설정 vs 로딩대기).
export type OllamaReason = 'unreachable' | 'cors' | 'timeout' | null;

export const ask = $state<{
	chat: Turn[];
	modelState: ModelState;
	modelProgress: number; // 0..1 · modelState 와 같은 생존범위(스토어)여야 회사 이동 언마운트 후 진행바 0% 멈춤 0
	selectedModel: string; // 현재 선택 WebLLM 모델 id (localStorage 영속)
	cachedModels: string[]; // 캐시 보유 모델 id 목록 (드롭다운 "받음" 배지)
	ollamaState: OllamaState;
	ollamaReason: OllamaReason;
	ollamaModel: string | null;
	ollamaModels: string[]; // detectOllama 설치 모델(채팅 가능) · 사용자 택1 칩
	consumedCarry: string; // 이미 자동실행한 carryQ · 재마운트에도 생존해 수동 종목검색 후 묵은 질문 재발화 차단
}>({
	chat: [],
	modelState: 'checking',
	modelProgress: 0,
	selectedModel: initialModel(),
	cachedModels: [],
	ollamaState: 'hidden',
	ollamaReason: null,
	ollamaModel: null,
	ollamaModels: [],
	consumedCarry: ''
});
