import os

from dotenv import load_dotenv

load_dotenv()


AMCREST_USER = os.getenv("AMCREST_USER")
AMCREST_PW = os.getenv("AMCREST_PW")
AMCREST_IP = os.getenv("AMCREST_IP")
YT_KEY = os.getenv("YT_KEY")

YOUTUBE_SERVER_URL = "rtmp://a.rtmp.youtube.com/live2/"


def transcode(width, height, fps):
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

    return command
