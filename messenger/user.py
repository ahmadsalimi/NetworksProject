
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict

import bcrypt

if TYPE_CHECKING:
    from .chat import Chat


@dataclass
class User:
    username: str
    password_hash: bytes
    chats: Dict[str, 'Chat'] = field(default_factory=dict)

    @staticmethod
    def from_userpass(username: str, password: str) -> 'User':
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return User(username, password_hash)

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.password_hash)
