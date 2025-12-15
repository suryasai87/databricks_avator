"""
Avatar Orchestrator - Cost-Optimized Implementation
Coordinates all avatar services with minimal resource usage
"""

import asyncio
import logging
import base64
from typing import Optional, Dict, List
from fastapi import WebSocket

from services.llm_service import LLMService
from services.tts_service import TTSService
from services.emotion_service import EmotionService
from services.lip_sync_service import LipSyncService
from services.cache_service import ResponseCache
from models.conversation import ConversationState
from config import settings

logger = logging.getLogger(__name__)


class AvatarOrchestrator:
    """
    Main orchestrator that coordinates all avatar services
    Cost-optimized: Uses caching, lightweight models, and efficient APIs
    """

    def __init__(self):
        self.llm_service: Optional[LLMService] = None
        self.tts_service: Optional[TTSService] = None
        self.emotion_service: Optional[EmotionService] = None
        self.lip_sync_service: Optional[LipSyncService] = None
        self.cache: Optional[ResponseCache] = None

        # Conversation states per connection
        self.conversations: Dict[str, ConversationState] = {}

    async def initialize(self):
        """Initialize all services"""
        logger.info("Initializing Avatar Orchestrator (Cost-Optimized)...")

        # Initialize cache first (reduces API calls)
        if settings.ENABLE_RESPONSE_CACHE:
            self.cache = ResponseCache(ttl_seconds=settings.CACHE_TTL_SECONDS)
            logger.info("Response cache enabled")

        # Initialize TTS (Edge-TTS - FREE)
        self.tts_service = TTSService(provider=settings.TTS_PROVIDER)
        await self.tts_service.initialize()
        logger.info(f"TTS service initialized: {settings.TTS_PROVIDER}")

        # Initialize Emotion Detection (lightweight, CPU-based)
        self.emotion_service = EmotionService()
        await self.emotion_service.initialize()
        logger.info("Emotion service initialized (text-based)")

        # Initialize Lip Sync (phoneme-based, CPU)
        self.lip_sync_service = LipSyncService()
        await self.lip_sync_service.initialize()
        logger.info("Lip sync service initialized")

        # Initialize LLM Service (Foundation Model API - pay-per-token)
        self.llm_service = LLMService(
            endpoint_name=settings.DATABRICKS_LLM_ENDPOINT
        )
        logger.info(f"LLM service initialized: {settings.DATABRICKS_LLM_ENDPOINT}")

        logger.info("All services initialized successfully")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        if self.cache:
            self.cache.clear()

    async def check_health(self) -> dict:
        """Check health of all services"""
        return {
            "healthy": True,
            "cost_mode": "optimized",
            "services": {
                "llm": self.llm_service is not None,
                "tts": self.tts_service is not None,
                "emotion": self.emotion_service is not None,
                "lip_sync": self.lip_sync_service is not None,
                "cache": self.cache is not None
            }
        }

    async def process_text_input(
        self,
        text: str,
        websocket: WebSocket,
        connection_id: str
    ):
        """
        Process text input from user

        Cost-optimized pipeline:
        1. Check cache first
        2. Detect emotion (text-based, lightweight)
        3. Get LLM response (Foundation Model API)
        4. Generate TTS audio (Edge-TTS - FREE)
        5. Generate lip sync data (phoneme-based)
        6. Stream response to client
        """
        try:
            # Get or create conversation state
            conversation = self.conversations.get(connection_id)
            if not conversation:
                conversation = ConversationState(connection_id=connection_id)
                self.conversations[connection_id] = conversation

            # Step 1: Check cache for similar queries
            cache_key = text.lower().strip()
            cached_response = None
            if self.cache:
                cached_response = self.cache.get(cache_key)

            # Step 2: Detect emotion from text (lightweight)
            logger.info(f"[{connection_id}] Detecting emotion...")
            emotion_data = await self.emotion_service.detect_from_text(text)

            await websocket.send_json({
                "type": "emotion_detected",
                "emotion": emotion_data["emotion"],
                "confidence": emotion_data["confidence"]
            })

            # Step 3: Generate or retrieve response
            if cached_response:
                logger.info(f"[{connection_id}] Using cached response")
                response_text = cached_response["text"]
            else:
                logger.info(f"[{connection_id}] Generating LLM response...")
                llm_response = await self.llm_service.generate_response(
                    user_message=text,
                    conversation_history=conversation.history,
                    detected_emotion=emotion_data["emotion"]
                )
                response_text = llm_response["response"]

                # Cache the response
                if self.cache:
                    self.cache.set(cache_key, {"text": response_text})

            logger.info(f"[{connection_id}] Response: {response_text[:100]}...")

            # Update conversation history
            conversation.add_turn(
                user_message=text,
                assistant_message=response_text,
                user_emotion=emotion_data["emotion"]
            )

            # Step 4: Send text response immediately
            await websocket.send_json({
                "type": "response_text",
                "text": response_text
            })

            # Step 5: Generate TTS audio (FREE with Edge-TTS)
            logger.info(f"[{connection_id}] Generating speech...")
            tts_result = await self.tts_service.synthesize(text=response_text)

            # Step 6: Generate lip sync data (phoneme-based)
            logger.info(f"[{connection_id}] Generating lip sync...")
            visemes = await self.lip_sync_service.generate_visemes(
                text=response_text,
                audio_duration=tts_result.get("duration", 0)
            )

            # Send lip sync data
            await websocket.send_json({
                "type": "lip_sync_data",
                "visemes": visemes,
                "duration": tts_result.get("duration", 0)
            })

            # Step 7: Send audio data (base64 encoded)
            audio_base64 = base64.b64encode(tts_result["audio"]).decode("utf-8")
            await websocket.send_json({
                "type": "audio_data",
                "audio": audio_base64,
                "format": "mp3"
            })

            # Send completion message
            await websocket.send_json({
                "type": "response_complete"
            })

        except Exception as e:
            logger.error(f"[{connection_id}] Error processing text: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": "Sorry, I encountered an error processing your request."
            })

    async def process_text_query(self, text: str, include_audio: bool = False) -> dict:
        """
        Simple text query without streaming (HTTP endpoint)
        """
        try:
            # Detect emotion
            emotion_data = await self.emotion_service.detect_from_text(text)

            # Check cache
            cache_key = text.lower().strip()
            cached = self.cache.get(cache_key) if self.cache else None

            if cached:
                response_text = cached["text"]
            else:
                # Generate response
                llm_response = await self.llm_service.generate_response(
                    user_message=text,
                    conversation_history=[],
                    detected_emotion=emotion_data["emotion"]
                )
                response_text = llm_response["response"]

                # Cache it
                if self.cache:
                    self.cache.set(cache_key, {"text": response_text})

            result = {
                "response": response_text,
                "emotion": emotion_data["emotion"],
                "cached": cached is not None
            }

            # Optionally include audio
            if include_audio:
                tts_result = await self.tts_service.synthesize(text=response_text)
                result["audio"] = base64.b64encode(tts_result["audio"]).decode("utf-8")
                result["audio_format"] = "mp3"

            return result

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error processing your request.",
                "error": str(e)
            }
