
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .message import Message
    from .user import User


@dataclass
class Chat:
    messages: List['Message'] = field(default_factory=list)

    def add_message(self, message: 'Message'):
        self.messages.append(message)

    def read_messages(self, user: 'User', count: int) -> List['Message']:
        messages = self.messages[-count:]
        for message in messages:
            if message.receiver == user:
                message.seen = True
        return messages

    @property
    def last_modified(self) -> datetime:
        return self.messages[-1].timestamp

    def unread_count(self, user: 'User') -> bool:
        return len([
            message for message in self.messages 
            if not message.seen and message.receiver == user
        ])
