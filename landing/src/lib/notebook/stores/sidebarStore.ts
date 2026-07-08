import { writable } from 'svelte/store';

export type PanelId = 'packages' | 'variables' | 'files' | 'docs' | 'dependencies';

export const sidebarOpen = writable<boolean>(false);
export const activePanel = writable<PanelId>('packages');

export function toggleSidebar(): void {
	sidebarOpen.update((v) => !v);
}

export function openPanel(panel: PanelId): void {
	activePanel.set(panel);
	sidebarOpen.set(true);
}

export function closeSidebar(): void {
	sidebarOpen.set(false);
}
