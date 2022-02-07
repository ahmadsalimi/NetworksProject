from dataclasses import dataclass
from enum import Enum
from glob import glob
import os
import queue
import threading
from typing import Any, Callable, Dict, List, Tuple
from uuid import UUID, uuid4

import cv2

from common.tcpserver import TCPServer


class RequestType(Enum):
    GetList = 0
    StartStream = 1
    GetNextFrame = 2
    CloseStream = 3


@dataclass
class MediaStreamRequest:
    type: RequestType
    args: Tuple[Any, ...]


VIDEO_EXTENSIONS = set(['mp4', 'avi',
                        'mkv', 'mov',
                        'flv', 'wmv',
                        'mpg', 'mpeg',
                        'm4v', '3gp',
                        '3g2'])


class StreamingError(Exception):
    pass


class VideoReader:

    def __init__(self, path: str, on_close: Callable[[UUID], None]) -> None:
        self.__video = cv2.VideoCapture(path)
        self.__frame_queue = queue.Queue(maxsize=16)
        self.__finished = False
        self.__closed = False
        self.__on_close = on_close
        self.fps: float = self.__video.get(cv2.CAP_PROP_FPS)
        self.uid = uuid4()
        self.__reading_thread = threading.Thread(target=self.__read_frames)
        self.__reading_thread.start()

    def __read_frames(self) -> None:
        while True:
            if self.finished:
                return
            ret, frame = self.__video.read()
            if not ret:
                with self.__frame_queue.mutex:
                    self.__finished = True
                return
            ret, frame = cv2.imencode('.jpg', frame)
            if ret:
                self.__frame_queue.put(frame.tobytes())

    @property
    def finished(self) -> bool:
        with self.__frame_queue.mutex:
            return self.__finished

    def nextframe(self) -> bytes:
        if self.finished and self.__frame_queue.empty():
            self.close()
            return None
        return self.__frame_queue.get()

    def close(self) -> None:
        with self.__frame_queue.mutex:
            if self.__closed:
                return
            self.__finished = True
            self.__frame_queue.queue.clear()
            self.__closed = True
        self.__video.release()
        self.__on_close(self.uid)
        self.__reading_thread.join()

    def __del__(self) -> None:
        self.close()


class MediaStreamServer(TCPServer[MediaStreamRequest, Any]):

    def __init__(self, port: int, root_directory: str) -> None:
        super().__init__(port)
        self.files = [os.path.basename(file)
                      for file in glob(os.path.join(root_directory, '*'))
                      if file.split('.')[-1] in VIDEO_EXTENSIONS]
        self.root_directory = root_directory
        self.streams: Dict[UUID, VideoReader] = {}

    def handle_request(self, _: UUID, request: MediaStreamRequest) -> Any:
        if request.type == RequestType.GetList:
            return self.get_list(*request.args)
        if request.type == RequestType.StartStream:
            return self.start_stream(*request.args)
        if request.type == RequestType.GetNextFrame:
            return self.get_next_frame(*request.args)
        if request.type == RequestType.CloseStream:
            return self.close_stream(*request.args)

    def get_list(self) -> List[str]:
        return self.files

    def __on_close(self, uid: UUID) -> None:
        del self.streams[uid]

    def start_stream(self, filename: str) -> Tuple[UUID, float]:
        if filename not in self.files:
            raise StreamingError(f'File {filename} does not exist')
        video_reader = VideoReader(os.path.join(self.root_directory, filename),
                                   on_close=self.__on_close)
        self.streams[video_reader.uid] = video_reader
        return video_reader.uid, video_reader.fps

    def get_next_frame(self, uid: UUID) -> bytes:
        if uid not in self.streams:
            raise StreamingError(f'Stream {uid} does not exist')
        return self.streams[uid].nextframe()

    def close_stream(self, uid: UUID) -> None:
        if uid not in self.streams:
            raise StreamingError(f'Stream {uid} does not exist')
        self.streams[uid].close()
