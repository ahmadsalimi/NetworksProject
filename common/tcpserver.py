from abc import ABC, abstractmethod
import socket
import threading
from typing import Generic, TypeVar
from uuid import UUID, uuid1

from .packet import Packet


TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class TCPServer(Generic[TRequest, TResponse], ABC):

    def __init__(self, port: int) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', port))

    def listen(self) -> None:
        self.sock.listen(5)
        while True:
            client, _ = self.sock.accept()
            print(f'accepted connection from {client.getpeername()}')
            threading.Thread(target=self.__handle_client, args=(client,)).start()

    def __handle_client(self, client: socket.socket) -> None:
        client_id = uuid1()
        while True:
            packet = Packet.read_from(client)
            try:
                response = self.handle_request(client_id, packet.data)
                packet = Packet(response, packet.message_id)
            except Exception as e:
                packet = Packet(e, packet.message_id, is_error=True)
            packet.send_to(client)

    @abstractmethod
    def handle_request(self, client_id: UUID, request: TRequest) -> TResponse:
        pass
