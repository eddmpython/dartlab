// 차트틀 (인디케이터 템플릿) 다중 저장 · 현재 차트 설정(지표·파라미터·축·캔들·봉주기·표시)을
// 이름 슬롯으로 저장/적용. localStorage 1키(상한 12, drawStore 무해 영속 패턴). 적용은 ChartCtl
// 필드 일괄 대입만 · PriceChart 의 기존 reconcile effect 들이 차트 반영을 이어받는다 (명령 0).
const browser = typeof window !== 'undefined'; // $app/environment 결합 제거 (4a-3)
import { OVERLAY_ALL, SUB_ALL, TFS, YMODES, CANDLES, type ChartCtl, type OverlayKey, type SubKey, type YMode, type CandleStyle, type TfKey } from './chartState.svelte';
import { IND_DEFS } from './indicatorParams';

export interface ChartTemplate {
	name: string;
	overlays: OverlayKey[];
	subs: SubKey[];
	indParams: Record<string, number[]>;
	yMode: YMode;
	candleStyle: CandleStyle;
	tf: TfKey;
	showVP: boolean;
	showRefs: boolean;
}

const KEY = 'dlTerm.tmpl';
export const TMPL_CAP = 12;

// 슬롯 단위 화이트리스트 검증 · 스키마 드리프트·손상 항목만 버리고 나머지는 살린다 (hydrate 와 동일 철학).
function sanitize(raw: unknown): ChartTemplate | null {
	if (!raw || typeof raw !== 'object') return null;
	const t = raw as Record<string, unknown>;
	if (typeof t.name !== 'string' || !t.name.trim()) return null;
	const indParams: Record<string, number[]> = {};
	if (t.indParams && typeof t.indParams === 'object') {
		for (const [k, v] of Object.entries(t.indParams as Record<string, unknown>)) {
			if (IND_DEFS[k] && Array.isArray(v) && v.length && v.every((x) => Number.isFinite(x))) indParams[k] = v as number[];
		}
	}
	return {
		name: t.name,
		overlays: Array.isArray(t.overlays) ? t.overlays.filter((k): k is OverlayKey => OVERLAY_ALL.includes(k as OverlayKey)) : [],
		subs: Array.isArray(t.subs) ? t.subs.filter((k): k is SubKey => SUB_ALL.includes(k as SubKey)) : [],
		indParams,
		yMode: YMODES.some((y) => y.v === t.yMode) ? (t.yMode as YMode) : 'normal',
		candleStyle: CANDLES.some((c) => c.v === t.candleStyle) ? (t.candleStyle as CandleStyle) : 'candle_solid',
		tf: TFS.some((x) => x.v === t.tf) ? (t.tf as TfKey) : 'D',
		showVP: t.showVP === true,
		showRefs: t.showRefs === true
	};
}

/** 저장된 차트틀 목록 · 손상·비배열은 빈 배열로 무해 처리. */
export function loadTemplates(): ChartTemplate[] {
	if (!browser) return [];
	try {
		const raw = localStorage.getItem(KEY);
		const arr: unknown = raw ? JSON.parse(raw) : [];
		if (!Array.isArray(arr)) return [];
		return arr.map(sanitize).filter((t): t is ChartTemplate => t != null);
	} catch {
		return [];
	}
}

function persist(list: ChartTemplate[]): void {
	if (!browser) return;
	try {
		if (!list.length) localStorage.removeItem(KEY);
		else localStorage.setItem(KEY, JSON.stringify(list.slice(-TMPL_CAP)));
	} catch {
		/* quota · 무해 */
	}
}

/** 현재 ctl 설정 스냅샷을 이름 슬롯에 저장 (같은 이름 = 덮어쓰기, 상한 초과 = 오래된 것 탈락). 반환 = 갱신 목록. */
export function saveTemplate(ctl: ChartCtl, name: string): ChartTemplate[] {
	const t: ChartTemplate = {
		name,
		overlays: [...ctl.overlays],
		subs: [...ctl.subs],
		indParams: Object.fromEntries(Object.entries(ctl.indParams).map(([k, v]) => [k, [...v]])),
		yMode: ctl.yMode,
		candleStyle: ctl.candleStyle,
		tf: ctl.tf,
		showVP: ctl.showVP,
		showRefs: ctl.showRefs
	};
	const list = [...loadTemplates().filter((x) => x.name !== name), t].slice(-TMPL_CAP);
	persist(list);
	return list;
}

/** 이름 슬롯 삭제. 반환 = 갱신 목록. */
export function deleteTemplate(name: string): ChartTemplate[] {
	const list = loadTemplates().filter((x) => x.name !== name);
	persist(list);
	return list;
}

/** 틀 적용 · ChartCtl 필드 일괄 대입. 차트 반영은 PriceChart reconcile effect 들이 자동 수행. */
export function applyTemplate(ctl: ChartCtl, t: ChartTemplate): void {
	ctl.overlays = [...t.overlays];
	ctl.subs = [...t.subs];
	ctl.indParams = Object.fromEntries(Object.entries(t.indParams).map(([k, v]) => [k, [...v]]));
	ctl.yMode = t.yMode;
	ctl.candleStyle = t.candleStyle;
	ctl.tf = t.tf;
	ctl.showVP = t.showVP;
	ctl.showRefs = t.showRefs;
}
