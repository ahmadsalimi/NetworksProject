from abc import ABC, abstractmethod
import threading
import time
from typing import Dict, Tuple, Type
import re

import bcrypt

from common.tcpclient import TCPClient
from messenger.messenger import MessageItem, MessengerError
from .media_ui import MediaUI
from .mediastream import MediaStreamClient
from .firewall import Firewall, PacketDropException
from .messenger import MessengerClient
from .chat_ui import LockedCurses, WinWrapper


class Menu(ABC):

    @abstractmethod
    def display(self) -> None:
        pass

    @abstractmethod
    def action(self, cmd: str) -> bool:
        pass

    def run(self) -> None:
        while True:
            try:
                self.display()
                cmd = input('> ')
                if self.action(cmd.strip()):
                    return
            except PacketDropException:
                print('packet dropped due to firewall rules')


class MainMenu(Menu):
    def __init__(self, messenger_port: int, stream_port: int) -> None:
        self.__admin_pass_hash: bytes = None
        self.servers: Dict[str, Tuple[Type[Menu], int]] = {
            'shalgham': (MessengerMainMenu, messenger_port),
            'choghondar': (MediaStreamMenu, stream_port),
        }

    def display(self) -> None:
        if self.__admin_pass_hash is None:
            password = input('Enter admin password: ')
            self.__admin_pass_hash = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt())
        print('1. Connect to external servers')
        print('2. Login as admin')
        print('3. Exit')

    def action(self, cmd: str) -> bool:
        if cmd == '1':
            server = input('Enter the server: ').strip().split(' via ')
            if server[0] not in self.servers:
                print(f'Unknown server {server[0]}')
                return False
            servermenu, port = self.servers[server[0]]
            if len(server) == 2:
                from common.proxyclient import ProxyClient
                proxy_port = int(server[1])
                tcpclient = ProxyClient('localhost', proxy_port, port)
            else:
                from common.tcpclient import TCPClient
                tcpclient = TCPClient('localhost', port)
            servermenu(tcpclient).run()
        elif cmd == '2':
            password = input('Enter admin password: ')
            if bcrypt.checkpw(password.encode(), self.__admin_pass_hash):
                AdminMenu().run()
            else:
                print('Incorrect password')
        elif cmd == '3':
            return True
        else:
            print('Invalid input')
        return False


class MessengerMainMenu(Menu):

    def __init__(self, tcpclient: TCPClient) -> None:
        self.client = MessengerClient(tcpclient)

    def display(self) -> None:
        print('1. Sign up')
        print('2. Login')
        print('3. Exit')

    def run(self) -> None:
        try:
            super().run()
        finally:
            try:
                self.client.client.exit()
            except PacketDropException:
                print('packet dropped due to firewall rules')

    def action(self, cmd: str) -> bool:
        try:
            if cmd == '1':
                while True:
                    username = input('Please enter your username: ')
                    if self.client.checkusername(username):
                        break
                    print('This username is already existed or '
                          'invalid. Please enter another one.')
                password = input('Please enter your password: ')
                self.client.signup(username, password)
            elif cmd == '2':
                username = input('Please enter your username: ')
                password = input('Please enter your password: ')
                self.client.login(username, password)
                InboxMenu(self.client).run()
            elif cmd == '3':
                return True
            else:
                print('Invalid input')
        except MessengerError as e:
            print(e.message)
        return False


class InboxMenu(Menu):

    def __init__(self, client: MessengerClient) -> None:
        self.client = client
        self.chat_finished = False
        self.n_messages = 5

    def display(self) -> None:
        print('Inbox:')
        print('\n'.join([
            f'{item.user} {f"({item.unread_count})" if item.unread_count > 0 else ""}'
            for item in self.client.get_inbox()
        ]))
        print('-----------')
        print('Enter "/exit" to close the messenger')

    def action(self, contact: str) -> bool:
        if contact == '/exit':
            self.client.logout()
            return True
        try:
            curses = LockedCurses()
            curses.start()
            self.chat_finished = False
            y, x = curses.getmaxyx()
            messages_win = curses.newwin(y, x, 0, 0)
            t = threading.Thread(
                target=self.__show_messages, 
                args=(messages_win, contact, x, y - 1))
            t.start()

            input_win = curses.newwin(1, x, y - 1, 0)

            while True:
                input_win.addstr(0, 0, ' >')
                message = input_win.getstr(0, 3, x - 5)
                input_win.refresh()
                input_win.clear()
                if message == '/exit':
                    break
                if mo := re.match(r'^/load\s+(\d+)$', message):
                    self.n_messages = min(int(mo.group(1)), y - 1)
                else:
                    self.client.send_message(contact, message)

            self.chat_finished = True
            t.join()
        finally:
            curses.teardown()
        return False

    def __show_messages(self, win: WinWrapper, contact: str, w: int, h: int) -> None:
        lines = [' ' * w for _ in range(h)]
        while not self.chat_finished:
            try:
                messages = self.client.read_messages(contact, self.n_messages)
            except:
                messages = []
            new_lines = [
                f"{self.__format_message(message, contact):<{w}}" for message in messages
            ] + [' ' * w for _ in range(h - len(messages) - 1)]
            for i, new in enumerate(new_lines):
                if lines[i] != new:
                    win.addstr(i, 0, new)
                    lines[i] = new
                    win.refresh()
            time.sleep(0.1)

    def __format_message(self, message: MessageItem, contact: str) -> str:
        return f"{f'({message.sender})' if message.sender == contact else ''} {message.text}"


class MediaStreamMenu(Menu):

    def __init__(self, tcpclient: TCPClient) -> None:
        self.client = MediaStreamClient(tcpclient)
        self.files = None

    def display(self) -> None:
        print('Welcome to CHOGHONDAR!\nPlease choose a media to display:\n')
        try:
            self.files = self.client.get_list()
        except PacketDropException:
            print('packet dropped due to firewall rules')
            self.files = []
        for i, file in enumerate(self.files):
            print(f'{i + 1}. {file}')
        print(f'{len(self.files) + 1}. Exit')

    def action(self, cmd: str) -> bool:
        if 0 < (idx := int(cmd)) < len(self.files) + 1:
            file = self.files[idx - 1]
            print('start playing...')
            ui = MediaUI(self.client, file)
            ui.show()
        elif idx == len(self.files) + 1:
            return True
        else:
            print('Invalid input :/')
        return False


class AdminMenu(Menu):

    def display(self) -> None:
        print('Enter the command:')
        print('activate whitelist/blacklist firewall')
        print('open/close <port>')
        print('exit')

    def action(self, cmd: str) -> bool:
        if cmd == 'activate whitelist firewall':
            Firewall.whitelist()
        elif cmd == 'activate blacklist firewall':
            Firewall.blacklist()
        elif mo := re.match(r'open (\d+)', cmd):
            Firewall.instance().open(int(mo.group(1)))
        elif mo := re.match(r'close (\d+)', cmd):
            Firewall.instance().close(int(mo.group(1)))
        elif cmd == 'exit':
            return True
        else:
            print('Invalid input')
        return False


class MessengerSignupMenu(Menu):
    def __init__(self) -> None:
        self.username = None
        self.password = None

    def display(self) -> None:
        print('Welcome to Messenger')
