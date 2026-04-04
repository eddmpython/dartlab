import { normalizeWidgetName } from "./widgetRegistry.js";

function normalizeWidgetSpec(widget, index = 0) {
	if (!widget) return null;
	if (typeof widget === "string") {
		const normalized = normalizeWidgetName(widget);
		return normalized
			? { key: `${normalized}-${index}`, widget: normalized, props: {}, title: null, description: null }
			: null;
	}

	const widgetName = normalizeWidgetName(widget.widget || widget.component);
	if (!widgetName) return null;
	return {
		key: widget.key || `${widgetName}-${index}`,
		widget: widgetName,
		props: widget.props || {},
		title: widget.title || null,
		description: widget.description || null,
	};
}

export function normalizeViewSpec(input) {
	if (!input) return null;
	const source = input.view || input;
	if (!source) return null;

	if (Array.isArray(source)) {
		return normalizeViewSpec({ widgets: source });
	}

	if (Array.isArray(source.charts)) {
		return buildChartView(source.charts, {
			title: source.title,
			subtitle: source.subtitle,
			source: source.source,
		});
	}

	if (!Array.isArray(source.widgets) && source.component) {
		return buildSingleWidgetView(source.component, source.props || {}, {
			title: source.title,
			description: source.description,
			viewTitle: source.viewTitle,
			subtitle: source.subtitle,
			source: source.source,
		});
	}

	const widgets = (source.widgets || [])
		.map((widget, index) => normalizeWidgetSpec(widget, index))
		.filter(Boolean);
	if (widgets.length === 0) return null;

	return {
		layout: typeof source.layout === "string" ? source.layout : "stack",
		title: source.title || null,
		subtitle: source.subtitle || null,
		source: source.source || null,
		widgets,
	};
}

export function buildSingleWidgetView(widget, props = {}, options = {}) {
	const view = {
		layout: options.layout || "stack",
		title: options.viewTitle || null,
		subtitle: options.subtitle || null,
		source: options.source || null,
		widgets: [
			{
				widget,
				props,
				key: options.key,
				title: options.title || null,
				description: options.description || null,
			},
		],
	};
	return normalizeViewSpec(view);
}

export function buildChartView(charts = [], options = {}) {
	if (!Array.isArray(charts) || charts.length === 0) return null;
	return normalizeViewSpec({
		layout: options.layout || "stack",
		title: options.title || "AI 생성 차트",
		subtitle: options.subtitle || null,
		source: options.source || null,
		widgets: charts.map((spec, index) => ({
			widget: "chart",
			key: `chart-${index}`,
			title: charts.length > 1 ? `차트 ${index + 1}` : null,
			props: { spec },
		})),
	});
}

