# Audio Format Issue - MP4/M4A Support

## Problem
The frontend is sending MP4/M4A audio files, but Dialogflow CX doesn't directly support this format. The supported formats are:
- LINEAR16 (WAV/PCM) ✅
- FLAC ✅
- OGG/Opus ✅
- AMR ✅
- MP4/M4A ❌ (Not directly supported)

## Current Solution
The code now:
1. **Auto-detects** the audio format from the file header
2. **Uses UNSPECIFIED encoding** for MP4/M4A files (may not work reliably)
3. **Logs warnings** when MP4/M4A is detected

## Recommended Solution: Audio Conversion

To properly support MP4/M4A, you need to convert the audio to LINEAR16 WAV format before sending to Dialogflow.

### Option 1: Convert on Frontend (Recommended)
Convert MP4/M4A to WAV on the client side before sending:

```javascript
// Example using Web Audio API or a library like pydub.js
async function convertToWav(audioBlob) {
    // Use a library or Web Audio API to convert
    // Return WAV blob
}
```

### Option 2: Convert on Backend
Add audio conversion library to the backend:

1. Install dependencies:
```bash
pip install pydub
# Also need ffmpeg: brew install ffmpeg (Mac) or apt-get install ffmpeg (Linux)
```

2. Add conversion function:
```python
from pydub import AudioSegment
import io

def convert_audio_to_wav(audio_bytes, input_format='m4a'):
    """Convert audio bytes to LINEAR16 WAV format."""
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=input_format)
    # Convert to WAV, 16kHz, mono, 16-bit
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    wav_bytes = io.BytesIO()
    audio.export(wav_bytes, format="wav")
    return wav_bytes.getvalue()
```

## Testing
Check the server logs when sending MP4 audio - you should see:
- Format detection logs
- Warnings about MP4/M4A format
- The encoding being used

## Next Steps
1. Check server logs to confirm MP4 is being detected
2. Decide on frontend or backend conversion
3. Implement conversion if UNSPECIFIED doesn't work

