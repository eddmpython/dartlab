<script lang="ts">
	import type {
		AuditFeeYear,
		CompanyRelations,
		DebtProfileBundle,
		FinMode,
		FinScope,
		BusinessTable,
		InvestmentPeriod,
		InvestmentTrendYear,
		InvestmentsView,
		NewsItem,
		NonRegularFiling,
		NoteSeriesBundle,
		ProductIndexItem,
		RegularFiling,
		ShareholderReturnYear,
		ShareholdersView,
		StmtKind,
		TerminalFinanceBundle,
		WorkforceYear
	} from '@dartlab/ui-contracts';
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import type { Company, Lang, Universe, UniversePercentile } from '../lib/types';
	import type { TerminalHosts } from '../lib/hosts';
	import { gradeTone } from '../lib/engine';
	import { forensicSignals } from '../lib/forensic'; // 풀스크린에 묻힌 결정론 적신호(감사독립성·단기상환벽) 우측 승격
	import Panel from '../ui/Panel.svelte';
	import { rollupProfitPool, type IndustryStageRollup } from '../../map/industryPool'; // 이익 풀 · 공정별 영업이익률×매출 rollup
	import ViewerOverlay from './ViewerOverlay.svelte'; // 얇은 셸 · 본체(ViewerStudio)는 셸 주입 lazy 로더
	import { viewerEntry } from '../lib/viewerEntry.svelte'; // 중앙 "공시뷰어" 버튼 신호 구독
	import { disclosureFocus } from '../lib/disclosureFocus.svelte'; // 주가차트 공시 dot 클릭 → 그 날짜 행 스크롤+하이라이트
	// 정량재무제표 = 공시뷰어 FinanceDialog 그대로 (한몸두입구) · 셸 주입 lazy 로더, 터미널 청크 무증가
	import { tx, txc, chgClass, sign, toneClass, fmtNum } from '../ui/helpers';
	import { fmtKRW } from '../lib/engine';
	import { lossSummary, controlShiftSummary, type ControlShift } from '../lib/holdings'; // 타법인출자 lossPct(앵커)·control-shift(지배이동) 순수계산
	import type { ListedLookup } from '../lib/holdings'; // 피출자사명→상장 종목 해소 hook 타입
	import { workforceTrend, returnTrend } from '../lib/reportSelfHistory'; // 인력·주주환원 자기이력(self-vs-self) 순수계산 · 다년 배열에서 시간축, 새 fetch 0
	import { requestFinFull } from '../lib/finFullEntry.svelte'; // 섹션 상세보기 → 중앙 재무 전체화면 특정 탭(people·shareholder) 열기 신호

	interface Props {
		co: Company;
		lang: Lang;
		hosts: TerminalHosts;
		repoUrl: string; // 셸 brand repo URL · 공시뷰어 오버레이(임베드 이슈링크)로 관통.
		onPick: (code: string) => void;
		lookupListed: ListedLookup; // 피출자사명→상장 종목 해소(출자 다이얼로그 시가 환산·클릭 이동)
		percentileIn: (code: string, universe: Universe) => UniversePercentile | null; // 유니버스 교차 백분위(상세보기 다이얼로그)
	}
	let { co, lang, hosts, repoUrl, onPick, lookupListed, percentileIn }: Props = $props();
	const rt = useDartLabRuntime();
	const base = rt.env.basePath;
	let viewerOpen = $state(false); // 공시뷰어 인터미널 오버레이 (정기공시 패널 ⤢)
	let holdingsOpen = $state(false); // 출자 관계 분석 전체화면 (타법인 출자 패널 ⤢)
	let tablesOpen = $state(false); // 재무제표 원표 모달 (재무 패널 ⤢)
	let pctCrossOpen = $state(false); // 유니버스 교차 백분위 다이얼로그 (업종 내 백분위 패널 → 상세보기)
	let riskDlgOpen = $state(false); // 리스크 경고등 설명 다이얼로그 (점검 차원 카탈로그 + 현상태 + 조건·소스)

	// 이익 풀 · 이 회사가 속한 산업의 "이익은 어느 공정 단계가 버나" (industries/{id}.json lazy fetch).
	// 우측=테이블·수치 정체성 → 막대차트 아닌 밀도 테이블(영업이익률·매출 + 이익최대/매출최대 마커).
	let profitPool = $state<IndustryStageRollup[] | null>(null);
	let poolToken = 0;
	$effect(() => {
		const ind = co.industry;
		profitPool = null;
		if (!ind) return;
		const tk = ++poolToken;
		void rt.company.industryProfitPool(ind).then((stages) => {
			if (tk !== poolToken) return;
			const rolled = stages ? rollupProfitPool(stages).filter((s) => s.opMarginPct !== null && s.revenue > 0) : [];
			profitPool = rolled.length ? rolled : null;
		});
	});
	// 영업이익률 내림차순 = "어디서 버나"가 맨 위로. 이익최대·매출최대 마커로 이익≠매출 가시화.
	const poolRows = $derived.by(() => {
		const pp = profitPool;
		if (!pp || pp.length === 0) return null;
		const marginMax = Math.max(...pp.map((s) => s.opMarginPct ?? 0), 0.01);
		const byMargin = [...pp].sort((a, b) => (b.opMarginPct ?? -1e9) - (a.opMarginPct ?? -1e9))[0];
		const byRev = [...pp].sort((a, b) => b.revenue - a.revenue)[0];
		const rows = [...pp]
			.sort((a, b) => (b.opMarginPct ?? -1e9) - (a.opMarginPct ?? -1e9))
			.map((s) => ({
				...s,
				isMarginMax: s.key === byMargin.key,
				isRevMax: s.key === byRev.key,
				barPct: Math.max(2, ((s.opMarginPct ?? 0) / marginMax) * 100)
			}));
		return { rows, byMargin, byRev, diverges: byMargin.key !== byRev.key };
	});
	function fmtPoolRev(v: number): string {
		// industries/{id}.json revenue 단위 = 억원
		return v >= 10000 ? `${(v / 10000).toFixed(1)}조` : `${Math.round(v).toLocaleString()}억`;
	}
	// 중앙 "공시뷰어" 버튼 신호(viewerEntry.pulse) 구독 · pulse 변할 때만 오버레이를 연다. seenPulse 는
	// 비반응 plain let(추적 0)이라 viewerOpen 쓰기가 effect 를 재발화시키지 않음(루프 없음).
	let seenViewerPulse = viewerEntry.pulse;
	$effect(() => {
		const p = viewerEntry.pulse;
		if (p !== seenViewerPulse) {
			seenViewerPulse = p;
			viewerOpen = true;
		}
	});
	// 주가차트 공시 dot 클릭(disclosureFocus.pulse) → 그 날짜 행을 정기/비정기 공시목록에서 스크롤·하이라이트(원문 링크 아님).
	// seenFocusPulse = 비반응 plain let · flashDate 쓰기가 effect 를 재발화시키지 않음(viewerEntry 동일 패턴, 루프 없음).
	const fdate = (s: string) => s.replace(/\D/g, '').slice(0, 8); // YYYY-MM-DD → YYYYMMDD (행 data-fdate 와 비교 키)
	let filingWrap = $state<HTMLElement | null>(null); // 정기‖비정기 공시 2분할 컨테이너 · querySelector 범위 한정
	let newsWrap = $state<HTMLElement | null>(null); // 종목뉴스 컨테이너 · 뉴스 dot 클릭 시 같은 날짜 행 스크롤·하이라이트
	let flashDate = $state<string | null>(null);
	let seenFocusPulse = disclosureFocus.pulse;
	let flashTimer: ReturnType<typeof setTimeout> | null = null;
	// wrap 안의 그 날짜(data-fdate) 행을 *모두* 각자 박스 중앙으로 스크롤 · 2분할(정기‖비정기 · 네이버‖GDELT)
	// 양 컬럼에 같은 날짜가 있으면 둘 다 이동(querySelectorAll). centerCol=true 면 첫 박스를 컬럼 뷰포트 중앙에
	// (= 그 패널을 화면 안으로 끌어올림). 반환 = 매치 행 있었는지(호출부 우선순위 분기용).
	function scrollWrapToDate(wrap: HTMLElement | null, d: string, centerCol: boolean): boolean {
		if (!wrap) return false;
		const rows = wrap.querySelectorAll(`[data-fdate="${d}"]`);
		let firstList: HTMLElement | null = null;
		rows.forEach((node) => {
			const list = (node as HTMLElement).closest('.filingList') as HTMLElement | null;
			if (!list) return;
			const lr = list.getBoundingClientRect();
			const rr = (node as HTMLElement).getBoundingClientRect();
			list.scrollTop += rr.top + rr.height / 2 - (lr.top + lr.height / 2);
			if (!firstList) firstList = list;
		});
		if (centerCol && firstList) {
			const col = (firstList as HTMLElement).closest('.col') as HTMLElement | null;
			if (col) {
				const cr = col.getBoundingClientRect();
				const lr2 = (firstList as HTMLElement).getBoundingClientRect();
				col.scrollBy({ top: lr2.top + lr2.height / 2 - (cr.top + cr.height / 2), behavior: 'smooth' });
			}
		}
		return firstList !== null;
	}
	$effect(() => {
		const p = disclosureFocus.pulse;
		if (p === seenFocusPulse) return;
		seenFocusPulse = p;
		const d = disclosureFocus.date;
		if (!d) return;
		if (flashTimer) clearTimeout(flashTimer);
		flashDate = null; // 같은 날짜 재클릭도 class off→on 으로 애니메이션 재생되도록 먼저 해제
		requestAnimationFrame(() => {
			flashDate = d; // 공시·뉴스 양쪽 [data-fdate==d] 행이 .flash 로 동시 점멸(클래스 바인딩 공유)
			// 공시(정기/비정기) 우선 컬럼 센터링. 그 날짜에 공시가 없으면(뉴스-only) 뉴스 패널을 화면으로 끌어올림.
			const inFiling = scrollWrapToDate(filingWrap, d, true);
			scrollWrapToDate(newsWrap, d, !inFiling);
			flashTimer = setTimeout(() => (flashDate = null), 3600);
		});
	});
	const localViewerHref = $derived(rt.viewer.urlForCompany(co.code));
	const viewerHref = $derived(localViewerHref ?? `${base}/viewer/company/${co.code}`);
	const externalTarget = $derived(localViewerHref ? undefined : '_blank');
	const externalRel = $derived(localViewerHref ? undefined : 'noopener');
	const tcls = (t: string) => (({ up: 'tUp', good: 'tGood', neutral: 'tNeu', warn: 'tWarn', down: 'tDn' }) as Record<string, string>)[t] || 'tNeu';

	let relations = $state<CompanyRelations | null>(null);
	let regFilings = $state<RegularFiling[]>([]);
	let nonRegFilings = $state<NonRegularFiling[]>([]);
	let nonRegState = $state<'loading' | 'ready' | 'empty'>('loading');
	// per-company read(notes 등)가 hang/실패해도 멈추지 않게 · 타임아웃 race. 타이머는 settle 시 해제(누수 없음).
	function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
		return new Promise<T>((resolve, reject) => {
			const t = setTimeout(() => reject(new Error('timeout')), ms);
			p.then(
				(v) => { clearTimeout(t); resolve(v); },
				(e) => { clearTimeout(t); reject(e); }
			);
		});
	}
	let news = $state<NewsItem[]>([]); // 종목 뉴스(네이버 헤드라인+스니펫) · 워커 /news 서버사이드 read
	let newsState = $state<'loading' | 'ready' | 'empty'>('loading');
	$effect(() => {
		const code = co.code;
		relations = null;
		regFilings = [];
		nonRegFilings = [];
		nonRegState = 'loading';
		news = [];
		newsState = 'loading';
		wf = [];
		srs = [];
		inv = null;
		invTrend = [];
		invPeriods = [];
		shareholders = null;
		shPeriods = [];
		auditFees = null;
		debtProfile = null;
		let cancelled = false;
		// 정기보고서 3패널 · 독립 스트림-인 (가벼운 인력·배당 먼저, 무거운 출자 나중)
		// 포렌식 적신호 소스(감사보수·부채프로파일) · 임계 초과 시에만 우측 프리뷰 렌더(forensicSignals).
		rt.report.auditFees(code).then((b) => {
			if (!cancelled) auditFees = b;
		});
		rt.report.debtProfile(code).then((b) => {
			if (!cancelled) debtProfile = b;
		});
		rt.report.workforce(code).then((b) => {
			if (!cancelled) wf = b ?? [];
		});
		rt.report.shareholderReturn(code).then((b) => {
			if (!cancelled) srs = b ?? [];
		});
		rt.report.investments(code).then((b) => {
			if (cancelled) return;
			inv = b?.latest ?? null;
			invTrend = b?.trend ?? [];
			invPeriods = b?.periods ?? [];
		});
		rt.report.shareholderPeriods(code).then((s) => {
			if (cancelled) return;
			shPeriods = s ?? [];
			shareholders = s?.at(-1) ?? null; // 최신기 = 인라인/다이얼로그 기본값
		});
		rt.company.relations(code).then((r) => {
			if (!cancelled) relations = r;
		});
		rt.filing.regular(code, 500).then((f) => {
			if (!cancelled) regFilings = f;
		});
		rt.filing.nonRegular(code).then((f) => {
			if (cancelled) return;
			nonRegFilings = f;
			nonRegState = f.length ? 'ready' : 'empty';
		});
		rt.news.forCompany(code, co.name?.kr).then((n) => {
			if (cancelled) return;
			news = n;
			newsState = n.length ? 'ready' : 'empty';
		});
		return () => {
			cancelled = true;
		};
	});
	// 뉴스 날짜별 그룹 (트랙별) · dot 클릭(focusDisclosure) 시 data-fdate 로 행 스크롤·하이라이트.
	const groupByDate = (items: NewsItem[]): [string, NewsItem[]][] => {
		const m = new Map<string, NewsItem[]>();
		for (const it of items) {
			const d8 = (it.date ?? '').replace(/\D/g, '').slice(0, 8);
			if (d8.length !== 8) continue;
			const cur = m.get(d8);
			if (cur) cur.push(it);
			else m.set(d8, [it]);
		}
		return [...m.entries()].sort((a, b) => (a[0] < b[0] ? 1 : -1));
	};
	// 좌=네이버(최근·스니펫 O) ‖ 우=GDELT(과거·제목+링크). track 으로 분리(공시 정기‖비정기 동형 2분할).
	const naverNews = $derived(news.filter((n) => n.track !== 'gdelt'));
	const gdeltNews = $derived(news.filter((n) => n.track === 'gdelt'));
	const naverByDate = $derived(groupByDate(naverNews));
	const gdeltByDate = $derived(groupByDate(gdeltNews));

	// 재무제표 · c.panel 전 기간(분기/연간 토글). 요약 탭 폐지, 손익·재무상태·현금흐름·비용·비율.
	let stmt = $state<StmtKind | 'RT'>('IS');
	let finMode = $state<FinMode>('quarter');
	let finScope = $state<FinScope | null>(null); // null = 자동(최신 데이터 범위). 연결/별도 토글 시 명시.
	let finBundle = $state<TerminalFinanceBundle | null>(null);
	// 재무 번들은 범위(연결/별도)에 따라 재조회 · 회사 전환 시 자동 범위로 리셋 (정의 순서상 fetch 보다 먼저).
	$effect(() => {
		void co.code;
		finScope = null;
	});
	$effect(() => {
		const code = co.code;
		const scope = finScope ?? undefined; // tracked → 토글 시 재조회
		finBundle = null;
		let cancelled = false;
		rt.finance.bundle(code, scope).then((b) => {
			if (!cancelled) finBundle = b;
		});
		return () => {
			cancelled = true;
		};
	});
	const tabs = [{ k: 'IS', kr: '손익', en: 'IS' }, { k: 'BS', kr: '재무상태', en: 'BS' }, { k: 'CF', kr: '현금흐름', en: 'CF' }, { k: 'RT', kr: '비율', en: 'Ratios' }] as const;
	const finModeLabel: Record<FinMode, string> = { ttm: 'TTM', quarter: '분기', annual: '연간' };
	const finScopeLabel = (s: FinScope): string => (s === 'CFS' ? (lang === 'en' ? 'CONS' : '연결') : lang === 'en' ? 'SEP' : '별도');
	const finView = $derived(finBundle ? (finBundle.views[finMode] ?? finBundle.views[finBundle.defaultMode]) : null);
	const KEY_ROWS = ['operatingIncome', 'netIncome', 'assets', 'equity', 'liabilities', 'cfOperating'];
	// 최신 기간부터(역순) 표시 · 차트는 오름차순 유지, 표만 reverse.
	const dispPeriods = $derived(finView ? finView.periods.slice().reverse() : []);
	const stmtRows = $derived(finView ? (stmt === 'RT' ? finView.ratios : finView.statements[stmt as StmtKind]) : []);
	// 표 단위 자동 · 조 고정이면 중형사 행 대부분이 0.0~0.1 소수점 범벅. 최대 절대값 50조 미만이면
	// 억(콤마·정수, FnGuide 관례) 전환 · 초대형사만 조 유지 (비율 탭 제외).
	const finUnitEok = $derived.by(() => {
		if (!finView) return false;
		let m = 0;
		for (const k of ['IS', 'BS', 'CF'] as StmtKind[]) for (const r of finView.statements[k]) for (const v of r.values) if (v != null && Math.abs(v) > m) m = Math.abs(v);
		return m > 0 && m < 50;
	});
	const finUnit = $derived(finUnitEok ? '억' : '조');
	const finVal = (v: number | null): string => (v == null ? '·' : finUnitEok ? fmtNum(v * 1e4, 0) : fmtNum(v, 1));

	// 정기보고서 시계열 (인력·주주환원·타법인출자) · runtime ReportPort, 패널별 독립 로드.
	// 구역 규칙(Terminal.svelte): 우측 = 테이블·수치·정성만, 그래프 금지 · 시계열 그래프는 중앙 재무 전체화면 탭.
	let wf = $state<WorkforceYear[]>([]);
	let srs = $state<ShareholderReturnYear[]>([]);
	let inv = $state<InvestmentsView | null>(null);
	let shareholders = $state<ShareholdersView | null>(null); // 역방향 소유 최신기 · 누가 이 회사를 소유하나(기관·법인 실명, 개인 익명)
	let invTrend = $state<InvestmentTrendYear[]>([]); // 출자 추이 · 다이얼로그 보조(자본 잠김 방향)
	let invPeriods = $state<InvestmentPeriod[]>([]); // 출자 시계열 · 다이얼로그 기간축/재생
	let shPeriods = $state<ShareholdersView[]>([]); // 최대주주 시계열 · 다이얼로그 기간축
	let auditFees = $state<AuditFeeYear[] | null>(null); // 포렌식 · 감사/비감사 보수(독립성 비율)
	let debtProfile = $state<DebtProfileBundle | null>(null); // 포렌식 · 사채 잔존만기(단기 상환벽)
	// 정기보고서 주석 · panel contentRaw 의 정부 XBRL 태그 런타임 직독(reportSource.noteSeries). 비용 체질·부문별 매출.
	// 우측 글랜스 한 줄(real digest) + '상세보기'→ NotesDashboardDialog(분기 시계열). 별도 bake 0. 최근 분기만.
	let noteBundle = $state<NoteSeriesBundle | null>(null);
	let notesState = $state<'idle' | 'loading' | 'ready' | 'empty' | 'error'>('idle');
	let dashOpen = $state(false); // 주석 상세 다이얼로그
	// 순수 런타임 lazy · 주석은 panel contentRaw(단일 row group 13~16MB 청크, 런타임에서 축소 불가) 직독이라 무겁다.
	// 회사 전환 콜드 버스트(가격·재무·공시·뉴스·16MB 출자…)와 경쟁시키지 않도록, 주석 패널 sentinel 이 뷰포트
	// 근처(800px)에 올 때만 read. notesWanted 는 sticky · 한 번 본 사용자는 이후 회사 즉시 로드. 별도 bake/재빌드 0.
	let notesSentinel = $state<HTMLElement | null>(null);
	let notesWanted = $state(false);
	$effect(() => {
		if (!notesSentinel || notesWanted) return;
		const io = new IntersectionObserver(
			(entries) => {
				if (entries.some((e) => e.isIntersecting)) {
					notesWanted = true;
					io.disconnect();
				}
			},
			{ rootMargin: '800px' }
		);
		io.observe(notesSentinel);
		return () => io.disconnect();
	});
	$effect(() => {
		const code = co.code;
		const wanted = notesWanted; // tracked · 스크롤로 wanted 되면 재실행하며 fetch
		noteBundle = null;
		if (!wanted) {
			notesState = 'idle'; // 아직 미요청 · 패널은 '스크롤하면 로드' 힌트만(13MB 보류)
			return;
		}
		notesState = 'loading';
		let cancelled = false;
		// Promise.resolve().then 으로 감싸 동기 throw 도 rejection 으로(effect throw 로 RightStack 깨짐 방지).
		// 타임아웃 25s · panel 단일 청크 13~16MB 콜드 read 흡수(lazy 로 경쟁은 피하되 read 자체는 무거움).
		withTimeout(Promise.resolve().then(() => rt.report.noteSeries(code)), 25_000).then(
			(b) => {
				if (cancelled) return;
				noteBundle = b;
				notesState = b && (b.cost || b.segment) ? 'ready' : 'empty';
			},
			(err) => {
				if (cancelled) return;
				console.warn('[terminal] report noteSeries load failed:', err);
				notesState = 'error';
			}
		);
		return () => {
			cancelled = true;
		};
	});
	// 글랜스 = 비율 적층 막대(바로 보임) + 상위 칩. series 최신점 비중%. design 카테고리 팔레트 색.
	const NOTE_PAL = ['var(--dl-cat-start)', 'var(--dl-cat-operation)', 'var(--dl-cat-engines)', 'var(--dl-cat-runtime)', 'var(--dl-cat-recipes)', 'var(--dl-accent)', 'var(--up)', 'var(--warn)'];
	const niceCat = (n: string): string => {
		const t = n.replace(/\s*및\s*/g, '·').replace(/(매입액|사용액|비용|비$)/g, '').trim();
		if (/^[A-Za-z]{1,4}$/.test(t)) return t.toUpperCase();
		return t.replace(/([a-z])([A-Z])/g, '$1 $2').slice(0, 8);
	};
	const barSegsOf = (s: NoteSeriesBundle['cost']): { segs: { name: string; pct: number; color: string }[] } | null => {
		const pts = s?.points;
		if (!pts || !pts.length || !s) return null;
		const last = pts[pts.length - 1]!;
		const segs = s.categories
			.map((name, i) => ({ name, pct: last.shares[i] ?? 0, color: name === '기타' ? 'var(--dimmer)' : (NOTE_PAL[i % NOTE_PAL.length] ?? 'var(--dim)') }))
			.filter((r) => r.pct > 0.05);
		return segs.length ? { segs } : null;
	};
	const costBar = $derived(barSegsOf(noteBundle?.cost ?? null));
	const segBar = $derived(barSegsOf(noteBundle?.segment ?? null));
	const topChips = (segs: { name: string; pct: number; color: string }[]): { name: string; pct: number; color: string }[] => segs.filter((s) => s.name !== '기타').sort((a, b) => b.pct - a.pct).slice(0, 3);
	// 사업 서술 표 · panel contentRaw HTML 표 격자전개(reportSource.businessTables). 생산능력·원재료·매출수주.
	// 글랜스(토픽 칩) + 상세보기 → BusinessTablesDialog. 노트와 같은 sentinel 게이트 공유(둘 다 panel 직독).
	let bizTables = $state<BusinessTable[] | null>(null);
	let bizState = $state<'idle' | 'loading' | 'ready' | 'empty' | 'error'>('idle');
	let bizOpen = $state(false);
	const BIZ_TOPIC_KR: Record<string, string> = { salesOrder: '매출·수주', rawMaterial: '원재료·생산', productService: '주요 제품' };
	$effect(() => {
		const code = co.code;
		const wanted = notesWanted;
		bizTables = null;
		if (!wanted) {
			bizState = 'idle';
			return;
		}
		bizState = 'loading';
		let cancelled = false;
		withTimeout(Promise.resolve().then(() => rt.report.businessTables(code)), 25_000).then(
			(b) => {
				if (cancelled) return;
				bizTables = b?.tables ?? null;
				bizState = b && b.tables.length ? 'ready' : 'empty';
			},
			(err) => {
				if (cancelled) return;
				console.warn('[terminal] report businessTables load failed:', err);
				bizState = 'error';
			}
		);
		return () => {
			cancelled = true;
		};
	});
	// 최신 연간 현금성자산 (BS 'cash', 조 단위) → 원 환산. 단기 상환벽 신호의 분모.
	const cashLatestWon = $derived.by<number | null>(() => {
		const av = finBundle?.views.annual;
		if (!av) return null;
		const row = av.statements.BS.find((r) => r.key === 'cash');
		if (!row) return null;
		for (let i = row.values.length - 1; i >= 0; i--) {
			const v = row.values[i];
			if (v != null) return v * 1e12;
		}
		return null;
	});
	const forensic = $derived(forensicSignals({ auditFees, debtProfile, cashLatestWon }));
	const wfLast = $derived(wf.length ? wf[wf.length - 1] : null);
	// 인력 자기이력 · 총원 궤적 + 계약직 비중 이동 (스냅샷 격자가 못 보여주는 시간축). 새 fetch 0(wf 이미 메모리).
	const wfTrend = $derived(workforceTrend(wf));
	// 연간 매출(조) ÷ 인원 = 1인당 매출(억) · finBundle annual 과 연도 매칭 (추가 fetch 없음)
	const revByYear = $derived.by<Map<string, number>>(() => {
		const out = new Map<string, number>();
		const av = finBundle?.views.annual;
		if (!av) return out;
		const row = av.statements.IS.find((r) => r.key === 'revenue');
		if (!row) return out;
		av.periods.forEach((p, i) => {
			const m = p.match(/^FY(\d{2})$/);
			const v = row.values[i];
			if (m && v != null) out.set('20' + m[1], v);
		});
		return out;
	});
	const revPerEmp = (w: { year: string; total: number | null }): number | null => {
		const rev = revByYear.get(w.year);
		return rev != null && w.total ? +((rev * 1e12) / w.total / 1e8).toFixed(1) : null; // 억
	};
	const srLast = $derived(srs.length ? srs[srs.length - 1] : null);
	// 주주환원 자기이력 · 최근 연속 배당 연수 + 배당성향 이동 + 소각(appears-when-clean). 새 fetch 0(srs 이미 메모리).
	const retTrend = $derived(returnTrend(srs));
	const fmtShares = (v: number | null): string => (v == null ? '·' : v >= 1e8 ? (v / 1e8).toFixed(1) + '억주' : v >= 1e4 ? (v / 1e4).toFixed(0) + '만주' : v.toLocaleString() + '주');
	// 타법인출자 도시에 섹션 · lossPct(적자 계열 자본, 항상 켜진 앵커) + control-shift(지배 이동). 새 fetch 0(inv·shPeriods 이미 메모리).
	const invLoss = $derived(inv && inv.rows.length ? lossSummary(inv.rows) : null);
	const ctrlShift = $derived(controlShiftSummary(shPeriods));
	// control-shift 자기정규화 문장(판정 0·형용사 0·명시 기간 라벨). 토큰 non-null 일 때만.
	const ctrlShiftText = (c: ControlShift, l: Lang): string => {
		const parts: string[] = [];
		if (c.fromPct != null && c.toPct != null)
			parts.push(l === 'en' ? `controlling stake ${c.fromPct.toFixed(0)}%→${c.toPct.toFixed(0)}% (${c.fromLabel}→${c.toLabel})` : `최대주주측 ${c.fromPct.toFixed(0)}%→${c.toPct.toFixed(0)}% (${c.fromLabel}→${c.toLabel})`);
		if (c.newNamed > 0) parts.push(l === 'en' ? `+${c.newNamed} new corp/inst holders` : `신규 법인·기관주주 ${c.newNamed}`);
		return parts.join(' · ');
	};

	const risks = $derived(co.risks);
	const pc = $derived(co.percentile);
	const pcCol = (p: number) => (p >= 80 ? 'var(--up)' : p >= 55 ? 'var(--good)' : p >= 35 ? 'var(--warn)' : 'var(--dn)');
	const pcFmtV = (m: { unit: string; v: number | null }) =>
		m.v == null
			? '·'
			: m.unit === 'rev'
				? (m.v / 1e12).toFixed(1) + '조'
				: m.unit === '배'
					? m.v.toFixed(1) + '배'
					: m.unit === '일'
						? m.v.toFixed(0) + '일'
						: m.unit === ''
							? m.v.toFixed(2)
							: m.v.toFixed(1) + (m.unit === '%' ? '%' : '');

	const cr = $derived(co.credit);
	const ch = $derived(co.changes);
	const chMax = $derived(Math.max(...ch.map((c) => (c.v == null ? 0 : Math.abs(c.v))), 1));
	const peers = $derived(co.peers);
	const peerMax = $derived(Math.max(...peers.map((p) => p.revenue || 0), 1));
	const e = $derived(co.eco);
	const govCells = $derived([
		{ l: lang === 'en' ? 'GOV' : '거버넌스', v: e.govGrade || '·', t: gradeTone('gov', e.govGrade) },
		{ l: lang === 'en' ? 'STABILITY' : '경영안정', v: e.stability || '·', t: gradeTone('stab', e.stability) },
		{ l: lang === 'en' ? 'OWNER %' : '대주주', v: e.holderPct != null ? e.holderPct.toFixed(1) + '%' : '·', t: 'neutral' },
		{ l: lang === 'en' ? 'OWNER Δ' : '지분변화', v: e.holderChange != null ? sign(e.holderChange, 1) + '%p' : '·', t: 'neutral' },
		{ l: lang === 'en' ? 'AUDIT' : '감사위험', v: e.auditRisk || (lang === 'en' ? 'n/a' : '해당없음'), t: gradeTone('audit', e.auditRisk) },
		{ l: lang === 'en' ? 'QUALITY' : '이익질', v: e.qualGrade || '·', t: gradeTone('qual', e.qualGrade) },
		{ l: lang === 'en' ? 'LIQUID' : '유동성', v: e.liqGrade || '·', t: gradeTone('liq', e.liqGrade) }
	]);
	// 현금흐름 실수치 (조) · 패널 제목 '현금흐름' 충족(기존엔 패턴 라벨만). FCF = 영업+투자.
	const cf = $derived(co.financials.cf);
	const cfCells = $derived([
		{ l: lang === 'en' ? 'CFO' : '영업CF', v: cf.op, good: cf.op != null ? cf.op > 0 : null },
		{ l: lang === 'en' ? 'CFI' : '투자CF', v: cf.inv, good: null },
		{ l: lang === 'en' ? 'CFF' : '재무CF', v: cf.fin, good: null },
		{ l: 'FCF', v: cf.fcf, good: cf.fcf != null ? cf.fcf > 0 : null }
	]);
	// 전년 대비 모멘텀 델타 (방향 신호). inv=true → 낮을수록 양호(부채). null 은 사전 제거(타입 확정).
	const govDeltas = $derived(
		([
			{ l: lang === 'en' ? 'Rev YoY' : '매출 YoY', v: e.revenueYoyPct ?? null, u: '%', inv: false },
			{ l: 'ROE Δ', v: e.roeDelta ?? null, u: '%p', inv: false },
			{ l: lang === 'en' ? 'OPM Δ' : '영업益 Δ', v: e.opMarginDelta ?? null, u: '%p', inv: false },
			{ l: lang === 'en' ? 'Debt Δ' : '부채 Δ', v: e.debtRatioDelta ?? null, u: '%p', inv: true }
		] as { l: string; v: number | null; u: string; inv: boolean }[]).filter(
			(d): d is { l: string; v: number; u: string; inv: boolean } => d.v != null
		)
	);
	const s = $derived(co.story);
	const dartUrl = 'https://dart.fss.or.kr/dsab007/main.do';
	let corpMeta = $state<Record<string, ProductIndexItem> | null>(null);
	rt.company.productIndex().then((m) => (corpMeta = m));
	const homepage = $derived(corpMeta?.[co.code]?.homepage ?? null);
	const homepageHost = $derived(homepage ? homepage.replace(/^https?:\/\//, '').replace(/\/$/, '') : '');
	const conf = $derived(cr.healthScore >= 70 ? 'HIGH' : 'MEDIUM');
</script>

<!-- RISK FLAGS · 글랜스는 점등(red/yellow)만. 헤더 '상세보기' → 점검 차원 전체 카탈로그·조건·현상태 다이얼로그. -->
<Panel {lang} className="eCredit" prov="real" title={{ kr: '리스크 경고등', en: 'RISK FLAGS' }}>
	{#snippet right()}<span><b class="tDn">{risks.filter((r) => r.lv === 'red').length}</b> <b class="tWarn">{risks.filter((r) => r.lv === 'yellow').length}</b></span><button class="finFullBtn" onclick={() => (riskDlgOpen = true)} title={lang === 'en' ? 'what each light checks · conditions & this company' : '각 경고등이 점검하는 조건 · 이 회사 현상태'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
	<div class="riskWrap">
		{#each risks as r, i (i)}
			<div class={'riskRow ' + r.lv}><span class={'riskDot ' + r.lv}></span><span class="riskName">{lang === 'en' ? r.en : r.kr}</span>{#if r.d}<span class="riskDetail">{r.d}</span>{/if}</div>
		{/each}
	</div>
</Panel>

<!-- 리스크 경고등 설명 · 점검 차원 전체 카탈로그 + 이 회사 현상태(점등/통과/판정불가) + 조건·소스. lazy: 닫혀 있으면 청크 무증가 -->
{#if riskDlgOpen}
	{#await import('./RiskFlagsDialog.svelte') then { default: RiskFlagsDialog }}
		<RiskFlagsDialog {co} {lang} onClose={() => (riskDlgOpen = false)} />
	{/await}
{/if}

<!-- 포렌식 적신호 · 풀스크린 재무탭에 묻힌 결정론 위험지표(감사독립성·단기상환벽) 승격. 임계 초과만 표시(정상=무표시). -->
{#if forensic.length}
	<Panel {lang} className="eCredit" prov="real" title={{ kr: '포렌식 적신호', en: 'FORENSIC FLAGS' }} sub={{ kr: '감사·부채 기준', en: 'audit·debt' }} flush>
		{#snippet right()}<button class="finFullBtn" onclick={() => (tablesOpen = true)} title={lang === 'en' ? 'open financials fullscreen' : '재무 전체화면에서 상세 보기'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
		<div class="riskWrap">
			{#each forensic as f (f.id)}
				<div class={'riskRow ' + (f.level === 'red' ? 'red' : 'yellow')}>
					<span class={'riskDot ' + (f.level === 'red' ? 'red' : 'yellow')}></span>
					<span class="riskName">{lang === 'en' ? f.en : f.kr}</span>
					<span class="riskDetail mono">{f.val}</span>
				</div>
			{/each}
		</div>
		<div class="finNote">{lang === 'en' ? 'breached thresholds only' : '임계 초과만 표시'}</div>
	</Panel>
{/if}

<!-- PERCENTILE -->
{#if pc && pc.metrics.length}
	<Panel {lang} className="eQuant" prov="real" title={{ kr: '업종 내 백분위', en: 'INDUSTRY PERCENTILE' }} sub={{ kr: pc.industry + ' ' + pc.n + '사', en: pc.industry + ' n=' + pc.n }} flush>
		{#snippet right()}<button class="finFullBtn" onclick={() => (pctCrossOpen = true)} title={lang === 'en' ? 'cross-universe percentile (industry · market · all listed)' : '유니버스 교차 백분위 · 업종·시장·전체상장사'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
		<!-- 좌우 2분할 · 셀 2줄(라벨·값 윗줄 / 반폭 얇은 막대 아랫줄) · 가로막대+중앙선 메타포 보존하며 높이 절반 -->
		<div class="pctList">
			{#each pc.metrics.filter((m) => m.axis !== 'gov') as m (m.en)}
				<div class="pctRow">
					<div class="pctHd">
						<span class="pctName">{txc(m, lang)}</span>
						<span class="pctVal"><b style={`color:${pcCol(m.p)}`}>{lang === 'en' ? 'top ' + (100 - m.p + 1) + '%' : '상위 ' + (100 - m.p + 1) + '%'}</b> <span class="dim">{pcFmtV(m)}</span></span>
					</div>
					<div class="pctTrack"><div class="pctFill" style={`width:${m.p}%;background:${pcCol(m.p)}`}></div><div class="pctMark" style="left:50%"></div></div>
				</div>
			{/each}
		</div>
	</Panel>
{/if}

<!-- 유니버스 교차 백분위 · 업종/시장/전체상장사 한 좌표(분포 사실만, 판정 0). lazy: 닫혀 있으면 청크 무증가 -->
{#if pctCrossOpen}
	{#await import('./PercentileCrossDialog.svelte') then { default: PercentileCrossDialog }}
		<PercentileCrossDialog {co} {lang} {percentileIn} onClose={() => (pctCrossOpen = false)} />
	{/await}
{/if}

<!-- 이익 풀 · 이 회사 산업의 공정별 영업이익률·매출 (이익은 어느 단계가 버나) -->
{#if poolRows}
	<Panel {lang} className="eIndustry" prov="real" title={{ kr: '이익 풀', en: 'PROFIT POOL' }} sub={{ kr: tx(co.sector, lang) + ' · 공정별 이익률·매출', en: tx(co.sector, lang) + ' · margin·rev by stage' }} flush>
		<div class="poolWrap">
			{#each poolRows.rows as s (s.key)}
				<div
					class="poolCol"
					class:poolMax={s.isMarginMax}
					title={`${s.name} · ${lang === 'en' ? 'OP margin' : '영업이익률'} ${s.opMarginPct}% · ${lang === 'en' ? 'rev' : '매출'} ${fmtPoolRev(s.revenue)} · ${s.companyCount}${lang === 'en' ? '' : '사'} · ${lang === 'en' ? 'cov' : '커버리지'} ${Math.round(s.coverageRatio * 100)}%`}
				>
					<span class="poolColName">{s.name}</span>
					<b class={'poolColOpm ' + ((s.opMarginPct ?? 0) < 0 ? 'tDn' : 'tUp')}>{s.opMarginPct}%</b>
					<span class="poolColRev mono"
						>{fmtPoolRev(s.revenue)}{#if s.isRevMax}<i class="poolTag">{lang === 'en' ? 'rev↑' : '매출↑'}</i>{/if}</span
					>
				</div>
			{/each}
		</div>
		<div class="poolNote">
			{#if poolRows.diverges}
				{#if lang === 'en'}Profit pools in <b>{poolRows.byMargin.name}</b> ({poolRows.byMargin.opMarginPct}%) · not the biggest-revenue stage ({poolRows.byRev.name}){:else}이익은 <b>{poolRows.byMargin.name}</b>({poolRows.byMargin.opMarginPct}%)에서 · 매출 최대({poolRows.byRev.name})와 다른 단계{/if}
			{:else}
				{#if lang === 'en'}Both profit & revenue peak at <b>{poolRows.byMargin.name}</b>{:else}이익·매출 모두 <b>{poolRows.byMargin.name}</b> 집중{/if}
			{/if} · {lang === 'en' ? 'listed-only · rev-weighted' : '상장사 기준·매출가중'}
		</div>
	</Panel>
{/if}

<!-- FINANCIALS -->
<Panel {lang} className="eAnalysis" prov="real" title={{ kr: '재무제표', en: 'FINANCIAL STATEMENTS' }} sub={finView ? { kr: finModeLabel[finMode] + ' · ' + finView.periods.length + '기 · ' + finUnit, en: finMode + ' · ' + finView.periods.length + 'p' } : undefined} flush>
	{#snippet right()}
		{#if finBundle && finBundle.availScopes.length > 1}
			<span class="segGroup mini">{#each finBundle.availScopes as s (s)}<button class={finBundle.scope === s ? 'seg on' : 'seg'} onclick={() => (finScope = s)} title={s === 'CFS' ? (lang === 'en' ? 'consolidated' : '연결재무제표') : (lang === 'en' ? 'separate' : '별도재무제표')}>{finScopeLabel(s)}</button>{/each}</span>
		{/if}
		{#if finBundle && finBundle.modes.length > 1}
			<span class="segGroup mini">{#each finBundle.modes as m (m)}<button class={finMode === m ? 'seg on' : 'seg'} onclick={() => (finMode = m)}>{lang === 'en' ? m.toUpperCase() : finModeLabel[m]}</button>{/each}</span>
		{/if}
		<button class="finFullBtn" onclick={() => (tablesOpen = true)} title={lang === 'en' ? 'quantitative statements (viewer dialog)' : '정량재무제표 · 공시뷰어와 동일 (IS/BS/CF/CIS/자본변동 · 연결/별도)'}>{lang === 'en' ? 'detail' : '상세보기'}</button>
	{/snippet}
	<div class="finTabs">{#each tabs as t (t.k)}<button class={'finTab ' + (stmt === t.k ? 'on' : '')} onclick={() => (stmt = t.k)}>{lang === 'en' ? t.en : t.kr}</button>{/each}</div>
	{#if finView}
		<div class="finScroll finScrollX"><table class="finTable">
			<thead><tr><th class="finAcct">{lang === 'en' ? 'ACCOUNT' : '계정'}</th>{#each dispPeriods as p (p)}<th class="r">{p}</th>{/each}</tr></thead>
			<tbody>
				{#each stmtRows as r (r.key)}
					<tr class={KEY_ROWS.includes(r.key) ? 'finKey' : ''}>
						<td class="finAcct">{lang === 'en' ? r.en : r.kr}{#if r.unit}<span class="finUnit">{r.unit}</span>{/if}</td>
						{#each r.values.slice().reverse() as val, i (i)}<td class={'r mono ' + (val != null && val < 0 ? 'tDn' : '')}>{val == null ? '·' : stmt === 'RT' ? fmtNum(val, 1) : finVal(val)}</td>{/each}
					</tr>
				{/each}
			</tbody>
		</table></div>
	{:else}
		<div class="chartLoad" style="height:90px">{lang === 'en' ? 'loading statements …' : '재무제표 불러오는 중 …'}</div>
	{/if}
</Panel>

<!-- 인력 · 생산성 (정기보고서 임직원 현황 · 인원·급여·근속·1인당매출) -->
{#if wfLast}
	<Panel {lang} className="eIndustry" prov="real" title={{ kr: '인력 · 생산성', en: 'WORKFORCE' }} sub={{ kr: wfLast.year, en: wfLast.year }} flush>
		{#snippet right()}<button class="finFullBtn" onclick={() => requestFinFull('people')} title={lang === 'en' ? 'workforce & pay timeseries (fullscreen PEOPLE tab)' : '인력·보수 시계열 · 전체화면 인력 탭'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
		<!-- 자기이력 1줄 · 스냅샷 격자가 못 보여주는 시간축(총원 궤적·계약직 비중 이동). 판정·형용사 0·명시 기간 라벨. -->
		{#if wfTrend && (wfTrend.headPct != null || (wfTrend.contractFromPct != null && wfTrend.contractToPct != null && Math.abs(wfTrend.contractToPct - wfTrend.contractFromPct) >= 1))}
			<div class="secSentBox">
				{#if wfTrend.headPct != null}
					<div class="secSent">▼ {lang === 'en' ? `headcount ${wfTrend.fromYear}→${wfTrend.toYear} ${sign(wfTrend.headPct, 0)}% (${wfTrend.headFrom.toLocaleString()}→${wfTrend.headTo.toLocaleString()})` : `총원 ${wfTrend.fromYear}→${wfTrend.toYear} ${sign(wfTrend.headPct, 0)}% (${wfTrend.headFrom.toLocaleString()}→${wfTrend.headTo.toLocaleString()}명)`}</div>
				{/if}
				{#if wfTrend.contractFromPct != null && wfTrend.contractToPct != null && Math.abs(wfTrend.contractToPct - wfTrend.contractFromPct) >= 1}
					<div class="secSent">▼ {lang === 'en' ? `contract share ${wfTrend.contractFromPct.toFixed(0)}%→${wfTrend.contractToPct.toFixed(0)}%` : `계약직 비중 ${wfTrend.contractFromPct.toFixed(0)}%→${wfTrend.contractToPct.toFixed(0)}%`}</div>
				{/if}
			</div>
		{/if}
		<div class="factGrid">
			<div class="factRow"><span class="factL">{lang === 'en' ? 'headcount' : '총원'}</span><span class="factV mono">{wfLast.total != null ? wfLast.total.toLocaleString() + (lang === 'en' ? '' : '명') : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'M / F' : '남 / 여'}</span><span class="factV mono">{wfLast.male != null ? wfLast.male.toLocaleString() : '·'} / {wfLast.female != null ? wfLast.female.toLocaleString() : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'regular : contract' : '정규 : 계약'}</span><span class="factV mono">{wfLast.regular != null ? wfLast.regular.toLocaleString() : '·'} : {wfLast.contract != null ? wfLast.contract.toLocaleString() : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'avg salary' : '평균급여'}</span><span class="factV mono">{wfLast.avgSalary != null ? (wfLast.avgSalary / 1e8).toFixed(2) + (lang === 'en' ? ' ×0.1B' : '억') : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'tenure' : '평균근속'}</span><span class="factV mono">{wfLast.tenure != null ? wfLast.tenure.toFixed(1) + (lang === 'en' ? 'y' : '년') : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'rev / emp' : '1인당 매출'}</span><span class="factV mono">{revPerEmp(wfLast) != null ? revPerEmp(wfLast) + (lang === 'en' ? ' ×0.1B' : '억') : '·'}</span></div>
		</div>
	</Panel>
{/if}

<!-- 주주환원 (배당 + 자사주 · 정기보고서) -->
{#if srLast}
	<Panel {lang} className="eValuation" prov="real" title={{ kr: '주주환원', en: 'SHAREHOLDER RETURN' }} sub={{ kr: srLast.year, en: srLast.year }} flush>
		{#snippet right()}<button class="finFullBtn" onclick={() => requestFinFull('shareholder')} title={lang === 'en' ? 'shareholder return & ownership timeseries (fullscreen RETURN tab)' : '주주환원·소유 시계열 · 전체화면 주주환원 탭'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
		<!-- 환원 자기이력 1줄 · 연속 배당 연수·배당성향 이동·소각(appears-when-clean). 흐름막대는 상세보기(center, 그래프 합법). -->
		{#if retTrend && (retTrend.streak >= 2 || (retTrend.payoutFromPct != null && retTrend.payoutToPct != null) || retTrend.cancelQty != null)}
			<div class="secSentBox">
				{#if retTrend.streak >= 2}
					<div class="secSent">▼ {lang === 'en' ? `${retTrend.streak}-yr consecutive dividend (~${retTrend.streakToYear})` : `최근 ${retTrend.streak}년 연속 배당 (~${retTrend.streakToYear})`}</div>
				{/if}
				{#if retTrend.payoutFromPct != null && retTrend.payoutToPct != null}
					<div class="secSent">▼ {lang === 'en' ? `payout ${retTrend.payoutFromPct.toFixed(0)}%→${retTrend.payoutToPct.toFixed(0)}% (${retTrend.payoutFromYear}→${retTrend.payoutToYear})` : `배당성향 ${retTrend.payoutFromPct.toFixed(0)}%→${retTrend.payoutToPct.toFixed(0)}% (${retTrend.payoutFromYear}→${retTrend.payoutToYear})`}</div>
				{/if}
				{#if retTrend.cancelQty != null}
					<div class="secSent">▼ {lang === 'en' ? `treasury cancelled ${fmtShares(retTrend.cancelQty)} (${retTrend.cancelYear})` : `자사주 소각 ${fmtShares(retTrend.cancelQty)} (${retTrend.cancelYear})`}</div>
				{/if}
			</div>
		{/if}
		<div class="factGrid">
			<div class="factRow"><span class="factL">DPS</span><span class="factV mono">{srLast.dps != null ? srLast.dps.toLocaleString() + (lang === 'en' ? ' KRW' : '원') : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'div yield' : '배당수익률'}</span><span class="factV mono">{srLast.yieldPct != null ? srLast.yieldPct.toFixed(1) + '%' : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'payout' : '배당성향'}</span><span class="factV mono">{srLast.payoutPct != null ? srLast.payoutPct.toFixed(1) + '%' : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'total dividend' : '현금배당총액'}</span><span class="factV mono">{srLast.totalDividend != null ? fmtKRW(srLast.totalDividend) : '·'}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'treasury (end)' : '자사주 기말'}</span><span class="factV mono">{fmtShares(srLast.treasuryEnd)}</span></div>
			<div class="factRow"><span class="factL">{lang === 'en' ? 'buyback / disposal' : '취득 / 처분'}</span><span class="factV mono">{fmtShares(srLast.buybackQty)} / {fmtShares(srLast.disposalQty)}</span></div>
		</div>
	</Panel>
{/if}

<!-- 타법인 출자 (자회사·투자 · 장부가액 상위) -->
{#if inv && inv.rows.length}
	<Panel {lang} className="eCredit" prov="real" title={{ kr: '타법인 출자', en: 'HOLDINGS' }} sub={{ kr: inv.year, en: inv.year }} flush>
		{#snippet right()}<span class="dim">{(inv?.rows.length ?? 0) + (inv?.moreCount ?? 0)}{lang === 'en' ? '' : '개사'}</span><button class="finFullBtn" onclick={() => (holdingsOpen = true)} title={lang === 'en' ? 'Relationship analysis (fullscreen)' : '출자 관계 분석 · 전체화면'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
		{#if (invLoss && invLoss.lossCount > 0 && invLoss.lossPct != null) || (ctrlShift && ((ctrlShift.fromPct != null && ctrlShift.toPct != null) || ctrlShift.newNamed > 0))}
			<div class="secSentBox">
				{#if invLoss && invLoss.lossCount > 0 && invLoss.lossPct != null}
					<div class="secSent">▼ {lang === 'en' ? `loss-making investees = ${invLoss.lossPct.toFixed(0)}% of investment book` : `적자 피출자사 = 출자 장부가의 ${invLoss.lossPct.toFixed(0)}%`}</div>
				{/if}
				{#if ctrlShift && ((ctrlShift.fromPct != null && ctrlShift.toPct != null) || ctrlShift.newNamed > 0)}
					<div class="secSent">▼ {ctrlShiftText(ctrlShift, lang)}</div>
				{/if}
			</div>
		{/if}
		<div class="finScroll"><table class="finTable">
			<thead><tr>
				<th class="finAcct">{lang === 'en' ? 'COMPANY' : '법인명'}</th>
				<th>{lang === 'en' ? 'PURPOSE' : '목적'}</th>
				<th class="r">{lang === 'en' ? 'STAKE' : '지분'}</th>
				<th class="r">{lang === 'en' ? 'BOOK' : '장부가'}</th>
				<th class="r">{lang === 'en' ? 'TARGET NET' : '피출자 순익'}</th>
			</tr></thead>
			<tbody>
				{#each inv.rows as r (r.name)}
					<tr class={r.stakePct != null && r.stakePct >= 50 ? 'finKey' : ''}>
						<td class="finAcct" title={r.name}>{r.name}</td>
						<td>{r.purpose}</td>
						<td class="r mono">{r.stakePct != null ? r.stakePct.toFixed(1) + '%' : '·'}</td>
						<td class="r mono">{r.bookValue != null ? fmtKRW(r.bookValue) : '·'}</td>
						<td class={'r mono ' + (r.targetNet != null && r.targetNet < 0 ? 'tDn' : '')}>{r.targetNet != null ? (r.targetNet < 0 ? '-' : '') + fmtKRW(Math.abs(r.targetNet)) : '·'}</td>
					</tr>
				{/each}
			</tbody>
		</table></div>
		{#if inv.moreCount}
			<div class="finNote">{lang === 'en' ? `+${inv.moreCount} more · book ${fmtKRW(inv.moreBook)}` : `외 ${inv.moreCount}개사 · 장부가 합계 ${fmtKRW(inv.moreBook)}`}</div>
		{/if}
	</Panel>
{/if}

<!-- 출자 관계 분석 전체화면 · 성격·위계 / 가치 / 효율 3축 진단 (lazy: 닫혀 있으면 청크 무증가) -->
{#if holdingsOpen && inv}
	{#await import('./HoldingsDialog.svelte') then { default: HoldingsDialog }}
		<HoldingsDialog {co} year={inv.year} rows={inv.rows} trend={invTrend} periods={invPeriods} {shareholders} shPeriods={shPeriods} {lang} {lookupListed} {onPick} onClose={() => (holdingsOpen = false)} />
	{/await}
{/if}

<!-- 정기보고서 주석 · 글랜스 한 줄(비용·부문 비중=real digest) + 상세보기(분기 시계열 다이얼로그). 정부 XBRL 직독.
     상태 피드백(loading/error/ready) 항상 렌더. 미공시(empty)만 숨김(클러터 회피). -->
{#if notesState !== 'empty'}
	<Panel {lang} className="eCredit" prov="real" title={{ kr: '정기보고서 주석', en: 'REPORT NOTES' }} flush>
		{#snippet right()}{#if notesState === 'ready'}<button class="finFullBtn" onclick={() => (dashOpen = true)} title={lang === 'en' ? 'cost chassis · segment revenue (quarterly)' : '비용 체질 · 부문별 매출 (분기 시계열)'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/if}{/snippet}
		<!-- lazy sentinel · 뷰포트 근처(800px) 진입 시 noteSeries read 트리거. panel contentRaw 무거워 콜드 버스트 회피. -->
		<div bind:this={notesSentinel} aria-hidden="true" style="height:0;margin:0"></div>
		{#if notesState === 'idle'}
			<div class="storyEmpty dim" role="status">{lang === 'en' ? 'scroll to load notes' : '스크롤하면 주석 로드'}</div>
		{:else if notesState === 'loading'}
			<div class="storyEmpty" role="status" aria-busy="true">{lang === 'en' ? 'reading notes …' : '주석 읽는 중 …'}</div>
		{:else if notesState === 'error'}
			<div class="storyEmpty" role="status">{lang === 'en' ? 'failed to load notes' : '주석 불러오지 못함'}</div>
		{:else}
			{#if costBar}
				<div class="noteSeg">
					<div class="noteSegHd"><span class="ngLabel">{lang === 'en' ? 'cost' : '비용'}</span></div>
					<div class="noteBar">{#each costBar.segs as s (s.name)}<i style={`width:${s.pct}%;background:${s.color}`} title={`${niceCat(s.name)} ${s.pct.toFixed(0)}%`}></i>{/each}</div>
					<div class="noteKeys">{#each topChips(costBar.segs) as s (s.name)}<span><i style={`background:${s.color}`}></i>{niceCat(s.name)} {s.pct.toFixed(0)}</span>{/each}</div>
				</div>
			{/if}
			{#if segBar}
				<div class="noteSeg">
					<div class="noteSegHd"><span class="ngLabel">{lang === 'en' ? 'seg' : '부문'}</span></div>
					<div class="noteBar">{#each segBar.segs as s (s.name)}<i style={`width:${s.pct}%;background:${s.color}`} title={`${niceCat(s.name)} ${s.pct.toFixed(0)}%`}></i>{/each}</div>
					<div class="noteKeys">{#each topChips(segBar.segs) as s (s.name)}<span><i style={`background:${s.color}`}></i>{niceCat(s.name)} {s.pct.toFixed(0)}</span>{/each}</div>
				</div>
			{/if}
			{#if !costBar && !segBar}
				<div class="noteGlance dim">{lang === 'en' ? 'detail ▸' : '상세보기 ▸'}</div>
			{/if}
		{/if}
	</Panel>
{/if}

<!-- 사업 서술 표 · 생산능력·원재료·매출수주 (II.사업의내용 표 격자전개). 글랜스 토픽 칩 + 상세보기. -->
{#if bizState !== 'empty'}
	<Panel {lang} className="eIndustry" prov="real" title={{ kr: '사업 서술 표', en: 'BUSINESS TABLES' }} flush>
		{#snippet right()}{#if bizState === 'ready'}<button class="finFullBtn" onclick={() => (bizOpen = true)} title={lang === 'en' ? 'production · materials · sales/orders' : '생산능력 · 원재료 · 매출수주'}>{lang === 'en' ? 'detail' : '상세보기'}</button>{/if}{/snippet}
		{#if bizState === 'idle'}
			<div class="storyEmpty dim" role="status">{lang === 'en' ? 'scroll to load' : '스크롤하면 로드'}</div>
		{:else if bizState === 'loading'}
			<div class="storyEmpty" role="status" aria-busy="true">{lang === 'en' ? 'reading tables …' : '표 읽는 중 …'}</div>
		{:else if bizState === 'error'}
			<div class="storyEmpty" role="status">{lang === 'en' ? 'failed to load' : '불러오지 못함'}</div>
		{:else if bizTables}
			<div class="noteKeys">{#each bizTables as t (t.topic)}<span>{BIZ_TOPIC_KR[t.topic] ?? t.title} <b>{t.rows.length}</b></span>{/each}</div>
		{/if}
	</Panel>
{/if}

<!-- 주석 상세 다이얼로그 (lazy) · import/마운트 실패는 {:catch} 로 가시화(과거 catch 부재 시 무표시=안 뜬 것처럼 보임). -->
{#if dashOpen}
	{#await import('./NotesDashboardDialog.svelte')}
		<!-- 청크 로딩 중 · 무표시(즉시 도착) -->
	{:then { default: NotesDashboardDialog }}
		<NotesDashboardDialog {co} {lang} cost={noteBundle?.cost ?? null} segment={noteBundle?.segment ?? null} onClose={() => (dashOpen = false)} />
	{:catch err}
		<div class="scrimWrap" role="presentation" onclick={() => (dashOpen = false)}>
			<div class="scrModal" role="dialog" aria-modal="true" tabindex="-1" aria-label={lang === 'en' ? 'notes' : '주석'} onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.key === 'Escape' && (dashOpen = false)}>
				<div class="scrHead"><span class="scrTitle">{lang === 'en' ? 'NOTES' : '주석'}</span><button class="scrClose" onclick={() => (dashOpen = false)} aria-label="close">✕</button></div>
				<div class="ndBody"><div class="storyEmpty">{lang === 'en' ? 'failed to open detail' : '상세 열기 실패'} · {String((err as Error)?.message ?? err)}</div></div>
			</div>
		</div>
	{/await}
{/if}

<!-- 사업 서술 표 상세 (lazy) -->
{#if bizOpen}
	{#await import('./BusinessTablesDialog.svelte') then { default: BusinessTablesDialog }}
		<BusinessTablesDialog {co} {lang} tables={bizTables ?? []} onClose={() => (bizOpen = false)} />
	{/await}
{/if}

<!-- 공급망 (dartlab 고유 · 공급사·고객사 제품·매출비중) -->
{#if relations && (relations.suppliers.length || relations.customers.length)}
	<Panel {lang} className="eIndustry" prov="real" title={{ kr: '공급망 · 거래선', en: 'SUPPLY CHAIN' }} flush>
		<div class="scWrap">
			<div class="scCol">
				<div class="scHd tUp">▼ {lang === 'en' ? 'SUPPLIERS' : '공급사'}</div>
				{#each relations.suppliers as e (e.stockCode + e.product)}
					<div class="scRow" role="button" tabindex="0" onclick={() => onPick(e.stockCode)} onkeydown={(ev) => ev.key === 'Enter' && onPick(e.stockCode)}>
						<span class="scName"><b>{e.corpName}</b>{#if e.product}<span class="scProd">{e.product}</span>{/if}</span>
						{#if e.ratio != null}<span class="scRatio mono">{e.ratio.toFixed(1)}%</span>{/if}
					</div>
				{/each}
			</div>
			<div class="scCol">
				<div class="scHd tDn">▲ {lang === 'en' ? 'CUSTOMERS' : '고객사'}</div>
				{#each relations.customers as e (e.stockCode + (e.product || ''))}
					<div class="scRow" role="button" tabindex="0" onclick={() => onPick(e.stockCode)} onkeydown={(ev) => ev.key === 'Enter' && onPick(e.stockCode)}>
						<span class="scName"><b>{e.corpName}</b>{#if e.product}<span class="scProd">{e.product}</span>{/if}</span>
						{#if e.ratio != null}<span class="scRatio mono">{e.ratio.toFixed(1)}%</span>{/if}
					</div>
				{/each}
			</div>
		</div>
	</Panel>
{/if}

<div class="rowSplit">
	<!-- CREDIT -->
	<Panel {lang} className="eCredit" prov="derived" title={{ kr: '신용분석', en: 'CREDIT' }} sub={{ kr: '비공식', en: 'unofficial' }} flush>
		<div class="creditTop"><div class="creditGrade"><span class="cgVal tCredit">{cr.grade}</span><span class="cgSub">{lang === 'en' ? 'health' : '건전도'} <b class={toneClass(cr.tone)}>{cr.healthScore}</b>/100 · PD <b class="tNeu">{cr.pd}</b></span></div></div>
		<div class="creditTracks">{#each cr.tracks as t (t.en)}<div class="ctRow"><span class="ctName">{txc(t, lang)}</span><div class="ctTrack"><div class="ctFill" style={`width:${t.score}%`}></div></div><span class="ctVal mono">{t.score}</span></div>{/each}</div>
		<div class="creditDiv">{lang === 'en' ? `Debt ${cr.basis.debtRatio != null ? cr.basis.debtRatio.toFixed(0) + '%' : '·'}, current ${cr.basis.curr != null ? cr.basis.curr + '%' : '·'}. Heuristic dCR · not official.` : `부채비율 ${cr.basis.debtRatio != null ? cr.basis.debtRatio.toFixed(0) + '%' : '·'}, 유동비율 ${cr.basis.curr != null ? cr.basis.curr + '%' : '·'}. 휴리스틱 dCR · 공식등급 아님.`}</div>
	</Panel>
	<!-- CHANGES -->
	<Panel {lang} className="eChanges" prov="derived" title={{ kr: '전년 대비 변화', en: 'YoY CHANGES' }} flush>
		<div class="chgList">
			{#each ch as c (c.en)}
				{@const has = c.v != null}
				{@const good = has && (c.invert ? c.v! < 0 : c.v! > 0)}
				{@const w = has ? Math.min(50, (Math.abs(c.v!) / chMax) * 50) : 0}
				<div class="chgRow">
					<span class="chgName">{txc(c, lang)}</span>
					<div class="chgBarWrap"><div class="chgBarMid"></div>{#if has}<div class={'chgBar ' + (c.v! >= 0 ? 'pos' : 'neg')} style={`width:${w}%;${c.v! >= 0 ? 'left:50%' : 'right:50%'};background:${good ? 'var(--up)' : 'var(--dn)'}`}></div>{/if}</div>
					<span class={'chgVal ' + (has ? (good ? 'tUp' : 'tDn') : 'tNeu')}>{has ? sign(c.v, 1) + c.unit : '·'}</span>
				</div>
			{/each}
		</div>
		<div class="finNote">직전 사업연도 대비</div>
	</Panel>
</div>

<!-- 공시 목록 · 정기 ‖ 비정기(allFilings) 2분할. data-fdate = 주가차트 공시 dot 클릭 시 스크롤·하이라이트 대상 키(YYYYMMDD). -->
<div class="rowSplit" bind:this={filingWrap}>
	<Panel {lang} className="eChanges" prov="real" title={{ kr: '정기공시', en: 'REGULAR' }} flush>
		{#snippet right()}<button class="finFullBtn" onclick={() => (viewerOpen = true)} title="공시뷰어 전체화면 · 터미널 안에서 열기">{lang === 'en' ? 'detail' : '상세보기'}</button>{/snippet}
		{#if regFilings.length}
			<div class="filingList">
				{#each regFilings as f (f.rceptNo)}
					<a class="filingRow" class:flash={flashDate === fdate(f.rceptDate)} data-fdate={fdate(f.rceptDate)} href={f.url} target="_blank" rel="noopener">
						<span class="flType">{f.reportType}</span>
						<span class="flYear mono">{f.year}</span>
						<span class="flDate mono">{f.rceptDate}</span>
						<span class="flArrow">↗</span>
					</a>
				{/each}
			</div>
		{:else}
			<div class="storyEmpty">{lang === 'en' ? 'no regular filings' : '정기공시 없음'}</div>
		{/if}
	</Panel>
	<Panel {lang} className="eChanges" prov="real" title={{ kr: '비정기공시', en: 'OTHER FILINGS' }} sub={{ kr: '수시', en: 'ad-hoc' }} flush>
		{#snippet right()}<span class="dim">{nonRegState === 'ready' ? nonRegFilings.length : ''}</span>{/snippet}
		{#if nonRegState === 'ready'}
			<div class="filingList">
				{#each nonRegFilings as f (f.rceptNo)}
					<a class="filingRow nonreg" class:flash={flashDate === fdate(f.rceptDate)} data-fdate={fdate(f.rceptDate)} href={f.url} target="_blank" rel="noopener" title={f.reportNm + (f.filer ? ' · ' + f.filer : '')}>
						<span class="flType">{f.reportNm}</span>
						<span class="flDate mono">{f.rceptDate.slice(2)}</span>
						<span class="flArrow">↗</span>
					</a>
				{/each}
			</div>
		{:else if nonRegState === 'loading'}
			<div class="storyEmpty">{lang === 'en' ? 'scanning recent filings …' : '최근 공시 스캔 중 …'}</div>
		{:else}
			<div class="storyEmpty">{lang === 'en' ? 'no non-regular filings' : '비정기공시 없음'}</div>
		{/if}
	</Panel>
</div>

<!-- 종목 뉴스 · 네이버(검색·제목+스니펫). private(언론사 저작권)을 워커가 서버사이드 read 해 표시(라이브 표시,
     재배포 아님). 클릭=원문 이동, 주가차트 뉴스 dot 클릭=그 날짜 행 스크롤·하이라이트 동기.
     GDELT(과거 트랙)는 한국 종목 커버리지 사실상 0(실측) · 데이터 있을 때만 우측에 분할 표시(평시 단일 전폭). -->
{#snippet newsCol(byDate: [string, NewsItem[]][])}
	{#each byDate as [d8, items] (d8)}
		{#each items as it (it.url)}
			<a class="newsRow" class:flash={flashDate === d8} data-fdate={d8} href={it.url} target="_blank" rel="noopener" title={it.title + (it.description ? '\n\n' + it.description : '')}>
				<span class="nwTop"><span class="nwTitle">{it.title}</span><span class="flArrow">↗</span></span>
				{#if it.description}<span class="nwDesc">{it.description}</span>{/if}
				<span class="nwMeta mono">{it.source}{it.date ? ' · ' + it.date.slice(2) : ''}</span>
			</a>
		{/each}
	{/each}
{/snippet}
<div class={gdeltNews.length ? 'rowSplit' : ''} bind:this={newsWrap}>
	<Panel {lang} className="eChanges" prov="real" title={gdeltNews.length ? { kr: '네이버', en: 'NAVER' } : { kr: '종목 뉴스', en: 'NEWS' }} flush>
		{#snippet right()}<span class="dim">{newsState === 'ready' ? naverNews.length : ''}</span>{/snippet}
		{#if newsState === 'loading'}
			<div class="storyEmpty">{lang === 'en' ? 'loading news …' : '뉴스 불러오는 중 …'}</div>
		{:else if naverByDate.length}
			<div class="filingList newsList">{@render newsCol(naverByDate)}</div>
		{:else}
			<div class="storyEmpty">{lang === 'en' ? 'no naver news yet' : '아직 수집된 뉴스 없음'}</div>
		{/if}
	</Panel>
	{#if gdeltNews.length}
		<Panel {lang} className="eChanges" prov="real" title={{ kr: 'GDELT', en: 'GDELT' }} flush>
			{#snippet right()}<span class="dim">{gdeltNews.length}</span>{/snippet}
			<div class="filingList newsList">{@render newsCol(gdeltByDate)}</div>
		</Panel>
	{/if}
</div>

<div class="rowSplit">
	<!-- PEERS -->
	<Panel {lang} className="eIndustry" prov="real" title={{ kr: '동종업종', en: 'INDUSTRY PEERS' }} flush>
		{#snippet right()}<a class="lensScan" href="{base}/map?focus={co.code}" target="_blank" rel="noopener" title={lang === 'en' ? 'industry map · full ecosystem view' : '산업지도 · 업종 생태계 전체 보기'}>{lang === 'en' ? 'map ↗' : '맵 ↗'}</a>{/snippet}
		<div class="peerList">
			{#each peers as p (p.code)}
				<div class={'peerRow' + (p.self ? ' self' : '')} role="button" tabindex="0" onclick={() => onPick(p.code)} onkeydown={(ev) => ev.key === 'Enter' && onPick(p.code)}>
					<div class="peerTop">
					<span class="peerName"><b>{p.name}</b><span class="pc">{p.code}</span></span>
					<span class="peerBar"><span class="peerBarTrack"><span class="peerBarFill" style={`width:${((p.revenue || 0) / peerMax) * 100}%`}></span></span><span class="peerRev">{p.revenue != null ? (p.revenue / 10000).toFixed(1) + '조' : '·'}</span></span>
					</div>
					{#if corpMeta?.[p.code]?.product}<span class="peerProd">{corpMeta?.[p.code]?.product}</span>{/if}
				</div>
			{/each}
		</div>
	</Panel>
	<!-- GOVERNANCE -->
	<Panel {lang} className="eIndustry" prov="real" title={{ kr: '거버넌스 · 현금흐름', en: 'GOVERNANCE' }} flush>
		{#if e.cfPattern}<div class="patBig"><div class="pv">{e.cfPattern}</div><div class="ps">{lang === 'en' ? 'cash-flow pattern' : '현금흐름 패턴'}{e.empCount != null ? ' · ' + e.empCount.toLocaleString() + (lang === 'en' ? ' emp' : '명') : ''}</div></div>{/if}
		<div class="govGrid">{#each govCells as c (c.l)}<div class="govCell"><span>{c.l}</span><b class={tcls(c.t)}>{c.v}</b></div>{/each}</div>
		<div class="cfRow">
			{#each cfCells as c (c.l)}
				<div class="cfCell"><span>{c.l}</span><b class={'mono ' + (c.v == null ? 'tNeu' : c.good === true ? 'tUp' : c.good === false ? 'tDn' : c.v < 0 ? 'tDn' : 'tNeu')}>{c.v == null ? '·' : (c.v >= 0 ? '+' : '') + c.v.toFixed(1) + '조'}</b></div>
			{/each}
		</div>
		{#if govDeltas.length}
			<div class="govDeltaRow">
				{#each govDeltas as d (d.l)}<span class="govDelta"><i>{d.l}</i><b class={(d.inv ? d.v < 0 : d.v > 0) ? 'tUp' : d.v === 0 ? 'tNeu' : 'tDn'}>{sign(d.v, 1)}{d.u}</b></span>{/each}
			</div>
		{/if}
	</Panel>
</div>

<div class="rowSplit">
	<!-- STORY -->
	<Panel {lang} className="eCredit" prov="real" title={{ kr: 'DART · 스토리', en: 'DART · STORY' }} flush>
		{#if s}
			<div class="storyCard"><span class="storyTag">DARTLAB STORY</span><div class="storyTitle">{s.title}</div><div class="storyMeta">{s.date} · {s.readTime ?? ''} · <a class="storyLink" href="{base}/blog/{s.slug}" target="_blank" rel="noopener">read ↗</a></div></div>
		{:else}
			<div class="storyEmpty">{lang === 'en' ? 'No published dartlab story yet.' : '발간된 dartlab 스토리는 아직 없습니다.'}</div>
		{/if}
		<div class="storyCard" style="border-top:1px solid var(--bd)"><div class="storyMeta">{lang === "en" ? "Company homepage" : "회사 홈페이지"}</div>{#if homepage}<a class="storyLink" href={homepage} target="_blank" rel="noopener noreferrer" style="font-family:var(--mono);font-size:10px">{homepageHost} ↗</a>{:else}<span class="storyLink" style="font-family:var(--mono);font-size:10px;color:var(--dimmer)">{lang === "en" ? "n/a" : "홈페이지 정보 없음"}</span>{/if}</div>
	</Panel>
	<!-- SUMMARY (derived, 정직: 가짜 tool-call 제거) -->
	<Panel {lang} className="eAnalysis" prov="derived" title={{ kr: 'dartlab 요약', en: 'DARTLAB SUMMARY' }} flush>
		{#snippet right()}<span class="conf">CONF <b class={conf === 'HIGH' ? 'tUp' : 'tWarn'}>{conf}</b></span>{/snippet}
		<div class="aiQ">▸ {lang === 'en' ? `${co.name.kr} financial health` : `${co.name.kr} 재무건전성`}</div>
		<div class="aiAnswer">{lang === 'en'
			? `Derived dCR ${cr.grade} (health ${cr.healthScore}/100, PD ${cr.pd}). OP margin ${co.fundamentals.opm != null ? co.fundamentals.opm.toFixed(1) + '%' : '·'}, ROE ${co.fundamentals.roe != null ? co.fundamentals.roe.toFixed(1) + '%' : '·'}, debt ${co.fundamentals.dr != null ? co.fundamentals.dr.toFixed(0) + '%' : '·'}. All from real finance/ecosystem/prices data.`
			: `dartlab 파생 신용 ${cr.grade} (건전도 ${cr.healthScore}/100, PD ${cr.pd}). 영업이익률 ${co.fundamentals.opm != null ? co.fundamentals.opm.toFixed(1) + '%' : '·'}, ROE ${co.fundamentals.roe != null ? co.fundamentals.roe.toFixed(1) + '%' : '·'}, 부채비율 ${co.fundamentals.dr != null ? co.fundamentals.dr.toFixed(0) + '%' : '·'}. 모두 finance/ecosystem/prices 실데이터 산출.`}</div>
	</Panel>
</div>

{#if viewerOpen}
	<ViewerOverlay
		code={co.code}
		studio={hosts.viewerStudio}
		{repoUrl}
		onclose={() => (viewerOpen = false)}
	/>
{/if}

{#if tablesOpen}
	{#if hosts.financeDialog}
		{#await hosts.financeDialog() then m}
			{@const FinanceDialog = m.default}
			<!-- .dlTermFinSkin: --fin-* 토큰 오버라이드 (terminal.css) · CSS 변수는 fixed 모달에도 DOM 상속으로 관통 -->
			<div class="dlTermFinSkin">
				<FinanceDialog code={co.code} corpName={co.name.kr} open={tablesOpen} onclose={() => (tablesOpen = false)} />
			</div>
		{/await}
	{:else}
		<!-- 열화 안내 · 이 셸은 정량 재무제표 모달 미지원 (숨김 금지 원칙: 기능 존재는 보이고 한계를 안내) -->
		<div class="hostFallback" role="presentation" onclick={() => (tablesOpen = false)}>
			<div class="hostFallbackPanel" role="dialog" aria-modal="true" tabindex="-1" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.key === 'Escape' && (tablesOpen = false)}>
				<div class="hostFallbackBar"><span>재무제표</span><button type="button" onclick={() => (tablesOpen = false)}>×</button></div>
				<div class="hostFallbackBody">{lang === 'en' ? 'Quantitative statements modal is not available in this shell · use the finance panel.' : '이 셸에선 정량 재무제표 모달을 지원하지 않습니다 · 재무 패널에서 확인하세요.'}</div>
			</div>
		</div>
	{/if}
{/if}

<style>
	/* 공시 dot 클릭 동기화 · 그 날짜 공시 행 일시 하이라이트(주가차트 공시 레일 → 위치 찾기). 3.6s 후 자동 소거(스포트라이트 길게). */
	.filingRow.flash,
	.newsRow.flash {
		animation: filingFlash 3.6s ease-out;
	}
	/* 종목 뉴스 행 · 제목+스니펫+출처 세로 레이아웃(공시 행과 달리 본문 1줄 노출). filingList 스크롤 박스 재사용. */
	.newsList {
		max-height: 230px;
	}
	.newsRow {
		display: flex;
		flex-direction: column;
		gap: 1px;
		padding: 5px 6px;
		border-bottom: 1px solid var(--bd, rgba(48, 58, 78, 0.4));
		text-decoration: none;
		color: inherit;
	}
	.newsRow:hover {
		background: rgba(91, 155, 240, 0.08);
	}
	.nwTop {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 6px;
	}
	.nwTitle {
		font-size: 11px;
		line-height: 1.35;
		color: var(--fg, #cfd3dc);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.nwDesc {
		font-size: 10px;
		line-height: 1.3;
		color: var(--dim, #8b919e);
		display: -webkit-box;
		-webkit-line-clamp: 1;
		line-clamp: 1;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.nwMeta {
		font-size: 9px;
		color: var(--dimmer, #6b7280);
	}
	@keyframes filingFlash {
		0%,
		55% {
			background: rgba(91, 155, 240, 0.28);
			box-shadow: inset 2px 0 0 var(--amber, var(--amber));
		}
		100% {
			background: transparent;
			box-shadow: inset 2px 0 0 transparent;
		}
	}

	/* 열화 안내 모달 · hosts.financeDialog 미주입 셸 전용 (component-scoped, 터미널 스킨 토큰) */
	.hostFallback {
		position: fixed;
		inset: 0;
		z-index: 120;
		display: grid;
		place-items: center;
		background: rgba(0, 0, 0, 0.66);
	}
	.hostFallbackPanel {
		width: min(420px, calc(100vw - 32px));
		border: 1px solid rgba(255, 255, 255, 0.12);
		background: #0f0f10;
		color: #e8eaef;
		border-radius: 4px;
		overflow: hidden;
	}
	.hostFallbackBar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 9px 12px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		font: 700 11px/1 var(--dl-font-mono, ui-monospace, monospace);
		color: var(--amber);
	}
	.hostFallbackBar button {
		border: 0;
		background: transparent;
		color: #a3a8b3;
		font-size: 18px;
		cursor: pointer;
	}
	.hostFallbackBody {
		padding: 18px 12px;
		font-size: 13px;
		line-height: 1.5;
		color: #a3a8b3;
	}
</style>
