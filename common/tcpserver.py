from abc import ABC, abstractmethod
import socket
import threading
import time
from typing import Dict, Generic, TypeVar
from uuid import UUID, uuid1

from .packet import Packet


TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class TCPServer(Generic[TRequest, TResponse], ABC):

    def __init__(self, port: int) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', port))

    def listen(self) -> None:
        try:
            self.sock.listen(5)
            while True:
                client, _ = self.sock.accept()
                print(f'accepted connection from {client.getpeername()}')
                threading.Thread(target=self.__handle_client, args=(client,)).start()
        finally:
            time.sleep(10)
            self.sock.close()

    def __handle_client(self, client: socket.socket) -> None:
        client_id = uuid1()
        while True:
            packet = Packet.read_from(client)
            if packet.is_exit:
                Packet(None, packet.message_id, is_exit=True).send_to(client)
                break
            try:
                response = self.handle_request(client_id, packet.data)
                packet = Packet(response, packet.message_id)
            except Exception as e:
                packet = Packet(e, packet.message_id, is_error=True)
            packet.send_to(client)
        print(f'closing connection from {client.getpeername()}')
        time.sleep(1)
        client.close()

    @abstractmethod
    def handle_request(self, client_id: UUID, request: TRequest) -> TResponse:
        pass
