from dataclasses import dataclass
import pickle
import socket
from typing import Any
from uuid import UUID, uuid1


@dataclass
class Packet:
    data: Any
    message_id: UUID = uuid1()
    is_error: bool = False

    @staticmethod
    def read_from(sock: socket.socket) -> 'Packet':
        length = int(sock.recv(10).decode('utf-8'))
        pickled = sock.recv(length)
        return pickle.loads(pickled)

    def send_to(self, sock: socket.socket) -> None:
        pickled = pickle.dumps(self)
        length = len(pickled)
        sock.send(f'{length:<10}'.encode('utf-8'))
        sock.send(pickled)
