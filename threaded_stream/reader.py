# import the necessary packages
import os
from threading import Thread

import cv2
from dotenv import load_dotenv

load_dotenv()


AMCREST_USER = os.getenv("AMCREST_USER")
AMCREST_PW = os.getenv("AMCREST_PW")
AMCREST_IP = os.getenv("AMCREST_IP")


def get_amcrest_rtsp_url(user, pw, ip):
    url = (
        f"rtsp://{user}:{pw}@{ip}:554/"
        "cam/realmonitor?channel=1&subtype=0&authbasic=64"
    )
    return url


class RTSPStream:
    def __init__(self, src=0):
        rtsp_url = get_amcrest_rtsp_url(AMCREST_USER, AMCREST_PW, AMCREST_IP)
        print(f"Received RTSP URL: {rtsp_url}")

        self.stream = cv2.VideoCapture(rtsp_url)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return
            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
