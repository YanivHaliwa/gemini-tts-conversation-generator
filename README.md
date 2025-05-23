# Gemini TTS Conversation Generator

A Python tool that uses Google's Gemini API to generate natural-sounding audio conversations from text scripts. This tool automatically identifies speakers in your script, assigns appropriate voices to each character, and generates audio with realistic multi-speaker dialogue.

## Features

- **Automatic Speaker Detection**: Automatically identifies speaker names from your script
- **Voice Assignment**: Intelligently assigns suitable voices to each speaker based on context
- **Multiple Speakers**: Handles conversations between two different speakers
- **High-Quality TTS**: Uses Google's Gemini 2.5 Flash Preview TTS for natural-sounding audio
- **Gender Balance**: Automatically selects male and female voices to match character context
- **Error Handling**: Robust error handling for voice selection and speaker detection

## Requirements

- Python 3.7+
- Google Generative AI Python SDK
- Google API key with Gemini API access

## Installation

```bash
# Clone the repository
git clone https://github.com/YanivHaliwa/gemini-tts-conversation-generator.git
cd gemini-tts-conversation-generator

# Install dependencies
pip install google-genai
```

## Usage

1. Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

2. Create a script file with dialogue. Format should have speaker names followed by a colon:

```
John: Hello there, how are you today?
Sarah: I'm doing well, thanks for asking! How about you?
John: Can't complain. The weather is beautiful today.
```

3. Run the script (choose one method):

   **Basic Usage:**

   ```bash
   python gemini_2_speakers_tts.py your_script.txt
   ```

   **With Custom Output Filename:**

   ```bash
   python gemini_2_speakers_tts.py your_script.txt -o custom_output_name
   ```

   **Command-line Options:**

   - First argument: Path to input script file (required)
   - `-o, --output`: Custom output filename (optional, auto-generated from speaker names if not provided)
4. The script will:

   - Extract speaker names from your dialogue (e.g., "John" and "Sarah")
   - Automatically generate a filename based on speakers (e.g., "john_sarah.wav") if none specified
   - Select appropriate voices for each speaker
5. The script will:

   - Extract speaker names from your dialogue
   - Select appropriate voices for each speaker
   - Generate natural-sounding audio with proper speaker differentiation

## Available Voices

The script uses Google's Gemini voices, which include a wide range of voice styles:

| Voice Name           | Style       | Gender |
| -------------------- | ----------- | ------ |
| Zephyr               | Bright      | Female |
| Puck                 | Upbeat      | Male   |
| Charon               | Informative | Male   |
| Kore                 | Firm        | Female |
| Fenrir               | Excitable   | Male   |
| Leda                 | Youthful    | Female |
| *and many more...* |             |        |

## Example

Input script (`conversation.txt`):

```
Alice: Hi Bob, have you heard about the new AI tools from Google?
Bob: Yes, the Gemini models are quite impressive! Have you tried them?
Alice: I'm using one right now to generate this conversation.
Bob: That's amazing! The voices sound so natural.
```

**Command:**

```bash
python gemini_2_speakers_tts.py conversation.txt
```

Check out the `examples` folder for more sample conversation scripts you can use with this tool.  These examples demonstrate different conversation styles and emotional tones that work well with voice synthesis.

**Output:**

```
🎧 Welcome to the Gemini Audio Generator CLI!
📁 Generating smart filename based on speakers: alice_bob

🔄 Extracting speakers from script...
👥 Detected speakers: Alice and Bob
🔄 Selecting best voices for each speaker...
🎙️ Selected voices:
   Alice: Leda
   Bob: Puck

🎤 Generating conversation audio...
✅ File saved to: demo.wav
```

## License

MIT License

## Author

Created by [Yaniv Haliwa](https://github.com/YanivHaliwa) for security testing and educational purposes.
