import argparse
from datetime import datetime
import json
import multiprocessing as mp
import os
from queue import Queue
import requests
import subprocess
from time import sleep, time

import cv2
from dotenv import load_dotenv
import numpy as np

from scorers import YOLOv5
from stream_utils import transcode, plot_boxes
from threaded_stream import RTSPStream


load_dotenv()

WIDTH = 2304
HEIGHT = 1296
FPS = 15

BIRD_DIR = "classifier/images"
MODEL_NAME = "effecientNet_B3"


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


def predict_img(prediction_queue, classified_queue):
    while True:
        array = prediction_queue.get()
        data = json.dumps(
            {"signature_name": "serving_default", "instances": array.tolist()}
        )
        headers = {"content-type": "application/json"}
        json_response = requests.post(
            f"http://localhost:8502/v1/models/{MODEL_NAME}:predict",
            data=data,
            headers=headers,
        )
        predictions = json.loads(json_response.text)["predictions"]
        pred_class = np.array(predictions[0]).argmax()
        if classified_queue.full():
            classified_queue.get()
        classified_queue.put((array, pred_class))
        print(pred_class)


def main():
    # construct the argument parse and parse the arguments
    args = get_args()

    # Load scorer
    scorer = YOLOv5()
    model = scorer.model

    # Start reading RTSP (input) stream from camera
    print("Sampling THREADED frames from webcam...")
    vs = RTSPStream().start()
    # fps = FPS().start()

    # Start ffmpeg (output) RTMP stream process
    ffmpeg_cmd = transcode(WIDTH, HEIGHT, FPS)
    p_ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # Start subprocess to send images to tf serve
    m = mp.Manager()
    prediction_queue = m.Queue(maxsize=10)
    classified_queue = m.Queue(maxsize=10)
    p_tf_serve = mp.Process(
        target=predict_img, args=(prediction_queue, classified_queue)
    )
    p_tf_serve.start()

    # collect inference times for analysis
    model_timers = []
    write_timers = []

    # Main streamer loop
    try:
        while True:
            start_time = time()

            # Read in a frame from the capture stream
            frame = vs.read()

            # Crop
            y, x = 0, 420
            h, w = 1280, 720
            # frame = frame[y : y + h, x : x + w]

            # Resize
            # frame = imutils.resize(frame, width=512, height=512)

            # Find objects
            detector_results = scorer.score_frame(frame)
            labels = detector_results[0]
            coords = detector_results[1]
            bird_boxes = []
            frame, bird_boxes = plot_boxes(model, detector_results, frame)
            if len(bird_boxes) > 0:
                print(f"Found {len(bird_boxes)} bird boxes")
                for box in bird_boxes:
                    h = box.shape[0]
                    w = box.shape[1]
                    if w > 50 and h > 50:
                        if not prediction_queue.full():
                            prediction_queue.put(box)
                        if not classified_queue.empty():
                            bird_img, bird_class = classified_queue.get()
                            file_name = f"bird_{bird_class}_{datetime.now()}.jpg"
                            cv2.imwrite(os.path.join(BIRD_DIR, file_name), bird_img)

            # Pause if needed to keep output around 30-40 FPS
            elapsed_time = time() - start_time
            model_timers.append(elapsed_time)
            if elapsed_time < (1 / FPS):
                pass
                sleep((1 / FPS) - elapsed_time)

            # Catch the occasional missed frame without crashing
            # TODO: this try statement needs a more elegant solution
            try:
                start_time = time()
                if args["display"] > 0:
                    pass
                    cv2.imshow("Frame", frame)
                    key = cv2.waitKey(1) & 0xFF
                p_ffmpeg.stdin.write(frame.tobytes())
                write_timers.append(time() - start_time)
            except:
                pass

    # Due to previous issues killing process, adding an int catch
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, killing stream")
        cv2.destroyAllWindows()
        vs.stop()
        p_ffmpeg.stdin.write(b"q\r\n")
        print(f"Avg frame processing time: {int(np.mean(model_timers)*1_000)}ms")
        print(f"Avg stream write time: {int(np.mean(write_timers)*1_000)}ms")


if __name__ == "__main__":
    main()
