import argparse
import os
import subprocess
from time import sleep, time

import imutils
import cv2
from dotenv import load_dotenv

from scorers import YOLOv5
from stream_utils import transcode
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
        default=-1,
        help="Whether or not frames should be displayed",
    )
    args = vars(ap.parse_args())
    return args


def plot_boxes(model, results, frame):
    labels, cord = results
    n = len(labels)
    x_shape, y_shape = frame.shape[1], frame.shape[0]
    for i in range(n):
        row = cord[i]
        # If score is less than 0.2 we avoid making a prediction.
        if row[4] < 0.2:
            continue
        x1 = int(row[0] * x_shape)
        y1 = int(row[1] * y_shape)
        x2 = int(row[2] * x_shape)
        y2 = int(row[3] * y_shape)
        bgr = (0, 255, 0)  # color of the box
        classes = model.names  # Get the name of label index
        label_font = cv2.FONT_HERSHEY_SIMPLEX  # Font for the label.
        cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)  # Plot the boxes
        cv2.putText(
            frame, classes[labels[i]], (x1, y1), label_font, 0.9, bgr, 2
        )  # Put a label over box.
        return frame


def main():
    # construct the argument parse and parse the arguments
    args = get_args()

    # Load scorer
    scorer = YOLOv5()
    model = scorer.model

    print("[INFO] sampling THREADED frames from webcam...")
    vs = RTSPStream().start()
    # fps = FPS().start()

    ffmpeg_cmd = transcode(WIDTH, HEIGHT, FPS)
    p = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # Main streamer loop
    try:
        while True:
            start_time = time()

            # Read in a frame from the capture stream
            frame = vs.read()

            # crop
            y, x = 0, 420
            h, w = 1080, 1080
            frame = frame[y : y + h, x : x + w]

            # resize
            # frame = imutils.resize(frame, width=512, height=512)

            # Find objects
            results = scorer.score_frame(frame)
            frame = plot_boxes(model, results, frame)

            # Pause if needed to keep output around 30-40 FPS
            elapsed_time = time() - start_time
            if elapsed_time < 50:
                sleep((50 - elapsed_time) * 0.001)

            # Catch the occasional missed frame without crashing
            try:
                if args["display"] > 0:
                    cv2.imshow("Frame", frame)
                    key = cv2.waitKey(1) & 0xFF
                p.stdin.write(frame.tobytes())
            except:
                pass

    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, killing stream")
        cv2.destroyAllWindows()
        vs.stop()
        p.kill()


if __name__ == "__main__":
    main()
