import os
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Default to Sarah
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

def synthesize(script_text, voice_id=None, output_dir=OUTPUT_DIR):
    """
    Synthesizes speech from text using ElevenLabs and saves as MP3.
    Returns the path to the saved audio file.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set in .env file")
        
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    # Use provided voice_id or default
    voice_id = voice_id or VOICE_ID
    
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "podcast_audio.mp3")
    
    try:
        # Try with a default model first
        model_id = "eleven_monolingual_v1"
        
        print(f"Using voice ID: {voice_id}")
        print(f"Using model: {model_id}")
        
        # Generate audio
        audio = client.text_to_speech.convert(
            text=script_text,
            voice_id=voice_id,
            model_id=model_id
        )
        
        # Save to file
        with open(filename, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        
        return filename
        
    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        print(f"Voice ID being used: {voice_id}")
        
        try:
            print("\nAttempting to list available voices...")
            voices = client.voices.get_all()
            print("\nAvailable voices:")
            for voice in voices.voices:
                print(f"- {voice.name}: {voice.voice_id}")
        except Exception as ve:
            print(f"\nCould not list voices: {str(ve)}")
        
        print("\nPlease check your API key and ensure it has the correct permissions.")
        print("Also, verify that the voice ID exists in your account.")
        raise