// setupFile — 각 테스트파일 전 D1 마이그레이션 적용(스키마 생성). migrations/ 경유(exec 멀티라인 금지).
import { applyD1Migrations, env } from 'cloudflare:test';

await applyD1Migrations(env.PUSHHUB_DB, env.TEST_MIGRATIONS);
