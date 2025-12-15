"""
Databricks Avatar Assistant - Cost-Optimized Backend
FastAPI application with WebSocket support for real-time avatar interaction
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import json
import os
from pathlib import Path

from avatar_orchestrator import AvatarOrchestrator
from utils.websocket_manager import WebSocketManager
from config import settings

# Get the directory containing this file
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown"""
    logger.info("Starting Databricks Avatar Assistant (Cost-Optimized)...")

    # Initialize orchestrator
    app.state.orchestrator = AvatarOrchestrator()
    await app.state.orchestrator.initialize()

    # Initialize WebSocket manager
    app.state.ws_manager = WebSocketManager()

    logger.info("Application started successfully")
    yield

    # Cleanup
    logger.info("Shutting down...")
    await app.state.orchestrator.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Databricks Avatar Assistant API",
    description="Cost-optimized expression-aware conversational avatar for Databricks",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Databricks Avatar Assistant",
        "version": "1.0.0",
        "cost_mode": "optimized"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    orchestrator: AvatarOrchestrator = app.state.orchestrator
    health_status = await orchestrator.check_health()

    return JSONResponse(
        status_code=200 if health_status["healthy"] else 503,
        content=health_status
    )


@app.get("/api/config")
async def get_config():
    """Get client configuration"""
    return {
        "tts_provider": settings.TTS_PROVIDER,
        "websocket_url": "/ws/avatar",
        "features": {
            "voice_input": True,
            "text_input": True,
            "emotion_detection": True,
            "lip_sync": True
        }
    }


@app.websocket("/ws/avatar")
async def avatar_websocket(websocket: WebSocket):
    """
    Main WebSocket endpoint for avatar interaction

    Client sends:
    - Text messages (JSON: {"type": "text_input", "text": "..."})
    - Control messages (JSON: {"type": "control", "command": "..."})

    Server sends:
    - Text responses
    - Audio data (base64 encoded)
    - Viseme data (lip-sync)
    - Emotion indicators
    - Status updates
    """
    await websocket.accept()

    orchestrator: AvatarOrchestrator = app.state.orchestrator
    ws_manager: WebSocketManager = app.state.ws_manager

    # Register connection
    connection_id = await ws_manager.register(websocket)
    logger.info(f"New WebSocket connection: {connection_id}")

    try:
        # Send initial greeting
        await websocket.send_json({
            "type": "greeting",
            "message": "Hello! I'm your Databricks assistant. How can I help you today?",
            "connection_id": connection_id
        })

        # Main message loop
        while True:
            # Receive message from client
            message = await websocket.receive()

            if "text" in message:
                # JSON message
                data = json.loads(message["text"])

                if data.get("type") == "text_input":
                    # Text input
                    await orchestrator.process_text_input(
                        text=data["text"],
                        websocket=websocket,
                        connection_id=connection_id
                    )

                elif data.get("type") == "transcription":
                    # Transcription from client-side Web Speech API
                    await orchestrator.process_text_input(
                        text=data["text"],
                        websocket=websocket,
                        connection_id=connection_id
                    )

                elif data.get("type") == "control":
                    # Control message
                    await handle_control_message(data, websocket, connection_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"Error in WebSocket connection {connection_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "An error occurred. Please try again."
            })
        except Exception:
            pass

    finally:
        # Unregister connection
        await ws_manager.unregister(connection_id)


async def handle_control_message(data: dict, websocket: WebSocket, connection_id: str):
    """Handle control messages from client"""
    command = data.get("command")

    if command == "stop_speaking":
        await websocket.send_json({
            "type": "control_response",
            "command": "stop_speaking",
            "status": "stopped"
        })

    elif command == "ping":
        await websocket.send_json({
            "type": "control_response",
            "command": "pong",
            "status": "ok"
        })

    elif command == "get_status":
        await websocket.send_json({
            "type": "status",
            "connection_id": connection_id,
            "services": {
                "llm": "ready",
                "tts": "ready",
                "emotion": "ready"
            }
        })


@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """
    HTTP endpoint for text-only chat (alternative to WebSocket)
    Useful for testing and simple integrations
    """
    orchestrator: AvatarOrchestrator = app.state.orchestrator

    text = request.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    include_audio = request.get("include_audio", False)

    response = await orchestrator.process_text_query(text, include_audio=include_audio)
    return response


# Serve frontend static files if available
if FRONTEND_DIST.exists():
    # Mount assets directory
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA for all non-API routes"""
        # Skip API routes
        if full_path.startswith(("api/", "ws/", "health", "docs", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve the requested file
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        # Fallback to index.html for SPA routing
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))

        raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
