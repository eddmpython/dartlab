import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
	return twMerge(clsx(inputs));
}

/**
 * 스와이프 제스처 핸들러.
 * @param {HTMLElement} el
 * @param {{ onSwipeLeft?: () => void, onSwipeRight?: () => void, edgeOnly?: boolean, edgeWidth?: number }} callbacks
 * @returns {() => void} cleanup
 */
export function createSwipeHandler(el, callbacks) {
	const threshold = 50;
	const maxVertical = 30;
	const edgeWidth = callbacks.edgeWidth || 30;
	let startX = 0, startY = 0, tracking = false;

	function onTouchStart(e) {
		const touch = e.touches[0];
		if (callbacks.edgeOnly && touch.clientX > edgeWidth) return;
		startX = touch.clientX;
		startY = touch.clientY;
		tracking = true;
	}

	function onTouchEnd(e) {
		if (!tracking) return;
		tracking = false;
		const touch = e.changedTouches[0];
		const dx = touch.clientX - startX;
		const dy = Math.abs(touch.clientY - startY);
		if (dy > maxVertical) return;
		if (dx > threshold) callbacks.onSwipeRight?.();
		else if (dx < -threshold) callbacks.onSwipeLeft?.();
	}

	el.addEventListener("touchstart", onTouchStart, { passive: true });
	el.addEventListener("touchend", onTouchEnd, { passive: true });
	return () => {
		el.removeEventListener("touchstart", onTouchStart);
		el.removeEventListener("touchend", onTouchEnd);
	};
}
