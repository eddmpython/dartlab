-- dartlab Push Hub — D1 스키마 (2 구독 테이블 + nonce). 개인조건·user_id·종목 컬럼 영구 0.
-- 정본 = mainPlan/watcher-notify-platform/06-p1-hub-worker.md §6. migrations/0001_init.sql 과 동일 내용.
CREATE TABLE IF NOT EXISTS subscriptions (
  endpoint TEXT PRIMARY KEY, p256dh TEXT NOT NULL, auth TEXT NOT NULL,
  uaClass TEXT NOT NULL DEFAULT 'other', createdAt TEXT NOT NULL, lastSeenAt TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS topicSubs (
  endpoint TEXT NOT NULL, topic TEXT NOT NULL, subscribedAt TEXT NOT NULL,
  PRIMARY KEY (endpoint, topic), FOREIGN KEY (endpoint) REFERENCES subscriptions(endpoint) ON DELETE CASCADE);
CREATE INDEX IF NOT EXISTS topicSubsTopicIdx ON topicSubs (topic);
CREATE TABLE IF NOT EXISTS sentNonce (nonce TEXT PRIMARY KEY, ts INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS sentNonceTsIdx ON sentNonce (ts);
-- threshold_cross 상태 커서 (직전 활성 매치 set). stateful 토픽(newOrders) 재크로싱 감지용.
-- 원천 데이터 베이크 아님 = 알림 dedup 메타(01-architecture §5). stateless 토픽(newIpo)은 미사용.
CREATE TABLE IF NOT EXISTS topicActive (topic TEXT NOT NULL, matchKey TEXT NOT NULL, PRIMARY KEY (topic, matchKey));
