"""협업 세션: SSE fan-out 기반 실시간 브로드캐스트.

dartlab share 실행 시 단일 룸을 생성하고,
여러 클라이언트가 같은 분석 세션을 실시간으로 공유한다.

아키텍처:
  Server→Client: SSE /api/room/stream (멤버별 asyncio.Queue)
  Client→Server: POST /api/room/{action}
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAX_MEMBERS = 10
MAX_CHAT_HISTORY = 100
QUEUE_MAX_SIZE = 64
HEARTBEAT_TIMEOUT = 60  # 초
CLEANUP_INTERVAL = 30  # 초


@dataclass
class RoomMember:
    """룸 참여자."""

    memberId: str
    publicId: str
    name: str
    role: str  # "host" | "viewer"
    accessLevel: str  # "full" | "readonly"
    last_heartbeat: float = field(default_factory=time.monotonic)
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=QUEUE_MAX_SIZE))

    def info(self) -> dict:
        """멤버 정보를 직렬화 가능한 dict로 반환한다."""
        return {"memberId": self.publicId, "name": self.name, "role": self.role}


@dataclass
class ChatMessage:
    """채팅 메시지."""

    memberId: str
    name: str
    text: str
    timestamp: float = field(default_factory=time.time)

    def toDict(self) -> dict:
        """채팅 메시지를 직렬화 가능한 dict로 반환한다."""
        return {
            "memberId": self.memberId,
            "name": self.name,
            "text": self.text,
            "timestamp": self.timestamp,
        }


class Room:
    """단일 협업 세션."""

    def __init__(self, roomId: str, hostName: str = "Host", hostAccess: str = "full"):
        self.roomId = roomId
        self.members: dict[str, RoomMember] = {}
        self.nav_state: dict = {}
        self.chat_history: list[ChatMessage] = []
        self.created_at = time.monotonic()
        self._lock = asyncio.Lock()
        self._analyzing = False

        # 호스트 자동 참여
        host = self._createMember(hostName, role="host", accessLevel=hostAccess)
        self.host_member_id = host.memberId
        self.members[host.memberId] = host

    @staticmethod
    def _createMember(name: str, *, role: str = "viewer", accessLevel: str = "readonly") -> RoomMember:
        return RoomMember(
            memberId=secrets.token_urlsafe(32),
            publicId=secrets.token_hex(4),
            name=name,
            role=role,
            accessLevel=accessLevel,
        )

    async def join(self, name: str, accessLevel: str = "readonly") -> RoomMember | None:
        """멤버 참여. 정원 초과 시 None 반환."""
        async with self._lock:
            if len(self.members) >= MAX_MEMBERS:
                return None
            member = self._createMember(name, accessLevel=accessLevel)
            self.members[member.memberId] = member

        await self.broadcast("member_join", member.info(), exclude=member.memberId)
        logger.info("[ROOM] %s 참여 (%s)", name, member.memberId[:4])
        return member

    async def leave(self, memberId: str) -> None:
        """멤버 퇴장."""
        async with self._lock:
            member = self.members.pop(memberId, None)
        if member:
            await self.broadcast("member_leave", {"memberId": member.publicId, "name": member.name})
            logger.info("[ROOM] %s 퇴장 (%s)", member.name, memberId[:4])

    def heartbeat(self, memberId: str) -> bool:
        """하트비트 갱신. 존재하지 않는 멤버면 False."""
        member = self.members.get(memberId)
        if not member:
            return False
        member.last_heartbeat = time.monotonic()
        return True

    async def broadcast(self, event: str, data: dict, *, exclude: str | None = None) -> None:
        """모든 멤버 큐에 이벤트 push."""
        dead: list[str] = []
        for mid, member in self.members.items():
            if mid == exclude:
                continue
            try:
                member.queue.put_nowait({"event": event, "data": data})
            except asyncio.QueueFull:
                dead.append(mid)
        # 큐 가득 찬 멤버 제거
        for mid in dead:
            removed = self.members.pop(mid, None)
            if removed:
                logger.warning("[ROOM] %s 큐 초과로 제거 (%s)", removed.name, mid[:4])

    def addChat(self, memberId: str, text: str) -> ChatMessage | None:
        """채팅 추가. 멤버가 없으면 None."""
        member = self.members.get(memberId)
        if not member:
            return None
        msg = ChatMessage(memberId=member.publicId, name=member.name, text=text)
        self.chat_history.append(msg)
        if len(self.chat_history) > MAX_CHAT_HISTORY:
            self.chat_history = self.chat_history[-MAX_CHAT_HISTORY:]
        return msg

    async def cleanupStale(self) -> None:
        """타임아웃된 멤버 제거 (호스트 제외)."""
        now = time.monotonic()
        stale: list[str] = []
        for mid, member in self.members.items():
            if mid == self.host_member_id:
                continue
            if now - member.last_heartbeat > HEARTBEAT_TIMEOUT:
                stale.append(mid)
        for mid in stale:
            await self.leave(mid)

    def getState(self) -> dict:
        """현재 룸 상태."""
        return {
            "roomId": self.roomId,
            "members": [m.info() for m in self.members.values()],
            "navState": self.nav_state,
            "chatHistory": [c.toDict() for c in self.chat_history[-50:]],
            "analyzing": self._analyzing,
        }

    def getMember(self, memberId: str) -> RoomMember | None:
        """멤버 ID로 RoomMember를 조회한다."""
        return self.members.get(memberId)


class RoomManager:
    """단일 룸 관리자."""

    def __init__(self):
        self._room: Room | None = None
        self._cleanup_task: asyncio.Task | None = None

    def createRoom(self, hostName: str = "Host", hostAccess: str = "full") -> Room:
        """새 협업 룸을 생성하고 호스트를 등록한다."""
        roomId = secrets.token_hex(6)
        self._room = Room(roomId, hostName, hostAccess)
        logger.info("[ROOM] 룸 생성: %s", roomId)
        return self._room

    def getRoom(self) -> Room | None:
        """현재 활성 룸을 반환한다."""
        return self._room

    def destroyRoom(self) -> None:
        """현재 룸을 파괴한다."""
        if self._room:
            logger.info("[ROOM] 룸 파괴: %s", self._room.roomId)
        self._room = None

    async def startCleanupLoop(self) -> None:
        """백그라운드 정리 루프."""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            room = self._room
            if room:
                await room.cleanupStale()

    def startBackgroundCleanup(self) -> None:
        """비활성 멤버 정리 백그라운드 태스크를 시작한다."""
        self._cleanup_task = asyncio.create_task(self.startCleanupLoop())

    def stopBackgroundCleanup(self) -> None:
        """백그라운드 정리 태스크를 취소한다."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# 싱글턴
roomManager = RoomManager()
