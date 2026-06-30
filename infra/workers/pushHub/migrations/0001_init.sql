-- 0001_init — pushHub D1 초기 스키마. schema.sql 과 동일(멀티라인 DDL → exec 'incomplete input' 회피용 migrations 경로).
-- vitest-pool-workers 하네스는 applyD1Migrations 로 이 파일을 읽는다([08 §4]).
CREATE TABLE IF NOT EXISTS subscriptions (
  endpoint TEXT PRIMARY KEY, p256dh TEXT NOT NULL, auth TEXT NOT NULL,
  uaClass TEXT NOT NULL DEFAULT 'other', createdAt TEXT NOT NULL, lastSeenAt TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS topicSubs (
  endpoint TEXT NOT NULL, topic TEXT NOT NULL, subscribedAt TEXT NOT NULL,
  PRIMARY KEY (endpoint, topic), FOREIGN KEY (endpoint) REFERENCES subscriptions(endpoint) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS topicSubsTopicIdx ON topicSubs (topic);
CREATE TABLE IF NOT EXISTS sentNonce (nonce TEXT PRIMARY KEY, ts INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS sentNonceTsIdx ON sentNonce (ts);
