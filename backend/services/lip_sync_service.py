"""
Lip Sync Service - Cost-Optimized Implementation
Uses phoneme-based viseme generation instead of GPU-intensive Wav2Lip
"""

import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


class LipSyncService:
    """
    Phoneme-based lip sync service

    Cost Optimization:
    - No GPU required - runs entirely on CPU
    - Generates visemes from text phonemes
    - Much faster than video-based lip sync
    - Perfect for 3D avatar with blend shapes
    """

    # Phoneme to viseme mapping (simplified)
    # Based on standard viseme sets for 3D animation
    PHONEME_TO_VISEME = {
        # Vowels
        'a': 'AA', 'e': 'E', 'i': 'I', 'o': 'O', 'u': 'U',
        # Consonants
        'b': 'PP', 'p': 'PP', 'm': 'PP',
        'f': 'FF', 'v': 'FF',
        'th': 'TH',
        'd': 'DD', 't': 'DD', 'n': 'DD',
        'k': 'kk', 'g': 'kk',
        's': 'SS', 'z': 'SS',
        'sh': 'CH', 'ch': 'CH', 'j': 'CH',
        'r': 'RR',
        'l': 'DD',
        'w': 'O',
        'y': 'I',
        'h': 'sil',
        ' ': 'sil',  # Silence for spaces
    }

    # Viseme blend shape names (for Three.js)
    VISEME_BLEND_SHAPES = {
        'sil': 'viseme_sil',    # Silence/neutral
        'PP': 'viseme_PP',      # p, b, m
        'FF': 'viseme_FF',      # f, v
        'TH': 'viseme_TH',      # th
        'DD': 'viseme_DD',      # t, d, n, l
        'kk': 'viseme_kk',      # k, g
        'CH': 'viseme_CH',      # sh, ch, j
        'SS': 'viseme_SS',      # s, z
        'RR': 'viseme_RR',      # r
        'AA': 'viseme_aa',      # a
        'E': 'viseme_E',        # e
        'I': 'viseme_I',        # i, y
        'O': 'viseme_O',        # o, w
        'U': 'viseme_U',        # u
    }

    def __init__(self):
        self.initialized = False

    async def initialize(self):
        """Initialize lip sync service"""
        logger.info("Lip sync service initialized (phoneme-based)")
        self.initialized = True

    async def generate_visemes(
        self,
        text: str,
        audio_duration: float = 0
    ) -> List[Dict]:
        """
        Generate viseme sequence from text

        Args:
            text: Text to generate visemes for
            audio_duration: Duration of audio in seconds (for timing)

        Returns:
            List of viseme dictionaries with timing
        """
        try:
            # Clean text
            clean_text = self._clean_text(text)

            # Generate phonemes
            phonemes = self._text_to_phonemes(clean_text)

            # Generate viseme sequence with timing
            visemes = self._phonemes_to_visemes(phonemes, audio_duration)

            logger.info(f"Generated {len(visemes)} visemes for {len(text)} chars")
            return visemes

        except Exception as e:
            logger.error(f"Error generating visemes: {str(e)}")
            return []

    def _clean_text(self, text: str) -> str:
        """Clean text for phoneme extraction"""
        # Remove special characters but keep letters and spaces
        clean = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        # Normalize whitespace
        clean = ' '.join(clean.split())
        return clean

    def _text_to_phonemes(self, text: str) -> List[str]:
        """
        Simple grapheme-to-phoneme conversion
        For production, consider using g2p-en library
        """
        phonemes = []
        i = 0

        while i < len(text):
            # Check for digraphs first
            if i < len(text) - 1:
                digraph = text[i:i+2]
                if digraph in ['th', 'sh', 'ch']:
                    phonemes.append(digraph)
                    i += 2
                    continue

            # Single character
            char = text[i]
            if char in self.PHONEME_TO_VISEME:
                phonemes.append(char)
            elif char.isalpha():
                # Default to closest vowel
                phonemes.append('a')

            i += 1

        return phonemes

    def _phonemes_to_visemes(
        self,
        phonemes: List[str],
        total_duration: float
    ) -> List[Dict]:
        """
        Convert phonemes to timed viseme sequence
        """
        if not phonemes:
            return []

        visemes = []

        # Calculate duration per phoneme
        if total_duration > 0:
            duration_per_phoneme = total_duration / len(phonemes)
        else:
            # Estimate: average speaking rate is about 10-15 phonemes per second
            duration_per_phoneme = 0.08  # 80ms per phoneme

        current_time = 0

        for phoneme in phonemes:
            viseme_code = self.PHONEME_TO_VISEME.get(phoneme, 'sil')
            blend_shape = self.VISEME_BLEND_SHAPES.get(viseme_code, 'viseme_sil')

            visemes.append({
                "start": round(current_time, 3),
                "end": round(current_time + duration_per_phoneme, 3),
                "value": viseme_code,
                "blendShape": blend_shape
            })

            current_time += duration_per_phoneme

        # Add final silence
        visemes.append({
            "start": round(current_time, 3),
            "end": round(current_time + 0.2, 3),
            "value": "sil",
            "blendShape": "viseme_sil"
        })

        return visemes

    def get_viseme_for_phoneme(self, phoneme: str) -> str:
        """Get viseme code for a specific phoneme"""
        return self.PHONEME_TO_VISEME.get(phoneme.lower(), 'sil')
