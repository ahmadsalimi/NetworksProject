import queue
import threading

import cv2
import numpy as np

from .mediastream import MediaStreamClient


class MediaUI:

    def __init__(self, client: MediaStreamClient, filename: str) -> None:
        self.__filename = filename
        self.__client = client
        self.__frame_queue = queue.Queue(maxsize=16)
        self.__uid, self.__fps = self.__client.start_stream(self.__filename)
        self.__finished = False
        self.__reading_thread = threading.Thread(target=self.__read_frames)
        self.__reading_thread.start()

    @property
    def finished(self) -> bool:
        with self.__frame_queue.mutex:
            return self.__finished

    @finished.setter
    def finished(self, value: bool) -> None:
        with self.__frame_queue.mutex:
            self.__finished = value

    def __read_frames(self) -> None:
        while True:
            if self.finished:
                return
            frame = self.__client.get_next_frame(self.__uid)
            if frame is None:
                self.finished = True
                return
            frame = np.frombuffer(frame, dtype=np.uint8)[:, None]
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            print('putting frame')
            self.__frame_queue.put(frame)

    def show(self) -> None:
        try:
            while True:
                if self.finished and self.__frame_queue.empty():
                    return
                frame: np.ndarray = self.__frame_queue.get()
                print('got frame')
                cv2.imshow(self.__filename, frame)
                if cv2.waitKey(int(1000 / self.__fps)) & 0xFF == ord("q"):
                    self.finished = True
                    threading.Thread(target=self.__client.close_stream,
                                     args=(self.__uid,),
                                     daemon=True).start()
                    return
        finally:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
