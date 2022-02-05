from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


@dataclass
class Message:
    sender: 'User'
    receiver: 'User'
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    seen: bool = False
