// vitest-pool-workers 설정 — Miniflare 로컬 D1 + worker.js 격리 실행.
// ⚠ config API 는 설치한 @cloudflare/vitest-pool-workers 버전에 따라 다를 수 있다(08 §4): 첫 npm test 가
// red 면 설치버전 공식 템플릿(npm create cloudflare → Worker+Vitest)에서 이 파일을 재스캐폴드하고 package.json
// 핀을 맞춘다. 아래는 0.8.x + vitest 2.x 기준 초안. 스키마 = migrations/(exec 멀티라인 금지).
import { defineWorkersConfig, readD1Migrations } from '@cloudflare/vitest-pool-workers/config';

const migrations = await readD1Migrations('./migrations');

export default defineWorkersConfig({
	test: {
		setupFiles: ['./test/applyMigrations.js'],
		poolOptions: {
			workers: {
				wrangler: { configPath: './wrangler.toml' },
				miniflare: {
					// 테스트 secret/vars 주입(wrangler.toml [vars] 에 더해). VAPID 키는 테스트 전용 더미.
					bindings: {
						TEST_MIGRATIONS: migrations,
						PUSHHUB_SEND_TOKEN: 'test-send-token',
						VAPID_SUBJECT: 'mailto:test@example.com',
						// 테스트 전용 P-256 키쌍(genVapid 로 생성, 프로덕션 무관 — 발송 fetch 는 fetchMock 으로 차단).
						VAPID_PRIVATE_KEY:
							'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg3PoNpGCBkId8doM1T1WneCDh0nfLzOVM4fVZC92SFmmhRANCAAQquY1f-f_ZKCzq75F2_TzB2gpAm31Dpo_YSBdbByckNBHhSIoT6PDxQajnZnjmcpxZ79VO3ZDgg86cHwmyvyZj',
						VAPID_PUBLIC_KEY: 'BCq5jV_5_9koLOrvkXb9PMHaCkCbfUOmj9hIF1sHJyQ0EeFIihPo8PFBqOdmeOZynFnv1U7dkOCDzpwfCbK_JmM',
						ALLOW_ORIGIN: 'https://eddmpython.github.io'
					}
				}
			}
		}
	}
});
