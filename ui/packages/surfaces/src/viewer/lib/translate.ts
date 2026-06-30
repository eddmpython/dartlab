// 공시뷰어 답변 번역 · Chrome 온디바이스 Translator API(내장 AI, Chrome 138+ 데스크톱).
//
// 결정론 한국어 답(answerCompose 의 composed.answer, SSOT)을 외부 전송 0·온디바이스로 번역만 한다.
// 전용 MT 모델이라 생성형 환각이 없다(숫자·계정명·기간 그대로). WebGPU 불필요 · Tier1 LLM 과 독립.
// Gemini Nano(Prompt API)는 한국어 생성 미지원(en/ja/es)이라 번역 레이어엔 쓰지 않는다.
//
// 모든 진입점은 기능 탐지 후 부재 시 안전 결과(supported:false)를 반환 · 결정론 답엔 영향 없음.

// 내장 AI 공통 4-값 가용성 enum.
export type Availability = 'unavailable' | 'downloadable' | 'downloading' | 'available';
export type TargetLang = 'en' | 'ja' | 'zh';
export const TARGET_LANGS: { code: TargetLang; label: string }[] = [
	{ code: 'en', label: 'EN' },
	{ code: 'ja', label: 'JA' },
	{ code: 'zh', label: 'ZH' }
];

export interface TranslateProgress {
	loaded: number; // 0..1 (downloadprogress e.loaded)
}
export interface TranslateOpts {
	onProgress?: (p: TranslateProgress) => void; // 언어팩 다운로드 진행
	signal?: AbortSignal;
}
export interface TranslateResult {
	supported: boolean; // Translator API + 해당 언어쌍 사용 가능?
	text: string; // 번역문(미지원 시 '')
	reason?: string; // 미지원/실패 사유(UI 표시용)
}

// 공식 surface 의 최소 구조 타입(lib.dom 미정의라 로컬 선언).
interface TranslatorInstance {
	translate(input: string): Promise<string>;
	destroy?(): void;
}
interface TranslatorStatic {
	availability(o: { sourceLanguage: string; targetLanguage: string }): Promise<Availability>;
	create(o: {
		sourceLanguage: string;
		targetLanguage: string;
		monitor?: (m: EventTarget) => void;
		signal?: AbortSignal;
	}): Promise<TranslatorInstance>;
}

function getTranslator(): TranslatorStatic | null {
	if (typeof self === 'undefined' || !('Translator' in self)) return null;
	return (self as unknown as { Translator: TranslatorStatic }).Translator;
}

export function translatorSupported(): boolean {
	return getTranslator() !== null;
}

// 결정론 한국어 답을 target 언어로 온디바이스 번역(환각 0). source 는 ko 고정.
export async function translateAnswer(
	text: string,
	target: TargetLang,
	opts: TranslateOpts = {}
): Promise<TranslateResult> {
	const T = getTranslator();
	if (!T) return { supported: false, text: '', reason: 'Translator API 미지원(Chrome 138+ 데스크톱 필요)' };
	if (!text.trim()) return { supported: true, text: '' };

	const pair = { sourceLanguage: 'ko', targetLanguage: target };
	let status: Availability;
	try {
		status = await T.availability(pair);
	} catch (e) {
		return { supported: false, text: '', reason: msg(e) };
	}
	if (status === 'unavailable') {
		return { supported: false, text: '', reason: `ko→${target} 번역을 이 기기에서 사용할 수 없습니다.` };
	}
	// 다운로드 필요 시 사용자 제스처 필요 · 호출은 click 핸들러 안이므로 통상 isActive.
	if (
		status !== 'available' &&
		typeof navigator !== 'undefined' &&
		navigator.userActivation &&
		!navigator.userActivation.isActive
	) {
		return { supported: false, text: '', reason: '언어팩 다운로드에는 사용자 클릭이 필요합니다.' };
	}

	let translator: TranslatorInstance | null = null;
	try {
		translator = await T.create({
			...pair,
			signal: opts.signal,
			monitor(m: EventTarget) {
				m.addEventListener('downloadprogress', (e: Event) => {
					const loaded = (e as unknown as { loaded?: number }).loaded ?? 0;
					opts.onProgress?.({ loaded });
				});
			}
		});
		return { supported: true, text: await translator.translate(text) };
	} catch (e) {
		return { supported: false, text: '', reason: msg(e) };
	} finally {
		translator?.destroy?.();
	}
}

function msg(e: unknown): string {
	return e instanceof Error ? e.message : String(e);
}
