import json
import subprocess
import textwrap


def run_curl(curl_string):
    # Define a function in python to run a CURL command
    curl_output = subprocess.check_output(textwrap.dedent(curl_string), shell=True)
    curl_output = curl_output.decode("UTF-8")
    json_output = json.loads(curl_output)
    return json_output


def save_token(access_token, file_path):
    with open(file_path) as f:
        newlines = []
        for line in f.readlines():
            if "OAUTH_ACCESS_TOKEN" in line:
                new_line = f"OAUTH_ACCESS_TOKEN={access_token}\n"
                newlines.append(new_line)
                print(f"Replacing with new access token {access_token[-3:]}")
            else:
                newlines.append(line)

    with open(file_path, "w") as f:
        for line in newlines:
            f.writelines(line)


# Get the OAUTH access token
def get_access_token(client_id, client_secret, refresh_token):
    post_request = textwrap.dedent(
        f"""\
curl -L -X POST \
'https://www.googleapis.com/oauth2/v4/token?\
client_id={client_id}&client_secret={client_secret}&\
refresh_token={refresh_token}&grant_type=refresh_token'
"""
    )

    json_response = run_curl(post_request)
    # print(json_response)
    access_token = json_response["access_token"]
    print(f"Received access_token {access_token[:3]}...{access_token[-3:]}")
    return access_token


# Get the RTSP stream URL
def get_rtsp_url(gcp_project_id, gcp_device_id, access_token):
    post_request = textwrap.dedent(
        f"""\
curl -X POST \
'https://smartdevicemanagement.googleapis.com/v1/enterprises/{gcp_project_id}/devices/{gcp_device_id}:executeCommand' \
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
