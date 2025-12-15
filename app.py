"""
Databricks Avatar Assistant - Full Featured Entry Point
FastAPI application with TTS, Emotion Detection, and LLM integration
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import json
import os
import sys
import base64
import asyncio
from pathlib import Path
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR / "static"
FRONTEND_DIST = APP_DIR / "frontend" / "dist"

# Try to import optional dependencies
TTS_AVAILABLE = False
EMOTION_AVAILABLE = False

try:
    import edge_tts
    TTS_AVAILABLE = True
    logger.info("Edge-TTS available (FREE TTS)")
except ImportError:
    logger.warning("edge-tts not available - TTS disabled")

try:
    from transformers import pipeline
    EMOTION_AVAILABLE = True
    logger.info("Transformers available for emotion detection")
except ImportError:
    logger.warning("transformers not available - emotion detection will use fallback")


# ============================================================================
# Services
# ============================================================================

class TTSService:
    """Edge-TTS Service (FREE)"""
    VOICE = "en-US-AriaNeural"

    async def synthesize(self, text: str) -> bytes:
        if not TTS_AVAILABLE:
            return b""
        try:
            import io
            communicate = edge_tts.Communicate(text, self.VOICE)
            audio_data = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])
            return audio_data.getvalue()
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""


class EmotionService:
    """Text-based emotion detection"""

    def __init__(self):
        self.classifier = None
        if EMOTION_AVAILABLE:
            try:
                self.classifier = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base",
                    device=-1,
                    top_k=1
                )
                logger.info("Emotion classifier loaded")
            except Exception as e:
                logger.warning(f"Could not load emotion model: {e}")

    def detect(self, text: str) -> Dict:
        if self.classifier:
            try:
                result = self.classifier(text[:512])
                if result and len(result) > 0:
                    pred = result[0] if isinstance(result[0], dict) else result[0][0]
                    return {"emotion": pred["label"].lower(), "confidence": pred["score"]}
            except Exception as e:
                logger.error(f"Emotion detection error: {e}")

        # Fallback rule-based detection
        text_lower = text.lower()
        if any(w in text_lower for w in ["happy", "great", "awesome", "thanks"]):
            return {"emotion": "joy", "confidence": 0.7}
        elif any(w in text_lower for w in ["angry", "frustrated", "annoying"]):
            return {"emotion": "anger", "confidence": 0.7}
        elif any(w in text_lower for w in ["sad", "disappointed", "sorry"]):
            return {"emotion": "sadness", "confidence": 0.7}
        elif any(w in text_lower for w in ["confused", "don't understand", "help"]):
            return {"emotion": "confusion", "confidence": 0.7}
        return {"emotion": "neutral", "confidence": 0.6}


class LipSyncService:
    """Phoneme-based lip sync (CPU)"""

    PHONEME_TO_VISEME = {
        'a': 'AA', 'e': 'E', 'i': 'I', 'o': 'O', 'u': 'U',
        'b': 'PP', 'p': 'PP', 'm': 'PP',
        'f': 'FF', 'v': 'FF',
        'd': 'DD', 't': 'DD', 'n': 'DD',
        'k': 'kk', 'g': 'kk',
        's': 'SS', 'z': 'SS',
        'r': 'RR', 'l': 'DD',
        ' ': 'sil',
    }

    def generate_visemes(self, text: str, duration: float = 0) -> List[Dict]:
        import re
        clean_text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        phonemes = list(clean_text)

        if not phonemes:
            return []

        duration_per = duration / len(phonemes) if duration > 0 else 0.08
        visemes = []
        current_time = 0

        for phoneme in phonemes:
            viseme = self.PHONEME_TO_VISEME.get(phoneme, 'sil')
            visemes.append({
                "start": round(current_time, 3),
                "end": round(current_time + duration_per, 3),
                "value": viseme
            })
            current_time += duration_per

        return visemes


class ResponseCache:
    """Simple response cache to reduce API calls"""

    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Dict]:
        import time
        entry = self.cache.get(key.lower().strip())
        if entry and time.time() - entry["time"] < self.ttl:
            return entry["value"]
        return None

    def set(self, key: str, value: Dict):
        import time
        self.cache[key.lower().strip()] = {"value": value, "time": time.time()}


class LLMService:
    """LLM Service with Databricks Foundation Model API support"""

    def __init__(self):
        self.host = os.getenv("DATABRICKS_HOST", "")
        self.token = os.getenv("DATABRICKS_TOKEN", "")
        self.endpoint = os.getenv("DATABRICKS_LLM_ENDPOINT", "databricks-meta-llama-3-1-70b-instruct")

    async def generate(self, user_message: str, emotion: str = "neutral") -> str:
        # Try Databricks API if configured
        if self.host and self.token:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.host}/serving-endpoints/{self.endpoint}/invocations",
                        headers={
                            "Authorization": f"Bearer {self.token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "messages": [
                                {"role": "system", "content": f"You are DataBot, a helpful Databricks assistant. User emotion: {emotion}. Be concise."},
                                {"role": "user", "content": user_message}
                            ],
                            "max_tokens": 300,
                            "temperature": 0.7
                        }
                    )
                    if response.status_code == 200:
                        return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LLM API error: {e}")

        # Fallback to mock responses
        return self._mock_response(user_message)

    def _mock_response(self, text: str) -> str:
        text_lower = text.lower()
        if "databricks" in text_lower:
            return "Databricks is a unified analytics platform that combines data engineering, data science, and business analytics. It provides collaborative notebooks, automated cluster management, and seamless integrations with popular ML frameworks."
        elif "spark" in text_lower:
            return "Apache Spark is the core compute engine in Databricks. It provides distributed processing for big data workloads, supporting batch and streaming data processing, machine learning, and SQL analytics at scale."
        elif "delta" in text_lower:
            return "Delta Lake is an open-source storage layer that brings ACID transactions to Apache Spark. It provides time travel, schema enforcement, and unified batch/streaming processing for reliable data lakes."
        elif "unity catalog" in text_lower:
            return "Unity Catalog is Databricks' unified governance solution for data and AI. It provides centralized access control, data lineage, and discovery across all your data assets."
        elif "mlflow" in text_lower:
            return "MLflow is an open-source platform for managing the ML lifecycle. It includes experiment tracking, model registry, and deployment capabilities, all integrated into Databricks."
        else:
            return f"Thank you for your question about '{text}'. As your Databricks assistant, I'm here to help with questions about the Databricks platform, Apache Spark, Delta Lake, Unity Catalog, MLflow, and more!"


# ============================================================================
# Application Setup
# ============================================================================

# Initialize services
tts_service = TTSService()
emotion_service = EmotionService()
lip_sync_service = LipSyncService()
response_cache = ResponseCache()
llm_service = LLMService()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        import uuid
        conn_id = str(uuid.uuid4())[:8]
        self.connections[conn_id] = websocket
        return conn_id

    async def disconnect(self, conn_id: str):
        self.connections.pop(conn_id, None)

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    logger.info("Starting Databricks Avatar Assistant...")
    logger.info(f"TTS Available: {TTS_AVAILABLE}")
    logger.info(f"Emotion Detection Available: {EMOTION_AVAILABLE}")
    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Databricks Avatar Assistant API",
    description="Cost-optimized conversational avatar for Databricks",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ============================================================================
# Routes
# ============================================================================

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    # Return empty favicon if not found
    return Response(content=b"", media_type="image/x-icon")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Databricks Avatar Assistant",
        "version": "1.0.0",
        "features": {
            "tts": TTS_AVAILABLE,
            "emotion_detection": EMOTION_AVAILABLE,
            "lip_sync": True,
            "caching": True
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "healthy": True,
        "services": {
            "tts": TTS_AVAILABLE,
            "emotion": EMOTION_AVAILABLE,
            "llm": True,
            "lip_sync": True,
            "cache": True
        }
    }


@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Chat endpoint with full features"""
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    include_audio = request.get("include_audio", False)

    # Check cache
    cached = response_cache.get(text)
    if cached:
        return {**cached, "cached": True}

    # Detect emotion
    emotion_data = emotion_service.detect(text)

    # Generate response
    response_text = await llm_service.generate(text, emotion_data["emotion"])

    result = {
        "response": response_text,
        "emotion": emotion_data["emotion"],
        "confidence": emotion_data["confidence"],
        "cached": False
    }

    # Generate audio if requested
    if include_audio and TTS_AVAILABLE:
        audio_data = await tts_service.synthesize(response_text)
        if audio_data:
            result["audio"] = base64.b64encode(audio_data).decode("utf-8")
            result["audio_format"] = "mp3"

    # Cache result
    response_cache.set(text, result)

    return result


@app.websocket("/ws/avatar")
async def avatar_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time avatar interaction"""
    await websocket.accept()
    conn_id = await manager.connect(websocket)
    logger.info(f"WebSocket connected: {conn_id}")

    try:
        # Send greeting
        await websocket.send_json({
            "type": "greeting",
            "message": "Hello! I'm your Databricks assistant. How can I help you today?",
            "connection_id": conn_id,
            "features": {
                "tts": TTS_AVAILABLE,
                "emotion": EMOTION_AVAILABLE
            }
        })

        while True:
            message = await websocket.receive()

            if "text" in message:
                data = json.loads(message["text"])

                if data.get("type") in ["text_input", "transcription"]:
                    user_text = data.get("text", "")
                    logger.info(f"[{conn_id}] Received: {user_text}")

                    # Detect emotion
                    emotion_data = emotion_service.detect(user_text)
                    await websocket.send_json({
                        "type": "emotion_detected",
                        "emotion": emotion_data["emotion"],
                        "confidence": emotion_data["confidence"]
                    })

                    # Check cache
                    cached = response_cache.get(user_text)
                    if cached:
                        response_text = cached.get("response", "")
                    else:
                        # Generate response
                        response_text = await llm_service.generate(user_text, emotion_data["emotion"])
                        response_cache.set(user_text, {"response": response_text})

                    # Send text response
                    await websocket.send_json({
                        "type": "response_text",
                        "text": response_text
                    })

                    # Generate and send TTS audio
                    if TTS_AVAILABLE:
                        audio_data = await tts_service.synthesize(response_text)
                        if audio_data:
                            # Generate lip sync data
                            word_count = len(response_text.split())
                            duration = (word_count / 150) * 60
                            visemes = lip_sync_service.generate_visemes(response_text, duration)

                            await websocket.send_json({
                                "type": "lip_sync_data",
                                "visemes": visemes,
                                "duration": duration
                            })

                            # Send audio
                            await websocket.send_json({
                                "type": "audio_data",
                                "audio": base64.b64encode(audio_data).decode("utf-8"),
                                "format": "mp3"
                            })

                    # Send completion
                    await websocket.send_json({
                        "type": "response_complete"
                    })

                elif data.get("type") == "control":
                    command = data.get("command")
                    if command == "ping":
                        await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conn_id}")
    except Exception as e:
        logger.error(f"WebSocket error [{conn_id}]: {e}")
    finally:
        await manager.disconnect(conn_id)


# Serve frontend if available
if FRONTEND_DIST.exists():
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        if full_path.startswith(("api/", "ws/", "health", "docs", "static")):
            raise HTTPException(status_code=404)

        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))

        raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
