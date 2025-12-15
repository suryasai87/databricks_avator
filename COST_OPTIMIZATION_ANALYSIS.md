# Databricks Avatar Assistant - Cost Optimization Analysis

## Executive Summary

This document outlines cost optimization strategies for deploying the Expression-Aware Conversational Avatar on Databricks while maintaining production quality.

**Estimated Monthly Savings: 70-85%** compared to the original architecture.

---

## Cost Comparison

### Original Architecture (High Cost)

| Component | Technology | Estimated Monthly Cost |
|-----------|-----------|----------------------|
| LLM | DBRX on Model Serving | $800-2000 |
| TTS | ElevenLabs API | $22-99 |
| ASR | Whisper Large (GPU) | $200-400 |
| Lip Sync | Wav2Lip (GPU) | $300-500 |
| Emotion Detection | DeepFace (GPU) | $100-200 |
| Vector Search | Dedicated Endpoint | $100-200 |
| Databricks App | Compute | $50-100 |
| **Total** | | **$1,572-3,499/mo** |

### Optimized Architecture (Cost-Effective)

| Component | Technology | Estimated Monthly Cost |
|-----------|-----------|----------------------|
| LLM | Foundation Model APIs (pay-per-token) | $50-150 |
| TTS | Kokoro/Edge-TTS (open-source/free) | $0 |
| ASR | Whisper.cpp (tiny) or Web Speech API | $0-20 |
| Lip Sync | Rhubarb + Three.js (CPU-based) | $0 |
| Emotion Detection | Text-based (transformers) | $0-10 |
| Vector Search | Serverless or self-hosted | $20-50 |
| Databricks App | Compute (optimized) | $30-50 |
| **Total** | | **$100-280/mo** |

---

## Detailed Optimization Strategies

### 1. LLM Service (70-90% Savings)

**Problem**: DBRX model serving requires dedicated GPU endpoints that run continuously.

**Solution**: Use Databricks Foundation Model APIs or External APIs

```python
# Cost-effective LLM approach
from databricks.sdk import WorkspaceClient

class CostEffectiveLLMService:
    """
    Uses Foundation Model APIs (pay-per-token) instead of dedicated endpoints
    """
    def __init__(self):
        self.client = WorkspaceClient()
        # Use Foundation Model API - pay per token
        self.model = "databricks-meta-llama-3-1-70b-instruct"
        # Or even cheaper: "databricks-meta-llama-3-1-8b-instruct"

    async def generate_response(self, messages: list) -> str:
        response = self.client.serving_endpoints.query(
            name="databricks-meta-llama-3-1-70b-instruct",  # Foundation Model
            messages=messages,
            max_tokens=300,  # Limit tokens to control cost
            temperature=0.7
        )
        return response.choices[0].message.content
```

**Alternative**: Use Claude API for complex queries, smaller local model for simple ones.

### 2. Text-to-Speech (100% Savings)

**Problem**: ElevenLabs charges per character ($0.30/1000 chars on starter plan).

**Solution**: Use open-source alternatives

**Option A: Kokoro TTS (Recommended)**
- High quality, open-source
- Runs on CPU
- No API costs

**Option B: Edge-TTS (Free Microsoft API)**
- High quality voices
- Free tier available
- Python: `edge-tts` package

```python
# edge_tts_service.py
import edge_tts
import asyncio

class EdgeTTSService:
    """Free Microsoft Edge TTS - no API costs"""

    VOICE = "en-US-JennyNeural"  # High quality female voice

    async def synthesize(self, text: str) -> bytes:
        communicate = edge_tts.Communicate(text, self.VOICE)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
```

### 3. Speech Recognition (80% Savings)

**Problem**: Whisper Large requires GPU and significant compute.

**Solution**: Multi-tier approach

1. **Primary**: Browser's Web Speech API (free, no server cost)
2. **Fallback**: Whisper.cpp with tiny/base model (CPU-efficient)

```typescript
// Browser-side speech recognition (FREE)
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;

recognition.onresult = (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript;
    sendToServer(transcript);
};
```

### 4. Lip Sync (90% Savings)

**Problem**: Wav2Lip requires GPU for real-time video synthesis.

**Solution**: Use Rhubarb Lip Sync + Three.js blend shapes

- Rhubarb extracts phonemes (runs on CPU)
- Three.js animates pre-rigged blend shapes
- All rendering happens client-side

```python
# rhubarb_lip_sync.py
import subprocess
import json

class RhubarbLipSync:
    """CPU-based lip sync using Rhubarb"""

    def generate_visemes(self, audio_path: str, text: str) -> list:
        # Run Rhubarb (CPU-based, fast)
        result = subprocess.run([
            'rhubarb',
            '-f', 'json',
            '-d', text,
            audio_path
        ], capture_output=True, text=True)

        data = json.loads(result.stdout)
        return data['mouthCues']  # Returns viseme timings
```

### 5. Emotion Detection (90% Savings)

**Problem**: DeepFace runs multiple GPU models for video analysis.

**Solution**: Text-based emotion detection only

```python
# text_emotion_service.py
from transformers import pipeline

class TextEmotionService:
    """Lightweight text-based emotion detection"""

    def __init__(self):
        # Small, fast model
        self.classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            device=-1  # CPU
        )

    def detect(self, text: str) -> dict:
        result = self.classifier(text)[0]
        return {
            "emotion": result["label"],
            "confidence": result["score"]
        }
```

### 6. Vector Search (50% Savings)

**Problem**: Dedicated Vector Search endpoint has minimum costs.

**Solution**: Use serverless or embedding caching

```python
# Optimize vector search usage
class OptimizedVectorSearch:
    def __init__(self):
        self.cache = {}  # Simple cache for common queries

    async def search(self, query: str, top_k: int = 3):
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Perform search
        results = await self._do_search(query, top_k)

        # Cache results
        self.cache[cache_key] = results
        return results
```

---

## Optimized Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Web Speech   │  │  Three.js    │  │   Audio Player   │   │
│  │ API (FREE)   │  │  Avatar      │  │   (TTS output)   │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 DATABRICKS APP (FastAPI)                     │
│                   (Serverless/Scale-to-zero)                 │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Edge-TTS   │  │  Rhubarb     │  │ Text Emotion     │   │
│  │   (FREE)     │  │  Lip Sync    │  │ (CPU model)      │   │
│  │              │  │  (CPU)       │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABRICKS PLATFORM SERVICES                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌───────────────────────────┐    │
│  │ Foundation Model API │  │ Vector Search (Serverless)│    │
│  │ (Pay-per-token)      │  │                           │    │
│  │ Llama 3.1 8B/70B    │  │                           │    │
│  └──────────────────────┘  └───────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: MVP (Lowest Cost)
- [ ] Edge-TTS for speech synthesis
- [ ] Web Speech API for recognition
- [ ] Foundation Model API for LLM
- [ ] Text-only emotion detection
- [ ] Simple phoneme-based lip sync

### Phase 2: Enhanced (Add as needed)
- [ ] Rhubarb for better lip sync
- [ ] Whisper.cpp fallback for ASR
- [ ] Response caching layer
- [ ] Vector Search integration

### Phase 3: Production Polish
- [ ] Advanced avatar animations
- [ ] Analytics and monitoring
- [ ] A/B testing framework
- [ ] Performance optimization

---

## Quick Start Commands

```bash
# Install cost-effective dependencies
pip install edge-tts transformers fastapi uvicorn

# Test Edge-TTS
python -c "import edge_tts; print('Edge-TTS ready')"

# Run locally (no Databricks cost during development)
uvicorn backend.main:app --reload
```

---

## Summary

By using this optimized architecture:

1. **LLM**: Pay-per-token instead of dedicated GPU → **80% savings**
2. **TTS**: Edge-TTS (free) instead of ElevenLabs → **100% savings**
3. **ASR**: Web Speech API (free) with Whisper fallback → **90% savings**
4. **Lip Sync**: Rhubarb (CPU) instead of Wav2Lip (GPU) → **90% savings**
5. **Emotion**: Text-based instead of video analysis → **90% savings**

**Total estimated savings: $1,400-3,200/month**
