import { SCAN_SCREEN_PRESETS, type ScanPreset } from '@dartlab/ui-contracts';

const STORAGE_KEY = 'dartlab.scan.user-presets.v1';

/** Python screens/*.json 코드젠과 사용자 저장본을 하나의 port 결과로 합친다. */
export function listScanPresets(): ScanPreset[] {
	const generated = SCAN_SCREEN_PRESETS.map((definition) => ({
		id: definition.id,
		label: definition.title,
		payload: definition as unknown as Record<string, unknown>
	}));
	return [...generated, ...readUserPresets().filter((item) => !generated.some((base) => base.id === item.id))];
}

export function saveScanPreset(preset: ScanPreset): void {
	if (typeof window === 'undefined' || !window.localStorage) return;
	const current = readUserPresets().filter((item) => item.id !== preset.id);
	current.push(preset);
	window.localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
}

function readUserPresets(): ScanPreset[] {
	if (typeof window === 'undefined' || !window.localStorage) return [];
	try {
		const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '[]');
		return Array.isArray(value)
			? value.filter(
					(item): item is ScanPreset =>
						item != null && typeof item.id === 'string' && typeof item.label === 'string' && item.payload != null
				)
			: [];
	} catch {
		return [];
	}
}
