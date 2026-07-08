import { writable, get } from 'svelte/store';

export interface WidgetDescriptor {
	id: string;
	type: string;
	config: Record<string, unknown>;
	value: unknown;
}

export interface WidgetOutput {
	widgets: WidgetDescriptor[];
	stdout?: string;
}

export const widgetCellMap = writable<Map<string, string>>(new Map());

let updateValueInPython: ((widgetId: string, value: unknown) => Promise<void>) | null = null;
let triggerReactive: ((cellId: string) => Promise<void>) | null = null;
let debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

export function initWidgetBridge(
	pyUpdater: (widgetId: string, value: unknown) => Promise<void>,
	reactiveTrigger: (cellId: string) => Promise<void>
): void {
	updateValueInPython = pyUpdater;
	triggerReactive = reactiveTrigger;
}

export async function onWidgetValueChange(widgetId: string, newValue: unknown): Promise<void> {
	if (!updateValueInPython || !triggerReactive) return;

	await updateValueInPython(widgetId, newValue);

	const cellMap = get(widgetCellMap);
	const cellId = cellMap.get(widgetId);
	if (!cellId) return;

	const existing = debounceTimers.get(widgetId);
	if (existing) clearTimeout(existing);

	debounceTimers.set(widgetId, setTimeout(async () => {
		debounceTimers.delete(widgetId);
		await triggerReactive!(cellId);
	}, 200));
}

export function registerWidgetCell(widgetId: string, cellId: string): void {
	widgetCellMap.update((m) => {
		const next = new Map(m);
		next.set(widgetId, cellId);
		return next;
	});
}

export function parseWidgetOutput(data: string): WidgetOutput | null {
	try {
		const parsed = JSON.parse(data);
		if (parsed && parsed.__chani_widget__) {
			return { widgets: [parsed] };
		}
		if (Array.isArray(parsed) && parsed.length > 0 && parsed[0]?.__chani_widget__) {
			return { widgets: parsed };
		}
		return null;
	} catch {
		return null;
	}
}

export function extractWidgetsFromHtml(html: string): { cleanHtml: string; widgetDescriptors: Map<string, WidgetDescriptor> } {
	const descriptors = new Map<string, WidgetDescriptor>();
	const regex = /<chani-widget data-widget-id="([^"]+)">({.*?})<\/chani-widget>/g;
	let match;

	let cleanHtml = html;
	while ((match = regex.exec(html)) !== null) {
		try {
			const descriptor = JSON.parse(match[2]) as WidgetDescriptor;
			descriptors.set(descriptor.id, descriptor);
			cleanHtml = cleanHtml.replace(match[0], `<div class="chani-widget-slot" data-widget-id="${descriptor.id}"></div>`);
		} catch {
			continue;
		}
	}

	return { cleanHtml, widgetDescriptors: descriptors };
}

export function destroyWidgetBridge(): void {
	updateValueInPython = null;
	triggerReactive = null;
	debounceTimers.forEach((t) => clearTimeout(t));
	debounceTimers.clear();
	widgetCellMap.set(new Map());
}
