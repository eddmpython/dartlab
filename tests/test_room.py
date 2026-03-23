"""Room 협업 세션 테스트."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from dartlab.server.room import (
    HEARTBEAT_TIMEOUT,
    MAX_CHAT_HISTORY,
    MAX_MEMBERS,
    QUEUE_MAX_SIZE,
    Room,
    RoomManager,
)

# ---------------------------------------------------------------------------
# Room 기본 기능
# ---------------------------------------------------------------------------


class TestRoom:
    def test_room_creates_with_host(self):
        room = Room("test-room", host_name="Alice")
        assert len(room.members) == 1
        host = list(room.members.values())[0]
        assert host.name == "Alice"
        assert host.role == "host"
        assert host.access_level == "full"

    @pytest.mark.asyncio
    async def test_join(self):
        room = Room("test-room")
        member = await room.join("Bob")
        assert member is not None
        assert member.name == "Bob"
        assert member.role == "viewer"
        assert len(room.members) == 2  # host + Bob

    @pytest.mark.asyncio
    async def test_join_max_members(self):
        room = Room("test-room")
        for i in range(MAX_MEMBERS - 1):  # host가 이미 1명
            m = await room.join(f"User{i}")
            assert m is not None
        assert len(room.members) == MAX_MEMBERS

        # 정원 초과
        overflow = await room.join("Overflow")
        assert overflow is None

    @pytest.mark.asyncio
    async def test_leave(self):
        room = Room("test-room")
        member = await room.join("Bob")
        assert len(room.members) == 2

        await room.leave(member.member_id)
        assert len(room.members) == 1
        assert member.member_id not in room.members

    @pytest.mark.asyncio
    async def test_leave_nonexistent(self):
        room = Room("test-room")
        await room.leave("nonexistent")  # 에러 없이 통과
        assert len(room.members) == 1

    def test_heartbeat(self):
        room = Room("test-room")
        host_id = room.host_member_id
        assert room.heartbeat(host_id) is True
        assert room.heartbeat("nonexistent") is False

    def test_get_member(self):
        room = Room("test-room")
        host = room.get_member(room.host_member_id)
        assert host is not None
        assert host.role == "host"
        assert room.get_member("nope") is None


# ---------------------------------------------------------------------------
# 브로드캐스트
# ---------------------------------------------------------------------------


class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_to_all(self):
        room = Room("test-room")
        m1 = await room.join("Alice")
        m2 = await room.join("Bob")

        # join 이벤트를 비우기
        for m in room.members.values():
            while not m.queue.empty():
                m.queue.get_nowait()

        await room.broadcast("test", {"msg": "hello"})

        # 모든 멤버가 받아야 함
        for m in room.members.values():
            assert not m.queue.empty()
            event = m.queue.get_nowait()
            assert event["event"] == "test"
            assert event["data"]["msg"] == "hello"

    @pytest.mark.asyncio
    async def test_broadcast_exclude(self):
        room = Room("test-room")
        m1 = await room.join("Alice")

        # join 이벤트를 비우기
        for m in room.members.values():
            while not m.queue.empty():
                m.queue.get_nowait()

        await room.broadcast("test", {"msg": "hello"}, exclude=m1.member_id)

        # Alice는 제외, host만 받아야 함
        host = room.get_member(room.host_member_id)
        assert not host.queue.empty()
        assert m1.queue.empty()

    @pytest.mark.asyncio
    async def test_broadcast_full_queue_evicts(self):
        room = Room("test-room")
        m1 = await room.join("Alice")

        # Alice의 큐를 가득 채움
        for i in range(QUEUE_MAX_SIZE):
            m1.queue.put_nowait({"event": "fill", "data": {"i": i}})

        # 큐 가득 찬 상태에서 브로드캐스트 → Alice 제거
        await room.broadcast("overflow", {"msg": "bye"})
        assert m1.member_id not in room.members


# ---------------------------------------------------------------------------
# 채팅
# ---------------------------------------------------------------------------


class TestChat:
    def test_add_chat(self):
        room = Room("test-room")
        host_id = room.host_member_id
        msg = room.add_chat(host_id, "Hello!")
        assert msg is not None
        assert msg.text == "Hello!"
        assert len(room.chat_history) == 1

    def test_add_chat_nonexistent_member(self):
        room = Room("test-room")
        msg = room.add_chat("nobody", "Hello!")
        assert msg is None

    def test_chat_history_cap(self):
        room = Room("test-room")
        host_id = room.host_member_id
        for i in range(MAX_CHAT_HISTORY + 20):
            room.add_chat(host_id, f"msg-{i}")
        assert len(room.chat_history) == MAX_CHAT_HISTORY


# ---------------------------------------------------------------------------
# 상태
# ---------------------------------------------------------------------------


class TestRoomState:
    @pytest.mark.asyncio
    async def test_get_state(self):
        room = Room("test-room", host_name="Host")
        await room.join("Bob")

        state = room.get_state()
        assert state["roomId"] == "test-room"
        assert len(state["members"]) == 2
        assert isinstance(state["navState"], dict)
        assert isinstance(state["chatHistory"], list)

    def test_nav_state_update(self):
        room = Room("test-room")
        room.nav_state.update({"stockCode": "005930", "topic": "IS"})
        assert room.nav_state["stockCode"] == "005930"


# ---------------------------------------------------------------------------
# 프레즌스 정리
# ---------------------------------------------------------------------------


class TestCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_stale_members(self):
        import time

        room = Room("test-room")
        member = await room.join("Stale")
        assert len(room.members) == 2

        # 강제로 하트비트를 과거로 설정
        member.last_heartbeat = time.monotonic() - HEARTBEAT_TIMEOUT - 1

        await room.cleanup_stale()
        assert member.member_id not in room.members
        assert len(room.members) == 1  # host만 남음

    @pytest.mark.asyncio
    async def test_host_not_cleaned_up(self):
        import time

        room = Room("test-room")
        host = room.get_member(room.host_member_id)
        host.last_heartbeat = time.monotonic() - HEARTBEAT_TIMEOUT - 100

        await room.cleanup_stale()
        assert room.host_member_id in room.members


# ---------------------------------------------------------------------------
# RoomManager
# ---------------------------------------------------------------------------


class TestRoomManager:
    def test_create_and_get(self):
        mgr = RoomManager()
        room = mgr.create_room("TestHost")
        assert mgr.get_room() is room
        assert room.room_id

    def test_destroy(self):
        mgr = RoomManager()
        mgr.create_room()
        mgr.destroy_room()
        assert mgr.get_room() is None

    def test_no_room(self):
        mgr = RoomManager()
        assert mgr.get_room() is None


# ---------------------------------------------------------------------------
# Member info
# ---------------------------------------------------------------------------


class TestMemberInfo:
    def test_info_dict(self):
        room = Room("test-room", host_name="Host")
        host = room.get_member(room.host_member_id)
        info = host.info()
        assert info["name"] == "Host"
        assert info["role"] == "host"
        assert "memberId" in info


# ---------------------------------------------------------------------------
# join 브로드캐스트
# ---------------------------------------------------------------------------


class TestJoinBroadcast:
    @pytest.mark.asyncio
    async def test_join_broadcasts_to_existing(self):
        room = Room("test-room")
        host = room.get_member(room.host_member_id)

        # 큐 비우기
        while not host.queue.empty():
            host.queue.get_nowait()

        await room.join("NewUser")

        # 호스트가 member_join 이벤트를 받아야 함
        assert not host.queue.empty()
        event = host.queue.get_nowait()
        assert event["event"] == "member_join"
        assert event["data"]["name"] == "NewUser"
