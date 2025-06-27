import os
from elevenlabs import generate, save, set_api_key
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

set_api_key(ELEVENLABS_API_KEY)

def synthesize(script_text, voice_id=VOICE_ID, output_dir=OUTPUT_DIR):
    """
    Synthesizes speech from text using ElevenLabs and saves as MP3.
    Returns the path to the saved audio file.
    """
    audio = generate(text=script_text, voice=voice_id)
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "podcast_audio.mp3")
    save(audio, filename)
    return filename 