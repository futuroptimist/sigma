from __future__ import annotations

from dataclasses import dataclass

from .interfaces import ConversationAudio, PushToTalkInterface


@dataclass
class PassthroughPushToTalk(PushToTalkInterface):
    """Simple push-to-talk shim that returns pre-recorded audio."""

    payload: ConversationAudio

    def capture(self) -> ConversationAudio:
        return self.payload
