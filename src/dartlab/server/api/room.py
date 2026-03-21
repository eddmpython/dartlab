"""Room 협업 세션 API — SSE fan-out + POST-back."""

from __future__ import annotations

import asyncio
import logging
import time

import orjson
from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ..models import (
    RoomAskRequest,
    RoomChatRequest,
    RoomJoinRequest,
    RoomNavigateRequest,
    RoomReactRequest,
)
from ..room import Room, RoomMember, room_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------


def _get_room() -> Room:
    room = room_manager.get_room()
    if room is None:
        raise HTTPException(status_code=404, detail="협업 세션이 활성화되지 않았습니다.")
    return room


def _get_member(request: Request, room: Room) -> RoomMember:
    member_id = request.headers.get("x-room-member", "")
    member = room.get_member(member_id)
    if member is None:
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")
    return member


def _require_full(member: RoomMember) -> None:
    if member.access_level != "full":
        raise HTTPException(status_code=403, detail="읽기 전용 토큰으로는 이 작업을 수행할 수 없습니다.")


# ---------------------------------------------------------------------------
# 엔드포인트
# ---------------------------------------------------------------------------


@router.post("/api/room/join")
async def room_join(req: RoomJoinRequest):
    """룸 참여 — member_id + 현재 상태 반환."""
    room = _get_room()
    member = await room.join(req.name)
    if member is None:
        raise HTTPException(status_code=409, detail="룸 정원이 초과되었습니다.")

    state = room.get_state()
    return {
        "memberId": member.member_id,
        "roomId": room.room_id,
        "members": state["members"],
        "navState": state["navState"],
        "chatHistory": state["chatHistory"],
    }


@router.post("/api/room/leave")
async def room_leave(request: Request):
    """룸 퇴장."""
    room = _get_room()
    member = _get_member(request, room)
    await room.leave(member.member_id)
    return {"status": "ok"}


@router.post("/api/room/heartbeat")
async def room_heartbeat(request: Request):
    """프레즌스 유지."""
    room = _get_room()
    member_id = request.headers.get("x-room-member", "")
    if not room.heartbeat(member_id):
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")
    return {"status": "ok", "members": len(room.members)}


@router.get("/api/room/state")
async def room_state():
    """현재 룸 상태."""
    room = _get_room()
    return room.get_state()


@router.get("/api/room/stream")
async def room_stream(request: Request):
    """SSE 스트림 — 브로드캐스트 수신."""
    room = _get_room()
    member_id = request.query_params.get("member", "")
    member = room.get_member(member_id)
    if member is None:
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")

    async def _generate():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(member.queue.get(), timeout=30)
                    yield {
                        "event": msg["event"],
                        "data": orjson.dumps(msg["data"]).decode(),
                    }
                except TimeoutError:
                    # keepalive — SSE comment
                    yield {"comment": "keepalive"}
        except asyncio.CancelledError:
            return

    return EventSourceResponse(_generate(), media_type="text/event-stream")


@router.post("/api/room/ask")
async def room_ask(req: RoomAskRequest, request: Request):
    """질문 → 전체 브로드캐스트."""
    room = _get_room()
    member = _get_member(request, room)
    _require_full(member)

    if room._analyzing:
        raise HTTPException(status_code=409, detail="이미 분석이 진행 중입니다.")

    room._analyzing = True
    try:
        # 시작 브로드캐스트
        await room.broadcast("ask_start", {
            "memberId": member.member_id,
            "name": member.name,
            "question": req.question,
            "company": req.company,
        })

        # 기존 스트리밍 인프라 재사용
        from ..streaming import stream_ask
        from ..models import AskRequest
        from ..resolve import try_resolve_company

        ask_req = AskRequest(
            company=req.company,
            question=req.question,
            stream=True,
        )
        resolved = try_resolve_company(ask_req)
        c = resolved.company

        if c:
            from ..cache import company_cache

            cached = company_cache.get(c.stockCode)
            if cached:
                c = cached[0]

        async for sse_event in stream_ask(c, ask_req):
            event_name = sse_event.get("event", "chunk")
            try:
                data = orjson.loads(sse_event.get("data", "{}"))
            except (orjson.JSONDecodeError, ValueError):
                data = {"raw": sse_event.get("data", "")}
            await room.broadcast(event_name, data)

            # 네비게이션 상태 업데이트 (meta 이벤트에서 종목 정보 추출)
            if event_name == "meta":
                room.nav_state.update({
                    k: v for k, v in data.items()
                    if k in ("stockCode", "corpName")
                })

    finally:
        room._analyzing = False

    return {"status": "ok"}


@router.post("/api/room/navigate")
async def room_navigate(req: RoomNavigateRequest, request: Request):
    """네비게이션 동기화."""
    room = _get_room()
    member = _get_member(request, room)
    _require_full(member)

    nav_update = {k: v for k, v in req.model_dump().items() if v is not None}
    room.nav_state.update(nav_update)

    await room.broadcast("navigate", {
        "memberId": member.member_id,
        "name": member.name,
        **nav_update,
    })
    return {"status": "ok"}


@router.post("/api/room/chat")
async def room_chat(req: RoomChatRequest, request: Request):
    """채팅 메시지."""
    room = _get_room()
    member = _get_member(request, room)

    msg = room.add_chat(member.member_id, req.text)
    if msg is None:
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")

    await room.broadcast("chat", msg.to_dict())
    return {"status": "ok"}


@router.post("/api/room/react")
async def room_react(req: RoomReactRequest, request: Request):
    """이모지 반응."""
    room = _get_room()
    member = _get_member(request, room)

    await room.broadcast("react", {
        "memberId": member.member_id,
        "name": member.name,
        "emoji": req.emoji,
        "targetEvent": req.targetEvent,
        "timestamp": time.time(),
    })
    return {"status": "ok"}
