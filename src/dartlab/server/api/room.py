"""Room 협업 세션 API: SSE fan-out + POST-back."""

from __future__ import annotations

import asyncio
import json
import logging
import time

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ..models import (
    RoomAskRequest,
    RoomChatRequest,
    RoomJoinRequest,
    RoomNavigateRequest,
    RoomReactRequest,
)
from ..room import Room, RoomMember, roomManager

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------


def _getRoom() -> Room:
    room = roomManager.getRoom()
    if room is None:
        raise HTTPException(status_code=404, detail="협업 세션이 활성화되지 않았습니다.")
    return room


def _getMember(request: Request, room: Room) -> RoomMember:
    memberId = request.headers.get("x-room-member", "")
    member = room.getMember(memberId)
    if member is None:
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")
    return member


def _requireFull(member: RoomMember) -> None:
    if member.accessLevel != "full":
        raise HTTPException(status_code=403, detail="읽기 전용 토큰으로는 이 작업을 수행할 수 없습니다.")


# ---------------------------------------------------------------------------
# 엔드포인트
# ---------------------------------------------------------------------------


@router.post("/api/room/join")
async def roomJoin(req: RoomJoinRequest):
    """룸 참여. 비공개 member token + 현재 상태 반환."""
    room = _getRoom()
    member = await room.join(req.name)
    if member is None:
        raise HTTPException(status_code=409, detail="룸 정원이 초과되었습니다.")

    state = room.getState()
    return {
        "memberId": member.memberId,
        "roomId": room.roomId,
        "members": state["members"],
        "navState": state["navState"],
        "chatHistory": state["chatHistory"],
    }


@router.post("/api/room/leave")
async def roomLeave(request: Request):
    """룸 퇴장."""
    room = _getRoom()
    member = _getMember(request, room)
    await room.leave(member.memberId)
    return {"status": "ok"}


@router.post("/api/room/heartbeat")
async def roomHeartbeat(request: Request):
    """프레즌스 유지."""
    room = _getRoom()
    memberId = request.headers.get("x-room-member", "")
    if not room.heartbeat(memberId):
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")
    return {"status": "ok", "members": len(room.members)}


@router.get("/api/room/state")
async def roomState():
    """현재 룸 상태."""
    room = _getRoom()
    return room.getState()


@router.get("/api/room/stream")
async def roomStream(request: Request):
    """SSE 스트림. 브로드캐스트 수신."""
    room = _getRoom()
    memberId = request.query_params.get("member", "")
    member = room.getMember(memberId)
    if member is None:
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")

    async def _generate():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(member.queue.get(), timeout=30)
                    yield {
                        "event": msg["event"],
                        "data": json.dumps(msg["data"], ensure_ascii=False),
                    }
                except TimeoutError:
                    # keepalive SSE comment
                    yield {"comment": "keepalive"}
        except asyncio.CancelledError:
            return

    return EventSourceResponse(_generate(), media_type="text/event-stream")


@router.post("/api/room/ask")
async def roomAsk(req: RoomAskRequest, request: Request):
    """질문 → 전체 브로드캐스트."""
    room = _getRoom()
    member = _getMember(request, room)
    _requireFull(member)

    if room._analyzing:
        raise HTTPException(status_code=409, detail="이미 분석이 진행 중입니다.")

    room._analyzing = True
    try:
        # 시작 브로드캐스트
        await room.broadcast(
            "ask_start",
            {
                "memberId": member.publicId,
                "name": member.name,
                "question": req.question,
                "company": req.company,
            },
        )

        # 스트리밍 인프라. AI가 종목을 자율 판단
        from ..models import AskRequest
        from ..streaming import streamAsk

        ask_req = AskRequest.model_validate(
            {
                "company": req.company,
                "question": req.question,
                "stream": True,
            }
        )

        async for sse_event in streamAsk(ask_req):
            event_name = sse_event.get("event", "chunk")
            try:
                data = json.loads(sse_event.get("data", "{}"))
            except (json.JSONDecodeError, ValueError):
                data = {"raw": sse_event.get("data", "")}
            await room.broadcast(event_name, data)

            # 네비게이션 상태 업데이트 (meta 이벤트에서 종목 정보 추출)
            if event_name == "meta":
                room.nav_state.update({k: v for k, v in data.items() if k in ("stockCode", "corpName")})

    finally:
        room._analyzing = False

    return {"status": "ok"}


@router.post("/api/room/navigate")
async def roomNavigate(req: RoomNavigateRequest, request: Request):
    """네비게이션 동기화."""
    room = _getRoom()
    member = _getMember(request, room)
    _requireFull(member)

    nav_update = {k: v for k, v in req.model_dump().items() if v is not None}
    room.nav_state.update(nav_update)

    await room.broadcast(
        "navigate",
        {
            "memberId": member.publicId,
            "name": member.name,
            **nav_update,
        },
    )
    return {"status": "ok"}


@router.post("/api/room/chat")
async def roomChat(req: RoomChatRequest, request: Request):
    """채팅 메시지."""
    room = _getRoom()
    member = _getMember(request, room)

    msg = room.addChat(member.memberId, req.text)
    if msg is None:
        raise HTTPException(status_code=401, detail="룸에 참여하지 않은 사용자입니다.")

    await room.broadcast("chat", msg.toDict())
    return {"status": "ok"}


@router.post("/api/room/react")
async def roomReact(req: RoomReactRequest, request: Request):
    """이모지 반응."""
    room = _getRoom()
    member = _getMember(request, room)

    await room.broadcast(
        "react",
        {
            "memberId": member.publicId,
            "name": member.name,
            "emoji": req.emoji,
            "targetEvent": req.targetEvent,
            "timestamp": time.time(),
        },
    )
    return {"status": "ok"}
