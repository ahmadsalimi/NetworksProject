from abc import ABC, abstractmethod
from ast import Dict
import socket
import threading
import time
import traceback
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from .packet import Packet


TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class TCPServer(Generic[TRequest, TResponse], ABC):

    def __init__(self, port: int) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', port))
        self.lock = threading.Lock()
        self.exit_clients: Dict[UUID, bool] = {}

    def listen(self) -> None:
        try:
            self.sock.listen(5)
            while True:
                client, _ = self.sock.accept()
                print(f'accepted connection from {client.getpeername()}')
                threading.Thread(target=self.__handle_client,
                                 args=(client,)).start()
        finally:
            time.sleep(10)
            self.sock.close()

    def __request_job(self, packet: Packet, client: socket.socket, client_id: UUID) -> None:
            if packet.is_exit:
                Packet(None, packet.message_id, is_exit=True).send_to(client)
                with self.lock:
                    self.exit_clients[client_id] = True
            try:
                response = self.handle_request(client_id, packet.data)
                packet = Packet(response, packet.message_id)
            except Exception as e:
                packet = Packet(e, packet.message_id, is_error=True)
                print(traceback.format_exc())
            # print(f'packet {packet.message_id} is being sent')
            packet.send_to(client)
            # print(f'packet {packet.message_id} sent')


    def __handle_client(self, client: socket.socket) -> None:
        client_id = uuid4()
        with self.lock:
            self.exit_clients[client_id] = False
        while True:
            packet = Packet.read_from(client)
            # print(f'packet {packet.message_id} received')
            with self.lock:
                if self.exit_clients[client_id]:
                    break
            threading.Thread(target=self.__request_job,
                            args=(packet, client, client_id),
                            daemon=True).start()
        with self.lock:
            del self.exit_clients[client_id]
        print(f'closing connection from {client.getpeername()}')
        time.sleep(1)
        client.close()

    @abstractmethod
    def handle_request(self, client_id: UUID, request: TRequest) -> TResponse:
        pass
