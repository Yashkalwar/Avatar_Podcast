import os
from dotenv import load_dotenv
from heygen_api import generate_video, poll_video_status, download_video
from elevenlabs_api import synthesize

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
TALKING_PHOTO_ID = os.getenv("TALKING_PHOTO_ID")
VOICE_ID = os.getenv("VOICE_ID")


def main():
    print("Enter your podcast script (end with Ctrl+D or Ctrl+Z on Windows):")
    try:
        script_text = "".join(iter(input, ""))
    except EOFError:
        pass
    if not script_text.strip():
        print("No script entered. Exiting.")
        return

    # Optionally save script
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    script_path = os.path.join(OUTPUT_DIR, "podcast_script.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_text)
    print(f"[Step 1] Script saved to {script_path}")

    # Synthesize audio
    print("[Step 2] Synthesizing audio with ElevenLabs...")
    audio_path = synthesize(script_text, voice_id=VOICE_ID, output_dir=OUTPUT_DIR)
    print(f"[Step 3] Audio saved to {audio_path}")

    # Generate video
    print("[Step 4] Sending audio to HeyGen...")
    video_id = generate_video(TALKING_PHOTO_ID, audio_path)
    print(f"[Step 5] Video generation started. Video ID: {video_id}")

    # Poll for completion
    print("[Step 6] Polling for video status...")
    video_url = poll_video_status(video_id)
    print(f"[Step 7] Video ready! Downloading from {video_url}")

    # Download video
    final_path = download_video(video_url, output_dir=OUTPUT_DIR)
    print(f"[Step 8] Video downloaded to {final_path}")

if __name__ == "__main__":
    main() 