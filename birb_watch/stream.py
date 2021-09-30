import json
import os
import subprocess
import textwrap

import cv2
from dotenv import load_dotenv
from flask import Flask, render_template, Response

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
OAUTH_REFRESH_TOKEN = os.getenv("OAUTH_REFRESH_TOKEN")
GCP_DEVICE_ID = os.getenv("GCP_DEVICE_ID")

# Define a function in python to run a CURL command
def run_curl(curl_string):
    # Run the curl command
    curl_output = subprocess.check_output(curl_string, shell=True)
    # Convert the output from bytes to string
    curl_output = curl_output.decode("UTF-8")
    json_output = json.loads(curl_output)
    # Return the output
    return json_output


# Get the OAUTH access token
def get_token():
    post_request = f"""\
curl -L -X POST \
'https://www.googleapis.com/oauth2/v4/token?\
client_id={OAUTH_CLIENT_ID}&client_secret={OAUTH_CLIENT_SECRET}&\
refresh_token={OAUTH_REFRESH_TOKEN}&grant_type=refresh_token'
    """

    json_response = run_curl(textwrap.dedent(post_request))
    print(json_response)
    access_token = json_response["access_token"]
    print(f"Received access_token {access_token[:3]}...{access_token[-3:]}")
    return access_token


# Get the RTSP stream URL
def get_rtsp_url(access_token):
    post_request = f"""\
curl -X POST \
'https://smartdevicemanagement.googleapis.com/v1/enterprises/{GCP_PROJECT_ID}/devices/{GCP_DEVICE_ID}:executeCommand' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer {access_token}' \
--data-raw '{{
    "command" : "sdm.devices.commands.CameraLiveStream.GenerateRtspStream",
    "params" : {{}}
}}'
    """

    json_response = run_curl(textwrap.dedent(post_request))
    rtsp_url = json_response["results"]["streamUrls"]["rtspUrl"]
    print(f"Received RTSP URL: {rtsp_url[:3]}...{rtsp_url[-3:]}")
    return rtsp_url


def gen_frames():
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()
        # cv2.imshow('frame', frame)
        print("success-------", success)
        if not success:
            break
        else:
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


app = Flask(__name__)

access_token = get_token()
rtsp_url = get_rtsp_url(access_token)
camera = cv2.VideoCapture(rtsp_url)


@app.route("/video_feed")
def video_feed():
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def index():
    """Video streaming home page."""
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
