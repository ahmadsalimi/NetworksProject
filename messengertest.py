import argparse
import threading
import time

from client.messenger import MessengerClient
from client.ui import LockedCurses
from common.proxyclient import ProxyClient
from common.tcpclient import TCPClient


def show_messages(win, contact: str, w: int, h: int):
    lines = [' ' * w for _ in range(h)]
    while not finish:
        try:
            messages = client.read_messages(contact, n_messages)
        except:
            messages = []
        new_lines = [
            f"{f'({message.sender}) {message.text}':<{w}}" for message in messages
        ] + [' ' * w for _ in range(h - len(messages) - 1)]
        for i, new in enumerate(new_lines):
            if lines[i] != new:
                win.addstr(i, 0, new)
                lines[i] = new
                win.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Messenger client')
    parser.add_argument('-p', '--port', type=int, default=8080, help='port')
    parser.add_argument('--proxy', type=int, default=None, help='proxy port (optional)')

    args = parser.parse_args()

    if args.proxy is None:
        client = TCPClient('localhost', args.port)
    else:
        client = ProxyClient('localhost', args.proxy, args.port)

    client = MessengerClient(client)
    while True:
        cmd = input('> ')
        if cmd == 'signup':
            username = input('Username: ')
            password = input('Password: ')
            client.signup(username, password)
        elif cmd == 'login':
            username = input('Username: ')
            password = input('Password: ')
            client.login(username, password)
        elif cmd == 'get_inbox':
            print(client.get_inbox())
        elif cmd == 'open':
            contact = input('Contact: ')
            try:
                curses = LockedCurses()
                curses.start()
                finish = False
                n_messages = 5
                y, x = curses.getmaxyx()
                win = curses.newwin(y, x, 0, 0)
                t = threading.Thread(target=show_messages, args=(win, contact, x, y - 1))
                t.start()

                inp_win = curses.newwin(1, x, y - 1, 0)

                while True:
                    inp_win.addstr(0, 0, ' >')
                    message = inp_win.getstr(0, 3, x - 5)
                    inp_win.refresh()
                    inp_win.clear()
                    if message == '/exit':
                        finish = True
                        break
                    if message.startswith('/load'):
                        n_messages = int(message.split()[-1])
                        if n_messages > y - 1:
                            n_messages = y - 1
                    else:
                        client.send_message(contact, message)
                
                finish = True
                t.join()
            finally:
                curses.teardown()
