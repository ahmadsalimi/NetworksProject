import socket
import argparse
from concurrent.futures import ThreadPoolExecutor


def send(src: socket.socket, dst: socket.socket, close_other: bool = False):
    while True:
        data = src.recv(4096)
        if not data:
            print(f'closing connection from {src.getpeername()}')
            if close_other:
                dst.close()
            break
        dst.send(data)


parser = argparse.ArgumentParser(description='Proxy server')
parser.add_argument('-p', '--port', type=int,
                    default=8080, help='Port to listen on')
args = parser.parse_args()

with ThreadPoolExecutor(max_workers=8) as executor:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', args.port))
        sock.listen(5)

        while True:
            client, _ = sock.accept()
            print(f'accepted connection from {client.getpeername()}')
            fd = client.makefile('r', encoding='utf-8')
            target_port = int(fd.readline())
            print(f'connecting to {target_port}')
            target_connection = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            target_connection.connect(('localhost', target_port))
            executor.submit(send, client, target_connection, close_other=True)
            executor.submit(send, target_connection, client)
