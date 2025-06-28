import os
import time
import requests
from dotenv import load_dotenv

# Load environment config
load_dotenv()

# Config
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
TALKING_PHOTO_ID = os.getenv("TALKING_PHOTO_ID")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

# API endpoints
UPLOAD_URL = "https://upload.heygen.com/v1/asset"
API_BASE = "https://api.heygen.com"

def _make_request(method, url, headers=None, json=None, data=None, stream=False):
    """Helper to handle API requests with error handling"""
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            data=data,
            stream=stream
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        error = e.response.text if hasattr(e, 'response') and e.response else str(e)
        print(f"API request failed: {error}")
        raise

def upload_audio(audio_path):
    """Upload audio file to HeyGen and return the URL"""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    print(f"Uploading {os.path.basename(audio_path)}...")
    
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "audio/mpeg"
    }
    
    with open(audio_path, 'rb') as f:
        response = _make_request('POST', UPLOAD_URL, headers=headers, data=f.read())
    
    return response.json()["data"]["url"]

def generate_video(avatar_id, audio_path, dimensions=None):
    """Generate video with given avatar and audio"""
    if not HEYGEN_API_KEY:
        raise ValueError("API key not found in environment")
    
    # Upload audio first
    audio_url = upload_audio(audio_path)
    print(f"Audio uploaded: {audio_url}")
    
    # Prepare video generation payload
    payload = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": "normal"
            },
            "voice": {"type": "audio", "audio_url": audio_url}
        }],
        "dimension": dimensions or {"width": 1280, "height": 720},
        "test": True
    }
    
    # Generate video
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE}/v2/video/generate"
    print(f"Generating video with {os.path.basename(audio_path)}...")
    
    response = _make_request('POST', url, headers=headers, json=payload)
    video_id = response.json()["data"]["video_id"]
    print(f"Video generation started. ID: {video_id}")
    
    return video_id

def poll_video_status(video_id, poll_interval=5, max_attempts=60):
    """Check video generation status until complete"""
    status_url = f"{API_BASE}/v1/video_status.get?video_id={video_id}"
    
    for attempt in range(1, max_attempts + 1):
        try:
            response = _make_request('GET', status_url, 
                                  headers={"X-Api-Key": HEYGEN_API_KEY})
            
            data = response.json()["data"]
            status = data["status"]
            
            if status == "completed":
                print(f"Video ready!")
                return data["video_url"]
                
            if status in ["failed", "error"]:
                error = data.get('error', 'Unknown error')
                raise Exception(f"Video generation failed: {error}")
                
            print(f"Status: {status} (attempt {attempt}/{max_attempts})")
            time.sleep(poll_interval)
            
        except Exception as e:
            if attempt == max_attempts:
                raise TimeoutError("Max attempts reached")
            print(f"Retrying... ({str(e)})")
            time.sleep(poll_interval)
    
    raise TimeoutError("Video generation timed out")

def download_video(video_url, output_dir=OUTPUT_DIR):
    """Download video to local directory"""
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"podcast_{int(time.time())}.mp4")
    
    print(f"Downloading video to {filename}...")
    
    response = _make_request('GET', video_url, stream=True)
    
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Download complete: {filename}")
    return filename