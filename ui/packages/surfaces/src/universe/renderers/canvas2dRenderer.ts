import type { UniverseVisualStatus } from '@dartlab/ui-contracts';
import { UNIVERSE_VISUAL_TOKENS } from '../visualGrammar';
import type { UniverseRenderFrame, UniverseRenderer } from './UniverseRenderer';

function statusForLane(lane: string): UniverseVisualStatus {
	return lane === 'fact' || lane === 'candidate' || lane === 'derived' || lane === 'scenario' ? lane : 'unknown';
}

function visibleLabelIds(frame: UniverseRenderFrame, anchorById: Map<string, { x: number; y: number }>): ReadonlySet<string> {
	if (frame.highlightedIds.size > 0) {
		const ids = new Set(frame.highlightedIds);
		if (frame.selectedId) ids.add(frame.selectedId);
		return ids;
	}
	const accepted: Array<{ x: number; y: number }> = [];
	const ids = new Set<string>();
	const ranked = [...frame.scene.nodes].sort((left, right) =>
		(right.presentation?.memberCount ?? 0) - (left.presentation?.memberCount ?? 0)
		|| left.nodeId.localeCompare(right.nodeId));
	for (const node of ranked) {
		const anchor = anchorById.get(node.nodeId);
		if (!anchor) continue;
		const radius = Math.max(5, Math.min(13, 5 + Math.sqrt(Math.max(0, node.presentation?.memberCount ?? 0)) * 0.46));
		const labelY = anchor.y - radius - 6;
		if (accepted.some((label) => Math.abs(label.x - anchor.x) < 104 && Math.abs(label.y - labelY) < 18)) continue;
		ids.add(node.nodeId);
		accepted.push({ x: anchor.x, y: labelY });
		if (ids.size >= 18) break;
	}
	if (frame.selectedId) ids.add(frame.selectedId);
	return ids;
}

export function createCanvas2dRenderer(canvas: HTMLCanvasElement): UniverseRenderer {
	const context = canvas.getContext('2d');
	if (!context) throw new Error('Universe Canvas 2D context is unavailable');
	return {
		render(frame: UniverseRenderFrame): void {
			const { width, height, dpr } = frame.viewport;
			canvas.width = Math.max(1, Math.round(width * dpr));
			canvas.height = Math.max(1, Math.round(height * dpr));
			canvas.style.width = `${width}px`;
			canvas.style.height = `${height}px`;
			context.setTransform(dpr, 0, 0, dpr, 0, 0);
			context.clearRect(0, 0, width, height);
			context.fillStyle = '#090d16';
			context.fillRect(0, 0, width, height);
			context.strokeStyle = 'rgba(141, 164, 197, .11)';
			context.lineWidth = 1;
			for (const fraction of [0.14, 0.5, 0.86]) {
				const x = 64 + fraction * Math.max(0, width - 128);
				context.beginPath(); context.moveTo(x, 28); context.lineTo(x, height - 28); context.stroke();
			}
			const anchorById = new Map(frame.anchors.anchors.map((anchor) => [anchor.nodeId, anchor]));
			for (const edge of frame.scene.edges) {
				const source = anchorById.get(edge.sourceId);
				const target = anchorById.get(edge.targetId);
				if (!source || !target) continue;
				const token = UNIVERSE_VISUAL_TOKENS[statusForLane(edge.lane)];
				context.strokeStyle = token.color;
				context.globalAlpha = frame.selectedId && edge.sourceId !== frame.selectedId && edge.targetId !== frame.selectedId ? 0.08 : 0.27;
				context.lineWidth = edge.lane === 'derived' ? 1.4 : 1;
				context.setLineDash(edge.lane === 'candidate' ? [4, 4] : []);
				const controlX = (source.x + target.x) / 2;
				context.beginPath(); context.moveTo(source.x, source.y); context.bezierCurveTo(controlX, source.y, controlX, target.y, target.x, target.y); context.stroke();
			}
			context.setLineDash([]);
			context.globalAlpha = 1;
			const labelIds = visibleLabelIds(frame, anchorById);
			for (const node of frame.scene.nodes) {
				const anchor = anchorById.get(node.nodeId);
				if (!anchor) continue;
				const selected = frame.selectedId === node.nodeId;
				const highlighted = frame.highlightedIds.size === 0 || frame.highlightedIds.has(node.nodeId);
				const radius = Math.max(5, Math.min(13, 5 + Math.sqrt(Math.max(0, node.presentation?.memberCount ?? 0)) * 0.46));
				context.globalAlpha = highlighted ? 1 : 0.16;
				context.fillStyle = selected ? '#f7f9fc' : '#111a29';
				context.strokeStyle = selected ? '#f7f9fc' : UNIVERSE_VISUAL_TOKENS[statusForLane(node.lane)].color;
				context.lineWidth = selected ? 3 : 1.5;
				context.beginPath(); context.arc(anchor.x, anchor.y, radius, 0, Math.PI * 2); context.fill(); context.stroke();
				if (labelIds.has(node.nodeId)) {
					context.fillStyle = selected ? '#ffffff' : '#aebcd0';
					context.font = `${selected ? 600 : 500} 10px ui-sans-serif, system-ui, sans-serif`;
					context.textAlign = 'center';
					context.fillText(node.label, anchor.x, anchor.y - radius - 6);
				}
			}
			context.globalAlpha = 1;
		},
		destroy(): void {
			context.clearRect(0, 0, canvas.width, canvas.height);
		}
	};
}
