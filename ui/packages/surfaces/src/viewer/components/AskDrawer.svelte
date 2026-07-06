<script lang="ts">
	// 본진 공시뷰어 우측 AI Q&A 채팅 드로어 · 헤더 아바타 버튼으로 열리고 격자를 밀고 나온다(push).
	// 모델은 명시적 [받기] 버튼+프로그래스바로 1회 다운로드(상태 가시화). 받기 전에도 결정론 답·근거는 즉시(다운로드 0).
	// 받은 뒤엔 질문하면 그 위에서 대화로 자동 응답(멀티턴). 근거 칩 → 부모 onSearchResult(셀 glow) 재사용.
	import { Download, Send, Sparkles, X } from 'lucide-svelte';
	import { plainText, search, type SearchHit, type SearchIndex } from '../lib/searchIndex';
	import { loadIntentModel, queryScope, type IntentModel } from '../lib/queryCanon';
	import { composeAnswer } from '../lib/answerCompose';
	import { resolveCompanies } from '../lib/companyNames';
	import { loadCompanyFinanceSignals } from '../lib/financeAsk';
	import { ask, type EvRef, type NavOption } from '../lib/askSession.svelte';
	import { translateAnswer, translatorSupported, TARGET_LANGS, type TargetLang } from '../lib/translate';
	import { deriveActions, type ViewerAction } from '../lib/viewerActions';
	import {
		isModelCached,
		routeChat,
		stripEcho,
		warmEngine,
		webgpuUsable,
		WEBLLM_MODELS,
		type AskEvidence,
		type ChatTurn,
		type Provider
	} from '../lib/webllm';
	import { detectOllama } from '../lib/ollama';
	import type { FinanceSignal } from '../lib/diff';
	import type { PanelBundle } from '../lib/types';

	// 로컬 Ollama 설치 4단계 · 인라인 렌더(blocked/no-model 에서도 항상 보임, 툴팁 클리핑 0). origin 은 실배포처 고정(환각 URL 금지).
	// {cmd:true} 줄은 monospace 코드 박스로 렌더해 명령을 복사·식별 가능하게 한다.
	const OLLAMA_STEPS: { t: string; cmd?: boolean }[] = [
		{ t: '1. 설치 · ollama.com 에서 받아 실행' },
		{ t: '2. 모델 받기 (터미널)' },
		{ t: 'ollama pull qwen2.5:3b', cmd: true },
		{ t: '한국어 강함: ollama pull exaone3.5:7.8b' },
		{ t: '3. 이 사이트 허용 (한 번만) · 1줄 실행 후 Ollama 재시작' },
		{ t: 'Windows: setx OLLAMA_ORIGINS "https://eddmpython.github.io"', cmd: true },
		{ t: 'macOS: launchctl setenv OLLAMA_ORIGINS "https://eddmpython.github.io"', cmd: true },
		{ t: 'Linux: systemctl edit ollama.service → Environment="OLLAMA_ORIGINS=https://eddmpython.github.io"', cmd: true },
		{ t: '4. 아래 [다시 연결] → "로컬 네트워크 접근 허용?"에 [허용]' }
	];
	// 상태별 한 줄 진단(인라인 가이드 위에 띄움). reason 4종을 구분해 정확히 안내(설치/모델/허용).
	const OLLAMA_NO_MODEL = 'Ollama는 켜졌는데 설치된 모델이 없습니다. 아래 2번으로 모델을 받은 뒤 다시 연결하세요.';
	const OLLAMA_BLOCKED = '로컬 모델에 연결하지 못했습니다. 아래 단계를 확인한 뒤 다시 연결하세요. 받기 전에도 근거·답은 그대로 됩니다.';

	let {
		code,
		bundle,
		searchIndex,
		corpName,
		carryQ = '',
		basePath = '',
		onAction,
		onclose
	}: {
		code: string;
		bundle: PanelBundle | null;
		searchIndex: SearchIndex | null;
		indexing?: boolean;
		corpName: string;
		basePath?: string; // 에셋 경로용 · 셸이 base($app/paths) 주입.
		carryQ?: string; // 이동 후 부모가 운반한 질문(새 회사 index 준비되면 1회 자동 ask)
		onAction: (a: ViewerAction) => void; // 챗→백뷰 제어 단일 채널(executeAction 으로 검증·실행)
		onclose: () => void;
	} = $props();

	let question = $state('');
	let busy = $state(false);
	let finSignals = $state<FinanceSignal[]>([]);
	let intentModel = $state<IntentModel | null>(null); // intentModel(HF 라이브, 번들 fallback) · query→intent 라우팅→섹션 scoping. 1회 로드.

	// opt-in 질문 수집 · 수신단(Cloudflare Worker) URL 이 설정된 경우만 활성(미설정=완전 비활성, UI 숨김). 기본 off, PII 0.
	// surfaces tsconfig 는 vite/client 타입 무의존 · import.meta.env 안전 캐스트(터미널 origin.ts 패턴).
	const FEEDBACK_URL: string =
		(import.meta as unknown as { env?: Record<string, string | undefined> }).env?.VITE_FEEDBACK_URL ?? '';
	let contribute = $state(false);
	$effect(() => {
		try {
			contribute = localStorage.getItem('dartlab.viewer.contributeQuestions') === '1';
		} catch {
			/* localStorage 불가 무시 */
		}
	});
	function toggleContribute() {
		contribute = !contribute;
		try {
			localStorage.setItem('dartlab.viewer.contributeQuestions', contribute ? '1' : '0');
		} catch {
			/* 무시 */
		}
	}
	// 익명 fire-and-forget · 질문 본문 + 예측 intent 만(회사코드/식별자 0). 실패 무음(AI 기능 무영향).
	function logQuestion(q: string, intent: string) {
		if (!FEEDBACK_URL || !contribute) return;
		void fetch(FEEDBACK_URL, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ q, intent })
		}).catch(() => {});
	}
	let guideOpen = $state(false); // hidden 상태에서 설치 가이드 펼침(blocked/no-model 은 항상 펼침)
	let inputEl = $state<HTMLTextAreaElement | null>(null);
	let scrollEl = $state<HTMLElement | null>(null);

	// 모바일이면 큰 모델(>2GB·3B)은 피커에서 숨김(저사양 OOM 방지). 드로어는 클라이언트 전용이라 window 안전.
	let isMobile = $state(false);
	let translatorOk = $state(false); // Chrome 내장 Translator 가용(WebGPU 무관)
	$effect(() => {
		isMobile = typeof window !== 'undefined' && window.matchMedia('(max-width: 880px)').matches;
		translatorOk = translatorSupported();
	});
	const pickerModels = $derived(WEBLLM_MODELS.filter((m) => !(isMobile && m.sizeMB > 2000)));
	const selModel = $derived(WEBLLM_MODELS.find((m) => m.id === ask.selectedModel) ?? WEBLLM_MODELS[0]);
	const notEmbed = (m: string) => !/embed|bge|nomic|mxbai|e5-/i.test(m); // 채팅 불가(임베딩) 모델 제외
	function sizeLabel(mb: number): string {
		return mb >= 1000 ? `${(mb / 1000).toFixed(1)}GB` : `${mb}MB`;
	}
	// 모델 선택 변경 · 영속 + modelState='checking' 으로 마운트 effect 재산정(선택 모델 캐시 여부 → 자동/받기).
	function onModelChange() {
		try {
			localStorage.setItem('dartlab.viewer.webllmModel', ask.selectedModel);
		} catch {
			/* localStorage 불가 무시 */
		}
		ask.modelState = 'checking';
	}

	// 결정론 답(det)을 선택 언어로 온디바이스 번역 (Chrome Translator·환각 0·WebGPU 불필요).
	async function translateTurn(ti: number, lang: TargetLang) {
		const t = ask.chat[ti];
		if (!t || t.trBusy) return;
		t.trBusy = true;
		t.trErr = null;
		t.tr = '';
		t.trLang = lang;
		const r = await translateAnswer(t.det, lang);
		if (r.supported) t.tr = r.text;
		else t.trErr = r.reason ?? '번역에 실패했습니다.';
		t.trBusy = false;
	}

	// 대화·모델·Ollama 상태는 askSession 모듈 스토어(ask) 에 둔다 · 회사 이동 시 viewer +page 가 bundle 을 잠시
	// null 로 만들어 AskDrawer 가 언마운트돼도 세션이 생존한다(크로스-회사 "AI 화면 그대로" 요구).
	const provider = $derived<Provider>(ask.ollamaState === 'ready' ? 'ollama' : 'webllm');

	// blocked 진단 한 줄 · reason 4종을 정확히. timeout=로딩 중일 수 있음, cors=허용 안 됨, unreachable=미실행.
	const ollamaDiag = $derived(
		ask.ollamaReason === 'timeout'
			? '응답이 늦습니다 · 큰 모델 로딩 중일 수 있어요. 잠시 후 다시 연결하세요.'
			: ask.ollamaReason === 'unreachable'
				? 'Ollama 응답이 비정상입니다 · 실행 상태를 확인하세요(1번).'
				: '대개 3번(사이트 허용) 누락입니다 · 설정 후 Ollama 재시작.'
	);

	// 마운트 1회: WebGPU 가용 → 캐시 보유 여부까지 물어 'cached'(이미 받음·빠른 불러오기) vs 'idle'(처음·~705MB) 분기.
	// 캐시 무관 항상 "705MB 받기"를 띄워 매 접속 재다운로드처럼 오해시키던 문제 제거. ready 는 같은 세션 생존이라 건드리지 않음.
	$effect(() => {
		if (ask.modelState !== 'checking') return;
		void webgpuUsable().then(async (v) => {
			if (ask.modelState !== 'checking') return; // 비동기 사이 상태 변동 가드
			if (!v) {
				ask.modelState = 'unsupported';
				return;
			}
			// 모델별 캐시 배지 · 비었으면 1회 수집(회사 이동 재마운트에도 생존). 큐레이션 3종만.
			if (ask.cachedModels.length === 0) {
				const flags = await Promise.all(WEBLLM_MODELS.map((m) => isModelCached(m.id)));
				ask.cachedModels = WEBLLM_MODELS.filter((_, i) => flags[i]).map((m) => m.id);
			}
			if (ask.modelState !== 'checking') return;
			if (await isModelCached(ask.selectedModel)) {
				void warmModel(ask.selectedModel, true); // 선택 모델 이미 받음 → 버튼 없이 자동 불러오기(다운로드 0)
			} else {
				ask.modelState = 'idle'; // 선택 모델 처음 · 명시 [받기](다운로드는 사용자 동의)
			}
		});
	});
	$effect(() => {
		void loadIntentModel().then((m) => (intentModel = m)); // 시드 라우팅 모델 1회 로드(모듈 캐시 → 1회)
	});
	// [회귀가드] ask.chat·ollama 는 code 변경에 불간섭(크로스-회사 대화 유지 핵심). 여기에 ask.chat=[] 또는
	// {#key code} 추가 시 회사 이동마다 대화 소멸 · 절대 금지. finance prefetch 만 code 따라간다.
	$effect(() => {
		const c = code;
		finSignals = [];
		void loadCompanyFinanceSignals(c).then((s) => {
			if (code === c) finSignals = s; // 경쟁 가드: 도착 시점 code 일치할 때만
		});
	});
	$effect(() => {
		requestAnimationFrame(() => inputEl?.focus());
	});

	function scrollBottom() {
		requestAnimationFrame(() => {
			if (scrollEl) scrollEl.scrollTop = scrollEl.scrollHeight;
		});
	}

	// 캐시에서 불러오는 중인지(받기 아님) · 진행바 카피 분기용. loading 진입 시점에 고정.
	let loadingFromCache = $state(false);

	// 선택 모델 GPU 적재 · fromCache=true 면 캐시에서(다운로드 0·몇 초), false 면 첫 다운로드. reload 로 모델만 교체.
	async function warmModel(modelId: string, fromCache: boolean) {
		if (ask.modelState === 'loading' || ask.modelState === 'ready') return;
		loadingFromCache = fromCache;
		ask.modelState = 'loading';
		ask.modelProgress = 0;
		try {
			await warmEngine(modelId, (p) => (ask.modelProgress = p.progress));
			ask.modelState = 'ready';
			if (!ask.cachedModels.includes(modelId)) ask.cachedModels = [...ask.cachedModels, modelId]; // 받음 배지 갱신
		} catch {
			ask.modelState = 'error';
		}
	}
	// 명시 버튼 전용 · 첫 다운로드(idle) · 재시도(error). cached 는 마운트에서 자동 불러오므로 버튼이 없다.
	function downloadModel() {
		void warmModel(ask.selectedModel, loadingFromCache); // 현재 선택 모델로(재시도는 직전 받기/불러오기 맥락 유지)
	}

	// 사용자 제스처(클릭) 안에서만 · Chrome 142 LNA 팝업이 제스처 직후에만 의미 있게 뜬다($effect/마운트 호출 금지).
	async function connectOllama() {
		ask.ollamaState = 'probing';
		const s = await detectOllama();
		if (s.ok) {
			ask.ollamaState = 'ready';
			ask.ollamaModels = s.models.filter(notEmbed); // 채팅 가능 모델만 택1 후보
			ask.ollamaModel = ask.ollamaModels.includes(s.pick ?? '') ? s.pick : (ask.ollamaModels[0] ?? s.pick);
			ask.ollamaReason = null;
		} else if (s.reason === 'no-model') {
			ask.ollamaState = 'no-model';
			ask.ollamaReason = null;
		} else {
			ask.ollamaState = 'blocked'; // unreachable/cors/timeout 통합(상태 1개) · 카피만 reason 으로 정확히
			ask.ollamaReason = s.reason ?? 'cors';
		}
	}

	// 현재 회사(=code) 패널에서 grounded 답 · 결정론(즉시) + (모델 ready 면) 대화 스트리밍.
	// b/i 를 인자로 받아 이동 직후 stale 클로저를 피한다(항상 현재 reactive 값으로 호출). busy 해제 책임은 여기.
	async function answerOnCompany(q: string, b: PanelBundle, i: SearchIndex) {
		// 결정론 섹션 scoping · query→intent(IDF 라우팅)→target 섹션 + canon 어휘보강. search 가 plain BM25 ⊕ (scope+canon)
		// 을 RRF 융합(매퍼0·모델0·dense0). 5업종 held-out top-6 섹션도달 56~71%→92~98%. 라우팅 틀려도 plain 보존(always-safe).
		const scope = queryScope(intentModel, q);
		const { hits, added } = search(i, q, { topK: 6, expand: false, scopeSections: scope.sections, scopeTerms: scope.terms });
		const evHits: SearchHit[] = [];
		const evItems: EvRef[] = [];
		let n = 1;
		for (const h of hits) {
			const cell = b.gridBySection.get(h.sectionKey)?.[h.rowIndex]?.cells?.[h.period] ?? '';
			const text = plainText(cell).slice(0, 700);
			if (!text) continue;
			evHits.push(h);
			evItems.push({ n: n++, period: h.period, path: [h.chapter, h.section, h.block].filter(Boolean).join(' > '), text, stale: h.stale });
		}
		const sigs = finSignals.length ? finSignals : await loadCompanyFinanceSignals(code);
		if (!finSignals.length && sigs.length) finSignals = sigs;
		const composed = composeAnswer(q, hits, added, sigs);
		logQuestion(q, composed.intent); // opt-in 익명 수집(설정+동의 시만) · 라우팅 개선 원천
		const aiReady = provider === 'ollama' ? ask.ollamaState === 'ready' : ask.modelState === 'ready';
		// suggestLlm(왜/종합/의미형)도 생성 트리거 · 근거 0건이어도 결정론 payload 로 grounded. (옛 코드는 산출만 하고 미사용)
		const useAi = aiReady && (evItems.length > 0 || composed.citedSignal != null || composed.suggestLlm);

		ask.chat.push({
			q,
			companyName: corpName,
			nav: [],
			det: composed.answer,
			citedLabel: composed.citedSignal?.label ?? null,
			evItems,
			evHits,
			ai: '',
			aiRunning: useAi,
			aiErr: null,
			tr: '',
			trLang: '',
			trBusy: false,
			trErr: null
		});
		const idx = ask.chat.length - 1;
		scrollBottom();

		// 액션 버스 · 답이 가리키는 곳으로 뒷화면 이동(근거 셀 점프·재무 열기·연도 시점). 결정론·즉시.
		for (const a of deriveActions({ q, targets: [], hits, intent: composed.intent, topHit: evHits[0] ?? null, visiblePeriods: b.periods })) onAction(a);

		if (!useAi) {
			// 의미형 질문인데 모델 미보유(받을 수 있는데 안 받음) → 결정론 답 뒤에 1줄 유도. unsupported 는 제외(헛유도 방지).
			if (composed.suggestLlm && !aiReady && ask.modelState !== 'unsupported') {
				ask.chat[idx].det += ' · 대화 모델을 받으면 이 질문을 더 깊이 풀어드릴 수 있어요(아래 [대화 모델 받기]).';
			}
			busy = false;
			return;
		}
		const history: ChatTurn[] = [];
		for (let k = 0; k < ask.chat.length; k++) {
			if (ask.chat[k].nav.length) continue; // 이동-칩 turn 은 history 제외
			// 회사 태그 프리픽스 · 이동 후 대명사/비교 맥락 유지("그럼 얘 매출은?" → 현재 회사 해석).
			history.push({ role: 'user', content: `[${ask.chat[k].companyName}] ${ask.chat[k].q}` });
			if (k !== idx) history.push({ role: 'assistant', content: ask.chat[k].ai || ask.chat[k].det });
		}
		const payload: AskEvidence[] = [
			{ n: 0, period: '', path: '결정론 분석(숫자 확정)', text: composed.answer },
			...evItems.map(({ n, period, path, text }) => ({ n, period, path, text }))
		];
		let buf = '';
		let last = 0;
		try {
			await routeChat(history, payload, {
				provider,
				ollamaModel: ask.ollamaModel ?? undefined,
				webllmModel: ask.selectedModel,
				onToken: (d) => {
					buf += d;
					const now = performance.now();
					if (now - last > 45) {
						ask.chat[idx].ai = stripEcho(buf); // 약한 모델 parroting/마커 누출 제거
						last = now;
						scrollBottom();
					}
				}
			});
			ask.chat[idx].ai = stripEcho(buf);
		} catch (e) {
			ask.chat[idx].aiErr = e instanceof Error ? e.message : String(e);
			if (provider === 'ollama') ask.ollamaState = 'blocked'; // 도중 사망 → 다음 질문 자동 WebLLM 강등
		} finally {
			ask.chat[idx].aiRunning = false;
			busy = false;
			scrollBottom();
		}
	}

	async function submitQuestion() {
		if (!searchIndex || !bundle || !question.trim() || busy) return;
		const q = question.trim();
		question = '';
		busy = true;

		// 0) 결정론 회사 감지(검색 전). 없는 회사·현재 회사 → [] → 현재 회사로 정상 답.
		const targets = await resolveCompanies(q, code);
		if (targets.length === 0) {
			await answerOnCompany(q, bundle, searchIndex);
			return;
		}

		// 단일 타 회사 감지 → *자동 이동*. 본문(viewer)이 그 회사로 바뀌고, 대화는 스토어로 유지되며, carryQ 로
		// 새 회사에서 원 질문 자동 답. 확인 칩 없이 바로(사용자 요구). 감지는 어절매칭이라 오탐 낮음.
		if (targets.length === 1) {
			onAction({ kind: 'navigateCompany', code: targets[0].code, carryQ: q });
			busy = false;
			return;
		}

		// 모호(≥2) → 자동선택 불가. 후보 칩 제시(클릭 시 그 회사로 이동+원질문 자동 답).
		ask.chat.push({
			q,
			companyName: corpName,
			nav: targets,
			det: `'${q}'에 여러 회사가 보여요. 어디로 갈까요?`,
			citedLabel: null,
			evItems: [],
			evHits: [],
			ai: '',
			aiRunning: false,
			aiErr: null,
			tr: '',
			trLang: '',
			trBusy: false,
			trErr: null
		});
		scrollBottom();
		busy = false;
	}

	// 이동 칩 클릭 · 부모로 위임(goto + 원질문 운반). 부모가 새 회사 로드 후 carryQ 로 자동 재실행.
	function clickNav(target: NavOption, carryQuestion: string) {
		onAction({ kind: 'navigateCompany', code: target.code, carryQ: carryQuestion });
	}

	// 이동 후 운반된 질문 1회 자동 실행 · carryQ + 새 회사 bundle/index 가 모두 reactive prop 이라,
	// "새 회사 인덱스 준비됨"을 effect 가 자연 감지해 1회 ask. ask.consumedCarry(스토어) 가드로 재실행 방지
	// · 재마운트에도 생존해 수동 종목검색 후 묵은 carryQ 재발화를 막는다.
	$effect(() => {
		const cq = carryQ;
		if (!cq || cq === ask.consumedCarry) return;
		if (!searchIndex || !bundle || !bundle.periods.length) return; // 새 회사 데이터 준비 대기(헛답 방지)
		if (bundle.stockCode !== code) return; // soft-swap: 번들이 아직 옛 회사면 대기(옛 데이터로 새 질문 답 방지)
		ask.consumedCarry = cq;
		busy = true;
		void answerOnCompany(cq, bundle, searchIndex); // 이동된 회사(=현재 code)로 답
	});

	function onKey(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
			e.preventDefault();
			void submitQuestion();
		}
	}
</script>

<!-- Ollama 설치 4단계 인라인 가이드 · hidden(펼침)·blocked·no-model 공용. 컨테이너 폭에 맞춰 줄바꿈(클리핑 0). -->
{#snippet guide()}
	<div class="ob-guide">
		{#each OLLAMA_STEPS as s (s.t)}
			{#if s.cmd}<code class="g-cmd">{s.t}</code>{:else}<span class="g-step">{s.t}</span>{/if}
		{/each}
		<span class="g-foot">연결되면 PC의 모델로 답합니다 · 외부 전송 0</span>
	</div>
{/snippet}

<aside class="ask-drawer">
	<header class="ad-head">
		<picture>
			<source srcset="{basePath}/avatar-detective.webp" type="image/webp" />
			<img src="{basePath}/avatar-detective.png" alt="" width="22" height="22" />
		</picture>
		<strong>공시 Q&A</strong>
		{#if ask.ollamaState === 'ready'}<span class="hd-badge" title="로컬 Ollama 사용 중 · 외부 전송 없음">Ollama · {ask.ollamaModel}</span>{/if}
		<button type="button" class="ad-x" onclick={onclose} aria-label="닫기"><X size={15} /></button>
	</header>

	<div class="ad-scroll" bind:this={scrollEl}>
		{#if ask.chat.length === 0}
			<div class="onboard">
				<picture>
					<source srcset="{basePath}/avatar.webp" type="image/webp" />
					<img class="onboard-ava" src="{basePath}/avatar.png" alt="" width="76" height="76" />
				</picture>

				<!-- 온디바이스 모델 영역 · 자식 폭을 한 컬럼(.ob-block)으로 묶어 좌우 정렬 일치 -->
				<div class="ob-block">
					{#if ask.modelState === 'idle'}
						<select class="model-pick" bind:value={ask.selectedModel} onchange={onModelChange} aria-label="대화 모델 선택">
							{#each pickerModels as m (m.id)}
								<option value={m.id}>{m.label} · {sizeLabel(m.sizeMB)} · {m.note}{ask.cachedModels.includes(m.id) ? ' · 받음' : ''}</option>
							{/each}
						</select>
						<button type="button" class="onboard-dl" onclick={downloadModel}><Download size={15} /> 대화 모델 받기</button>
						<span class="onboard-sub">처음 1회 {sizeLabel(selModel.sizeMB)} · 안 받아도 근거·답은 즉시</span>
					{:else if ask.modelState === 'cached'}
						<span class="onboard-sub">대화 모델 불러오는 중…</span>
					{:else if ask.modelState === 'loading'}
						<div class="onboard-bar"><div class="bar-fill" style="width:{Math.round(ask.modelProgress * 100)}%"></div><span class="bar-txt">{loadingFromCache ? '불러오는 중' : '받는 중'} {Math.round(ask.modelProgress * 100)}%</span></div>
					{:else if ask.modelState === 'ready'}
						<select class="model-pick" bind:value={ask.selectedModel} onchange={onModelChange} aria-label="대화 모델 변경">
							{#each pickerModels as m (m.id)}
								<option value={m.id}>{m.label} · {sizeLabel(m.sizeMB)} · {m.note}{ask.cachedModels.includes(m.id) ? ' · 받음' : ''}</option>
							{/each}
						</select>
						<span class="onboard-sub">{selModel.label} 준비됨 · 위에서 다른 모델로 바꿀 수 있어요(받은 모델은 즉시 전환)</span>
					{:else if ask.modelState === 'error'}
						<select class="model-pick" bind:value={ask.selectedModel} onchange={onModelChange} aria-label="대화 모델 선택">
							{#each pickerModels as m (m.id)}
								<option value={m.id}>{m.label} · {sizeLabel(m.sizeMB)} · {m.note}{ask.cachedModels.includes(m.id) ? ' · 받음' : ''}</option>
							{/each}
						</select>
						<button type="button" class="onboard-dl err" onclick={downloadModel}>로드 실패 · 다시</button>
					{:else if ask.modelState === 'unsupported'}
						<span class="onboard-sub">이 브라우저는 대화 미지원 · 근거·결정론 답은 됩니다</span>
					{/if}
				</div>

				<!-- 로컬 Ollama 옵션 영역 · 같은 .ob-block 컬럼. 자동 프로브 금지(클릭 시만). 가이드는 인라인(툴팁 클리핑 0). -->
				<div class="ob-block">
					{#if ask.ollamaState === 'hidden'}
						<button type="button" class="ollama-link" onclick={connectOllama}>로컬 Ollama 연결 · 더 좋은 품질</button>
						<button type="button" class="ob-guide-toggle" onclick={() => (guideOpen = !guideOpen)} aria-expanded={guideOpen}>설치 방법 {guideOpen ? '접기' : '보기'}</button>
						{#if guideOpen}{@render guide()}{/if}
					{:else if ask.ollamaState === 'probing'}
						<span class="onboard-sub">Ollama 찾는 중…</span>
					{:else if ask.ollamaState === 'ready'}
						<span class="ollama-on">● 로컬 모델 연결됨</span>
						{#if ask.ollamaModels.length > 1}
							<div class="ev-row ollama-pick">
								{#each ask.ollamaModels as m (m)}
									<button type="button" class="ev-chip" class:on={m === ask.ollamaModel} onclick={() => (ask.ollamaModel = m)}>{m}</button>
								{/each}
							</div>
						{:else}
							<span class="onboard-sub">{ask.ollamaModel}</span>
						{/if}
					{:else if ask.ollamaState === 'no-model'}
						<span class="ollama-warn">{OLLAMA_NO_MODEL}</span>
						{@render guide()}
						<button type="button" class="retry" onclick={connectOllama}>다시 연결</button>
					{:else if ask.ollamaState === 'blocked'}
						<span class="ollama-warn">{OLLAMA_BLOCKED}</span>
						<span class="ollama-diag">{ollamaDiag}</span>
						{@render guide()}
						<button type="button" class="retry" onclick={connectOllama}>다시 연결</button>
					{/if}
				</div>
			</div>
		{/if}
		{#each ask.chat as t, ti (ti)}
			{#if t.nav.length === 0 && ti > 0 && t.companyName !== ask.chat[ti - 1].companyName}
				<div class="co-divider">──── {t.companyName} ────</div>
			{/if}
			<div class="msg user">{t.q}</div>
			<div class="msg bot">
				{#if t.nav.length === 0 && (ti === 0 || t.companyName !== ask.chat[ti - 1].companyName) && t.companyName}
					<span class="co-badge">{t.companyName}</span>
				{/if}
				{#if t.nav.length}
					<!-- 이동 칩 turn · 답 대신 안내 + 칩(클릭 시 이동·원질문 자동 답) -->
					<p class="bot-text">{t.det}</p>
					<div class="ev-row">
						{#each t.nav as opt (opt.code)}
							<button type="button" class="nav-chip" onclick={() => clickNav(opt, t.q)}>→ {opt.name}({opt.code})로 이동해서 답하기</button>
						{/each}
					</div>
				{:else}
					{#if t.ai}
						<p class="bot-text">{t.ai}</p>
						<div class="det-line">{t.det}</div>
					{:else}
						<p class="bot-text">{t.det}</p>
						{#if t.aiRunning}<div class="gen"><span class="dot"></span>생성 중…</div>{/if}
					{/if}
					{#if translatorOk}
						<div class="tr-bar">
							{#each TARGET_LANGS as l (l.code)}
								<button type="button" class="tr-pill" class:on={t.trLang === l.code && !!t.tr} onclick={() => translateTurn(ti, l.code)} disabled={t.trBusy}>{l.label}</button>
							{/each}
							{#if t.trBusy}<span class="tr-busy">번역 중…</span>{/if}
						</div>
						{#if t.tr}<div class="tr-out">{t.tr}</div>{/if}
						{#if t.trErr}<div class="gen err">{t.trErr}</div>{/if}
					{/if}
					{#if t.aiErr}<div class="gen err">{t.aiErr}</div>{/if}
					{#if t.citedLabel}<div class="cite">재무: {t.citedLabel}</div>{/if}
					{#if t.evItems.length}
						<div class="ev-row">
							{#each t.evItems as e, i (e.n)}
								<button type="button" class="ev-chip" class:stale={e.stale} onclick={() => onAction({ kind: 'focusEvidence', hit: t.evHits[i] })} title={e.stale ? `${e.path} · 이 항목의 최근 언급은 과거 시점입니다` : e.path}>근거 {e.n} · {e.period}{#if e.stale} <span class="stale-tag">과거</span>{/if}</button>
							{/each}
						</div>
					{/if}
				{/if}
			</div>
		{/each}
	</div>

	<!-- 대화 중 모델 strip · 메시지 있고 아직 안 올렸을 때만(중앙 온보딩과 중복 방지). ready 면 숨김. -->
	{#if ask.chat.length > 0 && ask.modelState === 'idle' && ask.ollamaState !== 'ready'}
		<button type="button" class="ad-model dl" onclick={downloadModel}>
			<Download size={14} /> 대화 모델 받기 <span class="sz">처음 1회 ~705MB</span>
		</button>
	{:else if ask.chat.length > 0 && ask.modelState === 'loading'}
		<div class="ad-model bar">
			<div class="bar-fill" style="width:{Math.round(ask.modelProgress * 100)}%"></div>
			<span class="bar-txt">대화 모델 {loadingFromCache ? '불러오는' : '받는'} 중 {Math.round(ask.modelProgress * 100)}%</span>
		</div>
	{:else if ask.chat.length > 0 && ask.modelState === 'error'}
		<button type="button" class="ad-model dl err" onclick={downloadModel}>대화 모델 로드 실패 · 다시</button>
	{:else if ask.chat.length > 0 && ask.modelState === 'ready' && ask.ollamaState !== 'ready'}
		<!-- 대화 중에도 모델 교체 · 받은 모델은 즉시 전환, 안 받은 모델은 받기로. 답 품질 낮으면 3B 로 바꿀 수 있게. -->
		<select class="ad-model-pick" bind:value={ask.selectedModel} onchange={onModelChange} aria-label="대화 모델 변경">
			{#each pickerModels as m (m.id)}
				<option value={m.id}>{m.label}{ask.cachedModels.includes(m.id) ? ' · 받음' : ' · ' + sizeLabel(m.sizeMB)}</option>
			{/each}
		</select>
	{/if}

	<!-- 질문 익명 기여 opt-in · 수신단(VITE_FEEDBACK_URL) 설정된 경우만 노출. 기본 off. 검색 품질 개선용, PII 0. -->
	{#if FEEDBACK_URL}
		<button type="button" class="ad-contrib" class:on={contribute} onclick={toggleContribute} title="내 질문을 익명으로 보내 검색 품질 개선에 기여합니다(회사·식별정보 0). 언제든 끌 수 있어요.">
			<span class="cb">{contribute ? '☑' : '☐'}</span> 질문 익명 기여(검색 개선)
		</button>
	{/if}

	<div class="ad-askbox">
		<textarea bind:this={inputEl} bind:value={question} rows="1" placeholder="공시에 대해 질문…" onkeydown={onKey}></textarea>
		<button type="button" class="ad-send" onclick={submitQuestion} disabled={!searchIndex || busy || !question.trim()} aria-label="질문">
			{#if busy}<Sparkles size={15} />{:else}<Send size={15} />{/if}
		</button>
	</div>
</aside>

<style>
	.ask-drawer {
		min-width: 0;
		min-height: 0;
		height: 100%;
		display: flex;
		flex-direction: column;
		border-left: 1px solid #1e2433;
		background: #070b14;
		animation: adslide 0.18s ease-out;
	}
	@keyframes adslide {
		from { transform: translateX(24px); opacity: 0.4; }
		to { transform: translateX(0); opacity: 1; }
	}
	.ad-head {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 12px;
		border-bottom: 1px solid #1e2433;
		flex-shrink: 0;
	}
	.ad-head img { border-radius: 50%; }
	.ad-head strong { font-size: 13px; color: #f1f5f9; font-weight: 800; }
	.ad-x {
		margin-left: auto;
		display: grid;
		place-items: center;
		width: 26px;
		height: 26px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		background: transparent;
		color: #cbd5e1;
		cursor: pointer;
	}
	.ad-x:hover { border-color: rgba(var(--amber-rgb), 0.5); color: var(--amber); }
	.ad-scroll {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		padding: 12px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.msg {
		font-size: 13px;
		line-height: 1.55;
		white-space: pre-wrap;
		word-break: break-word;
	}
	.msg.user {
		align-self: flex-end;
		max-width: 92%;
		padding: 8px 11px;
		border-radius: 12px 12px 3px 12px;
		background: rgba(var(--amber-rgb), 0.14);
		color: #fde7cf;
	}
	.msg.bot {
		align-self: stretch;
		padding: 10px 11px;
		border: 1px solid #1e2433;
		border-radius: 12px 12px 12px 3px;
		background: #0a0e18;
	}
	.bot-text { margin: 0; color: #e2e8f0; font-size: 13px; line-height: 1.6; }
	.tr-bar { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; margin-top: 7px; }
	.tr-pill { height: 22px; padding: 0 8px; border: 1px solid #1e2433; border-radius: 999px; background: #050811; color: #cbd5e1; font: inherit; font-size: 11px; cursor: pointer; }
	.tr-pill.on { border-color: rgba(56, 189, 248, 0.5); color: #bae6fd; background: rgba(14, 165, 233, 0.08); }
	.tr-pill:disabled { opacity: 0.5; cursor: default; }
	.tr-busy { color: #94a3b8; font-size: 11px; }
	.tr-out { margin-top: 6px; padding: 8px 10px; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; background: rgba(14, 165, 233, 0.06); color: #dbeafe; font-size: 12px; line-height: 1.6; white-space: pre-wrap; }
	.det-line {
		margin-top: 7px;
		padding-top: 6px;
		border-top: 1px dashed #1e2433;
		color: #cbd5e1;
		font-size: 11px;
		line-height: 1.5;
	}
	.gen { display: flex; align-items: center; gap: 7px; margin-top: 7px; color: #cbd5e1; font-size: 11px; }
	.gen.err { color: #f87171; }
	.dot { width: 7px; height: 7px; border-radius: 50%; background: #38bdf8; animation: pulse 1s ease-in-out infinite; }
	@keyframes pulse { 50% { opacity: 0.3; } }
	.cite { margin-top: 6px; color: var(--amber); font-size: 11px; }
	.ev-row { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
	.ev-chip {
		max-width: 100%;
		padding: 4px 8px;
		border: 1px solid #1e2433;
		border-radius: 999px;
		background: #050811;
		color: #cbd5e1;
		font: inherit;
		font-size: 10.5px;
		cursor: pointer;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.ev-chip:hover { border-color: rgba(var(--amber-rgb), 0.55); color: var(--amber); }
	.ev-chip.on { border-color: rgba(52, 211, 153, 0.6); color: #34d399; background: rgba(52, 211, 153, 0.1); }
	.ollama-pick { justify-content: center; }
	.ev-chip.stale { border-style: dashed; }
	.stale-tag {
		margin-left: 3px;
		padding: 0 4px;
		border-radius: 6px;
		background: rgba(148, 163, 184, 0.16);
		color: #cbd5e1;
		font-size: 9px;
	}
	/* 크로스-회사 이동 · 전환 divider + 회사 배지 + 이동 칩 */
	.co-divider {
		align-self: stretch;
		text-align: center;
		margin: 6px 0 2px;
		color: #64748b;
		font-size: 10.5px;
		letter-spacing: 0.04em;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.co-badge {
		display: inline-block;
		margin-bottom: 6px;
		padding: 1px 7px;
		border: 1px solid #1e2433;
		border-radius: 999px;
		background: #050811;
		color: #94a3b8;
		font-size: 10px;
	}
	.nav-chip {
		max-width: 100%;
		padding: 5px 10px;
		border: 1px solid rgba(var(--amber-rgb), 0.55);
		border-radius: 999px;
		background: rgba(var(--amber-rgb), 0.1);
		color: var(--amber);
		font: inherit;
		font-size: 11px;
		font-weight: 600;
		cursor: pointer;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.nav-chip:hover { background: rgba(var(--amber-rgb), 0.2); }
	/* 중앙 온보딩 · 빈 대화 시 아바타 + 모델 영역 + Ollama 영역. 단일 폭(.ob-block)으로 좌우 정렬 일치. */
	.onboard {
		margin: auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
		text-align: center;
		padding: 20px 12px;
		width: 100%;
		max-width: 300px;
	}
	.onboard-ava {
		border-radius: 50%;
	}
	/* 정렬 컨테이너 · 모델/Ollama 자식을 같은 폭·같은 좌측선으로. 폭 혼재(240px warn vs inline-flex link) 제거. */
	.ob-block {
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 7px;
	}
	/* 모델 선택 드롭다운 · 받기 전 어떤 모델을 받을지 고른다. scan 다크 폼 스타일. */
	.model-pick {
		width: 100%;
		max-width: 240px;
		padding: 7px 10px;
		border: 1px solid #263145;
		border-radius: 8px;
		background: #0a0e18;
		color: #e2e8f0;
		font: inherit;
		font-size: 12px;
		cursor: pointer;
	}
	.model-pick:focus {
		outline: none;
		border-color: #38bdf8;
	}
	/* 대화 중 컴팩트 모델 교체 셀렉트 · 입력창 위 strip. 받은 모델 즉시 전환. */
	.ad-model-pick {
		flex-shrink: 0;
		align-self: flex-start;
		margin: 0 12px 8px;
		max-width: calc(100% - 24px);
		padding: 6px 10px;
		border: 1px solid #263145;
		border-radius: 8px;
		background: #0a0e18;
		color: #cbd5e1;
		font: inherit;
		font-size: 11.5px;
		cursor: pointer;
	}
	.ad-model-pick:focus {
		outline: none;
		border-color: #38bdf8;
	}
	/* opt-in 질문 기여 토글 · 입력창 위 작은 텍스트 버튼. 기본 muted, 켜지면 초록. */
	.ad-contrib {
		flex-shrink: 0;
		align-self: flex-start;
		margin: 0 12px 6px;
		padding: 2px 4px;
		border: none;
		background: transparent;
		color: #94a3b8;
		font: inherit;
		font-size: 10.5px;
		cursor: pointer;
	}
	.ad-contrib:hover {
		color: #cbd5e1;
	}
	.ad-contrib.on {
		color: #34d399;
	}
	.ad-contrib .cb {
		font-size: 11px;
	}
	.onboard-dl {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 9px 16px;
		border: 1px solid rgba(56, 189, 248, 0.5);
		border-radius: 10px;
		background: rgba(14, 165, 233, 0.1);
		color: #bae6fd;
		font: inherit;
		font-size: 13px;
		font-weight: 700;
		cursor: pointer;
	}
	.onboard-dl:hover {
		background: rgba(14, 165, 233, 0.2);
	}
	.onboard-dl.err {
		border-color: rgba(248, 113, 113, 0.5);
		color: #fca5a5;
		background: rgba(248, 113, 113, 0.08);
	}
	.onboard-sub {
		color: #94a3b8;
		font-size: 11px;
		line-height: 1.5;
	}
	.onboard-bar {
		position: relative;
		width: 200px;
		max-width: 80%;
		height: 30px;
		border: 1px solid #1e2433;
		border-radius: 8px;
		background: #0a0e18;
		overflow: hidden;
		display: grid;
		place-items: center;
	}
	/* model strip */
	.ad-model {
		flex-shrink: 0;
		margin: 0 12px 8px;
		font: inherit;
		font-size: 12px;
	}
	.ad-model.dl {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		align-self: flex-start;
		padding: 8px 12px;
		border: 1px solid rgba(56, 189, 248, 0.5);
		border-radius: 8px;
		background: rgba(14, 165, 233, 0.1);
		color: #bae6fd;
		cursor: pointer;
	}
	.ad-model.dl:hover { background: rgba(14, 165, 233, 0.18); }
	.ad-model.dl .sz { color: #94a3b8; font-size: 10px; }
	.ad-model.dl.err { border-color: rgba(248, 113, 113, 0.5); color: #fca5a5; background: rgba(248, 113, 113, 0.08); }
	.ad-model.bar {
		position: relative;
		height: 28px;
		border: 1px solid #1e2433;
		border-radius: 8px;
		background: #0a0e18;
		overflow: hidden;
		display: grid;
		place-items: center;
	}
	.bar-fill { position: absolute; left: 0; top: 0; bottom: 0; background: rgba(56, 189, 248, 0.22); transition: width 0.2s; }
	.bar-txt { position: relative; color: #bae6fd; font-size: 11px; }
	.ad-askbox {
		display: flex;
		align-items: flex-end;
		gap: 8px;
		flex-shrink: 0;
		padding: 0 12px 12px;
	}
	.ad-askbox textarea {
		flex: 1 1 auto;
		min-width: 0;
		max-height: 110px;
		height: 38px;
		padding: 9px 10px;
		border: 1px solid #263145;
		border-radius: 8px;
		background: #0a0e18;
		color: #f1f5f9;
		font: inherit;
		font-size: 13px;
		line-height: 1.4;
		resize: none;
		outline: none;
	}
	.ad-askbox textarea:focus { border-color: var(--amber); }
	.ad-send {
		display: grid;
		place-items: center;
		width: 38px;
		height: 38px;
		flex-shrink: 0;
		border: none;
		border-radius: 8px;
		background: var(--amber);
		color: #1a1206;
		cursor: pointer;
	}
	.ad-send:disabled { opacity: 0.45; cursor: default; }

	/* Ollama 옵션 레인 · 기존 팔레트 재사용(새 색 없음). ready 만 초록, 나머지 muted/warn. */
	.ollama-link {
		padding: 0;
		border: none;
		background: transparent;
		color: #94a3b8;
		font: inherit;
		font-size: 11px;
		cursor: pointer;
		text-decoration: underline;
		text-underline-offset: 2px;
	}
	.ollama-link:hover { color: var(--amber); }
	/* hidden 상태 가이드 펼치기 토글 · 작은 보조 링크(평소 접힘, 클릭 시 인라인 가이드). */
	.ob-guide-toggle {
		padding: 0;
		border: none;
		background: transparent;
		color: #64748b;
		font: inherit;
		font-size: 10.5px;
		cursor: pointer;
		text-decoration: underline;
		text-underline-offset: 2px;
	}
	.ob-guide-toggle:hover { color: #cbd5e1; }
	.ollama-on { display: inline-flex; align-items: center; gap: 5px; color: #34d399; font-size: 11px; }
	.ollama-warn { color: #cbd5e1; font-size: 11.5px; line-height: 1.55; text-align: center; }
	.ollama-diag { color: var(--dl-accent-light); font-size: 10.5px; line-height: 1.5; text-align: center; }
	.retry {
		padding: 5px 12px;
		border: 1px solid rgba(var(--amber-rgb), 0.4);
		border-radius: 7px;
		background: rgba(var(--amber-rgb), 0.08);
		color: var(--dl-accent-light);
		font: inherit;
		font-size: 11px;
		font-weight: 600;
		cursor: pointer;
	}
	.retry:hover { background: rgba(var(--amber-rgb), 0.18); }
	/* 인라인 설치 가이드 · 컨테이너 폭(최대 300px) 안에서 줄바꿈, 좌측 정렬. 절대배치/280px 툴팁 폐기로 클리핑 0. */
	.ob-guide {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 5px;
		padding: 10px 12px;
		border: 1px solid #1e2433;
		border-radius: 8px;
		background: #0a0e18;
		text-align: left;
	}
	.g-step { color: #e2e8f0; font-size: 11px; line-height: 1.5; }
	.g-cmd {
		display: block;
		padding: 5px 8px;
		border-radius: 6px;
		background: #050811;
		border: 1px solid #1e2433;
		color: #bae6fd;
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 10px;
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-all;
	}
	.g-foot { margin-top: 2px; color: #64748b; font-size: 10px; }
	.hd-badge {
		padding: 2px 8px;
		border: 1px solid rgba(52, 211, 153, 0.4);
		border-radius: 999px;
		background: rgba(52, 211, 153, 0.08);
		color: #34d399;
		font-size: 10px;
		font-weight: 700;
	}

	/* D5 · 모바일 터치 타깃 HIG(44px). 데스크톱(≥881px)은 위 기본값(26/38px) 불변.
	   드로어가 모바일에선 전체화면 오버레이(부모 +page @media)라 입력·닫기·전송이 손가락에 충분해야 한다. */
	@media (max-width: 880px) {
		.ad-head {
			padding: 12px 14px;
		}
		.ad-x {
			width: 40px;
			height: 40px;
		}
		.ad-askbox {
			padding: 0 14px 14px;
			gap: 10px;
		}
		.ad-askbox textarea {
			min-height: 44px;
			font-size: 16px; /* iOS 자동 줌인 방지(≥16px) */
		}
		.ad-send {
			width: 48px;
			height: 48px;
		}
		/* 온보딩 모델 영역 · 오버레이 풀폭이라 카드도 넉넉히. 받기 버튼 터치 타깃 확대. */
		.onboard {
			max-width: 420px;
		}
		.onboard-dl {
			min-height: 48px;
			font-size: 14px;
		}
		.retry {
			min-height: 44px;
		}
		.ad-model.dl {
			min-height: 44px;
		}
	}
</style>
