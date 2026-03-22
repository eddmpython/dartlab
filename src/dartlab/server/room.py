"""협업 세션 — SSE fan-out 기반 실시간 브로드캐스트.

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

    member_id: str
    name: str
    role: str  # "host" | "viewer"
    access_level: str  # "full" | "readonly"
    last_heartbeat: float = field(default_factory=time.monotonic)
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=QUEUE_MAX_SIZE))

    def info(self) -> dict:
        return {"memberId": self.member_id, "name": self.name, "role": self.role}


@dataclass
class ChatMessage:
    """채팅 메시지."""

    member_id: str
    name: str
    text: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "memberId": self.member_id,
            "name": self.name,
            "text": self.text,
            "timestamp": self.timestamp,
        }


class Room:
    """단일 협업 세션."""

    def __init__(self, room_id: str, host_name: str = "Host", host_access: str = "full"):
        self.room_id = room_id
        self.members: dict[str, RoomMember] = {}
        self.nav_state: dict = {}
        self.chat_history: list[ChatMessage] = []
        self.created_at = time.monotonic()
        self._lock = asyncio.Lock()
        self._analyzing = False

        # 호스트 자동 참여
        host = self._create_member(host_name, role="host", access_level=host_access)
        self.host_member_id = host.member_id
        self.members[host.member_id] = host

    @staticmethod
    def _create_member(name: str, *, role: str = "viewer", access_level: str = "readonly") -> RoomMember:
        return RoomMember(
            member_id=secrets.token_hex(4),
            name=name,
            role=role,
            access_level=access_level,
        )

    async def join(self, name: str, access_level: str = "readonly") -> RoomMember | None:
        """멤버 참여. 정원 초과 시 None 반환."""
        async with self._lock:
            if len(self.members) >= MAX_MEMBERS:
                return None
            member = self._create_member(name, access_level=access_level)
            self.members[member.member_id] = member

        await self.broadcast("member_join", member.info(), exclude=member.member_id)
        logger.info("[ROOM] %s 참여 (%s)", name, member.member_id[:4])
        return member

    async def leave(self, member_id: str) -> None:
        """멤버 퇴장."""
        async with self._lock:
            member = self.members.pop(member_id, None)
        if member:
            await self.broadcast("member_leave", {"memberId": member_id, "name": member.name})
            logger.info("[ROOM] %s 퇴장 (%s)", member.name, member_id[:4])

    def heartbeat(self, member_id: str) -> bool:
        """하트비트 갱신. 존재하지 않는 멤버면 False."""
        member = self.members.get(member_id)
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

    def add_chat(self, member_id: str, text: str) -> ChatMessage | None:
        """채팅 추가. 멤버가 없으면 None."""
        member = self.members.get(member_id)
        if not member:
            return None
        msg = ChatMessage(member_id=member_id, name=member.name, text=text)
        self.chat_history.append(msg)
        if len(self.chat_history) > MAX_CHAT_HISTORY:
            self.chat_history = self.chat_history[-MAX_CHAT_HISTORY:]
        return msg

    async def cleanup_stale(self) -> None:
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

    def get_state(self) -> dict:
        """현재 룸 상태."""
        return {
            "roomId": self.room_id,
            "members": [m.info() for m in self.members.values()],
            "navState": self.nav_state,
            "chatHistory": [c.to_dict() for c in self.chat_history[-50:]],
            "analyzing": self._analyzing,
        }

    def get_member(self, member_id: str) -> RoomMember | None:
        return self.members.get(member_id)


class RoomManager:
    """단일 룸 관리자."""

    def __init__(self):
        self._room: Room | None = None
        self._cleanup_task: asyncio.Task | None = None

    def create_room(self, host_name: str = "Host", host_access: str = "full") -> Room:
        room_id = secrets.token_hex(6)
        self._room = Room(room_id, host_name, host_access)
        logger.info("[ROOM] 룸 생성: %s", room_id)
        return self._room

    def get_room(self) -> Room | None:
        return self._room

    def destroy_room(self) -> None:
        if self._room:
            logger.info("[ROOM] 룸 파괴: %s", self._room.room_id)
        self._room = None

    async def start_cleanup_loop(self) -> None:
        """백그라운드 정리 루프."""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            room = self._room
            if room:
                await room.cleanup_stale()

    def start_background_cleanup(self) -> None:
        self._cleanup_task = asyncio.create_task(self.start_cleanup_loop())

    def stop_background_cleanup(self) -> None:
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# 싱글턴
room_manager = RoomManager()
