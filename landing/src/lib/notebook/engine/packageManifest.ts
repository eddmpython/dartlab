export interface PackageManifest {
	version: 1;
	packages: string[];
	updatedAt: string;
}

export function normalizePackageSpec(spec: string): string {
	const trimmed = spec.trim();
	if (!trimmed) throw new Error('Package spec is empty');
	if (/[\r\n]/.test(trimmed)) throw new Error('Package spec must be one line');
	if (trimmed.startsWith('-')) {
		throw new Error('pip options are not supported in browser notebooks');
	}
	return trimmed;
}

export function packageSpecKey(spec: string): string {
	const trimmed = spec.trim();
	const nameMatch = trimmed.match(/^([A-Za-z0-9][A-Za-z0-9._-]*)/);
	const key = nameMatch ? nameMatch[1] : trimmed;
	return key.toLowerCase().replace(/[-_.]+/g, '-');
}

export function mergePackageSpecs(current: string[], next: string[]): string[] {
	const byKey = new Map<string, string>();
	for (const spec of [...current, ...next]) {
		const normalized = normalizePackageSpec(spec);
		byKey.set(packageSpecKey(normalized), normalized);
	}
	return Array.from(byKey.values()).sort((a, b) => packageSpecKey(a).localeCompare(packageSpecKey(b)));
}

export function parseRequirementsText(text: string): string[] {
	const specs: string[] = [];
	for (const rawLine of text.split(/\r?\n/)) {
		const line = rawLine.replace(/\s+#.*$/, '').trim();
		if (!line || line.startsWith('#') || line.startsWith('-')) continue;
		specs.push(normalizePackageSpec(line));
	}
	return mergePackageSpecs([], specs);
}

export function parsePackageManifest(text: string): PackageManifest {
	const parsed = JSON.parse(text) as Partial<PackageManifest> | string[];
	const rawPackages = Array.isArray(parsed) ? parsed : parsed.packages;
	return {
		version: 1,
		packages: mergePackageSpecs([], rawPackages ?? []),
		updatedAt: Array.isArray(parsed) ? '' : parsed.updatedAt ?? ''
	};
}

export function serializePackageManifest(packages: string[], now = new Date()): string {
	const manifest: PackageManifest = {
		version: 1,
		packages: mergePackageSpecs([], packages),
		updatedAt: now.toISOString()
	};
	return JSON.stringify(manifest, null, 2);
}

function splitInstallArgs(input: string): string[] {
	const tokens: string[] = [];
	let current = '';
	let quote: '"' | "'" | null = null;
	let escaped = false;
	for (const ch of input) {
		if (escaped) {
			current += ch;
			escaped = false;
			continue;
		}
		if (ch === '\\') {
			escaped = true;
			continue;
		}
		if (quote) {
			if (ch === quote) {
				quote = null;
			} else {
				current += ch;
			}
			continue;
		}
		if (ch === '"' || ch === "'") {
			quote = ch;
			continue;
		}
		if (/\s/.test(ch)) {
			if (current) {
				tokens.push(current);
				current = '';
			}
			continue;
		}
		current += ch;
	}
	if (quote) throw new Error('Unclosed quote in pip install command');
	if (escaped) current += '\\';
	if (current) tokens.push(current);
	return tokens;
}

export function parsePipInstallCommand(code: string): string[] | null {
	const lines = code.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
	if (lines.length !== 1) return null;
	const match = lines[0].match(/^(?:%pip|!pip)\s+install\s+(.+)$/);
	if (!match) return null;
	const specs = splitInstallArgs(match[1]);
	if (specs.length === 0) throw new Error('Package spec is empty');
	return mergePackageSpecs([], specs);
}
