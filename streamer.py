import argparse
import os
import subprocess
from time import sleep

import imutils
import cv2
from dotenv import load_dotenv

from utils import transcode
from threaded_stream import RTSPStream

load_dotenv()

WIDTH = 512
HEIGHT = 512
FPS = 30


def get_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-n",
        "--num-frames",
        type=int,
        default=100,
        help="# of frames to loop over for FPS test",
    )
    ap.add_argument(
        "-d",
        "--display",
        type=int,
        default=1,
        help="Whether or not frames should be displayed",
    )
    args = vars(ap.parse_args())
    return args


def main():
    # construct the argument parse and parse the arguments
    args = get_args()

    print("[INFO] sampling THREADED frames from webcam...")
    vs = RTSPStream().start()
    # fps = FPS().start()

    ffmpeg_cmd = transcode(WIDTH, HEIGHT, FPS)
    p = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # Main streamer loop
    try:
        while True:
            frame = vs.read()

            # crop
            y, x = 0, 420
            h, w = 1080, 1080
            frame = frame[y : y + h, x : x + w]

            # resize
            # frame = imutils.resize(frame, width=400)

            # check to see if the frame should be displayed to our screen
            if args["display"] > 0:
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1) & 0xFF

            # write frame out to ffmpeg stream
            p.stdin.write(frame.tobytes())
            sleep(0.03)

    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, killing stream")
        cv2.destroyAllWindows()
        vs.stop()
        p.kill()


if __name__ == "__main__":
    main()
