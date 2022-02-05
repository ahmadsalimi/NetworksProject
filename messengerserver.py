
from messenger.messenger import Messenger


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run a Messenger server')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    server = Messenger(args.port)
    server.listen()
