"""prebuild·로컬 가공 단계 외부 네트워크 차단 가드.

prebuild 책임 = **로컬 parquet → derived parquet/JSON 변환만**. 외부 API 호출 (DART /
EDGAR / FRED / ECOS / Naver / KRX / HF) 는 sync 단계 책임이고 prebuild 안에 박히면
다음 문제가 발생한다:

1. sync 직후 API rate-limit 잔존 → prebuild 가 IP 차단 유발
2. 책임 경계 위반 → 한 단계 실패가 다른 단계까지 막음
3. CI 환경에서 외부 의존 → 빌드 비결정성

본 모듈은 ``enforceOffline()`` 호출 시 ``socket.socket.connect`` 를 monkey-patch 해서
외부 host 연결 시도를 즉시 ``OfflineViolation`` 으로 차단한다. 로컬·UNIX·HF 캐시
파일 IO 는 통과 (loopback / 도메인 소켓 / 파일은 socket connect 와 무관).

설계:

- socket connect 단계에서 차단 → httpx·requests·aiohttp·huggingface_hub 등 모든
  HTTP 클라이언트 동시 커버 (전부 결국 socket 으로 내려옴).
- allow-list 는 loopback IP (``127.0.0.1`` · ``::1`` · ``localhost``) 만 기본 허용.
  prebuild 가 로컬 DB / 로컬 서버 (예: pyserver / 로컬 OLAP) 에 접근하면 통과.
- ``enforceOffline()`` 는 idempotent. 두 번 호출해도 부작용 없다.
- 해제는 ``releaseOffline()`` — 테스트 fixture 에서만 사용. 운영 코드에서는 호출 금지.

Example:
    >>> from dartlab.core.offlineGuard import enforceOffline
    >>> enforceOffline()
    >>> import httpx  # 정상
    >>> httpx.get("https://opendart.fss.or.kr/...")  # OfflineViolation 발생
    Traceback (most recent call last):
        ...
    dartlab.core.offlineGuard.OfflineViolation: prebuild 단계 외부 네트워크 호출 차단: ...

prebuild 진입점 사용:

    def main():
        from dartlab.core.offlineGuard import enforceOffline
        enforceOffline()
        # ... 이하 로컬 parquet 처리

위반이 감지되면 traceback 으로 어느 라이브러리가 호출했는지 즉시 식별.
"""

from __future__ import annotations

import socket
import traceback
from typing import Iterable

_ORIGINAL_CONNECT = None
_ORIGINAL_CONNECT_EX = None
_ORIGINAL_GETADDRINFO = None
_ENFORCED = False
_STRICT = False

# DNS resolve cache: IP -> hostname. getaddrinfo 가 host name 으로 resolve 한 결과를
# socket.connect 시점에 raw IP 로 받기 때문에 hostname 매칭이 안 된다. getaddrinfo
# 를 monkey-patch 해서 호출되는 hostname 을 캐시하고, connect 시점에 IP -> hostname
# 역조회로 허용 여부 판정한다.
_dnsCache: dict[str, str] = {}

# loopback + HuggingFace dataset CDN 기본 허용. prebuild 가 HF 에서 raw / derived
# parquet 다운로드는 필수 (CI runner 는 디스크에 없음). 외부 API (DART/EDGAR/FRED/
# ECOS/Naver/KRX) 는 sync 단계 책임이므로 차단.
_LOOPBACK_HOSTS: frozenset[str] = frozenset(
    {
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "localhost",
    }
)

_DEFAULT_ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        *_LOOPBACK_HOSTS,
        # HuggingFace Hub — dataset 다운로드 (prebuild input).
        "huggingface.co",
        "cdn-lfs.huggingface.co",
        "cdn-lfs.hf.co",
        "hf.co",
        "hf-mirror.com",
    }
)


# HF host suffix — wildcard subdomain 매칭 (예: cdn-lfs-us-1.huggingface.co).
_ALLOWED_SUFFIXES: tuple[str, ...] = (
    ".huggingface.co",
    ".hf.co",
)

_extraAllowed: set[str] = set()


class OfflineViolation(RuntimeError):
    """prebuild·offline 단계에서 외부 네트워크 호출 시도 발생."""

    code = "OFFLINE_NETWORK_BLOCKED"


def _hostnameAllowed(host: str) -> bool:
    """순수 hostname 매칭 (cache 미사용)."""
    if _STRICT:
        return host in _LOOPBACK_HOSTS or host.startswith("127.")
    if host in _DEFAULT_ALLOWED_HOSTS:
        return True
    if host in _extraAllowed:
        return True
    # IPv4 loopback range 127.0.0.0/8
    if host.startswith("127."):
        return True
    # wildcard subdomain (예: cdn-lfs-us-1.huggingface.co).
    for suffix in _ALLOWED_SUFFIXES:
        if host.endswith(suffix):
            return True
    return False


def _isAllowedHost(host: str | bytes | None) -> bool:
    if host is None:
        return True
    if isinstance(host, bytes):
        try:
            host = host.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            return False
    host = host.strip().lower()
    if not host:
        return True
    if _hostnameAllowed(host):
        return True
    # IP 가 들어온 경우 — DNS resolve 시 캐시된 hostname 으로 역조회.
    cachedName = _dnsCache.get(host)
    if cachedName and _hostnameAllowed(cachedName):
        return True
    return False


def _extractHost(address) -> str | None:
    """socket connect address 에서 host 추출.

    AF_INET / AF_INET6 → tuple (host, port[, flowinfo, scopeid])
    AF_UNIX → str (file path)
    """
    if isinstance(address, (str, bytes)):
        # UNIX domain socket — 로컬 IPC, 통과.
        return None
    if isinstance(address, tuple) and address:
        host = address[0]
        if isinstance(host, (str, bytes)):
            return host if isinstance(host, str) else host.decode("utf-8", errors="replace")
    return None


def _guardedConnect(self, address):
    host = _extractHost(address)
    if host is None or _isAllowedHost(host):
        originalConnect = _ORIGINAL_CONNECT
        if originalConnect is None:
            raise RuntimeError("offline guard original connect가 초기화되지 않았습니다")
        return originalConnect(self, address)
    raise OfflineViolation(
        f"prebuild 단계 외부 네트워크 호출 차단: host={host!r} address={address!r}. "
        "외부 API 호출은 sync/ 단계로 이동시키시오. "
        "허용된 host 만 추가하려면 enforceOffline(allowedHosts=[...]) 또는 releaseOffline()."
    )


def _guardedConnectEx(self, address):
    host = _extractHost(address)
    if host is None or _isAllowedHost(host):
        originalConnectEx = _ORIGINAL_CONNECT_EX
        if originalConnectEx is None:
            raise RuntimeError("offline guard original connect_ex가 초기화되지 않았습니다")
        return originalConnectEx(self, address)
    raise OfflineViolation(f"prebuild 단계 외부 네트워크 호출 차단 (connect_ex): host={host!r} address={address!r}.")


def _guardedGetaddrinfo(host, *args, **kwargs):
    """getaddrinfo wrapper — hostname 으로 호출된 IP 들을 캐시.

    httpx / requests / huggingface_hub 모두 socket connect 전에 getaddrinfo 를 호출
    한다. 그 시점의 hostname 을 IP 별로 기록해두면 raw IP connect 시점에 역조회로
    허용/차단 판정 가능. hostname 허용된 경우에만 캐시 — 차단 host 의 IP 는 캐시
    안 함 (false negative 방지).
    """
    if _STRICT and isinstance(host, str) and not _hostnameAllowed(host.strip().lower()):
        raise OfflineViolation(
            f"strict offline 단계 DNS 호출 차단: host={host!r}. "
            "eager continuation child는 loopback 외 네트워크를 허용하지 않습니다."
        )
    originalGetaddrinfo = _ORIGINAL_GETADDRINFO
    if originalGetaddrinfo is None:
        raise RuntimeError("offline guard original getaddrinfo가 초기화되지 않았습니다")
    results = originalGetaddrinfo(host, *args, **kwargs)
    if host and isinstance(host, str):
        hostLower = host.strip().lower()
        if _hostnameAllowed(hostLower):
            for res in results:
                # res = (family, socktype, proto, canonname, sockaddr)
                sockaddr = res[4] if len(res) >= 5 else None
                if isinstance(sockaddr, tuple) and sockaddr:
                    ip = sockaddr[0]
                    if isinstance(ip, str):
                        _dnsCache[ip] = hostLower
    return results


def enforceOffline(
    allowedHosts: Iterable[str] | None = None,
    *,
    strict: bool = False,
) -> None:
    """외부 네트워크 호출 차단 가드 활성화.

    ``socket.socket.connect`` / ``connect_ex`` 를 monkey-patch. loopback 은 통과.

    Args:
        allowedHosts: 기본 loopback 외 추가 허용할 host 명/IP. 예: 로컬 OLAP 서버 IP.
        strict: ``True``면 HF와 추가 host도 제외하고 loopback만 허용.

    Idempotent — 이미 활성화돼 있으면 allowedHosts 만 추가하고 return.
    """
    global _ORIGINAL_CONNECT, _ORIGINAL_CONNECT_EX, _ORIGINAL_GETADDRINFO, _ENFORCED, _STRICT

    if allowedHosts:
        _extraAllowed.update(h.strip().lower() for h in allowedHosts if h and h.strip())
    _STRICT = _STRICT or strict

    if _ENFORCED:
        return

    _ORIGINAL_CONNECT = socket.socket.connect
    _ORIGINAL_CONNECT_EX = socket.socket.connect_ex
    _ORIGINAL_GETADDRINFO = socket.getaddrinfo
    socket.socket.connect = _guardedConnect  # type: ignore[method-assign]
    socket.socket.connect_ex = _guardedConnectEx  # type: ignore[method-assign]
    socket.getaddrinfo = _guardedGetaddrinfo  # type: ignore[assignment]
    _ENFORCED = True


def releaseOffline() -> None:
    """가드 해제 — 테스트 fixture 전용. 운영 코드에서는 호출 금지."""
    global _ORIGINAL_CONNECT, _ORIGINAL_CONNECT_EX, _ORIGINAL_GETADDRINFO, _ENFORCED, _STRICT

    if not _ENFORCED:
        return
    if _ORIGINAL_CONNECT is not None:
        socket.socket.connect = _ORIGINAL_CONNECT  # type: ignore[method-assign]
    if _ORIGINAL_CONNECT_EX is not None:
        socket.socket.connect_ex = _ORIGINAL_CONNECT_EX  # type: ignore[method-assign]
    if _ORIGINAL_GETADDRINFO is not None:
        socket.getaddrinfo = _ORIGINAL_GETADDRINFO  # type: ignore[assignment]
    _ORIGINAL_CONNECT = None
    _ORIGINAL_CONNECT_EX = None
    _ORIGINAL_GETADDRINFO = None
    _extraAllowed.clear()
    _dnsCache.clear()
    _ENFORCED = False
    _STRICT = False


def isOfflineEnforced() -> bool:
    """현재 가드 활성 상태."""
    return _ENFORCED


def whereCalled() -> str:
    """OfflineViolation 발생 위치 디버깅 보조 — stack trace 문자열."""
    return "".join(traceback.format_stack())


__all__ = [
    "OfflineViolation",
    "enforceOffline",
    "releaseOffline",
    "isOfflineEnforced",
    "whereCalled",
]
