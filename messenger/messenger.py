from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Tuple, Any
from uuid import UUID
from enum import Enum

from common.tcpserver import TCPServer
from .message import Message
from .chat import Chat
from .user import User


@dataclass
class InboxItem:
    user: str
    last_modified: datetime = datetime.min
    unread_count: int = 0

    @property
    def is_unread(self) -> bool:
        return self.unread_count > 0

    def __lt__(self, other: 'InboxItem') -> bool:
        return self.is_unread < other.is_unread or self.last_modified < other.last_modified


@dataclass
class MessageItem:
    sender: str
    receiver: str
    text: str
    timestamp: datetime
    seen: bool

    @staticmethod
    def from_message(message: Message) -> 'MessageItem':
        return MessageItem(message.sender.username,
                           message.receiver.username,
                           message.text,
                           message.timestamp,
                           message.seen)


class RequestType(Enum):
    Signup = 0
    Login = 1
    GetInbox = 2
    SendMessage = 3
    ReadMessages = 4
    CheckUsername = 5
    Logout = 6


@dataclass
class MessengerRequest:
    type: RequestType
    args: Tuple[Any, ...]


class MessengerError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def inject_user(f: Callable):
    def wrapper(self: 'Messenger', client_id: UUID, *args, **kwargs):
        if client_id not in self.onlines:
            raise MessengerError('Not logged in')
        user = self.onlines[client_id]
        return f(self, user, *args, **kwargs)
    return wrapper


def inject_contact(f: Callable):
    def wrapper(self: 'Messenger', user: User, contact_username: str, *args, **kwargs):
        if contact_username not in self.users:
            raise MessengerError(f'User {contact_username} not found')
        contact = self.users[contact_username]
        return f(self, user, contact, *args, **kwargs)
    return wrapper


class Messenger(TCPServer[MessengerRequest, Any]):

    def __init__(self, port: int) -> None:
        super().__init__(port)
        self.users: Dict[str, User] = {}
        self.onlines: Dict[UUID, User] = {}

    def handle_request(self, client_id: UUID, request: MessengerRequest) -> Any:
        if request.type == RequestType.Signup:
            return self.signup(*request.args)
        if request.type == RequestType.Login:
            return self.login(client_id, *request.args)
        if request.type == RequestType.GetInbox:
            return self.get_inbox(client_id)
        if request.type == RequestType.SendMessage:
            return self.send_message(client_id, *request.args)
        if request.type == RequestType.ReadMessages:
            return self.read_messages(client_id, *request.args)
        if request.type == RequestType.CheckUsername:
            return self.checkusername(*request.args)
        if request.type == RequestType.Logout:
            return self.logout(client_id)
        raise MessengerError(f'Unknown request type {request.type}')

    def checkusername(self, username: str) -> bool:
        return username not in self.users

    def signup(self, username: str, password: str) -> None:
        if username in self.users:
            raise MessengerError(f'Username {username} already exists')
        self.users[username] = User.from_userpass(username, password)

    def login(self, client_id: UUID, username: str, password: str) -> None:
        if username not in self.users:
            raise MessengerError(f'Username {username} not found')
        user = self.users[username]
        if not user.check_password(password):
            raise MessengerError(f'Invalid password')
        self.onlines[client_id] = user

    def logout(self, client_id: UUID) -> None:
        del self.onlines[client_id]

    @inject_user
    def get_inbox(self, user: User) -> List[InboxItem]:
        inbox = [InboxItem(username, chat.last_modified, chat.unread_count(user))
                 for username, chat in user.chats.items()]
        inbox += [InboxItem(username) for username in self.users
                  if username not in user.chats
                  and username != user.username]
        return sorted(inbox, reverse=True)

    @inject_user
    @inject_contact
    def send_message(self, user: User, contact: User, text: str) -> None:
        if contact.username not in user.chats:
            user.chats[contact.username] = contact.chats[user.username] = Chat()
        user.chats[contact.username].add_message(Message(user, contact, text))

    @inject_user
    @inject_contact
    def read_messages(self, user: User, contact: User, count: int) -> List[MessageItem]:
        if contact.username not in user.chats:
            raise MessengerError(f'Contact {contact.username} not found')
        messages = user.chats[contact.username].read_messages(user, count)
        return list(map(MessageItem.from_message, messages))
