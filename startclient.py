import argparse

from client.menu import MainMenu


parser = argparse.ArgumentParser(description='Run a Client')
parser.add_argument('-m', '--messenger-port', type=int, default=8080, help='Messenger port')
parser.add_argument('-s', '--stream-port', type=int, default=8081, help='Stream port')

args = parser.parse_args()

MainMenu(args.messenger_port, args.stream_port).run()
