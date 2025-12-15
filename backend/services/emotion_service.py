"""
Emotion Detection Service - Cost-Optimized Implementation
Uses lightweight text-based emotion detection instead of GPU-intensive video analysis
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EmotionService:
    """
    Lightweight emotion detection from text

    Cost Optimization:
    - Uses text-based analysis instead of video/audio analysis
    - Runs on CPU with minimal resources
    - Uses efficient transformer model (distilroberta)
    """

    def __init__(self):
        self.classifier = None
        self.initialized = False

    async def initialize(self):
        """Initialize emotion classifier"""
        try:
            from transformers import pipeline

            # Use a small, efficient emotion model
            # This runs on CPU and is very fast
            self.classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=-1,  # CPU
                top_k=1
            )
            self.initialized = True
            logger.info("Emotion classifier initialized (CPU mode)")

        except ImportError:
            logger.warning("Transformers not available - using rule-based fallback")
            self.initialized = True

        except Exception as e:
            logger.warning(f"Could not load emotion model: {e} - using fallback")
            self.initialized = True

    async def detect_from_text(self, text: str) -> Dict:
        """
        Detect emotion from text

        Args:
            text: Input text to analyze

        Returns:
            dict with 'emotion' and 'confidence'
        """
        try:
            if self.classifier:
                # Use transformer model
                result = self.classifier(text[:512])  # Limit input length

                if result and len(result) > 0:
                    # Handle nested list structure
                    prediction = result[0] if isinstance(result[0], dict) else result[0][0]

                    return {
                        "emotion": prediction["label"].lower(),
                        "confidence": prediction["score"]
                    }

            # Fallback to rule-based detection
            return self._rule_based_detection(text)

        except Exception as e:
            logger.error(f"Error detecting emotion: {str(e)}")
            return {"emotion": "neutral", "confidence": 0.5}

    def _rule_based_detection(self, text: str) -> Dict:
        """
        Simple rule-based emotion detection fallback
        """
        text_lower = text.lower()

        # Emotion keywords
        emotion_keywords = {
            "joy": ["happy", "great", "awesome", "love", "excited", "wonderful", "amazing", "thanks", "thank you"],
            "anger": ["angry", "frustrated", "annoying", "hate", "terrible", "worst", "stupid"],
            "sadness": ["sad", "disappointed", "sorry", "unfortunately", "failed", "problem"],
            "fear": ["worried", "scared", "afraid", "nervous", "anxious", "concern"],
            "surprise": ["wow", "amazing", "incredible", "unexpected", "really", "seriously"],
            "confusion": ["confused", "don't understand", "unclear", "what", "how", "why", "help"]
        }

        # Check for emotion keywords
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return {"emotion": emotion, "confidence": 0.7}

        # Default to neutral
        return {"emotion": "neutral", "confidence": 0.6}

    def get_response_tone(self, emotion: str) -> str:
        """
        Get recommended response tone based on detected emotion
        """
        tones = {
            "joy": "Match their positive energy with enthusiasm",
            "anger": "Be calm, patient, and solution-focused",
            "sadness": "Be supportive and empathetic",
            "fear": "Be reassuring and provide clear guidance",
            "surprise": "Acknowledge their reaction and provide context",
            "confusion": "Be extra clear with step-by-step explanations",
            "neutral": "Maintain professional, friendly tone"
        }
        return tones.get(emotion, tones["neutral"])
