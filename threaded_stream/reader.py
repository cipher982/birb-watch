# import the necessary packages
import os
from threading import Thread

import cv2
from dotenv import load_dotenv

load_dotenv()


RTSP_USER = os.getenv("RTSP_USER")
RTSP_PW = os.getenv("RTSP_PW")
RTSP_IP = os.getenv("RTSP_IP")


def get_amcrest_rtsp_url(user, pw, ip):
    url = (
        f"rtsp://{user}:{pw}@{ip}:554/"
        "cam/realmonitor?channel=1&subtype=0&authbasic=64"
    )
    return url


def get_reolink_rtsp_url(user, pw, ip):
    url = f"rtsp://{user}:{pw}@{ip}:554//h264Preview_01_main"
    return url


class RTSPStream:
    def __init__(self, src=0):
        rtsp_url = get_reolink_rtsp_url(RTSP_USER, RTSP_PW, RTSP_IP)
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
