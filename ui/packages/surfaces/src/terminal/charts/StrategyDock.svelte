<script lang="ts">
	// 전략 백테스트 도크 · 차트 워크스페이스 좌측 영구 패널(드랍다운 폐기 SSOT). 차트 클릭/팬/줌에 안 닫힘.
	//   헤더(접기·닫기) · 컨텍스트(종목·일봉) · ① 전략(조건 빌더) · ② 손절/익절 · ③ 검증(비용·OOS·게이트) · 결과 푸터(HonestyFooter).
	// BtConfig 의 조건 빌더 로직을 그대로 흡수(ctl.bt* 변이 → PriceChart $effect 재계산, tweak→see 무배선). 그래프 금지(3열 규칙) · equity 는 차트.
	// 접기=28px 스파인(결과 유지), 닫기=clearBtAll+도크 off(맨 차트 복귀). 폭 리사이즈(260~420).
	import type { Lang } from '../lib/types';
	import { type ChartCtl, PERIODS } from './chartState.svelte';
	import type { PortfolioBtResult } from '../lib/backtest';
	import { BT_PRESETS, BT_COSTS, RULE_PRESETS, SERIES_CATALOG, OP_LABEL, FAMILY_LABEL, FAMILY_ORDER } from '../lib/backtest';
	import type { Op, SeriesKey, StrategyRule, BtPresetDef, RulePreset } from '../lib/backtest';
	import HonestyFooter from './HonestyFooter.svelte';

	interface Props {
		ctl: ChartCtl;
		lang: Lang;
		pf?: PortfolioBtResult | null; // 결과(있으면 하단 푸터) · fill(좌패널) 모드에선 미전달(결과는 중앙 하단 보고서)
		code?: string;
		name?: string;
		fill?: boolean; // true = 좌측 패널 전체 차지(폭 100%·리사이즈·접기 없음). false = 차트 좌측 도크(레거시)
		onOpenReport?: () => void;
		onClose: () => void; // = clearBtAll + 백테스트 모드 종료
	}
	let { ctl, lang, pf = null, code, name, fill = false, onOpenReport, onClose }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	const OPS: Op[] = ['>', '<', '>=', '<=', 'crossUp', 'crossDown'];
	const seriesDef = (key: SeriesKey) => SERIES_CATALOG.find((s) => s.key === key);

	let collapsed = $state(false);
	let presetsOpen = $state(false); // 전략 ≥1 일 때 프리셋 그리드 접힘 토글(빈 상태는 항상 펼침)
	let presetQuery = $state(''); // 프리셋 검색 · 라벨·설명 토큰 매칭(15+ 프리셋 발견성)

	// 통합 프리셋 목록 · BT_PRESETS(단일지표)·RULE_PRESETS(편집가능 룰)를 패밀리로 묶어 한 picker 로.
	// '약하다'의 진짜 원인은 개수 아닌 평면 2열이 descKr 을 안 써서 발견성 0 → 패밀리 그룹 + 설명 동반.
	type PickItem = { kind: 'preset'; def: BtPresetDef } | { kind: 'rule'; def: RulePreset };
	const ALL_PRESETS: PickItem[] = [
		...BT_PRESETS.map((d): PickItem => ({ kind: 'preset', def: d })),
		...RULE_PRESETS.map((d): PickItem => ({ kind: 'rule', def: d }))
	];
	const presetsIn = (fam: string, q: string): PickItem[] => {
		const qq = q.trim().toLowerCase();
		return ALL_PRESETS.filter((it) => it.def.family === fam && (!qq || `${it.def.kr} ${it.def.en} ${it.def.descKr} ${it.def.descEn}`.toLowerCase().includes(qq)));
	};
	function pickPreset(it: PickItem) {
		if (it.kind === 'preset') ctl.addStrategy(it.def);
		else ctl.addRulePreset(it.def);
		presetsOpen = false;
		presetQuery = '';
	}

	// ── 검증 구간 · 항상 시작/종료 날짜창(기본 전체기간·일봉). period 칩은 날짜를 채우는 빠른선택. 국면 프리셋으로 원클릭 ──
	const PHASE_PRESETS = [
		{ k: 'covid', kr: '2020 코로나', en: '2020 COVID', from: '20200101', to: '20201231' },
		{ k: 'bear22', kr: '2022 약세', en: '2022 bear', from: '20220101', to: '20221231' },
		{ k: 'rec23', kr: '2023 회복', en: '2023 recovery', from: '20230101', to: '20231231' }
	];
	const dateInput = (t: string | null): string => (t && t.length === 8 ? `${t.slice(0, 4)}-${t.slice(4, 6)}-${t.slice(6, 8)}` : '');
	// 시작/종료 직접 입력(키보드·달력) · 빈값=데이터 경계 복원(창 항상 유효), 범위 밖 입력은 데이터 있는 날짜로 clamp, from>to 방어.
	function setWinPart(which: 'from' | 'to', v: string) {
		let ymd: string | null = v ? v.replace(/-/g, '') : null;
		if (!ymd) ymd = which === 'from' ? ctl.dataFromT : ctl.dataToT;
		if (ymd) {
			if (ctl.dataFromT && ymd < ctl.dataFromT) ymd = ctl.dataFromT;
			if (ctl.dataToT && ymd > ctl.dataToT) ymd = ctl.dataToT;
		}
		if (which === 'from') ctl.btWinFrom = ymd;
		else ctl.btWinTo = ymd;
		if (ctl.btWinFrom && ctl.btWinTo && ctl.btWinFrom > ctl.btWinTo) {
			if (which === 'from') ctl.btWinTo = ctl.btWinFrom;
			else ctl.btWinFrom = ctl.btWinTo;
		}
	}
	// 폭 리사이즈 · 드래그 핸들(우측 가장자리). 세션 한정 $state.
	let dockW = $state(320);
	function startResize(e: PointerEvent) {
		e.preventDefault();
		const startX = e.clientX;
		const startW = dockW;
		const move = (ev: PointerEvent) => { dockW = Math.max(260, Math.min(420, startW + (ev.clientX - startX))); };
		const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
		window.addEventListener('pointermove', move);
		window.addEventListener('pointerup', up);
	}

	const COST_FIELDS = [
		{ k: 'commissionBp' as const, kr: '수수료', en: 'fee', min: 0, max: 10, step: 0.5 },
		{ k: 'sellTaxBp' as const, kr: '거래세', en: 'tax', min: 0, max: 30, step: 1 },
		{ k: 'slippageBp' as const, kr: '슬리피지', en: 'slip', min: 0, max: 50, step: 5 }
	];
	function stepCost(k: (typeof COST_FIELDS)[number], dir: 1 | -1) {
		const next = Math.max(k.min, Math.min(k.max, +(ctl.btCostsBp[k.k] + dir * k.step).toFixed(1)));
		ctl.btCostsBp = { ...ctl.btCostsBp, [k.k]: next };
	}
	const costsDefault = $derived(ctl.btCostsBp.commissionBp === BT_COSTS.commissionBp && ctl.btCostsBp.sellTaxBp === BT_COSTS.sellTaxBp && ctl.btCostsBp.slippageBp === BT_COSTS.slippageBp);
	function stepStop(k: 'lossPct' | 'gainPct', dir: 1 | -1) {
		const cur = ctl.btStop[k] ?? 0;
		const next = Math.max(0, Math.min(50, cur + dir * 2));
		ctl.btStop = { ...ctl.btStop, [k]: next === 0 ? undefined : next };
	}

	// ── 룰 불변 편집 · 슬롯의 rule 을 clone·변형 후 setSlotRule ──
	function editRule(i: number, fn: (r: StrategyRule) => void) {
		const slot = ctl.btStrategies[i];
		if (!slot?.rule) return;
		const r = structuredClone(slot.rule);
		fn(r);
		ctl.setSlotRule(i, r);
	}
	const sideArr = (r: StrategyRule, side: 'entry' | 'exit') => (side === 'entry' ? r.entry : r.exit);
	function setLeft(i: number, side: 'entry' | 'exit', ci: number, key: SeriesKey) {
		editRule(i, (r) => { const c = sideArr(r, side)[ci]; c.left = key; c.leftParams = Object.fromEntries((seriesDef(key)?.params ?? []).map((p) => [p.name, p.def])); });
	}
	function stepLeftParam(i: number, side: 'entry' | 'exit', ci: number, name: string, dir: 1 | -1) {
		const pp = seriesDef(sideArr(ctl.btStrategies[i].rule!, side)[ci].left)?.params.find((p) => p.name === name);
		if (!pp) return;
		editRule(i, (r) => { const c = sideArr(r, side)[ci]; const v = c.leftParams[name] ?? pp.def; c.leftParams[name] = Math.max(pp.min, Math.min(pp.max, +(v + dir * pp.step).toFixed(2))); });
	}
	function setOp(i: number, side: 'entry' | 'exit', ci: number, op: Op) { editRule(i, (r) => { sideArr(r, side)[ci].op = op; }); }
	function setRightKind(i: number, side: 'entry' | 'exit', ci: number, kind: 'const' | 'series') {
		editRule(i, (r) => { const c = sideArr(r, side)[ci]; c.right = kind === 'const' ? { kind: 'const', value: 0 } : { kind: 'series', key: 'ma', params: { period: 60 } }; });
	}
	function setRightConst(i: number, side: 'entry' | 'exit', ci: number, value: number) { editRule(i, (r) => { const c = sideArr(r, side)[ci]; if (c.right.kind === 'const') c.right.value = value; }); }
	function setRightSeries(i: number, side: 'entry' | 'exit', ci: number, key: SeriesKey) { editRule(i, (r) => { const c = sideArr(r, side)[ci]; c.right = { kind: 'series', key, params: Object.fromEntries((seriesDef(key)?.params ?? []).map((p) => [p.name, p.def])) }; }); }
	function stepRightParam(i: number, side: 'entry' | 'exit', ci: number, name: string, dir: 1 | -1) {
		const c0 = sideArr(ctl.btStrategies[i].rule!, side)[ci];
		if (c0.right.kind !== 'series') return;
		const pp = seriesDef(c0.right.key)?.params.find((p) => p.name === name);
		if (!pp) return;
		editRule(i, (r) => { const c = sideArr(r, side)[ci]; if (c.right.kind === 'series') { const v = c.right.params[name] ?? pp.def; c.right.params[name] = Math.max(pp.min, Math.min(pp.max, +(v + dir * pp.step).toFixed(2))); } });
	}
	function addCond(i: number, side: 'entry' | 'exit') { editRule(i, (r) => { sideArr(r, side).push({ left: 'price', leftParams: {}, op: side === 'entry' ? '>' : '<', right: { kind: 'series', key: 'ma', params: { period: 60 } } }); }); }
	function removeCond(i: number, side: 'entry' | 'exit', ci: number) { editRule(i, (r) => { sideArr(r, side).splice(ci, 1); }); }
	function setCombine(i: number, side: 'entry' | 'exit', mode: 'AND' | 'OR') { editRule(i, (r) => { if (side === 'entry') r.entryCombine = mode; else r.exitCombine = mode; }); }

	// 접힘 스파인 헤드라인(결과 있으면 수익률 1개)
	const headRet = $derived(pf ? (pf.combo ? pf.combo.metrics.retPct : pf.slots[ctl.btFocus]?.result.metrics.retPct ?? pf.slots[0]?.result.metrics.retPct ?? null) : null);
	const sgn = (v: number) => (v >= 0 ? '+' : '') + v.toFixed(1);
</script>

{#if collapsed && !fill}
	<!-- 접힘 스파인(28px) · 차트 도크 모드에서만. 좌패널(fill) 모드는 접기 없음. -->
	<button class="sdSpine" onclick={() => (collapsed = false)} title={T('전략 도크 펼치기', 'expand strategy dock')}>
		<span class="sdSpineTtl">{T('전략 백테스트', 'STRATEGY LAB')}</span>
		{#if headRet != null}<span class={'sdSpineRet mono ' + (headRet >= 0 ? 'tUp' : 'tDn')}>{sgn(headRet)}%</span>{/if}
	</button>
{:else}
	<div class="stratDock" class:fill style={fill ? '' : `width:${dockW}px`}>
		<!-- 헤더(sticky) -->
		<div class="sdHeader">
			<span class="sdMark" aria-hidden="true"></span>
			<div class="sdTtlWrap">
				<span class="sdTtl">{T('전략 백테스트', 'STRATEGY LAB')}</span>
				<span class="sdSub">{T('규칙 조립 → 차트 위 즉시 검증', 'compose → verify on chart')}</span>
			</div>
			{#if !fill}<button class="sdHbtn" onclick={() => (collapsed = true)} aria-label="collapse" title={T('접기(결과 유지)', 'collapse')}>·</button>{/if}
			<button class="sdHbtn" onclick={onClose} aria-label="close" title={T('백테스트 종료', 'close & exit')}>✕</button>
		</div>

		<div class="sdBody">
			<div class="sdScope">
				{#each [{ v: 'single' as const, kr: '단일종목', en: 'Stock' }, { v: 'market' as const, kr: '시장', en: 'Market' }, { v: 'universe' as const, kr: '유니버스', en: 'Universe' }] as o (o.v)}
					<button class={ctl.btScope === o.v ? 'sdScopeBtn on' : 'sdScopeBtn'} onclick={() => (ctl.btScope = o.v)}>{T(o.kr, o.en)}</button>
				{/each}
			</div>
			<div class={ctl.btScope === 'single' ? 'sdScopeNote' : 'sdScopeNote callout'}>{ctl.btScope === 'universe' ? T('전 종목 횡단면 팩터 · 17년 상폐보존 · 제어·결과는 아래 보고서에 나타납니다.', 'cross-sectional factor · controls & results appear in the report below') : ctl.btScope === 'market' ? T('지수 타이밍 · 차트 상단의 [지수] 버튼에서 지수를 먼저 선택하세요. 선택한 지수에 전략을 적용합니다(미선택 시 결과 없음).', 'index timing · first pick an index from the [INDEX] button on the chart bar; the strategy then runs on that index (no result until chosen)') : T('이 종목에 매매 규칙을 적용해 검증.', 'apply a rule to this stock')}</div>
			<!-- 컨텍스트 · 종목·일봉 -->
			<div class="sdCtx">
				<span class="sdCtxSym">{name ?? ''} {code ?? ''}</span>
				<span class="sdCtxMeta">· {T('일봉', 'daily')}</span>
			</div>
			<!-- 검증 구간 = 백테스트 창(차트 줌과 공유·일봉 고정). 시작/종료 날짜 항상 표시 · 기본 전체기간, 데이터 있는 날짜 안에서만 조작(키보드 입력 가능). -->
			<div class="sdWindow">
				<div class="sdWinHd"><span class="sdWinLbl">{T('검증 구간', 'window')}</span><span class="sdWinHint">{T('이 기간으로 백테스트 · 차트도 같은 구간(일봉)', 'backtest over this period · chart shows the same range (daily)')}</span></div>
				<!-- 빠른선택 · 클릭 시 아래 시작/종료 날짜를 채움(최신 기준 역산 · 전체=MAX). -->
				<div class="sdWinSeg" role="radiogroup">
					{#each PERIODS as p (p)}<button class={ctl.btWindowChip === p ? 'sdWinBtn on' : 'sdWinBtn'} aria-pressed={ctl.btWindowChip === p} disabled={!ctl.dataToT} onclick={() => ctl.setWindowPeriod(p)}>{p}</button>{/each}
				</div>
				<!-- 시작/종료 직접 입력(키보드·달력) · min/max 가 데이터 있는 날짜로 제한. -->
				<div class="sdCustRow">
					<input class="sdDate mono" type="date" value={dateInput(ctl.btWinFrom)} min={dateInput(ctl.dataFromT) || undefined} max={dateInput(ctl.btWinTo) || dateInput(ctl.dataToT) || undefined} onchange={(e) => setWinPart('from', e.currentTarget.value)} aria-label={T('시작일', 'start')} />
					<span class="sdCustTo">~</span>
					<input class="sdDate mono" type="date" value={dateInput(ctl.btWinTo)} min={dateInput(ctl.btWinFrom) || dateInput(ctl.dataFromT) || undefined} max={dateInput(ctl.dataToT) || undefined} onchange={(e) => setWinPart('to', e.currentTarget.value)} aria-label={T('종료일', 'end')} />
				</div>
				<!-- 국면 프리셋 · 특정 역사 구간(체리피킹 예시) 원클릭. -->
				<div class="sdPhaseRow">
					{#each PHASE_PRESETS as ph (ph.k)}<button class="sdPhase" onclick={() => ctl.setCustomWin(ph.from, ph.to)}>{T(ph.kr, ph.en)}</button>{/each}
				</div>
				{#if ctl.btWindowIsSubset}
					<div class="sdCustNote">{T('⚠ 특정 구간만 보면 체리피킹(좋아 보이게 고른 구간) 위험 · 전체 기간과 비교하세요.', '⚠ a hand-picked window risks cherry-picking · compare with the full period.')}</div>
				{/if}
				{#if ctl.dataFromT && ctl.dataToT}
					<div class="sdRangeNote">{T('데이터', 'data')} {dateInput(ctl.dataFromT)} ~ {dateInput(ctl.dataToT)} · {T('일봉', 'daily')}</div>
				{/if}
			</div>

			<!-- ① 전략 -->
			<div class="btSection">
				<div class="ctMenuLbl">{T('① 전략 (최대 3 · 같은 차트 비교)', '① Strategies (up to 3)')}</div>
				{#if ctl.btStrategies.length === 0}
					<div class="btEmpty">
						<div class="btEmptyDesc">{T('당신의 매매 규칙(진입·청산)을 정의하면 · 미래참조 차단·실제 비용·표본 밖(OOS)으로 정직하게 검증해 차트 위에 그립니다. 아래에서 규칙을 조립하거나 프리셋을 출발점으로 고르세요.', 'Define your entry/exit rule · it is tested honestly (no look-ahead · real costs · out-of-sample) and drawn on the chart. Compose a rule or start from a preset below.')}</div>
				</div>
				{/if}
				{#each ctl.btStrategies as s, i (s.id)}
					<div class="btSlot" class:on={i === ctl.btFocus}>
						<div class="btSlotHd">
							<button class="btSwBtn" onclick={() => ctl.setBtFocus(i)} title={T('포커스', 'focus')} aria-label="focus"><i class="btSw" style={`background:${s.color}`}></i></button>
							<span class="btSlotLbl">{s.label}{#if s.rule}<em class="btRuleTag">{T('규칙', 'rule')}</em>{/if}</span>
							<button class="btDel" onclick={() => ctl.removeStrategy(i)} title={T('삭제', 'remove')} aria-label="remove">✕</button>
						</div>

						{#if i === ctl.btFocus}
							{#if s.rule}
								{@const rule = s.rule}
								{#each ['entry', 'exit'] as const as side (side)}
									{@const conds = side === 'entry' ? rule.entry : rule.exit}
									<div class="condBlk">
										<div class="condHd">
											<span>{side === 'entry' ? T('진입 조건', 'ENTRY') : T('청산 조건', 'EXIT')}</span>
											{#if conds.length > 1}
												<div class="combineTg">
													{#each ['AND', 'OR'] as const as m (m)}
														<button class={(side === 'entry' ? rule.entryCombine : rule.exitCombine) === m ? 'on' : ''} onclick={() => setCombine(i, side, m)}>{m}</button>
													{/each}
												</div>
											{/if}
										</div>
										{#each conds as c, ci (ci)}
											<div class="condRow">
												<select class="condSel" value={c.left} onchange={(e) => setLeft(i, side, ci, e.currentTarget.value as SeriesKey)}>
													<optgroup label={T('가격·기술', 'price/technical')}>
														{#each SERIES_CATALOG as sd (sd.key)}<option value={sd.key}>{T(sd.kr, sd.en)}</option>{/each}
													</optgroup>
													<optgroup label={T('펀더게이트 (재무·panel)', 'fundamental gate')}>
														<option value="fundGate">{T('Piotroski F (재무건강 0~9)', 'Piotroski F (0~9)')}</option>
													</optgroup>
												</select>
												{#each seriesDef(c.left)?.params ?? [] as pp (pp.name)}
													<span class="condP"><button onclick={() => stepLeftParam(i, side, ci, pp.name, -1)}>−</button><b>{c.leftParams[pp.name] ?? pp.def}</b><button onclick={() => stepLeftParam(i, side, ci, pp.name, 1)}>+</button></span>
												{/each}
												<select class="condOp" value={c.op} onchange={(e) => setOp(i, side, ci, e.currentTarget.value as Op)}>
													{#each OPS as op (op)}<option value={op}>{OP_LABEL[op]}</option>{/each}
												</select>
												<select class="condKind" value={c.right.kind} onchange={(e) => setRightKind(i, side, ci, e.currentTarget.value as 'const' | 'series')}>
													<option value="const">{T('값', 'const')}</option>
													<option value="series">{T('지표', 'series')}</option>
												</select>
												{#if c.right.kind === 'const'}
													<input class="condNum mono" type="number" value={c.right.value} onchange={(e) => setRightConst(i, side, ci, +e.currentTarget.value)} />
												{:else}
													<select class="condSel" value={c.right.key} onchange={(e) => setRightSeries(i, side, ci, e.currentTarget.value as SeriesKey)}>
														{#each SERIES_CATALOG as sd (sd.key)}<option value={sd.key}>{T(sd.kr, sd.en)}</option>{/each}
													</select>
													{#each seriesDef(c.right.key)?.params ?? [] as pp (pp.name)}
														<span class="condP"><button onclick={() => stepRightParam(i, side, ci, pp.name, -1)}>−</button><b>{c.right.kind === 'series' ? c.right.params[pp.name] ?? pp.def : pp.def}</b><button onclick={() => stepRightParam(i, side, ci, pp.name, 1)}>+</button></span>
													{/each}
												{/if}
												{#if conds.length > 1}<button class="condDel" onclick={() => removeCond(i, side, ci)} aria-label="remove condition">✕</button>{/if}
											</div>
										{/each}
										<button class="condAdd" onclick={() => addCond(i, side)}>＋ {T('조건', 'condition')}</button>
									</div>
								{/each}
								<div class="btDesc">{T('지표·연산자·임계값을 직접 조합 · 교육·탐색용(추천 아님)', 'compose your own rule · educational (not advice)')}</div>
							{:else}
								{@const pd = BT_PRESETS.find((d) => d.key === s.preset)}
								<div class="btSlotHd">
									<select class="btSelect mono" value={s.preset} onchange={(e) => { const p = BT_PRESETS.find((d) => d.key === e.currentTarget.value); if (p) ctl.setSlotPreset(i, p); }}>
										{#each BT_PRESETS as p (p.key)}<option value={p.key}>{T(p.kr, p.en)}</option>{/each}
									</select>
								</div>
								{#if pd}{#each pd.params as pp (pp.name)}
									<div class="ctRow btParamRow">
										<span class="btParamLbl">{T(pp.kr, pp.en)}</span>
										<button class="mItem" onclick={() => ctl.stepSlotParam(i, pp, -1)}>−</button>
										<b class="btParamVal mono">{s.params[pp.name] ?? pp.def}</b>
										<button class="mItem" onclick={() => ctl.stepSlotParam(i, pp, 1)}>+</button>
									</div>
								{/each}{/if}
							{/if}
						{/if}
					</div>
				{/each}
				{#snippet presetPicker()}
					<div class="ptPicker">
						<button class="ptCustomTop" onclick={() => { ctl.addCustomRule(); presetsOpen = false; presetQuery = ''; }}>＋ {T('커스텀 규칙 빌더 · 직접 조립', 'custom rule builder')}</button>
						<input class="ptSearch mono" type="text" placeholder={T('또는 프리셋 검색 (이름·설명)', 'or search presets by name or description')} bind:value={presetQuery} />
						<div class="ptScroll">
							{#each FAMILY_ORDER as fam (fam)}
								{@const items = presetsIn(fam, presetQuery)}
								{#if items.length}
									<div class="ptFamHd">{T(FAMILY_LABEL[fam].kr, FAMILY_LABEL[fam].en)} <span class="ptFamN">{items.length}</span></div>
									{#each items as it (it.kind + it.def.key)}
										<button class={'ptChip' + (it.kind === 'rule' ? ' rule' : '')} onclick={() => pickPreset(it)} title={it.kind === 'rule' ? T('편집가능 규칙 · 출발점', 'editable rule · starting point') : T('출발점 · 추천 아님', 'starting point · not advice')}>
											<span class="ptChipName">{T(it.def.kr, it.def.en)}{#if it.kind === 'rule'}<em class="ptRuleTag">{T('규칙', 'rule')}</em>{/if}</span>
											<span class="ptChipDesc">{T(it.def.descKr, it.def.descEn)}</span>
										</button>
									{/each}
								{/if}
							{/each}
						</div>
					</div>
				{/snippet}
				{#if ctl.btStrategies.length === 0}
					{@render presetPicker()}
				{:else if ctl.btStrategies.length < 3}
					<button class="btAddToggle" onclick={() => (presetsOpen = !presetsOpen)} aria-expanded={presetsOpen}>＋ {T('전략 추가', 'add strategy')} <span class="btAddCaret">{presetsOpen ? '▴' : '▾'}</span></button>
					{#if presetsOpen}{@render presetPicker()}{/if}
				{/if}
				{#if ctl.btStrategies.length >= 2}
					<div class="btDesc warn">{T('⚠ 여러 전략 같은 데이터 비교 = 사후선택 편향 · 단일종목 조합 = 타이밍 분산이지 자산 분산 아님', 'selection bias · single-stock combo = timing not asset')}</div>
				{/if}
			</div>

			<!-- ② 손절·익절 (공유) -->
			{#if ctl.btStrategies.length}
				<div class="btSection">
					<div class="ctMenuLbl">{T('② 손절·익절 (공유)', '② Stop / Take (shared)')}</div>
					<div class="ctRow btParamRow">
						<span class="btParamLbl">{T('손절', 'stop')}</span>
						<button class="mItem" onclick={() => stepStop('lossPct', -1)}>−</button>
						<b class="btParamVal mono">{ctl.btStop.lossPct != null ? '−' + ctl.btStop.lossPct : '·'}</b>
						<span class="btParamLbl">%</span>
						<button class="mItem" onclick={() => stepStop('lossPct', 1)}>+</button>
					</div>
					<div class="ctRow btParamRow">
						<span class="btParamLbl">{T('익절', 'take')}</span>
						<button class="mItem" onclick={() => stepStop('gainPct', -1)}>−</button>
						<b class="btParamVal mono">{ctl.btStop.gainPct != null ? '+' + ctl.btStop.gainPct : '·'}</b>
						<span class="btParamLbl">%</span>
						<button class="mItem" onclick={() => stepStop('gainPct', 1)}>+</button>
					</div>
					{#if ctl.btStop.lossPct || ctl.btStop.gainPct}<div class="btDesc warn">{T('⚠ 장중 터치/갭 관통 시 보수 체결(갭조정) 가정 · t+1 시가 모델과 시점 충돌(보수: 손절 우선)', 'gap-adjusted stop/take (worse of stop or gap-open) · conflicts with the t+1 fill model')}</div>{/if}
				</div>
			{/if}

			<!-- ③ 검증 · 비용 + OOS + 게이트(이것이 결과를 '진짜'로 만든다) -->
			<div class="btSection">
				<div class="ctMenuLbl">{T('③ 검증 · 비용·OOS·게이트 (공유)', '③ Validation · costs · OOS · gate')}</div>
				<!-- (a) 비용 -->
				<div class="ctRow">
					<button class={ctl.btCosts ? 'mItem on' : 'mItem'} onclick={() => (ctl.btCosts = !ctl.btCosts)}>{ctl.btCosts ? T('✓ 수수료·세금 포함', '✓ costs included') : T('수수료·세금 포함', 'include costs')}</button>
				</div>
				{#if ctl.btCosts}
					{#each COST_FIELDS as cf (cf.k)}
						<div class="ctRow btParamRow">
							<span class="btParamLbl">{T(cf.kr, cf.en)}</span>
							<button class="mItem" onclick={() => stepCost(cf, -1)}>−</button>
							<b class="btParamVal mono">{ctl.btCostsBp[cf.k]}</b>
							<span class="btParamLbl">bp</span>
							<button class="mItem" onclick={() => stepCost(cf, 1)}>+</button>
						</div>
					{/each}
					{#if !costsDefault}<div class="ctRow"><button class="mItem" onclick={() => (ctl.btCostsBp = { ...BT_COSTS })}>{T('비용 기본값', 'reset')}</button></div>{/if}
				{:else}
					<div class="btDesc warn">{T('⚠ 비용 미포함 · 실거래 대비 낙관적', '⚠ costs off · optimistic vs live')}</div>
				{/if}
				<!-- (b) OOS -->
				{#if ctl.btStrategies.length}
					<div class="sdSubLbl">{T('학습/검증 분할 (OOS)', 'train/test split (OOS)')}</div>
					<div class="ctRow ctRowWrap">
						{#each [{ v: 0, kr: '없음', en: 'off' }, { v: 0.7, kr: '70:30', en: '70:30' }, { v: 0.6, kr: '60:40', en: '60:40' }] as o (o.v)}
							<button class={ctl.btOosSplit === o.v ? 'mItem on' : 'mItem'} onclick={() => (ctl.btOosSplit = o.v)}>{T(o.kr, o.en)}</button>
						{/each}
					</div>
					{#if ctl.btOosSplit > 0}<div class="btDesc">{T('파란 구간 = 검증(고정 파라미터 · walk-forward 아님). 검증<학습이면 과최적화 신호', 'blue = out-of-sample (fixed params, not walk-forward); worse = overfit')}</div>{/if}
				{/if}
				<!-- (c) 펀더게이트 안내 -->
				<div class="btDesc">{T('펀더게이트는 ① 전략의 진입 조건으로 추가 · 가격 배경 음영. 값은 공시일 이후부터 적용(look-ahead 0)이며 분기말 기준 재무(후행 지표 · 실시간 아님).', 'add the fundamental gate as an ENTRY condition · tints the background. Applied only after the filing date (no look-ahead); reflects quarter-end financials (a lagging metric, not real-time).')}</div>
			</div>

		</div>

		<!-- 정직 고지 띠(sticky bottom·상존) · 체결모델·미래참조차단·B&H. 스크롤에 밀려나지 않음(정직 OS 사상). -->
		<div class="sdHonestBar">
			<div class="btBench">{T('비교 기준 · 보유(B&H) · 동일 비용', 'benchmark · buy & hold · same costs')}</div>
			<div class="btModelNote">{T('신호 t일 종가 → t+1일 시가 체결 · 미래참조 차단 · 과거 가정 노출형 시뮬레이션(추천 아님)', 'signal close(t) → fill open(t+1) · no look-ahead · not advice')}</div>
		</div>

		<!-- 결과 + 정직 푸터(sticky) · 그래프 금지(equity 는 차트). 결과 없으면 미표시. -->
		{#if pf && ctl.btStrategies.length}
			<HonestyFooter {pf} slots={ctl.btStrategies} focus={ctl.btFocus} withCosts={ctl.btCosts} adjusted={ctl.adj} {lang} onFocus={(i) => ctl.setBtFocus(i)} onOpenReport={onOpenReport ?? (() => {})} />
		{/if}

		<!-- 폭 리사이즈 핸들 · 차트 도크 모드에서만(좌패널 fill 은 컬럼 폭). -->
		{#if !fill}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="sdResize" onpointerdown={startResize} title={T('폭 조절', 'resize')}></div>
		{/if}
	</div>
{/if}

<style>
	.stratDock {
		position: relative;
		flex: none;
		height: 100%;
		display: flex;
		flex-direction: column;
		min-height: 0;
		background: var(--dl-bg-base, #0a0e15);
		border-right: 1px solid var(--dl-line-strong, #2a3142);
		font-family: var(--sans, inherit);
	}
	/* 좌패널 전체 차지 모드 · 컬럼 폭 100%(글로벌 좌측 레일 대체). */
	.stratDock.fill { width: 100%; flex: 1 1 auto; border-right: none; }
	/* 헤더 sticky */
	.sdHeader { flex: none; display: flex; align-items: center; gap: 7px; padding: 6px 8px; border-bottom: 1px solid var(--dl-line-strong, #2a3142); background: rgba(var(--amber-rgb), 0.05); }
	.sdMark { width: 4px; height: 22px; border-radius: 2px; background: var(--amber, var(--amber)); flex: none; }
	.sdTtlWrap { display: flex; flex-direction: column; gap: 1px; flex: 1 1 auto; min-width: 0; }
	.sdTtl { font-size: 12px; font-weight: 700; letter-spacing: 0.04em; color: var(--dl-ink, #c8cfdb); }
	.sdSub { font-size: 10px; color: var(--dim, #8b94a3); }
	.sdHbtn { background: none; border: 1px solid var(--dl-line, #1b2130); color: var(--dim, #8b94a3); cursor: pointer; font-size: 12px; line-height: 1; width: 22px; height: 22px; border-radius: 3px; font-family: inherit; }
	.sdHbtn:hover { color: var(--dl-ink, #c8cfdb); border-color: #3a4456; }
	.sdBody { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: 7px; display: flex; flex-direction: column; gap: 4px; }
	.sdCtx { display: flex; align-items: baseline; gap: 5px; font-size: 11px; flex-wrap: wrap; }
	.sdCtxSym { color: var(--dl-ink, #c8cfdb); font-weight: 600; }
	.sdCtxMeta { color: var(--dim, #8b94a3); }
	.sdSubLbl { font-size: 10.5px; color: var(--dim, #8b94a3); margin-top: 5px; }
	/* 검증 구간 = 백테스트 창. 박스+헤더로 '차트 기간' 오인 차단(UIUX 그룹핑). 11px floor 준수. */
	.sdWindow { display: flex; flex-direction: column; gap: 5px; margin: 2px 0 6px; padding: 6px 7px; border: 1px solid var(--dl-line-strong, #2a3142); border-radius: 5px; background: rgba(var(--amber-rgb), 0.03); }
	.sdWinHd { display: flex; flex-direction: column; align-items: flex-start; gap: 1px; }
	.sdWinLbl { font-size: 11px; font-weight: 600; color: #aeb6c2; letter-spacing: 0.02em; flex: none; }
	.sdWinHint { font-size: 11px; color: var(--dim, #8b94a3); text-align: left; }
	.sdWinSeg { display: inline-flex; flex: 1 1 auto; border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; overflow: hidden; }
	.sdWinBtn { flex: 1 1 0; font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: #aeb6c2; border: none; border-left: 1px solid var(--dl-line, #1b2130); padding: 3px 0; cursor: pointer; font-family: inherit; font-variant-numeric: tabular-nums; }
	.sdWinBtn:first-child { border-left: none; }
	.sdWinBtn:hover { color: var(--dl-ink, #c8cfdb); background: rgba(255, 255, 255, 0.04); }
	.sdWinBtn.on { background: var(--amber, var(--amber)); color: #1a1206; font-weight: 700; }
	.sdWinBtn:disabled { opacity: 0.4; cursor: default; }
	/* 검증 구간 · 시작/종료 날짜창(상시) + 국면 프리셋 + 체리피킹 정직 노트 + 데이터 범위 캡션. */
	.sdCustRow { display: flex; align-items: center; gap: 5px; margin-top: 1px; }
	.sdDate { flex: 1 1 0; min-width: 0; font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: var(--dl-ink, #c8cfdb); border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; padding: 3px 5px; font-family: inherit; color-scheme: dark; }
	.sdCustTo { color: var(--dim, #8b94a3); font-size: 12px; flex: none; }
	.sdPhaseRow { display: flex; flex-wrap: wrap; gap: 4px; }
	.sdPhase { font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: #aeb6c2; border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; padding: 3px 9px; cursor: pointer; font-family: inherit; }
	.sdPhase:hover { border-color: var(--amber, var(--amber)); color: var(--amber, var(--amber)); }
	.sdCustNote { font-size: 11px; color: var(--dim, #8b94a3); line-height: 1.5; }
	.sdRangeNote { font-size: 10.5px; color: var(--dimmer, #5b6573); font-variant-numeric: tabular-nums; }
	.btSection { margin-top: 4px; }
	/* 리사이즈 핸들 */
	.sdResize { position: absolute; top: 0; right: -3px; width: 6px; height: 100%; cursor: col-resize; z-index: 2; }
	.sdResize:hover { background: rgba(var(--amber-rgb), 0.25); }
	/* 접힘 스파인 */
	.sdSpine { flex: none; width: 28px; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; gap: 10px; padding: 10px 0; background: var(--dl-bg-base, #0a0e15); border-right: 1px solid var(--dl-line-strong, #2a3142); cursor: pointer; }
	.sdSpine:hover { background: rgba(var(--amber-rgb), 0.06); }
	.sdSpineTtl { writing-mode: vertical-rl; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; color: var(--amber, var(--amber)); }
	.sdSpineRet { writing-mode: vertical-rl; font-size: 12px; font-weight: 700; font-variant-numeric: tabular-nums; }

	/* ── 흡수: BtConfig 빌더 스타일(11px floor 유지) ── */
	.ctMenuLbl { font-size: 11px; font-weight: 600; color: #aeb6c2; margin-bottom: 4px; letter-spacing: 0.02em; }
	.ctRow { display: flex; align-items: center; gap: 4px; flex-wrap: nowrap; margin-bottom: 3px; }
	.ctRowWrap { flex-wrap: wrap; }
	.mItem { font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: #aeb6c2; border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 2px 8px; cursor: pointer; font-family: inherit; }
	.mItem:hover { color: var(--dl-ink, #c8cfdb); border-color: #3a4456; }
	.mItem.on { background: var(--amber, var(--amber)); color: #1a1206; border-color: var(--amber, var(--amber)); font-weight: 600; }
	.btSlot { border: 1px solid var(--dl-line, #1b2130); border-radius: 5px; padding: 5px 6px; margin-bottom: 4px; }
	.btSlot.on { border-color: #2a3142; background: rgba(255, 255, 255, 0.02); }
	.btSlotHd { display: flex; align-items: center; gap: 5px; }
	.btSwBtn { background: none; border: none; padding: 2px; cursor: pointer; display: inline-flex; }
	.btSw { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }
	.btSlotLbl { flex: 1 1 auto; min-width: 0; font-size: 11.5px; color: var(--dl-ink, #c8cfdb); display: flex; align-items: center; gap: 5px; }
	.btRuleTag { font-style: normal; font-size: 10px; color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.4); border-radius: 3px; padding: 0 3px; }
	.btSelect { flex: 1 1 auto; min-width: 0; font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: var(--dl-ink, #c8cfdb); border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 2px 4px; font-family: inherit; }
	.btAdd { width: 100%; margin-top: 2px; }
	.btDel { background: none; border: none; color: var(--dimmer, #5b6573); cursor: pointer; font-size: 12px; padding: 0 3px; }
	.btDel:hover { color: var(--dn, #f0616f); }
	.btParamRow { gap: 3px; }
	.btParamLbl { font-size: 11px; color: #8b94a3; }
	.btParamVal { font-size: 12px; min-width: 30px; text-align: center; color: var(--dl-ink, #c8cfdb); font-variant-numeric: tabular-nums; }
	.btDesc { font-size: 10.5px; color: var(--dim, #8b94a3); line-height: 1.5; margin-top: 3px; }
	.btDesc.warn { color: var(--amber, var(--amber)); }
	/* 정직 고지 띠 · sdBody 밖 sticky 하단(flex:none). 스크롤 내용과 무관하게 항상 보임. */
		.sdHonestBar { flex: none; padding: 5px 8px 6px; border-top: 1px solid var(--dl-line-strong, #2a3142); background: var(--dl-bg-base, #0a0e15); }
		.btBench { font-size: 10.5px; color: var(--dim, #8b94a3); }
		/* 전략 추가 토글 · 프리셋 그리드 접힘(전략 >=1). 빈 상태는 그리드 직접 노출. */
		.btAddToggle { width: 100%; margin-top: 4px; font-size: 11px; background: rgba(255, 255, 255, 0.03); border: 1px dashed var(--dl-line-strong, #2a3142); color: #aeb6c2; border-radius: 4px; padding: 6px 8px; cursor: pointer; font-family: inherit; display: flex; align-items: center; justify-content: center; gap: 6px; }
		.btAddToggle:hover { border-color: var(--amber, var(--amber)); color: var(--amber, var(--amber)); }
		.btAddCaret { color: var(--dimmer, #5b6573); }
	.btModelNote { font-size: 10px; color: var(--dimmer, #5b6573); line-height: 1.5; margin-top: 2px; }
	.btEmpty { padding: 10px; background: rgba(255, 255, 255, 0.02); border: 1px dashed var(--dl-line-strong, #2a3142); border-radius: 5px; margin-bottom: 4px; }
	.btEmptyDesc { font-size: 11px; color: #aeb6c2; line-height: 1.6; }
	.condBlk { margin-top: 5px; padding: 5px; border: 1px solid rgba(27, 33, 48, 0.7); border-radius: 4px; }
	.condHd { display: flex; align-items: center; justify-content: space-between; font-size: 11.5px; font-weight: 700; color: #aeb6c2; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 5px; }
	.combineTg { display: flex; gap: 2px; }
	.combineTg button { font-size: 10px; padding: 1px 6px; background: none; border: 1px solid var(--dl-line, #1b2130); color: var(--dimmer, #5b6573); border-radius: 3px; cursor: pointer; font-family: inherit; }
	.combineTg button.on { color: #a78bfa; border-color: rgba(167, 139, 250, 0.5); }
	.condRow { display: flex; align-items: center; gap: 3px; flex-wrap: wrap; margin-bottom: 3px; }
	.condSel, .condOp, .condKind { font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: var(--dl-ink, #c8cfdb); border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 2px 3px; font-family: inherit; }
	.condOp { min-width: 30px; }
	.condNum { width: 56px; font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: var(--dl-ink, #c8cfdb); border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 2px 4px; font-variant-numeric: tabular-nums; }
	.condP { display: inline-flex; align-items: center; gap: 1px; }
	.condP button { font-size: 11px; width: 17px; height: 17px; line-height: 1; background: none; border: 1px solid var(--dl-line, #1b2130); color: #aeb6c2; border-radius: 3px; cursor: pointer; padding: 0; }
	.condP b { font-size: 12px; min-width: 22px; text-align: center; font-family: var(--dl-font-mono, monospace); color: var(--dl-ink, #c8cfdb); font-variant-numeric: tabular-nums; }
	.condDel { background: none; border: none; color: var(--dimmer, #5b6573); cursor: pointer; font-size: 11px; padding: 0 2px; }
	.condDel:hover { color: var(--dn, #f0616f); }
	.condAdd { font-size: 10px; background: none; border: 1px dashed var(--dl-line-strong, #2a3142); color: #8b94a3; border-radius: 3px; padding: 3px 8px; cursor: pointer; font-family: inherit; margin-top: 2px; }
	.condAdd:hover { color: var(--dl-ink, #c8cfdb); }
		.sdScope { display: flex; gap: 3px; margin-bottom: 4px; }
	.sdScopeBtn { flex: 1 1 0; font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: #aeb6c2; border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; padding: 4px 0; cursor: pointer; font-family: inherit; }
	.sdScopeBtn.on { background: var(--amber, var(--amber)); color: #1a1206; border-color: var(--amber, var(--amber)); font-weight: 700; }
	.sdScopeNote { font-size: 10.5px; color: var(--dim, #8b94a3); line-height: 1.5; margin-bottom: 5px; }
	.sdScopeNote.callout { color: #d7c4a8; background: rgba(var(--amber-rgb), 0.07); border: 1px solid rgba(var(--amber-rgb), 0.3); border-radius: 4px; padding: 5px 7px; }
	/* 프리셋 picker · 4패밀리 카테고리 + 작은 칩(라벨+설명) + 스크롤 + 검색. '약하다'=발견성 0 해소(깎기). */
	.ptPicker { margin-top: 2px; }
	.ptSearch { width: 100%; box-sizing: border-box; font-size: 11px; background: var(--dl-bg-raised, #0e141f); color: var(--dl-ink, #c8cfdb); border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; padding: 4px 7px; margin-bottom: 4px; font-family: inherit; }
	.ptSearch::placeholder { color: var(--dimmer, #5b6573); }
	.ptScroll { max-height: 250px; overflow-y: auto; display: flex; flex-direction: column; gap: 2px; padding-right: 2px; }
	.ptFamHd { position: sticky; top: 0; background: var(--dl-bg-base, #0a0e15); font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--amber, var(--amber)); padding: 4px 2px 2px; display: flex; align-items: center; gap: 5px; z-index: 1; }
	.ptFamN { font-size: 9.5px; color: var(--dimmer, #5b6573); font-weight: 400; border: 1px solid var(--dl-line, #1b2130); border-radius: 7px; padding: 0 5px; }
	.ptChip { display: flex; flex-direction: column; gap: 1px; text-align: left; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; padding: 4px 7px; cursor: pointer; font-family: inherit; }
	.ptChip:hover { border-color: var(--amber, var(--amber)); background: rgba(var(--amber-rgb), 0.05); }
	.ptChip.rule { border-left: 2px dashed rgba(167, 139, 250, 0.5); }
	.ptChipName { font-size: 11.5px; color: var(--dl-ink, #c8cfdb); font-weight: 600; display: flex; align-items: center; gap: 5px; }
	.ptRuleTag { font-style: normal; font-size: 9px; color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.4); border-radius: 3px; padding: 0 3px; }
	.ptChipDesc { font-size: 10px; color: var(--dim, #8b94a3); line-height: 1.35; }
	/* 커스텀 빌더 진입점 · 검색창 위 상단 고정(스크롤 없이 발견). 클릭=슬롯 추가→프리셋 picker가 빌더로 교체(프리셋 공간 숨김). 보라=직접 규칙 신호. */
		.ptCustomTop { width: 100%; text-align: center; font-size: 11.5px; font-weight: 600; background: rgba(167, 139, 250, 0.07); border: 1px solid rgba(167, 139, 250, 0.4); color: #a78bfa; border-radius: 4px; padding: 6px; margin-bottom: 5px; cursor: pointer; font-family: inherit; }
	.ptCustomTop:hover { border-color: #a78bfa; background: rgba(167, 139, 250, 0.12); }
	.tUp { color: var(--up, #34d399); }
	.tDn { color: var(--dn, #f0616f); }
</style>
