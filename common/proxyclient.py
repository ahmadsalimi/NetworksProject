from .tcpclient import TCPClient


class ProxyClient(TCPClient):

    def __init__(self, host: str, proxy_port: int, actual_port: int) -> None:
        super().__init__(host, proxy_port)
        self.sock.send(f'{actual_port}\n'.encode('utf-8'))
