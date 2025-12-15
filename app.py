"""
Databricks Avatar Assistant - Minimal Entry Point
Simple FastAPI application for Databricks Apps
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Databricks Avatar Assistant API",
    description="Cost-optimized conversational avatar for Databricks",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "healthy": True,
        "services": {
            "api": True
        }
    }


@app.post("/api/chat")
async def chat_endpoint(request: dict):
    """Chat endpoint"""
    text = request.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    # Simple mock responses based on keywords
    text_lower = text.lower()
    if "databricks" in text_lower:
        response = "Databricks is a unified analytics platform that combines data engineering, data science, and business analytics."
    elif "spark" in text_lower:
        response = "Apache Spark is the core compute engine in Databricks, providing distributed processing for big data workloads."
    elif "delta" in text_lower:
        response = "Delta Lake is an open-source storage layer that brings ACID transactions to Apache Spark and big data workloads."
    else:
        response = f"Thank you for your question about '{text}'. As your Databricks assistant, I'm here to help with questions about the Databricks platform!"

    return {
        "response": response,
        "emotion": "neutral"
    }


@app.websocket("/ws/avatar")
async def avatar_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time avatar interaction"""
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    try:
        # Send greeting
        await websocket.send_json({
            "type": "greeting",
            "message": "Hello! I'm your Databricks assistant. How can I help you today?"
        })

        while True:
            message = await websocket.receive()

            if "text" in message:
                data = json.loads(message["text"])

                if data.get("type") in ["text_input", "transcription"]:
                    user_text = data.get("text", "")
                    logger.info(f"Received: {user_text}")

                    # Generate response
                    text_lower = user_text.lower()
                    if "databricks" in text_lower:
                        response = "Databricks is a unified analytics platform that combines data engineering, data science, and business analytics."
                    elif "spark" in text_lower:
                        response = "Apache Spark is the core compute engine in Databricks."
                    else:
                        response = f"Thank you for asking about '{user_text}'. I'm here to help with Databricks questions!"

                    # Send emotion
                    await websocket.send_json({
                        "type": "emotion_detected",
                        "emotion": "neutral",
                        "confidence": 0.8
                    })

                    # Send response
                    await websocket.send_json({
                        "type": "response_text",
                        "text": response
                    })

                    # Send completion
                    await websocket.send_json({
                        "type": "response_complete"
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
