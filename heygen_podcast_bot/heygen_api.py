import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
TALKING_PHOTO_ID = os.getenv("TALKING_PHOTO_ID")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

BASE_URL = "https://api.heygen.com/v1"
HEADERS = {"Authorization": f"Bearer {HEYGEN_API_KEY}"}


def generate_video(talking_photo_id, audio_file_path):
    """
    Uploads audio and requests video generation. Returns video_id.
    """
    url = f"{BASE_URL}/video/generate_by_photo"
    files = {"audio_file": open(audio_file_path, "rb")}
    data = {"photo_id": talking_photo_id}
    response = requests.post(url, headers=HEADERS, files=files, data=data)
    response.raise_for_status()
    return response.json()["data"]["video_id"]


def poll_video_status(video_id, poll_interval=5):
    """
    Polls HeyGen for video status. Returns video_url when ready.
    """
    url = f"{BASE_URL}/video/status/{video_id}"
    while True:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()["data"]
        status = data["status"]
        if status == "completed":
            return data["video_url"]
        elif status == "failed":
            raise Exception("Video generation failed.")
        print(f"[HeyGen] Status: {status}. Waiting {poll_interval}s...")
        time.sleep(poll_interval)


def download_video(video_url, output_dir=OUTPUT_DIR):
    """
    Downloads the video from video_url to output_dir with a timestamped filename.
    Returns the path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"podcast_{timestamp}.mp4")
    with requests.get(video_url, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return filename 