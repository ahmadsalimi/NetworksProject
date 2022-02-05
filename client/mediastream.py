from typing import Any, List, Tuple
from uuid import UUID

from common.tcpclient import TCPClient
from mediastream.mediastream import MediaStreamRequest, RequestType


class MediaStreamClient:

    def __init__(self, client: TCPClient[MediaStreamRequest, Any]) -> None:
        self.client = client

    def __ask(self, type: RequestType, *args: Any) -> Any:
        return self.client.ask(MediaStreamRequest(type, args))

    def get_list(self) -> List[str]:
        return self.__ask(RequestType.GetList)

    def start_stream(self, filename: str) -> Tuple[UUID, float]:
        return self.__ask(RequestType.StartStream, filename)

    def get_next_frame(self, uid: UUID) -> bytes:
        return self.__ask(RequestType.GetNextFrame, uid)

    def close_stream(self, uid: UUID) -> None:
        self.__ask(RequestType.CloseStream, uid)
