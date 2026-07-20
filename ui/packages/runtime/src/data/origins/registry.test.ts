// origins 레지스트리 단위 테스트 · hfMedia(회사 hero 이미지 serve SSOT) 배선 회귀 가드.
// hfMedia 가 dartlab-data(hf)와 **다른 repo** base 로 해석되는지, 미등록 origin 이 throw 하는지,
// 선행 슬래시가 정규화되는지 검증. 캐러셀 카드 hero src 가 잘못된 repo 로 새지 않게 고정.
import { describe, it, expect } from 'vitest';
import { originUrl, originConfigured, originCache, publicJsonPolicy } from './registry';
import { HF_MEDIA_RESOLVE, HF_RESOLVE } from './hf';

describe('origins.hfMedia', () => {
	it('hfMedia 는 dartlab-media repo 로 해석 · dartlab-data(hf) 와 다른 base', () => {
		const objectPath = `objects/sha256/ab/${'ab'.repeat(32)}.webp`;
		const media = originUrl('hfMedia', objectPath);
		expect(media).toBe(`${HF_MEDIA_RESOLVE}/${objectPath}`);
		expect(media).toContain('dartlab-media');
		// hf(데이터)와 분리됐는지 · 같은 path 가 다른 base 를 받는다.
		expect(HF_MEDIA_RESOLVE).not.toBe(HF_RESOLVE);
		expect(originUrl('hf', 'x')).toContain('dartlab-data');
	});

	it('선행 슬래시 정규화 · 중복 슬래시 없는 절대 URL', () => {
		expect(originUrl('hfMedia', '/manifests/companies.json')).toBe(`${HF_MEDIA_RESOLVE}/manifests/companies.json`);
	});

	it('hfMedia 는 비게이트 origin · 항상 configured', () => {
		expect(originConfigured('hfMedia')).toBe(true);
	});

	it('hfMedia 캐시 정책 · memory scope(이미지/매니페스트 재요청 절감)', () => {
		expect(originCache('hfMedia')?.scope).toBe('memory');
	});

	it('미등록 origin 은 throw · 배선순서 위반 노출', () => {
		expect(() => originUrl('duckdbHf', 'x')).toThrow();
	});
});

describe('public JSON policy SSOT', () => {
	it('퍼블릭 산출물은 HF 최신본 우선, 정적 파일은 장애 폴백', () => {
		expect(publicJsonPolicy('map/ecosystem.json').sourceOrder).toEqual(['hfLanding', 'localStatic']);
		expect(publicJsonPolicy('dashboards/finance.json').sourceOrder).toEqual(['hfLanding', 'localStatic']);
		expect(publicJsonPolicy('lenses/005930.json').sourceOrder).toEqual(['hfLanding', 'localStatic']);
	});

	it('회사 유니버스·시세·거시 최신본은 화면과 무관하게 무캐시', () => {
		for (const path of [
			'map/ecosystem.json',
			'map/search-index.json',
			'map/search-index-us.json',
			'map/prices-snapshot.json',
			'map/industryStats.json',
			'dashboards/macro.json'
		]) {
			expect(publicJsonPolicy(path).cache.scope).toBe('none');
		}
	});

	it('안정 퍼블릭 JSON만 6시간 영속 캐시', () => {
		const policy = publicJsonPolicy('map/companies/005930.json');
		expect(policy.cache).toEqual({ scope: 'persistent', ttlMs: 6 * 60 * 60_000, staleOnError: true });
	});
});
