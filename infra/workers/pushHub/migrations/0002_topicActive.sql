-- 0002_topicActive. threshold_cross stateful 토픽(newOrders) 직전 활성 매치 set 커서.
-- 재크로싱(하락 후 재상승) 발화용. 원천 베이크 아님 = 알림 dedup 메타(01-architecture §5).
CREATE TABLE IF NOT EXISTS topicActive (topic TEXT NOT NULL, matchKey TEXT NOT NULL, PRIMARY KEY (topic, matchKey));
