# Databricks Avatar Assistant

A cost-optimized, expression-aware conversational avatar for the Databricks platform.

## Cost Optimization

This implementation reduces costs by **70-85%** compared to the original architecture:

| Component | Original | Optimized | Savings |
|-----------|----------|-----------|---------|
| LLM | Dedicated DBRX endpoint (~$1,500/mo) | Foundation Model API (~$100/mo) | 93% |
| TTS | ElevenLabs (~$50/mo) | Edge-TTS (FREE) | 100% |
| ASR | Whisper GPU (~$300/mo) | Web Speech API (FREE) | 100% |
| Lip Sync | Wav2Lip GPU (~$400/mo) | Phoneme-based (CPU) | 100% |
| Emotion | DeepFace GPU (~$150/mo) | Text-based (CPU) | 100% |

**Estimated monthly cost: $100-280** (down from $1,500-3,500)

## Features

- Real-time voice and text conversations
- 3D animated avatar with lip-syncing
- Emotion detection and response adaptation
- Response caching for reduced API costs
- Databricks product expertise via RAG

## Quick Start

### Local Development (No Databricks costs)

```bash
# Clone and setup
cd databricks_avator

# Create environment file
cp .env.example .env
# Edit .env with your credentials (optional for local mock mode)

# Run locally
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

Visit http://localhost:3000

### Deploy to Databricks

```bash
# Set credentials
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"

# Deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh dev
```

## Project Structure

```
databricks_avator/
├── backend/                  # FastAPI backend
│   ├── main.py              # Application entry point
│   ├── avatar_orchestrator.py # Main orchestration logic
│   ├── services/
│   │   ├── llm_service.py   # Foundation Model API
│   │   ├── tts_service.py   # Edge-TTS (FREE)
│   │   ├── emotion_service.py # Text-based detection
│   │   ├── lip_sync_service.py # Phoneme-based
│   │   └── cache_service.py  # Response caching
│   └── config.py            # Configuration
├── frontend/                 # React + Three.js frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── lib/            # Hooks and utilities
│   │   └── stores/         # Zustand state
│   └── package.json
├── scripts/
│   ├── run_local.sh        # Local development
│   └── deploy.sh           # Databricks deployment
├── databricks.yml           # Asset Bundle config
└── README.md
```

## Technology Stack

### Backend (Cost-Optimized)
- **FastAPI** - Web framework
- **Edge-TTS** - FREE Microsoft TTS API
- **Transformers** - Lightweight emotion detection
- **Databricks SDK** - Foundation Model API integration

### Frontend
- **React** - UI framework
- **Three.js** - 3D avatar rendering
- **Zustand** - State management
- **Web Speech API** - FREE browser speech recognition

## Configuration

Environment variables (`.env`):

```env
# Databricks (for production)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token
DATABRICKS_LLM_ENDPOINT=databricks-meta-llama-3-1-70b-instruct

# TTS (FREE)
TTS_PROVIDER=edge-tts
TTS_VOICE=en-US-JennyNeural

# Cost Control
MAX_TOKENS_PER_RESPONSE=300
ENABLE_RESPONSE_CACHE=true
CACHE_TTL_SECONDS=3600
```

## Cost Control Features

1. **Response Caching** - Caches LLM responses to reduce API calls
2. **Token Limiting** - Limits response length (300 tokens default)
3. **Free TTS** - Edge-TTS has no usage limits
4. **Client-side ASR** - Web Speech API runs in browser (FREE)
5. **CPU-based Processing** - No GPU required for emotion/lip-sync

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /api/config` - Client configuration
- `POST /api/chat` - HTTP chat endpoint
- `WS /ws/avatar` - WebSocket for real-time interaction

## Development

```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend only
cd frontend
npm install
npm run dev
```

## License

MIT
