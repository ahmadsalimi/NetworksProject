# NetworksProject

## Members
Ahmad Salimi,
Kimia Noorbakhsh,
Alireza Ilami

## Description
This repository is for the Computer Networks course (CE-40443) project at Sharif University of Technology


## Usage

### Start messenger server

```bash
usage: startmessenger.py [-h] [-p PORT]

Run a Messenger server

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port to listen on
```

### Start media stream server

```bash
usage: startmediastream.py [-h] [-p PORT] [-d ROOT_DIRECTORY]

Run a Media Stream server

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port to listen on
  -d ROOT_DIRECTORY, --root-directory ROOT_DIRECTORY
                        Root directory
```

### Start proxy server

```bash
usage: proxy/proxy.py [-h] [-p PORT]

Proxy server

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port to listen on
```

### Start client

```bash
usage: startclient.py [-h] [-m MESSENGER_PORT] [-s STREAM_PORT]

Run a Client

optional arguments:
  -h, --help            show this help message and exit
  -m MESSENGER_PORT, --messenger-port MESSENGER_PORT
                        Messenger port
  -s STREAM_PORT, --stream-port STREAM_PORT
                        Stream port
```
