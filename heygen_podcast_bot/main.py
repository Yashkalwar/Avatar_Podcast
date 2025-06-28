import os
from dotenv import load_dotenv
from heygen_api import generate_video, poll_video_status, download_video
from elevenlabs_api import synthesize

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
TALKING_PHOTO_ID = os.getenv("TALKING_PHOTO_ID")
VOICE_ID = os.getenv("VOICE_ID")  # This is optional as we have a default

def gen_runner(script_text):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    script_path = os.path.join(OUTPUT_DIR, "podcast_script.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_text)
    print(f"[Step 1] Script saved to {script_path}")

    try:
        # Synthesize audio
        print("[Step 2] Synthesizing audio with ElevenLabs...")
        audio_path = synthesize(script_text, voice_id=VOICE_ID, output_dir=OUTPUT_DIR)
        print(f"[Step 3] Audio saved to {audio_path}")

        if not TALKING_PHOTO_ID:
            print("Warning: TALKING_PHOTO_ID not set in .env file. Video generation will be skipped.")
            return

        # Generate video
        print("[Step 4] Sending audio to HeyGen...")
        video_id = generate_video(
            avatar_id=TALKING_PHOTO_ID,
            audio_file_path=audio_path,
            dimensions={"width": 1280, "height": 720}
        )
        print(f"[Step 5] Video generation started. Video ID: {video_id}")

        # Poll for completion
        print("[Step 6] Polling for video status...")
        video_url = poll_video_status(video_id)
        print(f"[Step 7] Video ready! Downloading from {video_url}")

        # Download video
        final_path = download_video(video_url, output_dir=OUTPUT_DIR)
        print(f"[Step 8] Video downloaded to {final_path}")
        return final_path

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your API keys and settings in the .env file")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print("Error details:", e.response.text)



def main():
    print("Enter your podcast script (end with Ctrl+D or Ctrl+Z on Windows):")
    try:
        script_text = "".join(iter(input, ""))
    except EOFError:
        script_text = ""
    
    if not script_text.strip():
        print("No script entered. Exiting.")
        return

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save script
    script_path = os.path.join(OUTPUT_DIR, "podcast_script.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_text)
    print(f"[Step 1] Script saved to {script_path}")

    try:
        # Synthesize audio
        print("[Step 2] Synthesizing audio with ElevenLabs...")
        audio_path = synthesize(script_text, voice_id=VOICE_ID, output_dir=OUTPUT_DIR)
        print(f"[Step 3] Audio saved to {audio_path}")

        if not TALKING_PHOTO_ID:
            print("Warning: TALKING_PHOTO_ID not set in .env file. Video generation will be skipped.")
            return

        # Generate video
        print("[Step 4] Sending audio to HeyGen...")
        video_id = generate_video(
            avatar_id=TALKING_PHOTO_ID,
            audio_file_path=audio_path,
            dimensions={"width": 1280, "height": 720}
        )
        print(f"[Step 5] Video generation started. Video ID: {video_id}")

        # Poll for completion
        print("[Step 6] Polling for video status...")
        video_url = poll_video_status(video_id)
        print(f"[Step 7] Video ready! Downloading from {video_url}")

        # Download video
        final_path = download_video(video_url, output_dir=OUTPUT_DIR)
        print(f"[Step 8] Video downloaded to {final_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your API keys and settings in the .env file")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print("Error details:", e.response.text)

if __name__ == "__main__":
    main()