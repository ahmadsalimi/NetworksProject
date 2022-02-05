from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Set, TypeVar

from build import Any

if TYPE_CHECKING:
    from common.tcpclient import TCPClient


TCallable = TypeVar('TCallable')


class PacketDropException(Exception):
    pass


class Firewall(ABC):
    __instance = None

    @classmethod
    def instance(cls) -> 'Firewall':
        if cls.__instance is None:
            cls.__instance = BlackListFirewall()
        return cls.__instance

    @classmethod
    def blacklist(cls) -> None:
        cls.__instance = BlackListFirewall()

    @classmethod
    def whitelist(cls) -> None:
        cls.__instance = WhiteListFirewall()

    @staticmethod
    def filter_packet(function: TCallable) -> TCallable:
        def wrapper(self: 'TCPClient', *args: Any, **kwargs: Any) -> Any:
            if not Firewall.instance().check(self.sock.getpeername()[1]):
                raise PacketDropException()
            return function(self, *args, **kwargs)
        return wrapper

    @abstractmethod
    def open(self, port: int) -> None:
        pass

    @abstractmethod
    def close(self, port: int) -> None:
        pass

    @abstractmethod
    def check(self, port: int) -> bool:
        pass


class WhiteListFirewall(Firewall):

    def __init__(self) -> None:
        self.__list: Set[int] = set()

    def open(self, port: int) -> None:
        self.__list.add(port)

    def close(self, port: int) -> None:
        self.__list.discard(port)

    def check(self, port: int) -> bool:
        return port in self.__list


class BlackListFirewall(Firewall):

    def __init__(self) -> None:
        self.__list: Set[int] = set()

    def open(self, port: int) -> None:
        self.__list.discard(port)

    def close(self, port: int) -> None:
        self.__list.add(port)

    def check(self, port: int) -> bool:
        return port not in self.__list
