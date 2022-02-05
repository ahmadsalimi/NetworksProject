

import socket
import threading
from typing import Dict, Generic
from uuid import UUID
import warnings

from client.firewall import Firewall
from .packet import Packet
from .tcpserver import TRequest, TResponse


class Promise(Generic[TResponse]):
    def __init__(self) -> None:
        self.__condition = threading.Condition()
        self.__packet: Packet = None

    def notify(self, packet: Packet) -> None:
        with self.__condition:
            self.__packet = packet
            self.__condition.notify()

    def wait(self) -> TResponse:
        with self.__condition:
            self.__condition.wait()
            if self.__packet.is_error:
                raise self.__packet.data
            return self.__packet.data


class TCPClient(Generic[TRequest, TResponse]):

    def __init__(self, host: str, port: int) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.requests: Dict[UUID, Promise] = {}
        self.lock = threading.Lock()
        self.read_thread = threading.Thread(target=self.__read)
        self.read_thread.start()
        print(self.sock.getpeername())

    def __read(self) -> None:
        while True:
            packet = Packet.read_from(self.sock)
            with self.lock:
                if packet.message_id in self.requests:
                    self.requests[packet.message_id].notify(packet)
                    del self.requests[packet.message_id]
                    if packet.is_exit:
                        break
                else:
                    warnings.warn(f'unexpected packet {packet.message_id}')

    @Firewall.filter_packet
    def ask(self, request: TRequest) -> TResponse:
        packet = Packet(request)
        promise = Promise()
        with self.lock:
            self.requests[packet.message_id] = promise
        packet.send_to(self.sock)
        return promise.wait()

    @Firewall.filter_packet
    def exit(self) -> None:
        packet = Packet(None, is_exit=True)
        promise = Promise()
        with self.lock:
            self.requests[packet.message_id] = promise
        packet.send_to(self.sock)
        promise.wait()
        self.read_thread.join()
        self.sock.close()
