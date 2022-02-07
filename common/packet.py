from dataclasses import dataclass, field
import pickle
import socket
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Packet:
    data: Any
    message_id: UUID = field(default_factory=uuid4)
    is_error: bool = False
    is_exit: bool = False

    @staticmethod
    def read_from(sock: socket.socket) -> 'Packet':
        length = int(sock.recv(10).decode('utf-8'))
        pickled = sock.recv(length)
        while len(pickled) < length:
            pickled += sock.recv(length - len(pickled))
        return pickle.loads(pickled)

    def send_to(self, sock: socket.socket) -> None:
        pickled = pickle.dumps(self)
        length = len(pickled)
        sock.sendall(f'{length:<10}'.encode('utf-8'))
        sock.sendall(pickled)
