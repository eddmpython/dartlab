"""DartLab Tunnel Security 유닛 테스트.

보안 모듈의 핵심 기능을 검증:
- 토큰 생성/검증
- 화이트리스트
- Rate limiting
- Kill Switch
- 입력 검증
- 이상 탐지
"""

from __future__ import annotations

import time

from dartlab.server.security import (
    AnomalyDetector,
    SlidingWindowLimiter,
    TokenManager,
    TunnelKillSwitch,
    _is_whitelisted,
    validate_base_url,
    validate_stock_code,
    validate_topic,
)

# ──────────────────────────────────────────────────────────
# TokenManager
# ──────────────────────────────────────────────────────────


class TestTokenManager:
    def test_auto_generate_token(self):
        tm = TokenManager()
        assert len(tm.full_token) > 20
        assert len(tm.readonly_token) > 20
        assert tm.full_token != tm.readonly_token

    def test_custom_token(self):
        tm = TokenManager("my-custom-token-12345")
        assert tm.full_token == "my-custom-token-12345"

    def test_validate_full_token(self):
        tm = TokenManager()
        assert tm.validate(tm.full_token) == "full"

    def test_validate_readonly_token(self):
        tm = TokenManager()
        assert tm.validate(tm.readonly_token) == "readonly"

    def test_validate_invalid_token(self):
        tm = TokenManager()
        assert tm.validate("wrong-token") is None
        assert tm.validate("") is None

    def test_token_hash_does_not_leak(self):
        tm = TokenManager()
        h = tm.token_hash(tm.full_token)
        assert len(h) == 8
        assert tm.full_token not in h

    def test_readonly_derived_deterministic(self):
        tm1 = TokenManager("same-token")
        tm2 = TokenManager("same-token")
        assert tm1.readonly_token == tm2.readonly_token


# ──────────────────────────────────────────────────────────
# 화이트리스트
# ──────────────────────────────────────────────────────────


class TestWhitelist:
    def test_allowed_endpoints(self):
        assert _is_whitelisted("/api/status")
        assert _is_whitelisted("/api/search")
        assert _is_whitelisted("/api/spec")
        assert _is_whitelisted("/api/ask")
        assert _is_whitelisted("/api/company/005930")
        assert _is_whitelisted("/api/company/005930/index")
        assert _is_whitelisted("/api/company/005930/sections")
        assert _is_whitelisted("/api/company/005930/show/revenue")
        assert _is_whitelisted("/api/company/005930/viewer/operatingIncome")
        assert _is_whitelisted("/api/company/005930/diff")
        assert _is_whitelisted("/api/company/005930/diff/matrix")
        assert _is_whitelisted("/api/company/005930/insights")
        assert _is_whitelisted("/api/company/AAPL/show/revenue")

    def test_ai_profile_allowed(self):
        assert _is_whitelisted("/api/ai/profile")

    def test_blocked_endpoints(self):
        assert not _is_whitelisted("/api/ai/profile/secrets")
        assert not _is_whitelisted("/api/configure")
        assert not _is_whitelisted("/api/ollama/pull")
        assert not _is_whitelisted("/api/export/excel/005930")
        assert not _is_whitelisted("/api/export/templates")
        assert not _is_whitelisted("/api/oauth/authorize")
        assert not _is_whitelisted("/api/oauth/status")
        assert not _is_whitelisted("/api/codex/logout")
        assert not _is_whitelisted("/api/models/openai")

    def test_path_traversal_blocked(self):
        assert not _is_whitelisted("/api/company/../../etc/passwd")
        assert not _is_whitelisted("/api/company/../secrets")


# ──────────────────────────────────────────────────────────
# Rate Limiter
# ──────────────────────────────────────────────────────────


class TestRateLimiter:
    def test_under_limit_passes(self):
        rl = SlidingWindowLimiter()
        for _ in range(9):
            assert rl.check("/api/ask")

    def test_ask_limit_exceeded(self):
        rl = SlidingWindowLimiter()
        for _ in range(10):
            rl.check("/api/ask")
        assert not rl.check("/api/ask")

    def test_sse_concurrency_limit(self):
        rl = SlidingWindowLimiter()
        assert rl.sse_acquire()
        assert rl.sse_acquire()
        assert rl.sse_acquire()
        assert not rl.sse_acquire()  # 4번째 차단
        rl.sse_release()
        assert rl.sse_acquire()  # 해제 후 허용


# ──────────────────────────────────────────────────────────
# Kill Switch
# ──────────────────────────────────────────────────────────


class TestKillSwitch:
    def test_active_within_ttl(self):
        ks = TunnelKillSwitch(ttl=3600)
        assert ks.check()
        assert ks.remaining > 3590

    def test_expired_after_ttl(self):
        ks = TunnelKillSwitch(ttl=1)
        # TTL 강제 초과
        ks.start_time = time.monotonic() - 2
        assert not ks.check()

    def test_manual_kill(self):
        ks = TunnelKillSwitch(ttl=3600)
        assert ks.check()
        ks.kill("test")
        assert not ks.check()

    def test_remaining_decreases(self):
        ks = TunnelKillSwitch(ttl=10)
        r1 = ks.remaining
        time.sleep(0.1)
        r2 = ks.remaining
        assert r2 <= r1


# ──────────────────────────────────────────────────────────
# 입력 검증
# ──────────────────────────────────────────────────────────


class TestInputValidation:
    # 종목코드
    def test_valid_stock_codes(self):
        assert validate_stock_code("005930")
        assert validate_stock_code("AAPL")
        assert validate_stock_code("0004V0")

    def test_invalid_stock_codes(self):
        assert not validate_stock_code("")
        assert not validate_stock_code("../etc")
        assert not validate_stock_code("../../passwd")
        assert not validate_stock_code("abc")  # 3자 미만
        assert not validate_stock_code("a" * 11)  # 11자 초과
        assert not validate_stock_code("test;drop")

    # 토픽
    def test_valid_topics(self):
        assert validate_topic("revenue")
        assert validate_topic("operatingIncome")
        assert validate_topic("BS")
        assert validate_topic("a1")

    def test_invalid_topics(self):
        assert not validate_topic("")
        assert not validate_topic("1abc")  # 숫자 시작
        assert not validate_topic("a" * 52)  # 51자 초과
        assert not validate_topic("test/../etc")
        assert not validate_topic("test;drop")

    # base_url SSRF
    def test_valid_base_urls(self):
        assert validate_base_url("https://api.openai.com/v1")
        assert validate_base_url("https://api.anthropic.com")

    def test_ssrf_blocked(self):
        assert not validate_base_url("http://10.0.0.1:8080")
        assert not validate_base_url("http://192.168.1.1:3000")
        assert not validate_base_url("http://172.16.0.1/api")
        assert not validate_base_url("http://127.0.0.1:8080")
        assert not validate_base_url("http://0.0.0.0:8080")
        assert not validate_base_url("http://localhost:8080")

    def test_ollama_local_allowed(self):
        assert validate_base_url("http://localhost:11434")
        assert validate_base_url("http://127.0.0.1:11434")


# ──────────────────────────────────────────────────────────
# 이상 탐지
# ──────────────────────────────────────────────────────────


class TestAnomalyDetector:
    def test_normal_traffic(self):
        ks = TunnelKillSwitch(ttl=3600)
        ad = AnomalyDetector(ks)
        for i in range(5):
            ad.record(f"/api/company/00593{i}", 200)
        assert ks.check()  # kill switch 발동 안 됨

    def test_scraping_triggers_kill(self):
        ks = TunnelKillSwitch(ttl=3600)
        ad = AnomalyDetector(ks)
        # 11개 다른 종목 접근 → 스크래핑 감지
        for i in range(11):
            ad.record(f"/api/company/code{i:04d}", 200)
        assert not ks.check()

    def test_high_error_rate_triggers_kill(self):
        ks = TunnelKillSwitch(ttl=3600)
        ad = AnomalyDetector(ks)
        # 21개 중 15개 에러 → 71% 에러율
        for i in range(21):
            status = 500 if i < 15 else 200
            ad.record("/api/ask", status)
        assert not ks.check()
