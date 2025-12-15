"""
LLM Service - Cost-Optimized Implementation
Uses Databricks Foundation Model APIs (pay-per-token) instead of dedicated endpoints
"""

import logging
import os
from typing import List, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with Databricks Foundation Model APIs

    Cost Optimization:
    - Uses pay-per-token pricing instead of dedicated GPU endpoints
    - Limits max tokens per response
    - Supports fallback to local/mock mode for development
    """

    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.databricks_host = os.getenv("DATABRICKS_HOST", "")
        self.databricks_token = os.getenv("DATABRICKS_TOKEN", "")

        # System prompt for Databricks assistant
        self.system_prompt = """You are DataBot, a helpful and friendly AI assistant for Databricks.
You help users with questions about Databricks products, features, and best practices.

Key responsibilities:
- Answer questions about Databricks platform, tools, and services
- Provide code examples and best practices
- Explain technical concepts clearly
- Be empathetic and adjust your tone based on the user's emotional state
- Keep responses concise but thorough

Current user emotion: {emotion}

Be helpful, accurate, and friendly. Keep responses under 200 words for conversational flow."""

    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        detected_emotion: str,
        context: str = ""
    ) -> dict:
        """
        Generate response using Databricks Foundation Model API

        Args:
            user_message: Current user message
            conversation_history: Previous conversation turns
            detected_emotion: Detected user emotion

        Returns:
            dict with 'response' key
        """
        try:
            # If no Databricks credentials, use mock mode
            if not self.databricks_host or not self.databricks_token:
                logger.warning("No Databricks credentials - using mock mode")
                return self._mock_response(user_message, detected_emotion)

            # Prepare system message
            system_content = self.system_prompt.format(emotion=detected_emotion)

            # Build messages
            messages = [
                {"role": "system", "content": system_content}
            ]

            # Add conversation history (last 3 turns for cost efficiency)
            for turn in conversation_history[-3:]:
                messages.append({"role": "user", "content": turn["user_message"]})
                messages.append({"role": "assistant", "content": turn["assistant_message"]})

            # Add current message
            messages.append({"role": "user", "content": user_message})

            # Query Foundation Model API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.databricks_host}/serving-endpoints/{self.endpoint_name}/invocations",
                    headers={
                        "Authorization": f"Bearer {self.databricks_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": messages,
                        "max_tokens": 300,  # Limit for cost control
                        "temperature": 0.7
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result["choices"][0]["message"]["content"]

                    logger.info(f"LLM response generated: {len(response_text)} chars")

                    return {
                        "response": response_text,
                        "model": self.endpoint_name,
                        "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                    }
                else:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return self._mock_response(user_message, detected_emotion)

        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return self._mock_response(user_message, detected_emotion)

    def _mock_response(self, user_message: str, emotion: str) -> dict:
        """Generate mock response for development/fallback"""
        responses = {
            "databricks": "Databricks is a unified analytics platform that combines data engineering, data science, and business analytics. It provides collaborative notebooks, automated cluster management, and integrations with popular ML frameworks.",
            "spark": "Apache Spark is the core compute engine in Databricks. It provides distributed processing for big data workloads, supporting batch and streaming data processing, machine learning, and SQL analytics.",
            "delta": "Delta Lake is an open-source storage layer that brings ACID transactions to Apache Spark and big data workloads. It provides features like time travel, schema enforcement, and unified batch/streaming processing.",
            "default": f"I understand you're asking about '{user_message}'. As your Databricks assistant, I'm here to help! In production mode, I'll provide detailed answers about Databricks features, best practices, and technical guidance."
        }

        # Simple keyword matching for mock responses
        user_lower = user_message.lower()
        for keyword, response in responses.items():
            if keyword in user_lower:
                return {"response": response, "model": "mock", "tokens_used": 0}

        return {"response": responses["default"], "model": "mock", "tokens_used": 0}
