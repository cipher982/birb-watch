import os
import subprocess
from threading import Thread
import sys
from queue import Queue

import cv2
from dotenv import load_dotenv

load_dotenv()


AMCREST_USER = os.getenv("AMCREST_USER")
AMCREST_PW = os.getenv("AMCREST_PW")
AMCREST_IP = os.getenv("AMCREST_IP")
YT_KEY = os.getenv("YT_KEY")

YOUTUBE_SERVER_URL = "rtmp://a.rtmp.youtube.com/live2/"


def get_amcrest_rtsp_url(user, pw, ip):
    url = (
        f"rtsp://{user}:{pw}@{ip}:554/"
        "cam/realmonitor?channel=1&subtype=0&authbasic=64"
    )
    return url


def main():

    # Get the URL based on env variables
    rtsp_url = get_amcrest_rtsp_url(AMCREST_USER, AMCREST_PW, AMCREST_IP)
    print(f"Received RTSP URL: {rtsp_url}")

    # Bring stream into CV2
    cap = cv2.VideoCapture(rtsp_url)
    print("Loaded camera stream into cv2")

    # gather video info to ffmpeg
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fps = 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # command and params for ffmpeg
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        "{}x{}".format(width, height),
        "-r",
        str(fps),
        "-i",
        "-",
        "-f",
        "lavfi",
        "-i",
        "anullsrc",
        "-c:v",
        "libx264",
        "-x264-params",
        "keyint=120:scenecut=0",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "ultrafast",
        "-f",
        "flv",
        YOUTUBE_SERVER_URL + YT_KEY,
    ]

    # using subprocess and pipe to fetch frame data
    p = subprocess.Popen(command, stdin=subprocess.PIPE)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("frame read failed")
            break

        # YOUR CODE FOR PROCESSING FRAME HERE
        y = 0
        x = 0
        h = 512
        w = 512
        frame = frame[y : y + h, x : x + w]
        # write to pipe
        p.stdin.write(frame.tobytes())


if __name__ == "__main__":
    main()
