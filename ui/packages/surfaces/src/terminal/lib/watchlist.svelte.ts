// 공시 워치 (워치리스트) · 사용자 큐레이션 종목 *집합* + Tier 2 토대(이 기기 마지막 방문 시각). 가격·신선도
// 데이터는 보유하지 않는다(집합만) · 가격(priceOf)·재무유형(finType)·신선도(filing.nonRegular)는 소비처가
// 라이브 결합. 단일 localStorage 키 dlTerm.watch (termStore 공유 헬퍼 경유 · SSOT 1 키). 모듈 싱글턴 룬 상태
// (viewerEntry·disclosureFocus 동형) · prop drilling 없이 헤더 ☆ 와 좌측 패널이 같은 상태를 공유.
//
// Tier 0(집합)·Tier 1(절대시간 신선도, 소비처가 라이브 계산)은 영속 소실에 면역에 가깝다(집합 소실 = 재추가
// 만으로 복원, 신선도는 무상태). Tier 2(재방문 델타)는 visited 타임스탬프에 의존하므로 정직 가드(기기·시점 명시,
// "알림" 금지, 완결성 주장 금지) 충족 시에만 노출 · v1 은 토대만 저장하고 UI 미노출.
import { isKrStockCode } from '@dartlab/ui-contracts';
import { readStore, writeStore } from './termStore';

const KEY = 'dlTerm.watch' as const;
const CAP = 100; // 폭주 가드 (PRD 목표 10~30 · 명목 상한)
const isCode = isKrStockCode; // KRX 단축코드 판정 정본(영숫자 코드 0008Z0 포함)

interface WatchState {
	codes: string[]; // 추가 순서 유지 (표시 정렬은 소비처가 신선도순으로 재배열)
	visited: Record<string, number>; // code → 이 기기 마지막 방문 epoch ms (Tier 2 토대)
}

function load(): WatchState {
	const s = readStore<Partial<WatchState>>(KEY, {});
	const codes = Array.isArray(s.codes) ? s.codes.filter(isCode) : [];
	const visited = s.visited && typeof s.visited === 'object' ? (s.visited as Record<string, number>) : {};
	return { codes: [...new Set(codes)].slice(0, CAP), visited };
}

const state = $state<WatchState>(load());

function persist(): void {
	writeStore(KEY, state.codes.length || Object.keys(state.visited).length ? state : null);
}

function add(code: string): void {
	if (!isCode(code) || state.codes.includes(code)) return;
	state.codes = [...state.codes, code].slice(-CAP);
	persist();
}

function remove(code: string): void {
	if (!state.codes.includes(code)) return;
	state.codes = state.codes.filter((c) => c !== code);
	if (code in state.visited) {
		const { [code]: _drop, ...rest } = state.visited;
		state.visited = rest;
	}
	persist();
}

export const watchlist = {
	get codes(): string[] {
		return state.codes;
	},
	get count(): number {
		return state.codes.length;
	},
	has(code: string): boolean {
		return state.codes.includes(code);
	},
	add,
	remove,
	toggle(code: string): void {
		if (state.codes.includes(code)) remove(code);
		else add(code);
	},
	/** Tier 2 토대 · 이 기기에서 회사 렌더 시점 기록(v1 UI 미노출 · 재방문 델타 후속). 워치 종목만 기록. */
	markVisited(code: string): void {
		if (!isCode(code) || !state.codes.includes(code)) return;
		state.visited = { ...state.visited, [code]: Date.now() };
		persist();
	},
	visitedAt(code: string): number | null {
		return state.visited[code] ?? null;
	}
};
