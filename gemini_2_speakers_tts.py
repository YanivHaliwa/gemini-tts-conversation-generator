import argparse
import base64
import mimetypes
import os
import re
import struct
import sys
from pathlib import Path
from google import genai
from google.genai import types

def extract_speakers(text: str) -> tuple[str, str]:
    """
    Extracts the first two unique speaker names from a formatted dialogue.

    Args:
        text (str): The dialogue string, where each line starts with 'Name:'

    Returns:
        tuple[str, str]: (speaker1_name, speaker2_name)
    """
    seen = []
    for line in text.splitlines():
        if ":" in line:
            name = line.split(":", 1)[0].strip()
            if name and name not in seen:
                seen.append(name)
            if len(seen) == 2:
                return seen[0], seen[1]
    # Fallback if less than 2 found
    return (seen[0], None) if seen else (None, None)


def get_available_voices():
    return [
        ("Zephyr", "Bright", "Female"),
        ("Puck", "Upbeat", "Male"),
        ("Charon", "Informative", "Male"),
        ("Kore", "Firm", "Female"),
        ("Fenrir", "Excitable", "Male"),
        ("Leda", "Youthful", "Female"),
        ("Orus", "Firm", "Male"),
        ("Aoede", "Breezy", "Female"),
        ("Callirrhoe", "Easy-going", "Female"),  # Fixed spelling with two 'r's
        ("Autonoe", "Bright", "Female"),
        ("Enceladus", "Breathy", "Male"),
        ("Iapetus", "Clear", "Male"),
        ("Umbriel", "Easy-going", "Male"),
        ("Algieba", "Smooth", "Male"),
        ("Despina", "Smooth", "Female"),
        ("Erinome", "Clear", "Female"),
        ("Algenib", "Gravelly", "Male"),
        ("Rasalgethi", "Informative", "Male"),
        ("Laomedeia", "Upbeat", "Female"),
        ("Achernar", "Soft", "Female"),
        ("Alnilam", "Firm", "Male"),
        ("Schedar", "Even", "Male"),
        ("Gacrux", "Mature", "Female"),
        ("Pulcherrima", "Forward", "Female"),
        ("Achird", "Friendly", "Male"),
        ("Zubenelgenubi", "Casual", "Male"),
        ("Vindemiatrix", "Gentle", "Female"),
        ("Sadachbia", "Lively", "Male"),
        ("Sadaltager", "Knowledgeable", "Male"),
        ("Sulafat", "Warm", "Female"),
    ]

def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"\n✅ File saved to: {file_name}")

def detect_speakers_count(client, model, prompt):
    """Analyze the script and determine the two main speakers"""
    # Always return 2 since Gemini only supports 2 speakers
    return 2

def select_voices_for_speakers(client, model, prompt, speaker1_name, speaker2_name):
    """Select different voices for two named speakers in the script"""
    
    available_voices = get_available_voices()
    voice_names = [v[0] for v in available_voices]
    
    # Create a case-insensitive lookup for voice names
    voice_names_lower = [v.lower() for v in voice_names]
    
    # Create lists to look up gender by voice name
    male_voices = [v[0] for v in available_voices if v[2] == "Male"]
    female_voices = [v[0] for v in available_voices if v[2] == "Female"]
    
    # Handle case sensitivity for speaker names
    speaker1_display = speaker1_name
    speaker2_display = speaker2_name
    
    # Create a prompt for the model to suggest voices for specific named speakers
    speaker_suggestion_prompt = f"""Analyze this script with two speakers named '{speaker1_display}' and '{speaker2_display}'.
Suggest the best voice for each of these two speakers based on their character in the script.

Available male voices: {male_voices}
Available female voices: {female_voices}

Script:
{prompt}

Respond in this exact format:
{speaker1_name}: [voice_name]
{speaker2_name}: [voice_name]

Choose voices that sound different from each other and match the personality of each speaker.
Select male and female voices according to the script and context, and if the script not distinctly indicates then better you select one male one female voice."""
    
    # Get voice suggestions from the model
    response = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=[types.Part(text=speaker_suggestion_prompt)])]
    )
    
    text = response.candidates[0].content.parts[0].text.strip()
    
    # Parse the response to extract voices
    speaker_voices = {}
    lines = text.split('\n')
    for line in lines:
        # Case insensitive startswith check for speaker names
        if line.lower().startswith(f"{speaker1_name.lower()}:"):
            voice = line.split(":", 1)[1].strip()
            # Case-insensitive voice matching
            voice_lower = voice.lower()
            if voice_lower in voice_names_lower:
                # Use the correctly capitalized version from our list
                correct_index = voice_names_lower.index(voice_lower)
                speaker_voices[speaker1_name] = voice_names[correct_index]
        elif line.lower().startswith(f"{speaker2_name.lower()}:"):
            voice = line.split(":", 1)[1].strip()
            # Case-insensitive voice matching
            voice_lower = voice.lower()
            if voice_lower in voice_names_lower:
                # Use the correctly capitalized version from our list
                correct_index = voice_names_lower.index(voice_lower)
                speaker_voices[speaker2_name] = voice_names[correct_index]
    
    # Ensure we have different voices for each speaker
    if speaker1_name not in speaker_voices:
        speaker_voices[speaker1_name] = male_voices[0]
    
    if speaker2_name not in speaker_voices:
        # Choose a different voice type than speaker 1
        voice1_gender = next((v[2] for v in available_voices if v[0] == speaker_voices[speaker1_name]), "Male")
        if voice1_gender == "Male" and female_voices:
            speaker_voices[speaker2_name] = female_voices[0]
        elif male_voices:
            speaker_voices[speaker2_name] = male_voices[0]
        else:
            # Fallback to any voice that's different from speaker 1
            for voice in voice_names:
                if voice != speaker_voices[speaker1_name]:
                    speaker_voices[speaker2_name] = voice
                    break
            else:
                # Last resort: use the same voice if no alternatives
                speaker_voices[speaker2_name] = speaker_voices[speaker1_name]
    
    return speaker_voices 

def generate(script_path=None, output_file=None):
    """
    Generate audio from a conversation script.
    
    Args:
        script_path: Path to the conversation script file
        output_file: Optional output filename (without extension)
    """
    # Use command line arguments or prompt for input if not provided
    if not script_path:
        script_path = input("📄 Enter path to your script file (e.g., scene.txt): ").strip()
    
    if not os.path.isfile(script_path):
        print(f"❌ File not found: {script_path}")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        user_prompt = f.read()
    
    # Extract speaker names first for potential filename generation
    speaker1, speaker2 = extract_speakers(user_prompt)
    
    # Determine output filename
    if not output_file:
        if speaker1 and speaker2:
            # Create filename based on speakers' names
            speaker1_part = speaker1.lower().replace(" ", "_")
            speaker2_part = speaker2.lower().replace(" ", "_") 
            smart_name = f"{speaker1_part}_{speaker2_part}"

            #print(f"📁 Generating smart filename based on speakers: {smart_name}")
            file_name = smart_name
        else:
            # Fallback to script filename if no speakers found
            script_basename = Path(script_path).stem
            file_name = script_basename if script_basename else "output_audio"
            print(f"📁 Using filename based on input file: {file_name}")
    else:
        file_name = output_file

    print("\n🔄 Extracting speakers from script...")
    
    # Extract speaker names first
    speaker1, speaker2 = extract_speakers(user_prompt)
    
    # Handle missing speaker names with defaults
    if not speaker1:
        speaker1 = "Speaker 1"
    if not speaker2:
        speaker2 = "Speaker 2"
        
    print(f"👥 Detected speakers: {speaker1} and {speaker2}")
    print("\n🔄 Selecting best voices for each speaker...")

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-2.5-flash-preview-tts"
    model_chat = "gemini-2.5-flash-preview-04-17"
    
    # Get voices for the specific named speakers
    speaker_voices = select_voices_for_speakers(client, model_chat, user_prompt, speaker1, speaker2)
    
    print(f"🎙️ Selected voices:")
    print(f"   {speaker1}: {speaker_voices[speaker1]}")
    print(f"   {speaker2}: {speaker_voices[speaker2]}")

    # Create clear instructions for the model
    modified_prompt = f"""Please read this script as a conversation using these two distinct voices:
- Use voice {speaker_voices[speaker1]} for {speaker1}
- Use voice {speaker_voices[speaker2]} for {speaker2}

Apply consistent voices throughout the script, using the correct voice for each speaker.

===SCRIPT===
{user_prompt}"""

    print(f"\n🎤 Generating conversation audio...")

    contents = [types.Content(role="user", parts=[types.Part(text=modified_prompt)])]
    
    # Create configuration with exactly 2 speakers as required by the API
    speaker_voice_configs = [
        types.SpeakerVoiceConfig(
            speaker=speaker1,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    # Make sure we use the exact case-sensitive name from the API's allowed list
                    voice_name=speaker_voices[speaker1]
                )
            ),
        ),
        types.SpeakerVoiceConfig(
            speaker=speaker2,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    # Make sure we use the exact case-sensitive name from the API's allowed list
                    voice_name=speaker_voices[speaker2]
                )
            ),
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_voice_configs
            )
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content.parts:
            continue
        part = chunk.candidates[0].content.parts[0]
        if part.inline_data:
            inline_data = part.inline_data
            data_buffer = inline_data.data
            mime = inline_data.mime_type
            file_extension = mimetypes.guess_extension(mime) or ".wav"
            if mime != "audio/wav":
                print(f"\n Converting to WAV...")
                data_buffer = convert_to_wav(inline_data.data, mime)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    bits_per_sample = 16
    rate = 24000
    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif "audio/L" in param:
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate natural-sounding audio conversations from text scripts using Gemini AI",
        epilog="Example: python gemini_2_speakers_tts.py conversation.txt -o my_audio"
    )
    
    parser.add_argument(
        "input_file",
        help="Path to input script file with conversation", 
        type=str
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Output filename (without extension, default: auto-generated from speaker names)",
        type=str
    )
    
    return parser.parse_args()
    
if __name__ == "__main__":
    print("🎧 Welcome to the Gemini TTS Conversation Generator!")
    
    args = parse_arguments()
    
    # Check if API key is available
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ Error: Gemini API key not found.")
        print("Please set it using the GEMINI_API_KEY environment variable")
        sys.exit(1)
    
    # Generate conversation audio
    generate(args.input_file, args.output)
