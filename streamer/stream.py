import json
import os
import subprocess
import textwrap

import cv2
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
OAUTH_ACESS_TOKEN = os.getenv("OAUTH_ACESS_TOKEN")
OAUTH_REFRESH_TOKEN = os.getenv("OAUTH_REFRESH_TOKEN")
GCP_DEVICE_ID = os.getenv("GCP_DEVICE_ID")
YT_KEY = os.getenv("YT_KEY")

YOUTUBE_SERVER_URL = "rtmp://a.rtmp.youtube.com/live2/"
ENV_PATH = "../.env"

# Define a function in python to run a CURL command
def run_curl(curl_string):
    curl_output = subprocess.check_output(textwrap.dedent(curl_string), shell=True)
    curl_output = curl_output.decode("UTF-8")
    json_output = json.loads(curl_output)
    return json_output


def save_token(access_token, file_path):
    with open(file_path) as f:
        newlines = []
        for line in f.readlines():
            if "OAUTH_ACCESS_TOKEN" in line:
                print(f"Found old token: {line[-3:]}")
                new_line = f"OAUTH_ACCESS_TOKEN={access_token}"
                newlines.append(new_line)
                print(f"Replacing with new access token {access_token[-3:]}")
            else:
                newlines.append(line)

    with open(file_path, "w") as f:
        for line in newlines:
            f.writelines(line)


# Get the OAUTH access token
def get_access_token():
    post_request = textwrap.dedent(
        f"""\
curl -L -X POST \
'https://www.googleapis.com/oauth2/v4/token?\
client_id={OAUTH_CLIENT_ID}&client_secret={OAUTH_CLIENT_SECRET}&\
refresh_token={OAUTH_REFRESH_TOKEN}&grant_type=refresh_token'
"""
    )

    json_response = run_curl(post_request)
    # print(json_response)
    access_token = json_response["access_token"]
    print(f"Received access_token {access_token[:3]}...{access_token[-3:]}")
    return access_token


# Get the RTSP stream URL
def get_rtsp_url(access_token):
    post_request = textwrap.dedent(
        f"""\
curl -X POST \
'https://smartdevicemanagement.googleapis.com/v1/enterprises/{GCP_PROJECT_ID}/devices/{GCP_DEVICE_ID}:executeCommand' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer {access_token}' \
--data-raw '{{
    "command" : "sdm.devices.commands.CameraLiveStream.GenerateRtspStream",
    "params" : {{}}
}}'
"""
    )
    json_response = run_curl(post_request)
    rtsp_url = json_response["results"]["streamUrls"]["rtspUrl"]
    print(f"Received RTSP URL: {rtsp_url[:3]}...{rtsp_url[-3:]}")
    return rtsp_url


def main():
    try:
        rtsp_url = get_rtsp_url(OAUTH_ACESS_TOKEN)
        print("Using cached access_token")
    except:
        print("Access token expired, gathering new one. . .")
        access_token = get_access_token()
        save_token(access_token, ENV_PATH)
        rtsp_url = get_rtsp_url(access_token)

    cap = cv2.VideoCapture(rtsp_url)

    # gather video info to ffmpeg
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fps = 20
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
        "superfast",
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
