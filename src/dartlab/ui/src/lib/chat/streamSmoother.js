const DEFAULT_OPTIONS = {
	cadenceMs: 48,
	maxHoldMs: 180,
	minChunkLength: 6,
	targetChunkLength: 20,
	maxChunkLength: 48,
};

const STRONG_BOUNDARY_PATTERNS = [
	/(?:\r?\n){2,}/g,
	/(?:[.!?…。]["')\]]?(?:\s+|$))/g,
	/\r?\n/g,
];

const SOFT_BOUNDARY_PATTERNS = [
	/(?:[,;:]["')\]]?(?:\s+|$))/g,
	/\s+/g,
];

function clampOptions(options = {}) {
	const merged = { ...DEFAULT_OPTIONS, ...options };
	const minChunkLength = Math.max(1, Number(merged.minChunkLength) || DEFAULT_OPTIONS.minChunkLength);
	const targetChunkLength = Math.max(minChunkLength, Number(merged.targetChunkLength) || DEFAULT_OPTIONS.targetChunkLength);
	const maxChunkLength = Math.max(targetChunkLength, Number(merged.maxChunkLength) || DEFAULT_OPTIONS.maxChunkLength);

	return {
		cadenceMs: Math.max(16, Number(merged.cadenceMs) || DEFAULT_OPTIONS.cadenceMs),
		maxHoldMs: Math.max(32, Number(merged.maxHoldMs) || DEFAULT_OPTIONS.maxHoldMs),
		minChunkLength,
		targetChunkLength,
		maxChunkLength,
	};
}

function findLastBoundary(text, minIndex, patterns) {
	let lastBoundary = 0;
	for (const pattern of patterns) {
		pattern.lastIndex = 0;
		let match = pattern.exec(text);
		while (match) {
			const boundary = match.index + match[0].length;
			if (boundary >= minIndex) {
				lastBoundary = Math.max(lastBoundary, boundary);
			}
			if (pattern.lastIndex === match.index) {
				pattern.lastIndex += 1;
			}
			match = pattern.exec(text);
		}
	}
	return lastBoundary;
}

export function chooseStreamFlushIndex(text, options = {}, force = false) {
	if (!text) return 0;

	const config = clampOptions(options);
	const strongMinIndex = Math.min(
		text.length,
		force ? config.minChunkLength : config.targetChunkLength
	);
	const strongBoundary = findLastBoundary(text, strongMinIndex, STRONG_BOUNDARY_PATTERNS);
	if (strongBoundary > 0) return strongBoundary;

	const reachedHardLimit = text.length >= config.maxChunkLength;
	if (!force && !reachedHardLimit) return 0;

	const softMinIndex = Math.min(
		text.length,
		Math.max(config.minChunkLength, Math.floor(config.targetChunkLength * 0.6))
	);
	const softBoundary = findLastBoundary(text, softMinIndex, SOFT_BOUNDARY_PATTERNS);
	if (softBoundary > 0) return softBoundary;

	return Math.min(text.length, Math.max(config.minChunkLength, config.targetChunkLength));
}

export function createStreamSmoother(onChunk, options = {}) {
	const config = clampOptions(options);
	let buffer = "";
	let flushTimer = null;
	let firstBufferedAt = 0;

	function nowMs() {
		return Date.now();
	}

	function clearFlushTimer() {
		if (flushTimer) {
			clearTimeout(flushTimer);
			flushTimer = null;
		}
	}

	function scheduleFlush() {
		if (flushTimer || !buffer) return;
		flushTimer = setTimeout(() => {
			flushTimer = null;
			emitReady(false);
			if (buffer) {
				scheduleFlush();
			}
		}, config.cadenceMs);
	}

	function emitSlice(index) {
		if (!buffer || index <= 0) return false;
		const chunk = buffer.slice(0, index);
		if (!chunk) return false;
		onChunk?.(chunk);
		buffer = buffer.slice(index);
		firstBufferedAt = buffer ? nowMs() : 0;
		return true;
	}

	function emitReady(force = false) {
		if (!buffer) return false;
		const heldMs = firstBufferedAt ? nowMs() - firstBufferedAt : 0;
		const shouldForce = force || heldMs >= config.maxHoldMs || buffer.length >= config.maxChunkLength;
		const flushIndex = chooseStreamFlushIndex(buffer, config, shouldForce);
		if (flushIndex <= 0) return false;
		return emitSlice(flushIndex);
	}

	return {
		push(text) {
			if (!text) return;
			buffer += text;
			if (!firstBufferedAt) {
				firstBufferedAt = nowMs();
			}
			if (!emitReady(false)) {
				scheduleFlush();
			} else if (buffer) {
				scheduleFlush();
			}
		},
		flush() {
			clearFlushTimer();
			while (emitReady(true)) {
				// Force semantic slices first so the final flush still feels chunked.
			}
			if (buffer) {
				onChunk?.(buffer);
				buffer = "";
			}
			firstBufferedAt = 0;
		},
		reset() {
			clearFlushTimer();
			buffer = "";
			firstBufferedAt = 0;
		},
		getBufferedText() {
			return buffer;
		},
	};
}
