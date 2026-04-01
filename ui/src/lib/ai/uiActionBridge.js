import { buildChartView, normalizeViewSpec } from "./viewSpec.js";

export function collectViewsFromChartPayload(data) {
	const view = buildChartView(data?.charts || [], {
		title: data?.title || "AI 생성 차트",
		subtitle: data?.subtitle || null,
		source: { event: "chart", ...(data?.source || {}) },
	});
	return view ? [view] : [];
}

export function collectViewsFromRenderPayload(data) {
	const view = normalizeViewSpec(data);
	return view ? [view] : [];
}

export function collectViewsFromUiAction(action) {
	if (!action || action.action !== "render") return [];
	const view = normalizeViewSpec(action);
	return view ? [view] : [];
}

/**
 * UI side-effect 디스패처 — AI가 UI를 제어하는 핵심 진입점.
 *
 * 지원 액션:
 *   navigate       — 뷰어 topic 이동
 *   update/highlight — 뷰어 하이라이트
 *   toast          — 토스트 메시지
 *   layout         — 사이드바/패널/풀스크린 제어
 *   switch_view    — chat/viewer 뷰 전환
 *   select_company — 종목 선택 + 뷰어 로드
 */
export function applyUiActionSideEffect(
	action,
	{ workspace = null, uiStore = null, showToast = null, onCompanySelect = null } = {},
) {
	if (!action || typeof action !== "object") return;
	const actionName = action.action || "";

	// navigate / update / highlight — viewer 전용, 현재 비활성
	if (actionName === "navigate" || actionName === "update" || actionName === "highlight") {
		return;
	}

	if (actionName === "toast") {
		showToast?.(action.message || action.text || "", action.level || "info");
		return;
	}

	if (actionName === "layout") {
		if (!uiStore) return;
		const target = action.target;
		const value = action.value || "toggle";

		if (target === "sidebar") {
			if (value === "open") uiStore.sidebarOpen = true;
			else if (value === "close") uiStore.sidebarOpen = false;
			else uiStore.toggleSidebar();
		}
		return;
	}

	// switch_view — chat-only, viewer/dashboard 무시
	if (actionName === "switch_view") {
		return;
	}

	if (actionName === "select_company") {
		const company = {
			stockCode: action.stockCode,
			corpName: action.corpName || action.company || action.stockCode,
			market: action.market || "",
		};
		onCompanySelect?.(company);
		return;
	}
}
