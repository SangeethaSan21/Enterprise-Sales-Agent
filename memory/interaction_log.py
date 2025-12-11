"""
Interaction Log - Track all customer interactions across sessions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class InteractionType(Enum):
    """Types of customer interactions"""
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    DEMO = "demo"
    PROPOSAL_SENT = "proposal_sent"
    PROPOSAL_VIEWED = "proposal_viewed"
    CONTRACT_SENT = "contract_sent"
    CONTRACT_SIGNED = "contract_signed"
    CHAT = "chat"
    NOTE = "note"


class Interaction:
    """Represents a single interaction with a customer"""
    
    def __init__(self, customer_id: str, deal_id: str, interaction_type: InteractionType):
        self.interaction_id = f"INT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.customer_id = customer_id
        self.deal_id = deal_id
        self.interaction_type = interaction_type
        self.timestamp = datetime.now().isoformat()
        self.summary = ""
        self.details = ""
        self.participants = []
        self.next_steps = []
        self.sentiment = "neutral"  # positive, neutral, negative
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "interaction_id": self.interaction_id,
            "customer_id": self.customer_id,
            "deal_id": self.deal_id,
            "interaction_type": self.interaction_type.value,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "details": self.details,
            "participants": self.participants,
            "next_steps": self.next_steps,
            "sentiment": self.sentiment,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Interaction':
        """Create from dictionary"""
        interaction = cls(
            data['customer_id'],
            data['deal_id'],
            InteractionType(data['interaction_type'])
        )
        interaction.interaction_id = data['interaction_id']
        interaction.timestamp = data['timestamp']
        interaction.summary = data['summary']
        interaction.details = data['details']
        interaction.participants = data['participants']
        interaction.next_steps = data['next_steps']
        interaction.sentiment = data['sentiment']
        interaction.metadata = data['metadata']
        return interaction


class InteractionLog:
    """Manages interaction history"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.log_file = os.path.join(data_dir, "interactions.json")
        self.interactions: List[Interaction] = []
        self._load_interactions()
    
    def _load_interactions(self):
        """Load interactions from disk"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    for interaction_data in data.get('interactions', []):
                        interaction = Interaction.from_dict(interaction_data)
                        self.interactions.append(interaction)
                print(f"✅ Loaded {len(self.interactions)} interactions")
            except Exception as e:
                print(f"⚠️ Error loading interactions: {str(e)}")
        else:
            print("📝 Creating new interaction log")
            self._save_interactions()
    
    def _save_interactions(self):
        """Save interactions to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        data = {
            "interactions": [i.to_dict() for i in self.interactions],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_interaction(
        self,
        customer_id: str,
        deal_id: str,
        interaction_type: InteractionType,
        summary: str,
        details: str = "",
        sentiment: str = "neutral"
    ) -> Interaction:
        """Log a new interaction"""
        interaction = Interaction(customer_id, deal_id, interaction_type)
        interaction.summary = summary
        interaction.details = details
        interaction.sentiment = sentiment
        
        self.interactions.append(interaction)
        self._save_interactions()
        
        emoji = self._get_interaction_emoji(interaction_type)
        print(f"✅ {emoji} Logged {interaction_type.value}: {summary}")
        
        return interaction
    
    def log_email(self, customer_id: str, deal_id: str, subject: str, body: str = ""):
        """Log an email interaction"""
        return self.log_interaction(
            customer_id,
            deal_id,
            InteractionType.EMAIL,
            f"Email: {subject}",
            body
        )
    
    def log_call(self, customer_id: str, deal_id: str, summary: str, duration_minutes: int = 0):
        """Log a call interaction"""
        interaction = self.log_interaction(
            customer_id,
            deal_id,
            InteractionType.CALL,
            summary
        )
        interaction.metadata['duration_minutes'] = duration_minutes
        self._save_interactions()
        return interaction
    
    def log_meeting(self, customer_id: str, deal_id: str, summary: str, participants: List[str]):
        """Log a meeting interaction"""
        interaction = self.log_interaction(
            customer_id,
            deal_id,
            InteractionType.MEETING,
            summary
        )
        interaction.participants = participants
        self._save_interactions()
        return interaction
    
    def log_proposal_sent(self, customer_id: str, deal_id: str, proposal_name: str):
        """Log proposal sent"""
        return self.log_interaction(
            customer_id,
            deal_id,
            InteractionType.PROPOSAL_SENT,
            f"Sent proposal: {proposal_name}"
        )
    
    def log_chat_message(self, customer_id: str, deal_id: str, message: str):
        """Log a chat message"""
        return self.log_interaction(
            customer_id,
            deal_id,
            InteractionType.CHAT,
            message[:100]  # Summary is first 100 chars
        )
    
    def get_customer_interactions(self, customer_id: str) -> List[Interaction]:
        """Get all interactions for a customer"""
        return [i for i in self.interactions if i.customer_id == customer_id]
    
    def get_deal_interactions(self, deal_id: str) -> List[Interaction]:
        """Get all interactions for a deal"""
        return [i for i in self.interactions if i.deal_id == deal_id]
    
    def get_recent_interactions(self, customer_id: str, limit: int = 10) -> List[Interaction]:
        """Get recent interactions for a customer"""
        customer_interactions = self.get_customer_interactions(customer_id)
        return sorted(customer_interactions, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_interaction_timeline(self, customer_id: str) -> str:
        """Get formatted timeline of interactions"""
        interactions = self.get_customer_interactions(customer_id)
        
        if not interactions:
            return "No interactions recorded"
        
        # Sort by timestamp
        interactions.sort(key=lambda x: x.timestamp)
        
        timeline = f"\n📅 INTERACTION TIMELINE\n{'='*60}\n"
        
        for interaction in interactions:
            emoji = self._get_interaction_emoji(interaction.interaction_type)
            timestamp = datetime.fromisoformat(interaction.timestamp).strftime('%Y-%m-%d %H:%M')
            sentiment_emoji = self._get_sentiment_emoji(interaction.sentiment)
            
            timeline += f"\n{emoji} {timestamp} - {interaction.interaction_type.value.upper()}\n"
            timeline += f"   {interaction.summary}\n"
            if interaction.sentiment != "neutral":
                timeline += f"   Sentiment: {sentiment_emoji} {interaction.sentiment}\n"
            if interaction.next_steps:
                timeline += f"   Next: {', '.join(interaction.next_steps[:2])}\n"
        
        timeline += f"\n{'='*60}\n"
        timeline += f"Total Interactions: {len(interactions)}\n"
        
        return timeline
    
    def get_interaction_stats(self, customer_id: str) -> Dict:
        """Get interaction statistics"""
        interactions = self.get_customer_interactions(customer_id)
        
        stats = {
            "total": len(interactions),
            "by_type": {},
            "by_sentiment": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            },
            "latest": None
        }
        
        for interaction in interactions:
            # Count by type
            type_key = interaction.interaction_type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            
            # Count by sentiment
            stats["by_sentiment"][interaction.sentiment] += 1
        
        # Get latest interaction
        if interactions:
            latest = max(interactions, key=lambda x: x.timestamp)
            stats["latest"] = {
                "type": latest.interaction_type.value,
                "summary": latest.summary,
                "timestamp": latest.timestamp
            }
        
        return stats
    
    def _get_interaction_emoji(self, interaction_type: InteractionType) -> str:
        """Get emoji for interaction type"""
        emojis = {
            InteractionType.EMAIL: "📧",
            InteractionType.CALL: "📞",
            InteractionType.MEETING: "🤝",
            InteractionType.DEMO: "🖥️",
            InteractionType.PROPOSAL_SENT: "📄",
            InteractionType.PROPOSAL_VIEWED: "👀",
            InteractionType.CONTRACT_SENT: "📝",
            InteractionType.CONTRACT_SIGNED: "✍️",
            InteractionType.CHAT: "💬",
            InteractionType.NOTE: "📌"
        }
        return emojis.get(interaction_type, "📋")
    
    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment"""
        emojis = {
            "positive": "😊",
            "neutral": "😐",
            "negative": "😟"
        }
        return emojis.get(sentiment, "😐")


if __name__ == "__main__":
    # Test interaction log
    print("="*60)
    print("TESTING INTERACTION LOG")
    print("="*60 + "\n")
    
    log = InteractionLog()
    
    customer_id = "CUST-001"
    deal_id = "DEAL-001"
    
    # Log various interactions
    log.log_email(customer_id, deal_id, "Introduction to our solutions")
    log.log_call(customer_id, deal_id, "Discovery call - discussed pain points", 45)
    log.log_meeting(customer_id, deal_id, "Product demo", ["John Smith", "Sarah Johnson"])
    log.log_proposal_sent(customer_id, deal_id, "Enterprise Package Proposal")
    
    # Get timeline
    print(log.get_interaction_timeline(customer_id))
    
    # Get stats
    stats = log.get_interaction_stats(customer_id)
    print(f"\n📊 STATISTICS")
    print(f"Total Interactions: {stats['total']}")
    print(f"By Type: {stats['by_type']}")
    print(f"Sentiment: {stats['by_sentiment']}")
    
    if stats['latest']:
        print(f"\nLatest: {stats['latest']['type']} - {stats['latest']['summary']}")