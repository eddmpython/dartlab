import { describe, expect, it } from 'vitest';
import { localAiPort } from './aiSource';
import type { LocalApi } from '../api/localApi';

/**
 * 실측 회귀(2026-08-06): 준비 완료 판정이 정직해지자 기본 선호 런타임이 groundedReady=false 가
 * 됐는데, 화면은 선호값 하나만 보고 "사용 가능한 CLI 가 없습니다" 로 채팅 전체를 막았다.
 * 정작 서버는 실제로 도는 런타임으로 넘겨 답을 만들어 내고 있었다. 되는 제품을 화면이
 * 거부한 것이라 사용자에게는 제품이 없는 것과 같았다.
 */
function apiWith(payload: unknown): LocalApi {
	return { getJson: async () => payload } as unknown as LocalApi;
}

const CLAUDE = {
	runtimeId: 'claude',
	displayName: 'Claude Code',
	state: 'ready',
	version: '0.97',
	mcp: { connected: true },
	groundedReady: true
};
const BLOCKED = {
	runtimeId: 'codex',
	displayName: 'Codex',
	state: 'ready',
	version: '0.14',
	mcp: { connected: true },
	groundedReady: false
};

describe('localAiPort capabilities', () => {
	it('선호 런타임이 준비되지 않아도 준비된 것이 있으면 사용 가능으로 본다', async () => {
		const port = localAiPort(apiWith({ defaultRuntimeId: 'codex', runtimes: [BLOCKED, CLAUDE] }));

		const capabilities = await port.capabilities();

		expect(capabilities.tier).toBe('advanced');
		expect(capabilities.runtimeId).toBe('claude');
	});

	it('선호 런타임이 준비됐으면 그것을 그대로 고른다', async () => {
		const port = localAiPort(apiWith({ defaultRuntimeId: 'claude', runtimes: [BLOCKED, CLAUDE] }));

		const capabilities = await port.capabilities();

		expect(capabilities.runtimeId).toBe('claude');
	});

	it('준비된 런타임이 하나도 없을 때만 설치 경로를 안내한다', async () => {
		const port = localAiPort(apiWith({ defaultRuntimeId: 'codex', runtimes: [BLOCKED] }));

		const capabilities = await port.capabilities();

		expect(capabilities.tier).toBe('deterministic');
		expect(capabilities.upgradeHint).toBeTruthy();
	});
});
