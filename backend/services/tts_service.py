"""
Text-to-Speech Service - Cost-Optimized Implementation
Uses Edge-TTS (FREE Microsoft API) instead of paid services like ElevenLabs
"""

import logging
import io
from typing import Optional
import edge_tts

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service using Edge-TTS (FREE)

    Cost Optimization:
    - Edge-TTS is completely free (uses Microsoft Edge's TTS API)
    - High quality neural voices
    - No API key required
    - No usage limits

    Available voices: https://github.com/rany2/edge-tts
    """

    # High-quality voice options
    VOICES = {
        "female_us": "en-US-JennyNeural",
        "female_uk": "en-GB-SoniaNeural",
        "male_us": "en-US-GuyNeural",
        "male_uk": "en-GB-RyanNeural",
        "female_friendly": "en-US-AriaNeural",
        "male_professional": "en-US-DavisNeural"
    }

    def __init__(self, provider: str = "edge-tts", voice: Optional[str] = None):
        self.provider = provider
        self.voice = voice or self.VOICES["female_friendly"]
        self.initialized = False

    async def initialize(self):
        """Initialize TTS service"""
        logger.info(f"Initializing TTS service with voice: {self.voice}")
        self.initialized = True

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> dict:
        """
        Synthesize speech from text using Edge-TTS (FREE)

        Args:
            text: Text to synthesize
            voice: Voice to use (optional, defaults to configured voice)
            rate: Speech rate adjustment (e.g., "+10%", "-10%")
            pitch: Pitch adjustment (e.g., "+5Hz", "-5Hz")

        Returns:
            dict with 'audio' (bytes) and 'duration' (estimated)
        """
        try:
            selected_voice = voice or self.voice

            # Create Edge-TTS communicate object
            communicate = edge_tts.Communicate(
                text=text,
                voice=selected_voice,
                rate=rate,
                pitch=pitch
            )

            # Collect audio data
            audio_data = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])

            audio_bytes = audio_data.getvalue()

            # Estimate duration (rough calculation based on text length)
            # Average speaking rate is about 150 words per minute
            word_count = len(text.split())
            estimated_duration = (word_count / 150) * 60  # in seconds

            logger.info(f"Generated {len(audio_bytes)} bytes of audio for {word_count} words")

            return {
                "audio": audio_bytes,
                "duration": estimated_duration,
                "voice": selected_voice,
                "format": "mp3"
            }

        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            # Return empty audio on error
            return {
                "audio": b"",
                "duration": 0,
                "error": str(e)
            }

    async def get_available_voices(self) -> list:
        """Get list of available voices"""
        try:
            voices = await edge_tts.list_voices()
            return [
                {
                    "name": v["ShortName"],
                    "gender": v["Gender"],
                    "locale": v["Locale"]
                }
                for v in voices
                if v["Locale"].startswith("en-")
            ]
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            return []

    def set_voice(self, voice_key: str):
        """Set voice by key (e.g., 'female_us', 'male_uk')"""
        if voice_key in self.VOICES:
            self.voice = self.VOICES[voice_key]
            logger.info(f"Voice changed to: {self.voice}")
        else:
            logger.warning(f"Unknown voice key: {voice_key}")
