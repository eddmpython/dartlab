"""하위호환 re-export — 실제 로직은 engines/ai/dialogue.py.

이 모듈은 외부 코드가 dartlab.server.dialogue를 import할 경우를 위한 안전망.
새 코드는 engines/ai/dialogue에서 직접 import해야 한다.
"""

from __future__ import annotations

# 하위호환 re-export
from dartlab.engines.ai.conversation.dialogue import (  # noqa: F401
    ConversationState,
    build_conversation_state,
    build_dialogue_policy,
    conversation_state_to_meta,
    detect_viewer_intent,
)
