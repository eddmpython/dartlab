import ChartRenderer from "$lib/chart/ChartRenderer.svelte";
import ComparisonView from "$lib/components/ComparisonView.svelte";
import InsightDashboard from "$lib/components/InsightDashboard.svelte";
import TableRenderer from "$lib/components/TableRenderer.svelte";

export const widgetRegistry = {
	chart: ChartRenderer,
	comparison: ComparisonView,
	insight_dashboard: InsightDashboard,
	table: TableRenderer,
};

const COMPONENT_TO_WIDGET = {
	ChartRenderer: "chart",
	ComparisonView: "comparison",
	InsightDashboard: "insight_dashboard",
	TableRenderer: "table",
};

const WIDGET_TO_COMPONENT = {
	chart: "ChartRenderer",
	comparison: "ComparisonView",
	insight_dashboard: "InsightDashboard",
	table: "TableRenderer",
};

export function normalizeWidgetName(name) {
	if (!name || typeof name !== "string") return null;
	const trimmed = name.trim();
	if (!trimmed) return null;
	if (COMPONENT_TO_WIDGET[trimmed]) return COMPONENT_TO_WIDGET[trimmed];
	const normalized = trimmed
		.replace(/([a-z0-9])([A-Z])/g, "$1_$2")
		.replace(/[\s-]+/g, "_")
		.toLowerCase();
	return widgetRegistry[normalized] ? normalized : null;
}

export function getWidgetComponent(name) {
	const normalized = normalizeWidgetName(name);
	return normalized ? widgetRegistry[normalized] : undefined;
}

export function widgetToLegacyComponent(name) {
	const normalized = normalizeWidgetName(name);
	return normalized ? (WIDGET_TO_COMPONENT[normalized] || null) : null;
}

export function componentToWidget(name) {
	return COMPONENT_TO_WIDGET[name] || null;
}

