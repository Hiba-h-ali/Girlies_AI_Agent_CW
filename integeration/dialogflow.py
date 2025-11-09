import os
import json
import logging
import io
import subprocess
import tempfile
from google.auth import default
from google.oauth2 import service_account
from google.cloud.dialogflowcx import SessionsClient
from google.cloud.dialogflowcx_v3.types.session import DetectIntentRequest, DetectIntentResponse, QueryInput, TextInput, AudioInput, QueryParameters
from google.cloud.dialogflowcx_v3.types.audio_config import InputAudioConfig, AudioEncoding
import uuid


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import pydub for audio conversion
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    logger.info("pydub is available for audio conversion")
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available. Install with: pip install pydub")

# Check if ffmpeg is available for audio conversion
def _check_ffmpeg_available():
    """Check if ffmpeg is installed and available."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

FFMPEG_AVAILABLE = _check_ffmpeg_available()
if not FFMPEG_AVAILABLE:
    logger.warning("ffmpeg not available. Audio conversion will not work.")
    logger.warning("Install ffmpeg: brew install ffmpeg (Mac) or apt-get install ffmpeg (Linux)")

LOCATION = "us-central1"
PROJECT_ID = "girlies-ai-agent"
AGENT_ID = "4a8116a1-9f58-4b71-8cf0-f2faee516a2d"
LANGUAGE_CODE = "ar"
API_ENDPOINT = f"{LOCATION}-dialogflow.googleapis.com:443"

class Dialogflow:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Dialogflow, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Dialogflow._initialized:
            credentials = None
            # Option 1: Check for credentials file path from environment variable
            creds_file_path = os.environ.get("GCP_CREDENTIALS_FILE")
            if creds_file_path and os.path.exists(creds_file_path):
                credentials = service_account.Credentials.from_service_account_file(creds_file_path)
            # Option 2: Check for credentials JSON string
            elif os.environ.get("GCP_CREDENTIALS"):
                creds_json_string = os.environ.get("GCP_CREDENTIALS")
                creds_json = json.loads(creds_json_string)
                credentials = service_account.Credentials.from_service_account_info(creds_json)
            # Option 3: Check for default credentials file in project directory
            else:
                # Look for common credential file names in the project root
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                default_creds_files = [
                    os.path.join(project_root, "girlies-ai-agent-84d2cbf6976f.json"),
                    os.path.join(project_root, "credentials.json"),
                    os.path.join(project_root, "gcp-credentials.json"),
                ]
                for creds_file in default_creds_files:
                    if os.path.exists(creds_file):
                        credentials = service_account.Credentials.from_service_account_file(creds_file)
                        break
                # Option 4: Use default credentials (for local development with gcloud auth)
                if credentials is None:
                    try:
                        credentials, _ = default()
                    except Exception:
                        raise Exception(
                            "No GCP credentials found. Please set GCP_CREDENTIALS_FILE environment variable, "
                            "or place credentials.json in the project root, or run 'gcloud auth application-default login'"
                        )
            self.client = SessionsClient(credentials=credentials, client_options={"api_endpoint": API_ENDPOINT})
            Dialogflow._initialized = True

# يلي بتاخد الرسالة وبترد عليها 
    def detect_intent(self, query, session_id=None, audio_bytes=None, audio_file_path=None, audio_encoding=None, sample_rate_hertz=16000):
        """
        Detect intent from text or voice message.
        
        Args:
            query: Text query (str) - required for text input
            session_id: Optional session ID (str)
            audio_bytes: Audio data as bytes - required for audio input
            audio_file_path: Path to audio file - alternative to audio_bytes
            audio_encoding: Audio encoding format (auto-detected if None)
            sample_rate_hertz: Sample rate in Hz (default: 16000)
        
        Returns:
            tuple: (response_text, session_id)
        """
        session_id = session_id or str(uuid.uuid4())
        session_path = self.build_session_path(session_id)
        
        # Determine if input is audio or text
        if audio_bytes is not None or audio_file_path is not None:
            # Handle audio input
            if audio_file_path:
                with open(audio_file_path, 'rb') as f:
                    audio_bytes = f.read()
            
            # Auto-detect and convert audio format if needed
            if audio_encoding is None:
                logger.info(f"Auto-detecting audio format (audio size: {len(audio_bytes)} bytes)")
                detected_format = self._detect_audio_format(audio_bytes)
                logger.info(f"Detected format: {detected_format}")
                
                # Convert MP4/M4A to WAV if needed
                if detected_format in ['mp4', 'm4a']:
                    logger.info(f"Converting {detected_format} to WAV format for Dialogflow compatibility...")
                    try:
                        audio_bytes = self._convert_audio_to_wav(audio_bytes, input_format=detected_format)
                        detected_format = 'wav'  # Now it's WAV
                    except Exception as e:
                        logger.error(f"Conversion failed: {str(e)}")
                        raise ValueError(f"Failed to convert {detected_format} audio: {str(e)}")
                
                # Set encoding based on final format
                if detected_format == 'wav':
                    # Extract sample rate from WAV header
                    if len(audio_bytes) >= 28:
                        sample_rate_hertz = int.from_bytes(audio_bytes[24:28], byteorder='little')
                    else:
                        sample_rate_hertz = 16000
                    audio_encoding = AudioEncoding.AUDIO_ENCODING_LINEAR_16
                elif detected_format == 'flac':
                    audio_encoding = AudioEncoding.AUDIO_ENCODING_FLAC
                    sample_rate_hertz = 16000
                elif detected_format == 'ogg':
                    audio_encoding = AudioEncoding.AUDIO_ENCODING_OGG_OPUS
                    sample_rate_hertz = 16000
                else:
                    # Default to LINEAR16
                    audio_encoding = AudioEncoding.AUDIO_ENCODING_LINEAR_16
                    sample_rate_hertz = 16000
                
                logger.info(f"Using encoding: {audio_encoding}, sample rate: {sample_rate_hertz} Hz")
            
            query_input = self.build_audio_query_input(audio_bytes, audio_encoding, sample_rate_hertz)
        elif query:
            # Handle text input
            query_input = self.build_query_input(query)
        else:
            raise ValueError("Either 'query' (text) or 'audio_bytes'/'audio_file_path' must be provided")
        
        request = self.build_detect_intent_request(query_input, session_path)
        response = self.client.detect_intent(request=request)
        return self.extract_response_text(response), session_id
    
    def _detect_audio_format(self, audio_bytes):
        """
        Detect audio format from bytes and return format name.
        
        Returns:
            str: Format name ('mp4', 'm4a', 'wav', 'flac', 'ogg', 'unknown')
        """
        if len(audio_bytes) < 12:
            return 'unknown'
        
        # Check file signatures (magic bytes)
        header_hex = audio_bytes[:12].hex()
        logger.info(f"Audio file header (first 12 bytes): {header_hex}")
        
        # MP4/M4A files start with ftyp box (bytes 4-8)
        if len(audio_bytes) >= 8 and audio_bytes[4:8] == b'ftyp':
            # Check for M4A specific brand
            if b'm4a' in audio_bytes[8:20] or b'M4A' in audio_bytes[8:20]:
                return 'm4a'
            return 'mp4'
        
        # WAV files start with "RIFF" and contain "WAVE"
        elif audio_bytes[0:4] == b'RIFF' and len(audio_bytes) >= 12 and audio_bytes[8:12] == b'WAVE':
            return 'wav'
        
        # FLAC files start with "fLaC"
        elif audio_bytes[0:4] == b'fLaC':
            return 'flac'
        
        # OGG files start with "OggS"
        elif audio_bytes[0:4] == b'OggS':
            return 'ogg'
        
        return 'unknown'
    
    def _convert_audio_to_wav(self, audio_bytes, input_format='mp4'):
        """
        Convert audio bytes to LINEAR16 WAV format.
        Tries pydub first (recommended), falls back to ffmpeg subprocess.
        
        Args:
            audio_bytes: Original audio data
            input_format: Format of input audio ('mp4', 'm4a', 'flac', 'ogg', etc.)
        
        Returns:
            bytes: WAV audio data in LINEAR16 format, 16kHz, mono, 16-bit
        """
        # Try pydub first (cleaner and more reliable)
        if PYDUB_AVAILABLE:
            try:
                logger.info(f"Converting {input_format} audio to WAV using pydub...")
                logger.info(f"Input: {len(audio_bytes)} bytes")
                
                # Create AudioSegment from bytes
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=input_format)
                
                # Convert to WAV format: 16kHz, mono, 16-bit (LINEAR16)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                
                # Export to WAV bytes
                wav_buffer = io.BytesIO()
                audio.export(wav_buffer, format="wav")
                wav_bytes = wav_buffer.getvalue()
                
                logger.info(f"Successfully converted audio using pydub: {len(wav_bytes)} bytes, WAV format, 16kHz, mono, 16-bit")
                return wav_bytes
                
            except Exception as e:
                logger.warning(f"pydub conversion failed: {str(e)}, trying ffmpeg fallback...")
                # Fall through to ffmpeg method
        
        # Fallback to ffmpeg subprocess
        if not FFMPEG_AVAILABLE:
            error_msg = "Audio conversion requires either pydub (pip install pydub) or ffmpeg (brew install ffmpeg / apt-get install ffmpeg)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create temporary files for input and output
        input_ext = input_format if input_format != 'm4a' else 'm4a'
        with tempfile.NamedTemporaryFile(suffix=f'.{input_ext}', delete=False) as input_file:
            input_file.write(audio_bytes)
            input_file_path = input_file.name
        
        output_file_path = None
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
                output_file_path = output_file.name
            
            logger.info(f"Converting {input_format} audio to WAV format using ffmpeg...")
            logger.info(f"Input: {len(audio_bytes)} bytes, Output: {output_file_path}")
            
            # Use ffmpeg to convert to LINEAR16 WAV:
            # - Sample rate: 16000 Hz
            # - Channels: 1 (mono)
            # - Sample format: s16le (16-bit signed little-endian = LINEAR16)
            # - Format: wav
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', input_file_path,  # Input file
                '-ar', '16000',          # Sample rate: 16kHz
                '-ac', '1',              # Channels: mono
                '-acodec', 'pcm_s16le',  # Audio codec: 16-bit PCM (LINEAR16)
                '-f', 'wav',             # Format: WAV
                '-y',                    # Overwrite output file
                output_file_path         # Output file
            ]
            
            # Run ffmpeg (suppress output unless there's an error)
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode != 0:
                error_msg = f"ffmpeg conversion failed: {result.stderr}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Read the converted WAV file
            with open(output_file_path, 'rb') as f:
                wav_bytes = f.read()
            
            logger.info(f"Successfully converted audio using ffmpeg: {len(wav_bytes)} bytes, WAV format, 16kHz, mono, 16-bit")
            return wav_bytes
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg conversion timed out")
            raise ValueError("Audio conversion timed out")
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            raise ValueError(f"Failed to convert audio from {input_format} to WAV: {str(e)}")
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(input_file_path):
                    os.unlink(input_file_path)
                if output_file_path and os.path.exists(output_file_path):
                    os.unlink(output_file_path)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {str(e)}")

    def build_session_path(self, session_id):
        return f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}/sessions/{session_id}"
    
    def build_query_input(self, query):
        """Build query input for text messages."""
        text_input = TextInput(text=query)
        return QueryInput(text=text_input, language_code=LANGUAGE_CODE)
    
    def build_audio_query_input(self, audio_bytes, audio_encoding=AudioEncoding.AUDIO_ENCODING_LINEAR_16, sample_rate_hertz=16000):
        """Build query input for voice/audio messages."""
        audio_config = InputAudioConfig(
            audio_encoding=audio_encoding,
            sample_rate_hertz=sample_rate_hertz
        )
        audio_input = AudioInput(config=audio_config, audio=audio_bytes)
        return QueryInput(audio=audio_input, language_code=LANGUAGE_CODE)
    
    def build_detect_intent_request(self, query_input, session_path):
        return DetectIntentRequest(session=session_path, query_input=query_input)

    def extract_response_text(self, response):
        if not response.query_result.response_messages:
            return ""
        
        else:
            return response.query_result.response_messages[0].text.text[0]
    
    