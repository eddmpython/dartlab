// vitest-pool-workers 설정. Cloudflare 0.18.x 는 Vitest 4 + cloudflareTest 플러그인 API 를 쓴다.
// 스키마 = migrations/(exec 멀티라인 금지).
import { cloudflareTest, readD1Migrations } from '@cloudflare/vitest-pool-workers';
import { defineConfig } from 'vitest/config';

const migrations = await readD1Migrations('./migrations');

export default defineConfig({
	plugins: [
		cloudflareTest({
			wrangler: { configPath: './wrangler.toml' },
			miniflare: {
				// 테스트 secret/vars 주입(wrangler.toml [vars] 에 더해). VAPID 키는 테스트 전용 더미.
				bindings: {
					TEST_MIGRATIONS: migrations,
					PUSHHUB_SEND_TOKEN: 'test-send-token',
					VAPID_SUBJECT: 'mailto:test@example.com',
					// 테스트 전용 P-256 키쌍(genVapid 로 생성, 프로덕션 무관. 발송 fetch 는 fetchMock 으로 차단).
					VAPID_PRIVATE_KEY:
						'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg3PoNpGCBkId8doM1T1WneCDh0nfLzOVM4fVZC92SFmmhRANCAAQquY1f-f_ZKCzq75F2_TzB2gpAm31Dpo_YSBdbByckNBHhSIoT6PDxQajnZnjmcpxZ79VO3ZDgg86cHwmyvyZj',
					VAPID_PUBLIC_KEY: 'BCq5jV_5_9koLOrvkXb9PMHaCkCbfUOmj9hIF1sHJyQ0EeFIihPo8PFBqOdmeOZynFnv1U7dkOCDzpwfCbK_JmM',
					ALLOW_ORIGIN: 'https://eddmpython.github.io'
				}
			}
		})
	],
	test: {
		setupFiles: ['./test/applyMigrations.js']
	}
});
