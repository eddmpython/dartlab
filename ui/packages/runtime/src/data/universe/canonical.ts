const SHA256_PATTERN = /^sha256:[0-9a-f]{64}$/;

function stableValue(value: unknown): unknown {
	if (Array.isArray(value)) return value.map(stableValue);
	if (value && typeof value === 'object') {
		const record = value as Record<string, unknown>;
		return Object.fromEntries(Object.keys(record).sort().map((key) => [key, stableValue(record[key])]));
	}
	return value;
}

export function canonicalStringify(value: unknown): string {
	return JSON.stringify(stableValue(value));
}

export function isSha256Id(value: string): boolean {
	return SHA256_PATTERN.test(value);
}

export async function canonicalSha256(value: unknown): Promise<string> {
	const subtle = globalThis.crypto?.subtle;
	if (!subtle) throw new Error('Universe canonical SHA-256 is unavailable');
	const bytes = new TextEncoder().encode(canonicalStringify(value));
	const digest = await subtle.digest('SHA-256', bytes);
	const hex = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
	return `sha256:${hex}`;
}

export function stripSha256(value: string): string {
	if (!isSha256Id(value)) throw new Error('Universe value requires a SHA-256 identity');
	return value.slice('sha256:'.length);
}
