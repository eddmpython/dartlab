import type { UniverseScene } from '@dartlab/ui-contracts';
import type { UniverseAnchorLayout, UniverseViewport } from '../layout';

export interface UniverseRenderFrame {
	scene: UniverseScene;
	anchors: UniverseAnchorLayout;
	viewport: UniverseViewport;
	selectedId: string | null;
	highlightedIds: ReadonlySet<string>;
}

export interface UniverseRenderer {
	render(frame: UniverseRenderFrame): void;
	destroy(): void;
}
