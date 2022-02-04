from typing import Any, List
from common.tcpclient import TCPClient
from messenger.messenger import InboxItem, MessageItem, MessengerRequest, RequestType


class MessengerClient:

    def __init__(self, client: TCPClient[MessengerRequest, Any]) -> None:
        self.client = client

    def __ask(self, type: RequestType, *args: Any) -> Any:
        return self.client.ask(MessengerRequest(type, args))

    def signup(self, username: str, password: str) -> None:
        self.__ask(RequestType.Signup, username, password)

    def login(self, username: str, password: str) -> None:
        self.__ask(RequestType.Login, username, password)

    def get_inbox(self) -> List[InboxItem]:
        return self.__ask(RequestType.GetInbox)

    def send_message(self, to: str, message: str) -> None:
        self.__ask(RequestType.SendMessage, to, message)

    def read_messages(self, contact: str, count: int) -> List[MessageItem]:
        return self.__ask(RequestType.ReadMessages, contact, count)
