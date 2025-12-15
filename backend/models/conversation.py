"""
Conversation State Management
"""

from typing import List, Dict, Optional
from datetime import datetime


class ConversationState:
    """
    Manages conversation history and state for a connection
    """

    def __init__(self, connection_id: str, max_history: int = 10):
        self.connection_id = connection_id
        self.max_history = max_history
        self.history: List[Dict] = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.metadata: Dict = {}

    def add_turn(
        self,
        user_message: str,
        assistant_message: str,
        user_emotion: Optional[str] = None
    ):
        """Add a conversation turn"""
        turn = {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "user_emotion": user_emotion,
            "timestamp": datetime.now().isoformat()
        }

        self.history.append(turn)
        self.last_activity = datetime.now()

        # Keep only last N turns to control context size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_context_summary(self) -> str:
        """Get a summary of recent conversation context"""
        if not self.history:
            return "No previous conversation."

        summary_parts = []
        for turn in self.history[-3:]:
            summary_parts.append(f"User: {turn['user_message'][:100]}")
            summary_parts.append(f"Assistant: {turn['assistant_message'][:100]}")

        return "\n".join(summary_parts)

    def clear_history(self):
        """Clear conversation history"""
        self.history = []

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "connection_id": self.connection_id,
            "history_length": len(self.history),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
