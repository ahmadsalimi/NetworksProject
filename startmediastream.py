from mediastream.mediastream import MediaStreamServer


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run a Media Stream server')
    parser.add_argument('-p', '--port', type=int,
                        default=8081, help='Port to listen on')
    parser.add_argument('-d', '--root-directory', type=str,
                        default='./videos', help='Root directory')
    args = parser.parse_args()

    server = MediaStreamServer(args.port, args.root_directory)
    server.listen()
