<script lang="ts">
	import { onMount } from 'svelte';

	interface Step {
		selector?: string;
		title: string;
		// 본문 단락 배열 · 각각 한 문단
		body: string[];
		// 핵심 가치 한 줄 (왜 유용한지)
		why?: string;
		// "직접 해보기" 데모 (옵션)
		demo?: { label: string; run: () => void | Promise<void> };
	}

	interface Props {
		open: boolean;
		onClose: () => void;
		colorMetric: string;
		viewMode: string;
		enterIndustryAction: (id: string) => void | Promise<void>;
		selectCompanyAction: (stockCode: string) => void | Promise<void>;
		addCompareAction: (stockCode: string) => void | Promise<void>;
		clearSelectionAction: () => void;
	}

	let {
		open,
		onClose,
		colorMetric = $bindable(),
		viewMode = $bindable(),
		enterIndustryAction,
		selectCompanyAction,
		addCompareAction,
		clearSelectionAction
	}: Props = $props();

	let stepIdx = $state(0);
	let highlight = $state<{ x: number; y: number; w: number; h: number } | null>(null);
	// 퀵투어(3스텝) vs 풀투어(12스텝)
	const QUICK_COUNT = 3;
	let fullMode = $state(false);

	const STEPS: Step[] = [
		{
			title: '산업지도에 오신 걸 환영합니다',
			body: [
				'한국 상장사 · 34개 산업 · 공급망 네트워크를 한 화면에서 분석하는 도구입니다.',
				'이 투어는 "무엇을 클릭하면 무엇이 보이는지" 를 **실제로 보여드립니다.** 단순한 설명이 아니라 화면이 같이 바뀝니다.',
				'좌우 화살표 키 · Enter / Esc 또는 아래 버튼으로 진행. 각 스텝의 **"▶ 실제로 해보기"** 버튼이 있으면 꼭 눌러보세요.'
			],
			why: '5분이면 이 지도의 전부를 쓸 줄 알게 됩니다.'
		},
		{
			selector: '.brand-bar',
			title: '1 / 13  ·  좌측 상단 · 빠른 액션 바',
			body: [
				'이 작은 아이콘들이 자주 쓰는 액션입니다.',
				'• **아바타** · 언제든 dartlab 홈 랜딩으로 복귀\n• **GitHub** · 전체 소스·이슈 트래커\n• **커피 컵** · 후원 (오픈소스 유지에 도움)\n• **?** · 지금 보고 있는 이 투어를 다시 시작'
			],
			why: '투어는 ? 버튼으로 언제든 재실행 가능 · 기능 추가될 때마다 다시 돌려 보세요.'
		},
		{
			selector: '.color-switch',
			title: '2 / 13  ·  색상 기준 · 이 지도의 핵심',
			body: [
				'**이 하나의 셀렉터가 지도 전체의 색을 바꿉니다.** 단순히 산업별 색상만 있는 게 아니라, 재무 지표 기반 스코어를 색으로 투사합니다.',
				'기본 "산업 팔레트" 는 34개 산업 고유 색 · 어디가 무슨 산업인지 구분용.',
				'**ROE 로 바꾸면** 산업 내에서 누가 주주 돈을 잘 굴리는지 빨강→초록 그라디언트로 즉시 드러납니다. 산업 전체에 적용되므로 한눈에 우량/부진이 보여요.',
				'지금 직접 눌러 보세요 · 화면 전체 색이 바뀌는 게 보입니다.'
			],
			why: '"어느 산업·어느 회사가 우량한가" 에 1초 안에 답하는 도구입니다.',
			demo: {
				label: '▶ ROE 로 바꿔보기 (화면 색 변화)',
				run: () => {
					colorMetric = 'roe';
				}
			}
		},
		{
			selector: '.color-switch',
			title: '3 / 13  ·  다른 관점 · 성장률',
			body: [
				'ROE는 수익성. 그런데 "돈 안 벌어도 커지는 회사" 는 CAGR 로 보여야 합니다.',
				'**매출 CAGR 3년** 으로 바꾸면 고성장 기업(바이오·IT) 이 초록으로, 정체·역성장 기업이 빨강으로 바뀝니다.',
				'다른 옵션:\n• **영업이익률** · 본업 마진 경쟁력\n• **부채비율** · 재무 건전성 (역방향: 낮을수록 초록)\n• **매출 규모** · 대기업 vs 중소 구분',
				'5개 관점으로 같은 지도를 5가지 다른 질문에 활용 가능합니다.'
			],
			why: '한 화면에서 관점만 바꾸면 5개의 서로 다른 분석이 됩니다.',
			demo: {
				label: '▶ 매출 CAGR 로 바꾸기',
				run: () => {
					colorMetric = 'revCagr';
				}
			}
		},
		{
			selector: '.view-switch',
			title: '4 / 13  ·  관점 4종 · 산업 / 히트맵 / 전회사 / 드릴다운',
			body: [
				'같은 데이터를 네 가지 배율로 봅니다.',
				'• **산업 지도** (기본) · 34개 버블. 거시적 탐색, 공급 플로우 파악.\n• **히트맵** · Finviz 스타일 treemap. 시장 전체가 한눈에.\n• **전 회사** · 상장사 전부를 한 그래프에.\n• **산업 내부** · 산업 하나만 열어 공정별 클러스터링.',
				'지금 **히트맵 뷰**로 이동해 시장 전체를 봅니다.'
			],
			why: '거시(산업) → 중범위(산업 내부) → 미시(회사) 로 자연스럽게 내려가는 구조.',
			demo: {
				label: '▶ 히트맵 뷰로 이동',
				run: () => {
					viewMode = 'treemap';
				}
			}
		},
		{
			title: '5 / 13  ·  히트맵 · 시장 전체가 한눈에',
			body: [
				'**Treemap 히트맵**은 상장사를 면적으로 표현합니다. 크기 = 매출, 색 = 현재 색상 기준.',
				'우측 상단에서 **크기 기준**을 매출/ROE/OPM/CAGR로 전환할 수 있습니다.',
				'셀을 클릭하면 회사 카드가 FloatingCard 윈도우로 열립니다.',
				'기본 색상(ROE)에서 부채비율로 바꾸면 "큰데 빚 많은 회사"가 즉시 보입니다.'
			],
			why: '"3초에 시장 전체를 읽는다" · 이것이 히트맵의 힘.',
			demo: {
				label: '▶ 산업 지도로 복귀',
				run: () => {
					viewMode = 'atlas';
				}
			}
		},
		{
			selector: '.view-switch',
			title: '6 / 13  ·  산업 버블 클릭 = 업종 체력 카드',
			body: [
				'산업 지도에서 **업종 버블을 클릭하면 업종 체력 카드**가 나타납니다.',
				'ROE/OPM/CAGR 분포 박스플롯, 평균값, Top 기업이 한눈에. "업종 상세 →" 버튼으로 드릴다운합니다.',
				'"이 업종 지금 좋은가?" 에 3초 만에 답합니다.'
			],
			demo: {
				label: '▶ 산업 지도로 복귀',
				run: () => {
					viewMode = 'atlas';
				}
			}
		},
		{
			title: '7 / 13  ·  산업 버블 클릭 = 내부 보기',
			body: [
				'산업 지도에서 **버블을 클릭하면 그 산업 안으로 드릴다운** 됩니다.',
				'예시로 반도체 산업을 열어 보겠습니다. 공정별(설계 / FAB / 패키징 / 장비 / 소재) 로 회사가 자동 클러스터링되고, 공급망 엣지가 함께 표시됩니다.',
				'버튼 누른 뒤 **왼쪽 사이드바의 공정 토글** 로 원하는 공정만 필터할 수 있고, **마우스 휠**로 줌, **드래그**로 팬 됩니다.'
			],
			why: '한 산업 안의 "누가 공급하고 누가 받는가" 밸류체인 관계가 가장 명확히 보이는 뷰.',
			demo: {
				label: '▶ 반도체 산업 내부 진입',
				run: async () => {
					await enterIndustryAction('semiconductor');
				}
			}
		},
		{
			title: '8 / 13  ·  회사 클릭 = 우측 카드 펼침',
			body: [
				'**회사 노드를 클릭하면 우측 패널이 열립니다.** 삼성전자를 자동 선택해서 실제 카드를 보여드리겠습니다.',
				'카드는 **6 섹션** 구조:\n**① 재무 한눈에** · 매출 · 영업이익 · 순이익 · 총자산 (최신년)\n**② 5년 추이 sparkline** · 3 라인(매출/영업이익/순이익) 한 그림으로\n**③ 재무 스코어** · ROE · 영업이익률 · 부채비율 · CAGR + 산업 내 분위(%)\n**④ 공급망 구조** · HHI 집중도 게이지 · Top1/3 의존도 · 상위 공급 산업 막대\n**⑤ 핵심 거래 Top 5** · 금액 기준 정밀 공급사/고객사 (예: "삼성디스플레이 ← 코닝 8조")\n**⑥ AI 분석 + 블로그** · dartlab AI 서술 + 강점/약점 칩 + 심층 분석 글',
				'블로그 포스트가 있는 회사는 **카드 맨 위에 파란 배너**로 강조됩니다.'
			],
			why: '회사 하나의 "정체성 + 수익성 + 공급망 + 정성 분석" 을 한 카드에 통합 · /company 같은 별도 페이지 안 만듭니다.',
			demo: {
				label: '▶ 삼성전자 카드 펼치기',
				run: async () => {
					await selectCompanyAction('005930');
				}
			}
		},
		{
			title: '9 / 13  ·  체력 진단 레이더 + peer 분위',
			body: [
				'카드에 **5축 레이더 차트**가 있습니다 · 수익성/성장/안정성/품질/지배구조를 한눈에.',
				'**빨강 영역** = 이 회사, **회색 영역** = 업종 중앙값. 빨강이 회색 밖으로 나가면 업종 평균 초과.',
				'재무 스코어의 **"산업 내 분위" 배지**와 함께 보면 · 절대값이 아닌 peer 대비 위치가 보입니다.',
				'ROE 10%가 유통업에선 우량, 바이오에선 평범인 이유가 여기서 명확해집니다.'
			],
			why: '레이더 + 분위로 "이 회사의 체력"을 업종 맥락에서 즉시 판단.'
		},
		{
			title: '10 / 13  ·  비교 · 우측 패널 2분할',
			body: [
				'한 회사 카드 하단 **"+ 비교에 추가"** 를 누르고 다음 회사를 클릭하면 우측 패널이 **760px 폭 2분할**로 확장됩니다.',
				'지금 SK하이닉스를 자동으로 추가해서 삼성전자 vs SK하이닉스 비교를 보여드립니다.',
				'비교 모드에서 양쪽의 **같은 행(재무/공급망/AI)** 이 나란히 있으므로, 공통 공급사·고객사가 자연스럽게 드러납니다.',
				'별도 `/compare` 페이지 안 만들고 이 패널에서 끝 · URL `?compare=A,B` 로 공유도 가능합니다.'
			],
			why: '"비교" 는 이 도구의 핵심 사용법. 두 회사의 차이가 즉시 눈에 들어옵니다.',
			demo: {
				label: '▶ SK하이닉스 비교 추가',
				run: async () => {
					await addCompareAction('000660');
				}
			}
		},
		{
			title: '11 / 13  ·  심층 탭 · 잠자는 데이터를 깨우다',
			body: [
				'회사 카드 상단에 **[요약] [심층]** 탭이 있습니다.',
				'**요약 탭**: 재무 + sparkline + 레이더 + 공급망 + AI · 지금까지 본 내용.',
				'**심층 탭**: 아코디언으로 지배구조, 인력, 현금흐름 패턴, 감사 리스크, 이익의 질, 유동성, 주주환원, 신용등급, 업종 내 위치 · scan 엔진의 횡단 지표를 전부 여기서 볼 수 있습니다.',
				'각 아코디언을 펼치면 상세 지표가 나옵니다.'
			],
			why: 'scan의 횡단 지표, credit의 독립 신용평가, macro의 거시 맥락이 이 하나의 탭에 모두 연결됩니다.'
		},
		{
			title: '12 / 13  ·  블로그 + 공유',
			body: [
				'지금 본 상태를 URL 로 공유 가능합니다.',
				'• `/map?focus=005930` · 페이지 열자마자 삼성전자 카드 펼쳐짐\n• `/map?compare=005930,000660` · 비교 모드 진입\n• `/map` 기본 URL · 투어 처음부터',
				'블로그 본문·SNS·슬랙에 바로 임베드하세요. 별도 페이지 없어도 모든 분석이 이 URL 하나로 표현됩니다.',
				'비교 상태는 곧 복잡해지니까, 뷰를 초기화하고 넘어가겠습니다.'
			],
			why: '"링크 하나로 분석 공유" · 이게 진짜 웹 네이티브 분석 도구의 모습.',
			demo: {
				label: '▶ 선택 해제 (뷰 초기화)',
				run: () => {
					clearSelectionAction();
				}
			}
		},
		{
			title: '13 / 13  ·  끝 · 이제 직접 탐험해보세요',
			body: [
				'**투어 끝났습니다.** ? 버튼으로 언제든 재시작 가능합니다.',
				'가장 빠르게 쓰는 법 (4가지 습관):\n\n**1. 히트맵(T)으로 시장 전체 스캔** · 3초에 시장 파악.\n**2. 색상 기준 먼저 바꿔 보세요** · ROE / 성장률 / 부채 중 질문에 맞게.\n**3. 업종 버블 클릭 → 체력 카드 → 드릴다운** · 거시에서 미시로.\n**4. 회사 카드 심층 탭** · scan의 횡단 지표가 여기에.',
				'잘못된 산업 분류나 엣지를 발견하면 회사 카드 하단 **"신고"** 로 GitHub Issue 즉시 제출해주세요.',
				'이 지도 만든 사람에게 후원하고 싶으면 커피 아이콘 클릭 · 반갑습니다.'
			],
			why: '툴은 만들었고, 인사이트는 당신이 찾아내는 겁니다.'
		}
	];

	function position() {
		const step = STEPS[stepIdx];
		if (!step?.selector) {
			highlight = null;
			return;
		}
		const el = document.querySelector(step.selector);
		if (!el) {
			highlight = null;
			return;
		}
		const r = (el as HTMLElement).getBoundingClientRect();
		highlight = { x: r.left - 6, y: r.top - 6, w: r.width + 12, h: r.height + 12 };
	}

	$effect(() => {
		if (open) {
			void stepIdx;
			requestAnimationFrame(() => {
				position();
			});
		}
	});

	onMount(() => {
		const ro = new ResizeObserver(() => open && position());
		ro.observe(document.body);
		const onScroll = () => open && position();
		window.addEventListener('scroll', onScroll, true);
		return () => {
			ro.disconnect();
			window.removeEventListener('scroll', onScroll, true);
		};
	});

	function maxStep(): number {
		return fullMode ? STEPS.length - 1 : QUICK_COUNT - 1;
	}
	function next() {
		if (stepIdx < maxStep()) stepIdx += 1;
		else if (!fullMode) {
			// 퀵투어 끝 → "더 알아보기" 선택지 (finish 에서 처리)
			finish();
		} else {
			finish();
		}
	}
	function expandToFull() {
		fullMode = true;
		// 3스텝 끝에서 4스텝으로 이어서 진행
		stepIdx = QUICK_COUNT;
	}
	function prev() {
		if (stepIdx > 0) stepIdx -= 1;
	}
	function finish() {
		try {
			localStorage.setItem('dartlab.map.tour.done', '1');
		} catch {
			/* noop */
		}
		stepIdx = 0;
		fullMode = false;
		onClose();
	}
	function skip() {
		finish();
	}

	async function runDemo() {
		const d = STEPS[stepIdx].demo;
		if (!d) return;
		await d.run();
		await new Promise((r) => setTimeout(r, 200));
		position();
	}

	function handleKey(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape') skip();
		else if (e.key === 'ArrowRight' || e.key === 'Enter') next();
		else if (e.key === 'ArrowLeft') prev();
	}

	const POP_W = 640;
	let popStyle = $derived.by(() => {
		if (!highlight) {
			return 'top:50%;left:50%;transform:translate(-50%,-50%);';
		}
		const vw = typeof window !== 'undefined' ? window.innerWidth : 1200;
		const vh = typeof window !== 'undefined' ? window.innerHeight : 800;
		if (highlight.x + highlight.w + POP_W + 24 < vw) {
			return `top:${Math.min(vh - 360, Math.max(16, highlight.y))}px;left:${highlight.x + highlight.w + 16}px;`;
		}
		const leftPos = Math.max(16, Math.min(highlight.x, vw - POP_W - 16));
		return `top:${Math.min(vh - 360, highlight.y + highlight.h + 16)}px;left:${leftPos}px;`;
	});

	function renderBody(body: string[]): string {
		// simple inline format: **bold** -> <strong>, \n -> <br>
		return body
			.map((p) =>
				p
					.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
					.replace(/\n/g, '<br />')
			)
			.map((p) => `<p>${p}</p>`)
			.join('');
	}
</script>

<svelte:window onkeydown={handleKey} />

{#if open}
	<div class="tour-root" role="dialog" aria-modal="true" aria-label="가이드 투어">
		<svg class="mask-svg" xmlns="http://www.w3.org/2000/svg">
			<defs>
				<mask id="tour-mask">
					<rect width="100%" height="100%" fill="white" />
					{#if highlight}
						<rect
							x={highlight.x}
							y={highlight.y}
							width={highlight.w}
							height={highlight.h}
							rx="10"
							fill="black"
						/>
					{/if}
				</mask>
			</defs>
			<rect width="100%" height="100%" fill="rgba(5,8,17,0.82)" mask="url(#tour-mask)" />
			{#if highlight}
				<rect
					x={highlight.x}
					y={highlight.y}
					width={highlight.w}
					height={highlight.h}
					rx="10"
					fill="none"
					stroke="#60a5fa"
					stroke-width="2.5"
				/>
			{/if}
		</svg>

		<div class="popover" style={popStyle}>
			<div class="header-row">
				<div class="step-idx">STEP {stepIdx + 1} / {maxStep() + 1}{#if !fullMode} (퀵투어){/if}</div>
				<button class="skip" onclick={skip} title="튜토리얼 건너뛰기">건너뛰기</button>
			</div>

			<h3>{STEPS[stepIdx].title}</h3>

			<div class="body">
				{@html renderBody(STEPS[stepIdx].body)}
			</div>

			{#if STEPS[stepIdx].why}
				<div class="why">
					<span class="why-label">💡 왜 유용한가</span>
					<span>{STEPS[stepIdx].why}</span>
				</div>
			{/if}

			{#if STEPS[stepIdx].demo}
				<button class="demo-btn" onclick={runDemo}>
					{STEPS[stepIdx].demo!.label}
				</button>
			{/if}

			<div class="actions">
				<div class="nav">
					{#if stepIdx > 0}
						<button class="ghost" onclick={prev}>← 이전</button>
					{:else}
						<span class="nav-placeholder"></span>
					{/if}
					{#if !fullMode && stepIdx === QUICK_COUNT - 1}
						<!-- 퀵투어 마지막 → 풀투어 선택 -->
						<button class="ghost" onclick={finish}>여기서 끝내기</button>
						<button class="primary" onclick={expandToFull}>더 알아보기 ({STEPS.length - QUICK_COUNT}스텝) →</button>
					{:else if stepIdx < maxStep()}
						<button class="primary" onclick={next}>다음 →</button>
					{:else}
						<button class="primary" onclick={finish}>완료</button>
					{/if}
				</div>
			</div>

			<div class="progress">
				<div class="progress-fill" style:width="{((stepIdx + 1) / (maxStep() + 1)) * 100}%"></div>
			</div>
		</div>
	</div>
{/if}

<style>
	.tour-root {
		position: fixed;
		inset: 0;
		z-index: 110;
		pointer-events: none;
	}
	.mask-svg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: auto;
	}
	.popover {
		position: absolute;
		width: 640px;
		max-height: calc(100vh - 32px);
		overflow-y: auto;
		background: #0f1219;
		border: 1px solid #334155;
		border-radius: 12px;
		padding: 24px 28px 18px;
		color: #f1f5f9;
		box-shadow: 0 20px 48px rgba(0, 0, 0, 0.6);
		pointer-events: auto;
	}
	@media (max-width: 640px) {
		.popover {
			width: 100vw;
			max-height: 60vh;
			position: fixed;
			bottom: 0;
			left: 0;
			top: auto !important;
			border-radius: 16px 16px 0 0;
			transform: none !important;
		}
	}
	.header-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
	}
	.step-idx {
		font-size: 10px;
		color: #60a5fa;
		font-family: monospace;
		font-weight: 700;
		letter-spacing: 0.08em;
	}
	.skip {
		background: none;
		border: none;
		color: #64748b;
		font-size: 11px;
		cursor: pointer;
		padding: 4px 8px;
		border-radius: 4px;
	}
	.skip:hover {
		color: #cbd5e1;
		background: #1e2433;
	}
	.popover h3 {
		margin: 0 0 12px;
		font-size: 22px;
		font-weight: 700;
		color: #f1f5f9;
		line-height: 1.4;
	}
	.body {
		font-size: 16px;
		line-height: 1.75;
		color: #cbd5e1;
	}
	.body :global(p) {
		margin: 0 0 10px;
	}
	.body :global(p:last-child) {
		margin-bottom: 0;
	}
	.body :global(strong) {
		color: #f1f5f9;
		font-weight: 600;
	}
	.why {
		margin-top: 14px;
		padding: 10px 12px;
		background: linear-gradient(135deg, rgba(96, 165, 250, 0.1), rgba(52, 211, 153, 0.06));
		border: 1px solid rgba(96, 165, 250, 0.25);
		border-radius: 8px;
		font-size: 14px;
		line-height: 1.6;
		color: #cbd5e1;
	}
	.why-label {
		display: inline-block;
		color: #60a5fa;
		font-weight: 600;
		margin-right: 6px;
	}
	.demo-btn {
		margin-top: 14px;
		width: 100%;
		padding: 12px 16px;
		background: linear-gradient(135deg, rgba(96, 165, 250, 0.22), rgba(52, 211, 153, 0.15));
		border: 1px solid rgba(96, 165, 250, 0.5);
		border-radius: 8px;
		color: #93c5fd;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.15s;
	}
	.demo-btn:hover {
		background: linear-gradient(135deg, rgba(96, 165, 250, 0.38), rgba(52, 211, 153, 0.25));
		color: #f1f5f9;
		border-color: #60a5fa;
		transform: translateY(-1px);
	}
	.actions {
		margin-top: 16px;
	}
	.nav {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 8px;
	}
	.nav-placeholder {
		flex: 1;
	}
	.actions button {
		font-size: 13px;
		padding: 8px 16px;
		border-radius: 6px;
		cursor: pointer;
	}
	.actions .ghost {
		background: none;
		border: 1px solid #334155;
		color: #cbd5e1;
	}
	.actions .ghost:hover {
		background: #1e2433;
		color: #f1f5f9;
	}
	.actions .primary {
		background: #60a5fa;
		color: #050811;
		font-weight: 600;
		border: 1px solid #60a5fa;
		margin-left: auto;
	}
	.actions .primary:hover {
		background: #93c5fd;
	}
	.progress {
		margin-top: 14px;
		height: 4px;
		background: #1e2433;
		border-radius: 2px;
		overflow: hidden;
	}
	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #60a5fa, #34d399);
		transition: width 0.3s;
	}
</style>
