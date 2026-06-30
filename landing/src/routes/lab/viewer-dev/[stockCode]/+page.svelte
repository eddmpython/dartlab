<script lang="ts">
	// 공시뷰어 · panel 하나로 브라우저 readWide → TOC + 항목×기간 격자 + 타임라인 + 원본 링크.
	// 디자인 = scan 방식(flat #050811 · #1e2433 보더 · 오렌지 단일 액센트). 풀블리드(좌우 패딩 0 · 갭 0).
	import { onMount, untrack } from 'svelte';
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { Maximize2, Minimize2, Columns3, MessageSquare, Bug, Table2, X, Plus, Search, Download } from 'lucide-svelte';
	import { brand } from '$lib/brand';
	import Header from '$lib/components/sections/Header.svelte';
	import AskDrawer from '$lib/viewer/dev/AskDrawer.svelte';
	import { hfUrl } from '@dartlab/ui-runtime/data/parquet/hfRange';
	import {
		loadPanelBundle,
		PanelTocTree,
		PanelMatrix,
		ComparisonMatrix,
		TimelineRibbon,
		CommandPalette,
		CompanySearch,
		GiscusPanel,
		FinanceDialog,
		executeAction,
		type ViewerAction,
		type ViewerApi,
		loadCompanies,
		buildIndexChunked,
		type SearchIndex,
		type SearchHit,
		buildCompareBoard,
		commonPeriods,
		type PanelBundle,
		marketForCode,
		panelToCsv,
		financeToExcel,
		downloadText,
		loadFinanceStatement,
		KIND_LABELS,
		type FinanceKind,
		type FinanceStatement
	} from '@dartlab/ui-surfaces/viewer';

	let { data }: { data: { code: string; vs?: string[]; vsRejected?: Array<{ code: string; reason: string }> } } = $props();
	const code = $derived(data.code);
	const vsCodes = $derived(data.vs ?? []);

	// 회사명 · panel 엔 없음 → ecosystem(code→name) 해석. corp(panel) 우선, 없으면 ecosystem.
	let nameMap = $state<Map<string, string>>(new Map());
	onMount(() => {
		void loadCompanies().then((l) => (nameMap = new Map(l.map((c) => [c.code, c.name]))));
		try {
			if (localStorage.getItem('dartlab:cmpHint') === 'done') cmpHintDismissed = true;
		} catch {
			/* localStorage 불가 무시 */
		}
		// D3 · 모바일(≤880px)은 동시표시 기간 1개가 기본(390px 에 260px 셀 3개 강제 가로스크롤 회피).
		// 데스크톱은 cols=3 그대로(이 분기는 mount 시 1회·좁은 화면에서만). 이후 사용자 cols 토글은 자유.
		if (typeof window !== 'undefined' && window.matchMedia('(max-width: 880px)').matches) cols = 1;
	});

	const COL_CHOICES = [3, 6, 9] as const;

	let bundle = $state<PanelBundle | null>(null);
	let errorMsg = $state<string | null>(null);
	let loading = $state(true);
	let swapping = $state(false); // 회사 전환 중 · 옛 화면 유지 + 미세 인디케이터(soft swap, 전체화면 스피너 회피)
	let activeSectionKey = $state<string | undefined>(undefined);
	let activeBlock = $state<string | null>(null); // 활성 주석(blockLeaf) · null 이면 섹션 전체
	let windowEnd = $state(0); // periods 시작 인덱스 (0 = 최신, 좌측)
	let cols = $state(3);
	let isFullscreen = $state(false);
	let discussOpen = $state(false);
	let financeOpen = $state(false); // 정량재무제표 다이얼로그
	let askOpen = $state(false); // AI 공시 Q&A 드로어 (헤더 아바타 버튼 → 우측 push)
	let stockSearchOpen = $state(false); // 종목검색 팝오버 (화면내검색 ⌘K 와 분리된 회사전환 입력)
	let askCarryQ = $state(''); // AI 가 타 회사 감지 → 이동 후 새 회사 index 준비되면 운반·자동 ask 할 질문
	let annualOnly = $state(false); // 연간만(사업보고서) 필터 · period 축을 회사별 결산보정 annual 로 거름
	let searchIndex = $state<SearchIndex | null>(null);
	let indexing = $state(false);
	let glowCell = $state<{ rowIndex: number; period: string } | null>(null);

	// ── 회사 간 비교 (?vs=) ── 단일 뷰어 위에 additive. vs 없으면 전부 비활성.
	let vsBundles = $state<PanelBundle[]>([]); // 비교 추가 회사 bundle (reference=bundle, 나머지=여기)
	let vsLoading = $state(false);
	let vsFailed = $state(0);
	let lockedPeriod = $state(''); // 비교 모드 = 한 시점 lock
	let addOpen = $state(false); // 회사 추가 팝오버
	let cmpHintDismissed = $state(false); // 비교 모드 안내 띠 · 한 번 닫으면 localStorage 로 다시 안 뜸
	// 비교 모드 판정 · 파생을 일찍 선언(windowPeriods 등이 참조). vsCodes/bundle/vsBundles 에만 의존.
	const compareMode = $derived(vsCodes.length > 0);
	function dismissCmpHint() {
		cmpHintDismissed = true;
		try {
			localStorage.setItem('dartlab:cmpHint', 'done');
		} catch {
			/* localStorage 불가 무시 */
		}
	}
	const allBundles = $derived(bundle ? [bundle, ...vsBundles] : []);

	// code 바뀌면(검색 이동) 재로드 · soft swap. 첫 로드만 전체화면 스피너, 회사 전환은 옛 화면을 유지한 채
	// 새 번들을 백그라운드 로드 후 준비되면 교체(studio·AskDrawer 언마운트 0 → 깜빡임 없는 매끄러운 전환).
	$effect(() => {
		const c = code;
		try {
			localStorage.setItem('dartlab:lastViewer', c); // 마지막 본 종목 캐시 (재방문 시 /viewer 가 복원)
		} catch {
			/* localStorage 불가 무시 */
		}
		errorMsg = null;
		// 첫 로드(bundle 없음)=전체화면 로딩 / 회사 전환(bundle 있음)=미세 swap 인디케이터. untrack 으로 bundle 을
		// effect 의존성에서 제외(여기서 bundle 을 set 하므로 그냥 읽으면 자기재발화).
		if (untrack(() => bundle) === null) loading = true;
		else swapping = true;
		let cancelled = false;
		loadPanelBundle(c)
			.then((b) => {
				if (cancelled) return; // 빠른 연속 전환 · 옛 응답이 새 회사를 덮어쓰지 않게
				bundle = b; // 새 회사 화면으로 교체(리셋도 이 시점에만 → 전환 중 옛 화면 안정)
				windowEnd = 0;
				activeBlock = null;
				activeSectionKey = b.toc.chapters[0]?.sections[0]?.sectionKey;
				if (!b.periods.length) errorMsg = '이 종목의 panel 데이터가 없습니다 (HF 업로드 대기 중일 수 있음).';
			})
			.catch((e) => {
				if (cancelled) return;
				errorMsg = `로드 실패: ${e instanceof Error ? e.message : String(e)}`;
			})
			.finally(() => {
				if (cancelled) return;
				loading = false;
				swapping = false;
			});
		return () => {
			cancelled = true;
		};
	});

	// 본문 검색 색인 · bundle 로드 후 타임슬라이싱 빌드(메인스레드 비차단). code 바뀌면 재빌드.
	$effect(() => {
		const b = bundle;
		searchIndex = null;
		if (!b || !b.periods.length) {
			indexing = false;
			return;
		}
		indexing = true;
		let cancelled = false;
		void buildIndexChunked(b).then((idx) => {
			if (!cancelled) {
				searchIndex = idx;
				indexing = false;
			}
		});
		return () => {
			cancelled = true;
		};
	});

	// 비교 회사(?vs) 병렬 로드 · allSettled(한 회사 실패해도 나머지 비교). code/vs 바뀌면 재로드.
	$effect(() => {
		const codes = vsCodes;
		void code; // code 바뀌면도 재로드(reference 교체)
		if (!codes.length) {
			vsBundles = [];
			vsLoading = false;
			vsFailed = 0;
			return;
		}
		let cancelled = false;
		vsLoading = true;
		vsFailed = 0;
		void Promise.allSettled(codes.map((c) => loadPanelBundle(c))).then((results) => {
			if (cancelled) return;
			vsBundles = results
				.filter((r): r is PromiseFulfilledResult<PanelBundle> => r.status === 'fulfilled' && r.value.periods.length > 0)
				.map((r) => r.value);
			vsFailed = results.length - vsBundles.length;
			vsLoading = false;
		});
		return () => {
			cancelled = true;
		};
	});

	// 검색 결과 클릭 → 그 섹션·기간으로 격자 점프 + 셀 글로우. 매번 새 객체로 설정해 PanelMatrix 가 재트리거하고
	// 강조 수명(스크롤 도착 후 dwell)을 직접 소유한다 · 여기서 클리어 타이머를 돌리면 먼 스크롤 중 강조가 꺼진다.
	function onSearchResult(hit: SearchHit) {
		pickSection(hit.sectionKey);
		pickPeriod(hit.period);
		glowCell = { rowIndex: hit.rowIndex, period: hit.period };
	}

	// 종목검색 · 다른 회사 공시뷰어로 이동(단일). 대화는 askSession 스토어로 유지된다(수동 이동도 동행).
	// askCarryQ 비움 = 수동 이동엔 자동질문 없음(직전 AI 이동의 묵은 carryQ 재발화 차단).
	function onStockPick(c: string) {
		stockSearchOpen = false;
		askCarryQ = '';
		if (c && c !== code) void goto(`${base}/lab/viewer-dev/${c}`);
	}

	// AI 가 질문에서 타 회사 감지 → 자동 이동. 단일 뷰어로 goto 후 *완료된 뒤* 원질문 운반(carryQ).
	// ★goto 전에 askCarryQ 를 set 하면 옛 회사 mount 의 carryQ effect 가 먼저 발화해 옛 회사 데이터로
	// 답하고 consumedCarry 를 소비 → 새 회사 mount 가 skip(삼성 데이터로 하이닉스 답하는 race). goto 완료
	// 후 set 해야 새 회사 mount 만 픽업한다. 대화는 askSession 스토어로 유지(언마운트 무관).
	async function onAskNavigate(targetCode: string, carryQuestion: string) {
		if (!targetCode || targetCode === code) return;
		await goto(`${base}/lab/viewer-dev/${targetCode}`);
		askCarryQ = carryQuestion;
	}

	// 전체보기 Esc 해제.
	$effect(() => {
		if (!isFullscreen) return;
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') isFullscreen = false;
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});

	const periods = $derived(bundle?.periods ?? []);
	// "연간만" 필터 시 사업보고서(annual) period 만 · 빈 결과면 자동으로 전체로 폴백(빈 화면 방지).
	const annualPeriods = $derived.by(() => {
		const b = bundle;
		return b ? periods.filter((p) => b.periodKind[p] === 'annual') : [];
	});
	const visiblePeriods = $derived(annualOnly && annualPeriods.length ? annualPeriods : periods);
	// 비교 모드 = 한 시점만 강조(타임라인은 시점 선택기). 단일 모드 = 기존 윈도.
	const windowPeriods = $derived(
		compareMode ? (lockedPeriod ? [lockedPeriod] : []) : visiblePeriods.slice(windowEnd, windowEnd + cols)
	);
	// 활성 섹션 행 · 주석(blockLeaf) 선택 시 그 주석만(기간별), 아니면 섹션 전체.
	const rows = $derived.by(() => {
		if (!activeSectionKey || !bundle) return [];
		const base = bundle.gridBySection.get(activeSectionKey) ?? [];
		return activeBlock ? base.filter((r) => r.blockLeaf === activeBlock) : base;
	});
	const dartUrls = $derived(bundle?.dartUrlByPeriod ?? {});
	const sectionLabel = $derived.by(() => {
		const s = activeSectionKey?.split('␟').pop() ?? '';
		return activeBlock ? `${s} · ${activeBlock}` : s;
	});
	const corpName = $derived(bundle?.corpName || nameMap.get(code) || '');

	// ── 데이터 다운로드 (공개 HF 데이터셋) ── 보고 있는 회사의 panel·재무 parquet 직접 받기 + 전체 데이터셋.
	const dlMarket = $derived(marketForCode(code));
	const panelDlUrl = $derived(hfUrl(`${dlMarket === 'US' ? 'edgar' : 'dart'}/panel/${code}.parquet`));
	const financeDlUrl = $derived(hfUrl(`dart/finance/${code}.parquet`));
	const DATASET_URL = 'https://huggingface.co/datasets/eddmpython/dartlab-data';

	// 일반인용 다운로드 · 브라우저에 로드된 데이터를 CSV/Excel 로(서버 0). 공시 수평화표=CSV, 재무제표=Excel(멀티시트).
	let financeDownloading = $state(false);
	function downloadPanelCsv() {
		if (bundle) downloadText(panelToCsv(bundle), `${corpName || code}_공시수평화.csv`, 'text/csv;charset=utf-8');
	}
	async function downloadFinanceExcel() {
		if (financeDownloading) return;
		financeDownloading = true;
		try {
			const sheets: Array<{ name: string; statement: FinanceStatement }> = [];
			for (const k of ['IS', 'BS', 'CF', 'CIS'] as FinanceKind[]) {
				const st = await loadFinanceStatement(code, dlMarket, k, 'annual', 'CFS');
				if (st && st.rows.length) sheets.push({ name: KIND_LABELS[k], statement: st });
			}
			if (sheets.length) downloadText(financeToExcel(sheets), `${corpName || code}_재무제표_연간연결.xls`, 'application/vnd.ms-excel');
		} finally {
			financeDownloading = false;
		}
	}

	// ── 비교 모드 파생 (compareMode·allBundles 는 위에서 선언) ──
	const cmpCompanies = $derived(
		allBundles.map((b) => ({ code: b.stockCode, corpName: b.corpName || nameMap.get(b.stockCode) || b.stockCode }))
	);
	// compare 본진은 $lib/viewer/compare. route 는 section/period/bundle 만 넘기고 정렬 계약은 모듈이 담당.
	const compareBoard = $derived(
		compareMode && activeSectionKey && lockedPeriod && allBundles.length >= 2
			? buildCompareBoard(allBundles, { sectionKey: activeSectionKey, period: lockedPeriod, block: activeBlock })
			: null
	);
	const compareMeta = $derived(
		compareBoard ? `항목 ${compareBoard.diagnostics.rowCount}` : vsLoading ? '비교 회사 로드 중' : '비교 대기'
	);
	// 비교 시점 기본 = 최신 공통 기간. 유효하지 않으면 보정.
	$effect(() => {
		if (!compareMode || allBundles.length < 2) return;
		const cp = commonPeriods(allBundles);
		if (!lockedPeriod || !cp.includes(lockedPeriod)) lockedPeriod = cp[0] ?? '';
	});

	// ── 비교 회사 추가/제거 (URL ?vs=) ──
	function vsUrl(codes: string[]): string {
		const q = codes.filter((c) => c && c !== code).join(',');
		return `${base}/lab/viewer-dev/${code}${q ? `?vs=${q}` : ''}`;
	}
	function addCompany(c: string) {
		if (!c || c === code || vsCodes.includes(c) || allBundles.length >= 6) return;
		addOpen = false;
		void goto(vsUrl([...vsCodes, c]));
	}
	function removeCompany(c: string) {
		void goto(vsUrl(vsCodes.filter((x) => x !== c)));
	}

	// 섹션/주석 이동은 보고 있던 기간 윈도우를 보존 · 기간축은 섹션 무관 글로벌이라 리셋할 이유 없음(같은 시점의
	// 다른 TOC 를 보려는 흐름). 리셋은 축 변경(연간토글)·회사 변경 때만.
	function pickSection(sectionKey: string) {
		activeSectionKey = sectionKey;
		activeBlock = null; // 섹션 헤더 클릭 = 전체
	}
	function pickBlock(sectionKey: string, blockLeaf: string) {
		activeSectionKey = sectionKey;
		activeBlock = blockLeaf; // 개별 주석 선택 = 그 주석만
	}
	function pickPeriod(p: string) {
		if (compareMode) {
			lockedPeriod = p; // 비교 = 시점 lock (N사 동시 그 시점)
			return;
		}
		const idx = visiblePeriods.indexOf(p);
		if (idx >= 0) windowEnd = idx;
	}
	function moveNewer() {
		if (compareMode) {
			const i = visiblePeriods.indexOf(lockedPeriod);
			if (i > 0) lockedPeriod = visiblePeriods[i - 1];
			return;
		}
		windowEnd = Math.max(0, windowEnd - 1);
	}
	function moveOlder() {
		if (compareMode) {
			const i = visiblePeriods.indexOf(lockedPeriod);
			if (i >= 0 && i + 1 < visiblePeriods.length) lockedPeriod = visiblePeriods[i + 1];
			return;
		}
		windowEnd = Math.min(visiblePeriods.length - 1, windowEnd + 1);
	}
	function toggleAnnual() {
		annualOnly = !annualOnly;
		windowEnd = 0; // 축이 바뀌므로 최신으로 리셋
	}

	// 액션 버스 호스트 · 기존 mutator + 라이브 검증 게터를 ViewerApi 로 묶어 executeAction 에 주입.
	function setCols(n: 3 | 6 | 9) {
		cols = n;
	}
	function openFinance() {
		financeOpen = true;
	}
	function closeFinance() {
		financeOpen = false;
	}
	const viewerApi: ViewerApi = {
		navigateCompany: onAskNavigate,
		focusEvidence: onSearchResult,
		setSection: pickSection,
		setBlock: pickBlock,
		setPeriod: pickPeriod,
		moveNewer,
		moveOlder,
		setCols,
		toggleAnnual,
		openFinance,
		closeFinance,
		addCompare: addCompany,
		removeCompare: removeCompany,
		hasSection: (k) => !!bundle?.gridBySection.has(k),
		hasPeriod: (p) => visiblePeriods.includes(p),
		knownCode: (c) => c !== code && nameMap.has(c)
	};
	const onAction = (a: ViewerAction) => {
		executeAction(a, viewerApi);
	};
	const lockedIdx = $derived(visiblePeriods.indexOf(lockedPeriod));
	const canNewer = $derived(compareMode ? lockedIdx > 0 : windowEnd > 0);
	const canOlder = $derived(compareMode ? lockedIdx >= 0 && lockedIdx + 1 < visiblePeriods.length : windowEnd + 1 < visiblePeriods.length);
</script>

<svelte:head><title>{corpName || code} 공시뷰어 (dev) · dartlab</title><meta name="robots" content="noindex" /></svelte:head>

{#if !isFullscreen}
	<Header context="landing" />
{/if}

<main class="viewer-page" class:fullscreen={isFullscreen}>
	<header class="page-head">
		{#if swapping}<div class="swap-bar" aria-hidden="true"></div>{/if}
		<div class="ph-left">
			{#if compareMode}
				<div class="chips">
					{#each cmpCompanies as c (c.code)}
						<span class="chip" class:ref={c.code === code}>
							<span class="chip-name">{c.corpName}</span>
							{#if c.code !== code}
								<button type="button" class="chip-x" onclick={() => removeCompany(c.code)} title="비교에서 제거"><X size={10} /></button>
							{/if}
						</span>
					{/each}
				</div>
				{#if sectionLabel}<span class="ph-section">{sectionLabel}</span>{/if}
			{:else}
				<h1 class="ph-corp">{corpName || code}</h1>
				<span class="ph-code">{code}</span>
				{#if bundle && sectionLabel}<span class="ph-section">{sectionLabel}</span>{/if}
			{/if}
		</div>
		<div class="ph-right">
			<div class="stock-wrap">
				<button type="button" class="fs-btn" class:active={stockSearchOpen} onclick={() => (stockSearchOpen = !stockSearchOpen)} title="종목검색 · 다른 회사 공시뷰어로 이동">
					<Search size={13} /> 종목검색
				</button>
				{#if stockSearchOpen}
					<div class="stock-pop"><CompanySearch onpick={onStockPick} /></div>
				{/if}
			</div>
			<CommandPalette index={searchIndex} toc={bundle?.toc ?? null} {indexing} onResult={onSearchResult} onSection={pickSection} />
			<button type="button" class="fs-btn ask-trigger" class:active={askOpen} onclick={() => (askOpen = !askOpen)} title="AI 공시 Q&A · 근거 검색 + 즉시 답(다운로드 0)">
				<picture><source srcset="{base}/avatar-detective.webp" type="image/webp" /><img class="ask-ava" src="{base}/avatar-detective.png" alt="" width="16" height="16" /></picture> AI
			</button>
			<button type="button" class="fs-btn" onclick={() => (financeOpen = true)} title="재무제표 정량 (IS/BS/CF/CIS/자본변동 · 연결/별도)">
				<Table2 size={13} /> 재무제표(정량)
			</button>
			<div class="data-dl">
				<button type="button" class="fs-btn"><Download size={13} /> 데이터</button>
				<div class="data-pop">
					<div class="dp-h">이 회사 데이터 · 공개 다운로드</div>
					<div class="dp-sub">보기 쉬운 형식 · Excel · Sheets · 메모장</div>
					<button type="button" class="dp-link dp-btn" onclick={downloadPanelCsv} disabled={!bundle}>공시 수평화표 <span class="dp-ext">CSV</span></button>
					{#if dlMarket !== 'US'}
						<button type="button" class="dp-link dp-btn" onclick={downloadFinanceExcel} disabled={financeDownloading}>재무제표 (IS·BS·CF·CIS) <span class="dp-ext">{financeDownloading ? '생성 중…' : 'Excel'}</span></button>
					{/if}
					<div class="dp-sub">원본 · 개발자용 (parquet)</div>
					<a class="dp-link" href={panelDlUrl} download>공시 panel <span class="dp-ext">.parquet</span></a>
					{#if dlMarket !== 'US'}
						<a class="dp-link" href={financeDlUrl} download>재무제표 <span class="dp-ext">.parquet</span></a>
					{/if}
					<a class="dp-link dp-ds" href={DATASET_URL} target="_blank" rel="noreferrer">전체 데이터셋 (모든 회사) ↗</a>
					<div class="dp-policy">
						<div>원자료 <b>{dlMarket === 'US' ? 'SEC EDGAR' : 'DART 전자공시'}</b> · 가공·수평화 <b>dartlab</b> · 배포 HuggingFace 공개 데이터셋.</div>
						<div>{dlMarket === 'US' ? '미국 정부 저작물(퍼블릭 도메인)' : '공공데이터(공공데이터법)'} · 영리·비영리 <b>자유 이용·재배포 가능</b> · <b>출처 표기 권장</b>(DART/SEC · dartlab).</div>
						<div class="dp-warn">⚠ 데이터 정확성·완전성 미보증(원자료는 공시제출인 책임) · <b>투자 판단·자문이 아닙니다</b>.</div>
						<a class="dp-terms" href={dlMarket === 'US' ? 'https://www.sec.gov/os/accessing-edgar-data' : 'https://opendart.fss.or.kr/intro/terms.do'} target="_blank" rel="noreferrer">{dlMarket === 'US' ? 'SEC EDGAR 이용조건' : 'DART 이용약관'} ↗</a>
					</div>
				</div>
			</div>
			<button type="button" class="fs-btn" onclick={() => (discussOpen = true)} title="공시 토론 (GitHub Discussions)">
				<MessageSquare size={13} /> 토론
			</button>
			<a class="fs-btn" href="{brand.repo}/issues/new" target="_blank" rel="noopener" title="이슈 등록 · 버그·요청 (GitHub)">
				<Bug size={13} /> 이슈
			</a>
			{#if bundle}
				<div class="add-wrap">
					<button type="button" class="fs-btn" class:active={compareMode} onclick={() => (addOpen = !addOpen)} title="회사 간 비교 · 회사 추가 (최대 6)" disabled={allBundles.length >= 6}>
						<Plus size={13} /> 비교
					</button>
					{#if addOpen}
						<div class="add-pop">
							<p class="add-hint">
								추가한 회사를 <b>지금 보는 시점·항목 그대로</b> 나란히 비교합니다 (최대 6사).<br />
								<span class="add-eg">예: 삼성전자 + SK하이닉스 → 같은 재무상태표를 한 화면에</span>
							</p>
							<CompanySearch onpick={addCompany} />
						</div>
					{/if}
				</div>
				{#if compareMode}
					<span class="meta">{cmpCompanies.length}사 · {lockedPeriod} · {compareMeta}</span>
				{:else}
					<span class="meta">항목 {rows.length} · 기간 {visiblePeriods.length}{annualOnly ? '(연간)' : ''}</span>
				{/if}
				<button type="button" class="annual-btn" class:active={annualOnly} onclick={toggleAnnual} title="사업보고서(연간)만 표시 · 회사 결산월 보정">연간만</button>
				{#if !compareMode}
					<div class="cols" title="동시 표시 기간 수 (가로 폭)">
						<Columns3 size={13} />
						{#each COL_CHOICES as n (n)}
							<button type="button" class="col-btn" class:active={cols === n} onclick={() => (cols = n)}>{n}</button>
						{/each}
					</div>
				{/if}
				<button type="button" class="fs-btn" onclick={() => (isFullscreen = !isFullscreen)} title={isFullscreen ? '전체보기 해제 (Esc)' : '전체보기'}>
					{#if isFullscreen}<Minimize2 size={13} /> 복귀{:else}<Maximize2 size={13} /> 전체{/if}
				</button>
			{/if}
		</div>
	</header>

	{#if bundle && !loading}
		<div class="ribbon-bar">
			<TimelineRibbon periods={visiblePeriods} {windowPeriods} onpick={pickPeriod} onnewer={moveNewer} onolder={moveOlder} {canNewer} {canOlder} />
		</div>
	{/if}

	{#if compareMode && allBundles.length >= 2 && !cmpHintDismissed}
		<div class="cmp-hint">
			<span
				><b>비교 모드</b> · 같은 시점·같은 항목으로 회사를 나란히. 시점은 <b>상단 타임라인</b>, 항목은
				<b>좌측 TOC</b> 에서 고르고, 회사 빼기는 칩의 ✕</span
			>
			<button type="button" class="cmp-hint-x" onclick={dismissCmpHint} title="안내 닫기"><X size={12} /></button>
		</div>
	{/if}

	{#if loading}
		<div class="state">
			<picture>
				<source srcset="{base}/avatar-study.webp" type="image/webp" />
				<img class="state-avatar" src="{base}/avatar-study.png" alt="" width="72" height="72" />
			</picture>
			<div class="spinner"></div>
			<p>{corpName || code} 공시 본문을 여는 중</p>
		</div>
	{:else if errorMsg}
		<div class="state">
			<picture>
				<source srcset="{base}/avatar-curious.webp" type="image/webp" />
				<img class="state-avatar" src="{base}/avatar-curious.png" alt="" width="72" height="72" />
			</picture>
			<p>{errorMsg}</p>
		</div>
	{:else if bundle}
		<div class="studio" class:ask-open={askOpen} class:swapping>
			<aside class="toc">
				<PanelTocTree toc={bundle.toc} {activeSectionKey} {activeBlock} onpick={pickSection} onpickBlock={pickBlock} />
			</aside>
			<section class="board">
				{#if compareMode}
					{#if allBundles.length < 2}
						{#if vsLoading}
							<div class="cmp-loading"><div class="spinner"></div><p>비교 회사 여는 중…</p></div>
						{:else}
							<div class="cmp-loading"><p>비교 가능한 회사 데이터가 없습니다{vsFailed ? ` (${vsFailed}개 실패)` : ''}.</p></div>
						{/if}
					{:else}
						<ComparisonMatrix
							rows={compareBoard?.rows ?? []}
							companies={cmpCompanies}
							period={lockedPeriod}
						/>
					{/if}
				{:else}
					<PanelMatrix {rows} periods={windowPeriods} dartUrlByPeriod={dartUrls} glow={glowCell} />
				{/if}
			</section>
			{#if askOpen}
				<AskDrawer
					{code}
					{bundle}
					{searchIndex}
					{indexing}
					{corpName}
					carryQ={askCarryQ}
					{onAction}
					onclose={() => (askOpen = false)}
				/>
			{/if}
		</div>
	{/if}
</main>

<GiscusPanel {code} {corpName} open={discussOpen} onclose={() => (discussOpen = false)} />
<FinanceDialog {code} {corpName} open={financeOpen} onclose={() => (financeOpen = false)} />

<style>
	.viewer-page {
		height: 100vh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		background: #050811;
		color: #f1f5f9;
		padding: 56px 0 0;
	}
	.viewer-page.fullscreen {
		position: fixed;
		inset: 0;
		z-index: 100;
		padding: 0;
	}

	.page-head {
		position: relative;
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 8px 12px;
		border-bottom: 1px solid #1e2433;
	}
	/* 회사 전환 진행 바 · 헤더 하단에 얇게, 레이아웃 시프트 0(absolute overlay). */
	.swap-bar {
		position: absolute;
		left: 0;
		right: 0;
		bottom: -1px;
		height: 2px;
		overflow: hidden;
		background: rgba(var(--dl-accent-rgb), 0.12);
	}
	.swap-bar::before {
		content: '';
		position: absolute;
		top: 0;
		bottom: 0;
		width: 40%;
		background: var(--dl-accent);
		animation: swapslide 1s ease-in-out infinite;
	}
	@keyframes swapslide {
		0% {
			left: -40%;
		}
		100% {
			left: 100%;
		}
	}
	.ph-left {
		display: flex;
		align-items: baseline;
		gap: 8px;
		min-width: 0;
	}
	.ph-corp {
		margin: 0;
		font-size: 20px;
		font-weight: 800;
		letter-spacing: -0.02em;
		color: #f1f5f9;
		white-space: nowrap;
	}
	.ph-code {
		flex-shrink: 0;
		font-size: 11px;
		color: #64748b;
		font-family: monospace;
	}
	.ph-section {
		min-width: 0;
		font-size: 12px;
		color: #94a3b8;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.ph-section::before {
		content: '·';
		margin-right: 6px;
		color: #475569;
	}
	.ph-right {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-shrink: 0;
	}
	.meta {
		font-size: 11px;
		color: #94a3b8;
		white-space: nowrap;
	}
	.cols {
		display: inline-flex;
		align-items: center;
		gap: 2px;
		padding: 2px 4px 2px 6px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		color: #64748b;
	}
	.col-btn {
		padding: 2px 6px;
		border: none;
		border-radius: 4px;
		background: transparent;
		color: #94a3b8;
		font-family: monospace;
		font-size: 11px;
		cursor: pointer;
	}
	.col-btn:hover {
		color: #cbd5e1;
	}
	.col-btn.active {
		background: rgba(var(--dl-accent-rgb), 0.14);
		color: var(--dl-accent);
	}
	.fs-btn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		height: 30px;
		padding: 0 9px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: #050811;
		color: #94a3b8;
		font: inherit;
		font-size: 11px;
		cursor: pointer;
		white-space: nowrap;
	}
	.fs-btn:hover {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
	}
	.fs-btn.active {
		border-color: rgba(var(--dl-accent-rgb), 0.5);
		background: rgba(var(--dl-accent-rgb), 0.12);
		color: var(--dl-accent);
		font-weight: 600;
	}
	.fs-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	/* 데이터 다운로드 · 버튼 hover 시 팝오버(다운로드 링크 + 정책) */
	.data-dl {
		position: relative;
	}
	.data-pop {
		position: absolute;
		top: calc(100% + 6px);
		right: 0;
		z-index: 50;
		width: 320px;
		display: none;
		flex-direction: column;
		gap: 4px;
		padding: 10px;
		background: #0a0e18;
		border: 1px solid #263145;
		border-radius: 8px;
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
	}
	.data-dl:hover .data-pop,
	.data-dl:focus-within .data-pop {
		display: flex;
	}
	.dp-h {
		font-size: 10px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 2px;
	}
	.dp-link {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 5px 8px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		color: #e2e8f0;
		font-size: 12px;
		text-decoration: none;
	}
	.dp-link:hover {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
		background: rgba(var(--dl-accent-rgb), 0.06);
	}
	.dp-sub {
		margin-top: 4px;
		font-size: 9px;
		color: #475569;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.dp-btn {
		width: 100%;
		font: inherit;
		font-size: 12px;
		cursor: pointer;
		text-align: left;
		background: rgba(var(--dl-accent-rgb), 0.08);
		border-color: rgba(var(--dl-accent-rgb), 0.4);
		color: #f1f5f9;
	}
	.dp-btn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.dp-ext {
		font-size: 10px;
		color: #64748b;
	}
	.dp-ds {
		color: #cbd5e1;
	}
	.dp-policy {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-top: 4px;
		padding-top: 6px;
		border-top: 1px solid #1e2433;
		font-size: 10px;
		line-height: 1.5;
		color: #94a3b8;
	}
	.dp-policy b {
		color: #cbd5e1;
		font-weight: 600;
	}
	.dp-warn {
		color: #fbbf24;
	}
	.dp-warn b {
		color: #fbbf24;
	}
	.dp-terms {
		align-self: flex-start;
		color: var(--dl-accent);
		text-decoration: none;
	}
	.dp-terms:hover {
		text-decoration: underline;
	}

	/* 회사 간 비교 · 칩 + 추가 팝오버 */
	.chips {
		display: flex;
		align-items: center;
		gap: 5px;
		flex-wrap: wrap;
		min-width: 0;
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		height: 24px;
		padding: 0 4px 0 9px;
		border: 1px solid #1e2433;
		border-radius: 12px;
		background: #0a0e18;
		font-size: 12px;
		color: #cbd5e1;
		white-space: nowrap;
	}
	.chip.ref {
		border-color: rgba(var(--dl-accent-rgb), 0.5);
		background: rgba(var(--dl-accent-rgb), 0.1);
		color: #f8fafc;
		padding-right: 9px;
	}
	.chip-name {
		font-weight: 600;
		max-width: 130px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.chip-x {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		height: 16px;
		border: none;
		border-radius: 50%;
		background: transparent;
		color: #64748b;
		cursor: pointer;
		padding: 0;
	}
	.chip-x:hover {
		background: rgba(248, 113, 113, 0.15);
		color: #f87171;
	}
	.add-wrap {
		position: relative;
	}
	.add-pop {
		position: absolute;
		top: calc(100% + 6px);
		right: 0;
		z-index: 60;
	}
	.add-hint {
		max-width: 320px;
		margin: 0 0 8px;
		padding: 8px 10px;
		background: #0a0e18;
		border: 1px solid #263145;
		border-radius: 6px;
		font-size: 11px;
		line-height: 1.55;
		color: #cbd5e1;
	}
	.add-hint b {
		color: var(--dl-accent-light);
		font-weight: 700;
	}
	.add-eg {
		color: #64748b;
		font-size: 10px;
	}
	/* 종목검색 팝오버 · 화면내검색(⌘K)과 분리된 회사전환 입력 */
	.stock-wrap {
		position: relative;
	}
	.stock-pop {
		position: absolute;
		top: calc(100% + 6px);
		left: 0;
		z-index: 60;
	}
	.cmp-loading {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
		color: #94a3b8;
		font-size: 13px;
	}
	.annual-btn {
		height: 30px;
		padding: 0 10px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: #050811;
		color: #94a3b8;
		font: inherit;
		font-size: 11px;
		cursor: pointer;
		white-space: nowrap;
	}
	.annual-btn:hover {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
	}
	.annual-btn.active {
		border-color: rgba(var(--dl-accent-rgb), 0.5);
		background: rgba(var(--dl-accent-rgb), 0.12);
		color: var(--dl-accent);
		font-weight: 600;
	}

	.ribbon-bar {
		flex-shrink: 0;
		padding: 6px 12px;
		border-bottom: 1px solid #1e2433;
	}
	.cmp-hint {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 6px 12px;
		background: rgba(var(--dl-accent-rgb), 0.08);
		border-bottom: 1px solid rgba(var(--dl-accent-rgb), 0.25);
		font-size: 11px;
		line-height: 1.45;
		color: #cbd5e1;
	}
	.cmp-hint b {
		color: var(--dl-accent-light);
		font-weight: 700;
	}
	.cmp-hint-x {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		padding: 2px;
		background: none;
		border: none;
		color: #64748b;
		cursor: pointer;
		flex-shrink: 0;
	}
	.cmp-hint-x:hover {
		color: #f1f5f9;
	}

	.state {
		flex: 1 1 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 14px;
		text-align: center;
	}
	.state-avatar {
		border-radius: 50%;
		opacity: 0.95;
		filter: drop-shadow(0 4px 16px rgba(var(--dl-accent-rgb), 0.18));
	}
	.state p {
		color: #94a3b8;
		font-size: 13px;
		margin: 0;
	}
	.spinner {
		width: 28px;
		height: 28px;
		border: 2px solid #1e2433;
		border-top-color: var(--dl-accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.studio {
		flex: 1 1 auto;
		min-height: 0;
		display: grid;
		grid-template-columns: 240px 1fr;
	}
	.studio.ask-open {
		grid-template-columns: 240px minmax(0, 1fr) 380px;
	}
	/* soft swap · 전환 중 문서영역(TOC·격자)만 살짝 죽여 "로딩 중" 신호 + 묵은 클릭 차단. 드로어는 또렷이 유지. */
	.studio.swapping .toc,
	.studio.swapping .board {
		opacity: 0.5;
		pointer-events: none;
		transition: opacity 0.15s;
	}
	.ask-trigger {
		gap: 5px;
	}
	.ask-ava {
		border-radius: 50%;
		vertical-align: middle;
	}
	.ask-trigger.active {
		border-color: rgba(var(--dl-accent-rgb), 0.6);
		color: var(--dl-accent);
		background: rgba(var(--dl-accent-rgb), 0.1);
	}
	@media (max-width: 1120px) {
		.studio.ask-open {
			grid-template-columns: minmax(0, 1fr) 360px;
		}
		.studio.ask-open .toc {
			display: none;
		}
	}
	@media (max-width: 720px) {
		/* D2 · 모바일에서 드로어를 격자 아래로 적층(grid 1열)하지 않는다. 적층하면 board(상단·죽은 공간) +
		   drawer(하단·끼임)로 둘 다 못 쓴다. 대신 드로어를 전체화면 오버레이로 띄워 board 위에 덮는다.
		   board grid 는 단일 1fr 그대로 유지(데스크톱 push grid 미사용) → board 는 정상 풀폭으로 살아있고,
		   드로어는 그 위에 fixed 로 덮인다. .ask-open 의 3번째(380px) 트랙을 만들지 않아 board 압착 0. */
		.studio.ask-open {
			position: relative; /* 드로어 오버레이의 positioning context · board/ribbon 아래 studio 영역에 정확히 덮임 */
			grid-template-columns: 1fr;
		}
		.studio.ask-open :global(.ask-drawer) {
			position: absolute;
			inset: 0; /* studio 영역(헤더·리본 아래) 전체를 덮는 오버레이 · 전체화면/일반 모두 정확 */
			z-index: 90;
			border-left: none;
			box-shadow: 0 -8px 40px rgba(0, 0, 0, 0.6);
		}
	}
	.toc {
		min-height: 0;
		overflow-y: auto;
		border-right: 1px solid #1e2433;
		padding: 8px;
	}
	.board {
		min-width: 0;
		min-height: 0;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	@media (max-width: 880px) {
		.studio {
			grid-template-columns: 1fr;
		}
		.toc {
			/* D4 · 모바일 TOC 상단 접이: 더 얕게(140px) + 자체 스크롤. 격자에 세로 공간 양보. */
			max-height: 140px;
			border-right: none;
			border-bottom: 1px solid #1e2433;
		}

		/* D1 · 헤더 11버튼 가로 오버플로(scrollW 927 > 390) 해소. 데스크톱은 nowrap 한 줄 유지,
		   모바일에선 줄바꿈(wrap)으로 모든 버튼을 화면 안에 둔다. 가로스크롤(overflow-x:auto) 대신 wrap 을
		   택한 이유: .stock-pop/.data-pop/.add-pop 가 absolute 라 overflow 컨테이너에 세로로도 클리핑된다. */
		.page-head {
			flex-wrap: wrap;
			gap: 8px 10px;
			padding: 8px 10px;
		}
		.ph-left {
			/* 회사명이 0폭으로 압착돼 "삼"으로 잘리던 문제 · 한 줄 통째로 차지하게 해 온전히 보이게 한다. */
			flex: 1 0 100%;
			min-width: 0;
		}
		.ph-corp {
			font-size: 17px;
			overflow: hidden;
			text-overflow: ellipsis;
		}
		.ph-right {
			/* 두 번째 줄에 버튼들을 줄바꿈 배치 · flex-shrink 해제하고 wrap 허용. */
			flex: 1 1 100%;
			flex-wrap: wrap;
			gap: 8px;
		}
		/* D5 · 터치 타깃 44px(HIG). 헤더 버튼·연간만 토글 높이 확대(데스크톱 30px 불변). */
		.fs-btn,
		.annual-btn {
			min-height: 44px;
		}
		.cols {
			min-height: 44px;
		}
		.col-btn {
			min-height: 36px;
			min-width: 32px;
		}
	}
</style>
