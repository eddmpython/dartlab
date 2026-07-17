<script lang="ts">
	// ── 터미널 구역 규칙 (불가침) ──
	// 좌측 레일 + 상단 헤더 = 네비게이션 (검색·목록·이동·상태)
	// 중앙 스택            = 시각화 중심 (차트·그래프·전체화면 분석)
	// 우측 스택            = 테이블·텍스트·수치·정성 · 그래프 배치 금지 (그래프는 중앙으로)
	import './terminal.css';
	import type { Candle, DartLabRuntime, MacroLatest } from '@dartlab/ui-contracts';
	import { setDartLabRuntime } from '@dartlab/ui-runtime';
	import type { Engine } from './lib/engine';
	import type { TerminalHosts, TerminalBrandLinks } from './lib/hosts';
	import type { Lang } from './lib/types';
	import { chgClass, fmtNum, sign, sparkPts } from './ui/helpers';
	import BrandMark from './ui/BrandMark.svelte'; // 브랜드 마크 SSOT (아바타·이름·표면 태그)
	import BrandSocial from './ui/BrandSocial.svelte'; // SNS 행 SSOT (마크업+간격+별 배지 소유)
	import BrandSwitch from './ui/BrandSwitch.svelte'; // 브랜드 색 테마 · SNS 행 첫 아이콘(카드·랜딩 Header 와 동일 컨트롤)
	import DataMenu from './ui/DataMenu.svelte'; // 상단 「데이터」 · 이 회사 데이터 공개 다운로드(viewer DataDownloadMenu 동형)
	import LeftRail from './panels/LeftRail.svelte';
	import StrategyDock from './charts/StrategyDock.svelte'; // 백테스트 모드 = 좌패널 전체를 조작 패널로 교체(좌중우 중 좌)
	import CenterStack from './panels/CenterStack.svelte';
	import RightStack from './panels/RightStack.svelte';
	import SourcesModal from './panels/SourcesModal.svelte';
	import GiscusPanel from './panels/GiscusPanel.svelte';
	import SupportDialog from './panels/SupportDialog.svelte';
	import IndustryDialog from './panels/IndustryDialog.svelte';
	import FilingSearchDialog from './panels/FilingSearchDialog.svelte';
	import IpoDialog from './panels/IpoDialog.svelte';
	import { ChartCtl } from './charts/chartState.svelte';
	import { classifyTailwind, hasNegativeTailwind } from './lib/macroMappings';
	import { LAST_SYM_KEY } from './lib/lastSymbol';
	import { warmCompany } from './lib/warmup';
	import { fetchGithubStars } from './lib/githubStars';
	import { readStore, writeStore } from './lib/termStore';

	interface Props {
		eng: Engine;
		/** 데이터 포트 묶음 · 앱 셸(landing route · ui/web 브리지)이 주입. 전역 locator 금지. */
		runtime: DartLabRuntime;
		/** 뷰어 컴포넌트 주입 · 셸이 lazy 로더 제공 (terminal → viewer 역의존 제거, 4a-3). */
		hosts: TerminalHosts;
		/** 헤더 SNS·외부 링크 · 셸이 자기 brand 에서 주입 (surface 가 brand 소유 안 함, 4b). */
		links: TerminalBrandLinks;
		/** 카드뉴스(편집 캐러셀) 보유 종목코드 집합 · 셸(landing /terminal)이 manifests/carousels.json을 로드해 주입.
		 *  회사명 옆 링크 줄에 *해당 종목에 한해* 「카드뉴스」를 노출(개별). 미주입 시 링크 없음(standalone 무해). */
		cardsCodes?: Set<string>;
		/** 카드뉴스 클릭 핸들러 · 셸이 인스타식 포스트 다이얼로그(Deck+캡션)를 오버레이로 띄운다. Deck=landing 의존이라
		 *  surface 는 콜백만 받는다(viewer 포트와 동형 호스트 주입). */
		onOpenCards?: (code: string) => void;
		initial?: string;
	}
	let { eng, runtime, hosts, links, cardsCodes, onOpenCards, initial = '005930' }: Props = $props();
	// 하위 패널 전체가 useDartLabRuntime() 컨텍스트로 같은 인스턴스를 본다 (컴포넌트 init 시 1회).
	setDartLabRuntime(runtime);
	// base path · $app/paths 대신 runtime 환경 계약 (ui/web 셸에서도 동작)
	const base = runtime.env.basePath;
	const allowTerminalAsk = $derived(runtime.env.kind === 'local');

	// 종목 결정 우선순위: ?sym= 딥링크(산업·인사이트 등 내부 링크) > 마지막 본 종목(localStorage) > initial
	const urlSym = typeof location !== 'undefined' ? new URLSearchParams(location.search).get('sym') : null;
	const lastSym = typeof localStorage !== 'undefined' ? localStorage.getItem(LAST_SYM_KEY) : null;
	const first = eng.featured(1)[0] || initial;
	let sym = $state(
		urlSym && eng.buildCompany(urlSym) ? urlSym
		: lastSym && eng.buildCompany(lastSym) ? lastSym
		: eng.buildCompany(initial) ? initial : first
	);
	let lang = $state<Lang>('kr');
	let sourcesOpen = $state(false);
	let discussOpen = $state(false); // 종목 토론 드로어 (giscus)
	let supportOpen = $state(false); // 후원·기여 센터 다이얼로그
	let industryOpen = $state(false); // 산업 분석 다이얼로그 (좌측 산업 sweep 행 클릭)
	let industryId = $state('');
	let filingSearchOpen = $state(false); // 전역 공시 본문 검색 팔레트 (⌘⇧F · statusBar)
	// IPO 공모 다이얼로그 · ?ipo=1 딥링크(왓처 newIpo 푸시 클릭)로도 열림. 시장 수준 발굴이라 종목 무관.
	const urlIpo = typeof location !== 'undefined' ? new URLSearchParams(location.search).get('ipo') : null;
	let ipoOpen = $state(urlIpo === '1');
	let sectorFilter = $state('');
	let bottomTab = $state<'screener' | 'watch'>(readStore<string>('dlTerm.bottomTab', 'screener') === 'watch' ? 'watch' : 'screener');
	const chartCtl = new ChartCtl();
	// GitHub 스타 수 · SNS 버튼 옆 라이브 배지(사회적 증명). null = 미조회/실패(배지 숨김).
	let ghStars = $state<number | null>(null);
	fetchGithubStars(links.repo).then((n) => (ghStars = n));
	// 출처 모달 "최근 일자" · 라이브 재무 최신 분기 (finance.bundle in-flight dedup, 추가 다운로드 0)
	let finLatest = $state('');
	$effect(() => {
		const c = co?.code;
		finLatest = '';
		if (!c) return;
		void runtime.finance.bundle(c).then((b) => {
			if (co?.code !== c) return;
			finLatest = b?.views.quarter?.periods.at(-1) ?? b?.views.annual?.periods.at(-1) ?? '';
		});
	});
	let cmd = $state('');
	let flash = $state<string | null>(null);
	let flashTimer: ReturnType<typeof setTimeout> | null = null;
	$effect(() => { writeStore('dlTerm.bottomTab', bottomTab === 'watch' ? 'watch' : null); });

	// viewer 식 자동완성 검색
	let cmdInput = $state<HTMLInputElement | null>(null);
	let showSuggest = $state(false);
	let selIdx = $state(-1);
	const suggestions = $derived(showSuggest ? eng.suggest(cmd, 8) : []);
	function onInput() {
		showSuggest = cmd.trim().length > 0;
		selIdx = -1;
	}
	function onKey(e: KeyboardEvent) {
		if (!suggestions.length) return;
		if (e.key === 'ArrowDown') { e.preventDefault(); selIdx = (selIdx + 1) % suggestions.length; }
		else if (e.key === 'ArrowUp') { e.preventDefault(); selIdx = (selIdx - 1 + suggestions.length) % suggestions.length; }
		else if (e.key === 'Escape') { showSuggest = false; selIdx = -1; }
		else if (e.key === 'Enter' && selIdx >= 0) { e.preventDefault(); choose(suggestions[selIdx].code); }
	}
	function choose(code: string) {
		pick(code);
		cmd = '';
		showSuggest = false;
		selIdx = -1;
	}
	$effect(() => {
		const onDocKey = (e: KeyboardEvent) => {
			// 차트 전체화면 중엔 양보 · 오버레이 밑 보이지 않는 검색창에 포커스가 걸려 이후 모든
			// 타이핑·ESC 를 삼키던 트랩 버그. 전체화면의 ⌘K·/ 는 차트 심볼 점프(PriceChart)가 받는다.
			if (document.querySelector('.dlTerm .chartWrap.full')) return;
			const tag = (e.target as HTMLElement | null)?.tagName;
			const inInput = tag === 'INPUT' || tag === 'TEXTAREA';
			// ⌘⇧F = 전역 공시 본문 검색 팔레트(cmdBar ⌘K=종목 점프와 분리). 차트 전체화면 가드 위에서 이미 양보.
			if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'f') { e.preventDefault(); filingSearchOpen = true; }
			else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); cmdInput?.focus(); }
			else if (e.key === '/' && !inInput) { e.preventDefault(); cmdInput?.focus(); }
		};
		window.addEventListener('keydown', onDocKey);
		return () => window.removeEventListener('keydown', onDocKey);
	});

	const co = $derived(eng.buildCompany(sym));
	// 회사 선택 시 포트 경유로 모든 온디맨드 소스를 병렬 워밍업(패널 effect 전 캐시 준비).
	$effect(() => {
		const c = co;
		if (c) warmCompany(runtime, c.code);
	});
	const tickerCodes = $derived(eng.featured(14));
	// 회사 티커 스파크라인 · recent.parquet(최근 30거래일 전종목) 재사용, 추가 다운로드 0 (어댑터 캐시 공유)
	let recentMap = $state<Record<string, Candle[]> | null>(null);
	runtime.price.govRecent().then((m) => (recentMap = m));
	// 실 경제지표 최신값 (ECOS·FRED 시계열) · 종목명·주가차트 윗단 KPI 티커에 합류.
	let macroLatest = $state<MacroLatest[]>([]);
	runtime.macro.getLatest().then((m) => (macroLatest = m));
	const fmtMacro = (m: MacroLatest): string => {
		const v = m.v.toLocaleString('en-US', { maximumFractionDigits: m.def.digits ?? 2 });
		const signed = m.def.yoy && m.v > 0 ? '+' + v : v;
		const u = m.def.unit;
		return u === 'pt' || u === '원' ? signed : u === '$/t' ? '$' + signed : signed + u;
	};
	// 경제·시장 KPI (CenterStack 헤더 티커) · 실 지표 최신값+스파크라인 + 매크로 국면 KR/US + 섹터 순풍·역풍 + 시장폭/평균.
	const macroKpis = $derived.by<{ l: string; v: string; t: string; s?: number[]; id?: string }[]>(() => {
		const m = eng.raw.macro;
		const tw = eng.sectorTailwinds();
		const r1 = Object.values(eng.raw.prices.data).map((p) => p.return1m).filter((x): x is number => x != null);
		const up = r1.length ? (r1.filter((x) => x > 0).length / r1.length) * 100 : null;
		const avg = r1.length ? r1.reduce((a, b) => a + b, 0) / r1.length : null;
		const out: { l: string; v: string; t: string; s?: number[]; id?: string }[] = [];
		// id = MACRO_SERIES 시계열 식별자 → 마퀴 클릭 시 차트 econ 오버레이 토글(04 §5). 아래 파생 항목은 id 없음(비클릭).
		for (const ml of macroLatest)
			out.push({ l: lang === 'en' ? ml.def.en : ml.def.kr, v: fmtMacro(ml), t: ml.chg == null || ml.chg === 0 ? 'tNeu' : ml.chg > 0 ? 'tUp' : 'tDn', s: ml.spark, id: ml.def.id });
		if (m) {
			// quadrant 결측(빌더 입력 부족) 방어 · 방향 미상은 중립 톤 (크래시 금지)
			const dir = (g?: string) => (g == null ? 'tNeu' : g === 'rising' || g === '상승' ? 'tUp' : 'tDn');
			out.push({ l: 'KR', v: lang === 'en' ? m.kr.phase : m.kr.phaseLabel, t: dir(m.kr.quadrant?.growth) });
			out.push({ l: 'US', v: lang === 'en' ? m.us.phase : m.us.phaseLabel, t: dir(m.us.quadrant?.growth) });
		}
		if (tw[0]) out.push({ l: lang === 'en' ? 'tailwind' : '순풍', v: (lang === 'en' ? tw[0].en : tw[0].kr) + ' +' + tw[0].blended.toFixed(2), t: 'tUp' });
		if (tw.length > 1) {
			const lo = tw[tw.length - 1];
			const cls = classifyTailwind(lo.blended);
			const negative = hasNegativeTailwind(tw) && lo.blended < 0;
			const kpiTone = negative ? 'tDn' : cls.tone === 'up' ? 'tUp' : cls.tone === 'good' ? 'tGood' : 'tNeu';
			const value = (lang === 'en' ? lo.en : lo.kr) + ' ' + (lo.blended > 0 ? '+' : '') + lo.blended.toFixed(2);
			out.push({ l: negative ? (lang === 'en' ? 'headwind' : '역풍') : (lang === 'en' ? 'weak tw' : '약순풍'), v: value, t: kpiTone });
		}
		if (up != null) out.push({ l: lang === 'en' ? 'breadth' : '시장폭', v: up.toFixed(0) + '%↑', t: up >= 50 ? 'tUp' : 'tDn' });
		if (avg != null) out.push({ l: lang === 'en' ? 'avg 1M' : '평균1M', v: sign(avg, 1) + '%', t: avg >= 0 ? 'tUp' : 'tDn' });
		return out;
	});
	const langTabs: { k: Lang; l: string }[] = [{ k: 'kr', l: '한국어' }, { k: 'en', l: 'EN' }];

	function setFlash(msg: string, ms = 900) {
		flash = msg;
		if (flashTimer) clearTimeout(flashTimer);
		flashTimer = setTimeout(() => (flash = null), ms);
	}
	function pick(code: string) {
		const built = eng.buildCompany(code);
		if (!built) {
			setFlash(lang === 'en' ? 'no data' : '데이터 없음', 1400);
			return;
		}
		sym = code;
		try { localStorage.setItem(LAST_SYM_KEY, code); } catch { /* 시크릿 모드 등 */ }
		setFlash(code + ' · ' + built.name.kr);
	}
	function handleSectorFilter(id: string) {
		sectorFilter = sectorFilter === id ? '' : id;
		bottomTab = 'screener';
	}
	function openIndustry(id: string) {
		industryId = id;
		industryOpen = true;
	}
	function go(e: Event) {
		e.preventDefault();
		const r = eng.search(cmd);
		if (r) {
			pick(r);
			cmd = '';
		} else setFlash(lang === 'en' ? 'no match' : '검색 결과 없음', 1300);
	}

	// clock
	let now = $state(new Date());
	$effect(() => {
		const id = setInterval(() => (now = new Date()), 1000);
		return () => clearInterval(id);
	});
	const pad = (n: number) => String(n).padStart(2, '0');
	const clock = $derived(`${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())} KST`);
</script>

<div class="dlTerm">
	{#if !co}
		<div class="bootScreen">
			<img src="{base}/avatar.png" alt="DartLab" width="22" height="22" style="width:22px;height:22px;border-radius:50%" />
			<div class="bootMark">DartLab <span>terminal</span></div>
			<div class="bootBar"><div class="bootFill"></div></div>
			<div class="bootMsg">{lang === 'en' ? 'company not found' : '회사 데이터를 찾을 수 없습니다'}</div>
		</div>
	{:else}
		<header class="topBar">
			<BrandMark tag="terminal" href="{base}/" {base} title="dartlab" />
			<form class="cmdBar" onsubmit={go} role="search">
				<span class="cmdPrompt">‹GO›</span>
				<input class="cmdInput" bind:this={cmdInput} bind:value={cmd} spellcheck={false}
					oninput={onInput} onkeydown={onKey} onfocus={onInput}
					onblur={() => setTimeout(() => (showSuggest = false), 120)}
					placeholder={lang === 'en' ? 'Search code or name  (005930 · 삼성전자 · 기아)' : '종목코드 · 회사명 검색'} />
				<kbd class="cmdKbd">⌘K</kbd>
				<button class="cmdGo" type="submit">GO</button>
				{#if flash}<span class="cmdFlash">{flash}</span>{/if}
				{#if showSuggest && suggestions.length}
					<div class="suggest">
						{#each suggestions as s, i (s.code)}
							<button type="button" class={'suggestRow' + (i === selIdx ? ' on' : '')}
								onmousedown={() => choose(s.code)} onmouseenter={() => (selIdx = i)}>
								<span class="sgName">{s.name}</span>
								<span class="sgCode mono">{s.code}</span>
								<span class="sgInd">{s.industry}</span>
							</button>
						{/each}
					</div>
				{/if}
			</form>
			<div class="topRight">
				<div class="langSwitch">{#each langTabs as t (t.k)}<button class={'langBtn ' + (lang === t.k ? 'on' : '')} onclick={() => (lang = t.k)}>{t.l}</button>{/each}</div>
				<span class="clock mono">{clock}</span>
				<span class="connDot"><span class="dot"></span>HF</span>
				<div class="hdrLinks">
					{#if co}
						<DataMenu {runtime} code={co.code} corpName={co.name.kr} {lang} />
						<a class="hdrLink hdrViewer" href="{base}/viewer/company/{co.code}" target="_blank" rel="noopener" title={lang === 'en' ? 'Disclosure viewer · full filing text with financial reading' : '공시뷰어 · 공시 원문·재무 읽기 전용 뷰'}>{lang === 'en' ? 'Viewer' : '공시뷰어'}</a>
						<a class="hdrLink hdrReport" href="{base}/report?sym={co.code}" target="_blank" rel="noopener" title={lang === 'en' ? 'Corporate analysis report · printable (PDF)' : '기업분석보고서 · 인쇄 가능 (PDF)'}>{lang === 'en' ? 'Report' : '보고서'}</a>
						<a class="hdrLink hdrCards" href="{base}/cards" target="_blank" rel="noopener" title={lang === 'en' ? 'Card stories · Instagram-style feed (all companies)' : '카드뉴스 · 인스타그램형 피드(전체 회사)'}>{lang === 'en' ? 'Cards' : '카드뉴스'}</a>
						<a class="hdrLink hdrBlog" href="{base}/blog" target="_blank" rel="noopener" title={lang === 'en' ? 'Blog · company stories, disclosure reading, dartlab news' : '블로그 · 기업 이야기·공시 읽기·dartlab 소식'}>{lang === 'en' ? 'Blog' : '블로그'}</a>
					{/if}
					{#if allowTerminalAsk}
						<a class="hdrLink hdrAsk" href={runtime.navigation.href({ kind: 'chat' })} title="AI 챗 모드 · 대화형 분석 작업대" aria-label="챗 모드" style="display:inline-flex;align-items:center;gap:4px">
							<picture><source srcset="{base}/avatar-detective.webp" type="image/webp" /><img src="{base}/avatar-detective.png" alt="" width="14" height="14" style="border-radius:50%" /></picture>챗
						</a>
					{/if}
					<button class={'hdrLink' + (ipoOpen ? ' on' : '')} onclick={() => (ipoOpen = true)} title={lang === 'en' ? 'IPO offerings · live discovery from registration statements (equity)' : '신규상장 IPO 공모 발굴 · 증권신고서(지분증권) 라이브'}>IPO</button>
					<button class={'hdrLink' + (discussOpen ? ' on' : '')} onclick={() => (discussOpen = !discussOpen)} title="종목 토론 · giscus(GitHub Discussions) 인-터미널">{lang === 'en' ? 'Discuss' : '토론'}</button>
					<a class="hdrLink" href="{links.repo}/issues/new" target="_blank" rel="noopener" title="GitHub 이슈 등록 · 버그·요청">{lang === 'en' ? 'Issue' : '이슈'}</a>
				</div>
				<BrandSocial {links} {ghStars} {lang} onSupport={() => (supportOpen = true)}>
					{#snippet leading()}<BrandSwitch />{/snippet}
				</BrandSocial>
			</div>
		</header>

		<div class="tickerStrip"><div class="tickerTrack">
			{#each tickerCodes.concat(tickerCodes) as c, i (i)}
				{@const px = eng.priceOf(c)}
				{#if px}
					{@const sp = recentMap?.[c]}
					<span class="tickerItem" role="button" tabindex="0" onclick={() => pick(c)} onkeydown={(ev) => ev.key === 'Enter' && pick(c)}>
						<b>{eng.nameOf(c)}</b>
						{#if sp && sp.length > 1}<svg class={'kpiSpark ' + chgClass(px.return1m)} viewBox="0 0 34 11" preserveAspectRatio="none" aria-hidden="true"><polyline points={sparkPts(sp.map((k) => k.c))} fill="none" stroke="currentColor" stroke-width="1.1" /></svg>{/if}
						<span class="mono">{fmtNum(px.currentPrice)}</span>
						<span class={'mono ' + chgClass(px.return1m)}>{sign(px.return1m, 1)}%</span>
					</span>
				{/if}
			{/each}
		</div></div>

		<main class="board">
			<div class="col colL">
				{#if chartCtl.btReportMode}
					<!-- 백테스트 모드 · 좌패널 전체가 조작 패널(스코프·프리셋버튼·커스텀·검증). LeftRail(매크로·스크리너) 교체. -->
					<StrategyDock ctl={chartCtl} {lang} code={co.code} name={co.name.kr} fill onClose={() => { chartCtl.clearBtAll(); chartCtl.btReportMode = false; chartCtl.btDockOpen = false; }} />
				{:else}
					<LeftRail {eng} {lang} active={sym} onPick={pick} onIndustry={openIndustry} onFilingSearch={() => (filingSearchOpen = true)} {sectorFilter} {bottomTab} onSectorFilter={handleSectorFilter} onBottomTab={(tab) => (bottomTab = tab)} />
				{/if}
			</div>
			<div class="col colC"><CenterStack {co} {lang} ctl={chartCtl} kpis={macroKpis} suggest={(q, n) => eng.suggest(q, n)} onPick={pick} {cardsCodes} {onOpenCards} /></div>
			<div class="col colR"><RightStack {co} {lang} {hosts} repoUrl={links.repo} onPick={pick} lookupListed={eng.lookupListed} percentileIn={eng.percentileIn} /></div>
		</main>

		<footer class="statusBar">
			<span class="sbItem"><b class="tAmber">⌘K</b> {lang === 'en' ? 'JUMP' : '종목점프'}</span>
			<span class="sbItem"><b class="tAmber">/</b> {lang === 'en' ? 'FOCUS' : '검색창'}</span>
			<button class="sbItem sbSrcBtn" onclick={() => (sourcesOpen = true)} title={lang === 'en' ? 'data sources & licenses' : '데이터 출처·라이선스'}>
				<b class="tAmber">ⓘ</b> {lang === 'en' ? 'SOURCES' : '데이터 출처'}
			</button>
			<span class="sbItem dim">DATA · {eng.source}</span>
			<span class="sbItem" style="gap:6px">
				<span class="provTag pReal">{lang === 'en' ? 'REAL' : '실데이터'}</span><span class="dim">{lang === 'en' ? 'EOD · daily batch' : 'EOD·일배치'}</span>
				<span class="provTag pDeriv">파생</span><span class="dim">{lang === 'en' ? 'computed' : '계산'}</span>
			</span>
			<span class="sbSpacer"></span>
			<span class="sbItem dim">prices {co.price.asOf} · {eng.raw.index.length} 종목 · KR</span>
			<span class="sbItem"><b class="tUp">{co.code}</b> {co.name.kr} · {co.marketLabel}</span>
		</footer>
		<SourcesModal {lang} open={sourcesOpen} onClose={() => (sourcesOpen = false)} pricesAsOf={co.price.asOf} macroAsOf={eng.raw.macro?.asOf ?? ''} financeLatest={finLatest || (co.trendQuarter?.periods.at(-1) ?? '')} />
		<GiscusPanel code={co.code} name={co.name.kr} {lang} open={discussOpen} onClose={() => (discussOpen = false)} />
		<SupportDialog {lang} {links} {base} open={supportOpen} onClose={() => (supportOpen = false)} />
		{#if filingSearchOpen}
			<FilingSearchDialog {lang} onPick={pick} onClose={() => (filingSearchOpen = false)} />
		{/if}
		{#if ipoOpen}
			<IpoDialog {lang} onClose={() => (ipoOpen = false)} />
		{/if}
		{#if industryOpen}
			<IndustryDialog {eng} {industryId} {lang} onClose={() => (industryOpen = false)} onPick={(c) => { pick(c); industryOpen = false; }} />
		{/if}
	{/if}
</div>
