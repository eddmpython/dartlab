import { describe, expect, it } from 'vitest';
import {
	mergePackageSpecs,
	packageSpecKey,
	parsePackageManifest,
	parsePipInstallCommand,
	parseRequirementsText,
	serializePackageManifest
} from './packageManifest';

describe('packageManifest', () => {
	it('deduplicates package specs by canonical package name', () => {
		expect(mergePackageSpecs(['Polars==1.0.0'], ['polars==1.1.0', 'micropip'])).toEqual([
			'micropip',
			'polars==1.1.0'
		]);
		expect(packageSpecKey('my_pkg.extra>=2')).toBe('my-pkg-extra');
	});

	it('parses requirements text without pip options or comments', () => {
		expect(parseRequirementsText(`
			# notebook deps
			requests==2.32.0 # pure python
			-r other.txt
			duckdb
		`)).toEqual(['duckdb', 'requests==2.32.0']);
	});

	it('roundtrips the workspace package manifest', () => {
		const text = serializePackageManifest(['requests', 'polars'], new Date('2026-01-02T03:04:05.000Z'));
		expect(parsePackageManifest(text)).toEqual({
			version: 1,
			packages: ['polars', 'requests'],
			updatedAt: '2026-01-02T03:04:05.000Z'
		});
	});

	it('recognizes local notebook pip install commands', () => {
		expect(parsePipInstallCommand('%pip install requests "polars==1.0.0"')).toEqual([
			'polars==1.0.0',
			'requests'
		]);
		expect(parsePipInstallCommand('print("not pip")')).toBeNull();
		expect(() => parsePipInstallCommand('!pip install --index-url https://example.test requests')).toThrow(
			'pip options are not supported'
		);
	});
});
