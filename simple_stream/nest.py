import os
import subprocess

import cv2
from dotenv import load_dotenv

import utils

load_dotenv()


GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
OAUTH_ACCESS_TOKEN = os.getenv("OAUTH_ACCESS_TOKEN")
OAUTH_REFRESH_TOKEN = os.getenv("OAUTH_REFRESH_TOKEN")
GCP_DEVICE_ID = os.getenv("GCP_DEVICE_ID")
YT_KEY = os.getenv("YT_KEY")

YOUTUBE_SERVER_URL = "rtmp://a.rtmp.youtube.com/live2/"
ENV_PATH = ".env"


def main():
    try:
        rtsp_url = utils.get_rtsp_url(GCP_PROJECT_ID, GCP_DEVICE_ID, OAUTH_ACCESS_TOKEN)
        print("Using cached access_token")
    except:
        print("Access token expired, gathering new one. . .")
        access_token = utils.get_access_token(
            OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REFRESH_TOKEN
        )
        utils.save_token(access_token, ENV_PATH)
        rtsp_url = utils.get_rtsp_url(GCP_PROJECT_ID, GCP_DEVICE_ID, access_token)

    cap = cv2.VideoCapture(rtsp_url)

    # gather video info to ffmpeg
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fps = 20
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # command and params for ffmpeg
    command = [
        "ffmpeg",
        "-framerate",
        "20",
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

        # write to pipe
        p.stdin.write(frame.tobytes())


if __name__ == "__main__":
    main()
