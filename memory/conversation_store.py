"""
Conversation Store - Manages multi-session conversations
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class Message:
    """Represents a single message in a conversation"""
    
    def __init__(self, role: str, content: str):
        self.role = role  # 'user' or 'agent'
        self.content = content
        self.timestamp = datetime.now().isoformat()
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        msg = cls(data['role'], data['content'])
        msg.timestamp = data['timestamp']
        msg.metadata = data.get('metadata', {})
        return msg


class Conversation:
    """Represents a conversation session"""
    
    def __init__(self, conversation_id: str, customer_id: str, deal_id: str):
        self.conversation_id = conversation_id
        self.customer_id = customer_id
        self.deal_id = deal_id
        self.started_at = datetime.now().isoformat()
        self.ended_at = None
        self.messages: List[Message] = []
        self.summary = ""
        self.key_points = []
        self.action_items = []
        self.active = True
    
    def add_message(self, role: str, content: str) -> Message:
        """Add a message to conversation"""
        message = Message(role, content)
        self.messages.append(message)
        return message
    
    def end_conversation(self, summary: str = ""):
        """Mark conversation as ended"""
        self.active = False
        self.ended_at = datetime.now().isoformat()
        if summary:
            self.summary = summary
    
    def to_dict(self) -> Dict:
        return {
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "deal_id": self.deal_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "messages": [m.to_dict() for m in self.messages],
            "summary": self.summary,
            "key_points": self.key_points,
            "action_items": self.action_items,
            "active": self.active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Conversation':
        conv = cls(data['conversation_id'], data['customer_id'], data['deal_id'])
        conv.started_at = data['started_at']
        conv.ended_at = data.get('ended_at')
        conv.messages = [Message.from_dict(m) for m in data['messages']]
        conv.summary = data.get('summary', '')
        conv.key_points = data.get('key_points', [])
        conv.action_items = data.get('action_items', [])
        conv.active = data.get('active', True)
        return conv


class ConversationStore:
    """Manages conversation history across sessions"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.conversations_file = os.path.join(data_dir, "conversations.json")
        self.conversations: Dict[str, Conversation] = {}
        self.active_conversations: Dict[str, str] = {}  # customer_id -> conversation_id
        self._load_conversations()
    
    def _load_conversations(self):
        """Load conversations from disk"""
        if os.path.exists(self.conversations_file):
            try:
                with open(self.conversations_file, 'r') as f:
                    data = json.load(f)
                    for conv_data in data.get('conversations', []):
                        conv = Conversation.from_dict(conv_data)
                        self.conversations[conv.conversation_id] = conv
                        if conv.active:
                            self.active_conversations[conv.customer_id] = conv.conversation_id
                print(f"✅ Loaded {len(self.conversations)} conversations")
            except Exception as e:
                print(f"⚠️ Error loading conversations: {str(e)}")
        else:
            print("📝 Creating new conversation store")
            self._save_conversations()
    
    def _save_conversations(self):
        """Save conversations to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        data = {
            "conversations": [c.to_dict() for c in self.conversations.values()],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.conversations_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def start_conversation(self, customer_id: str, deal_id: str) -> Conversation:
        """Start a new conversation"""
        # End any active conversation for this customer
        if customer_id in self.active_conversations:
            old_conv_id = self.active_conversations[customer_id]
            self.end_conversation(old_conv_id)
        
        # Create new conversation
        conv_id = f"CONV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        conversation = Conversation(conv_id, customer_id, deal_id)
        
        self.conversations[conv_id] = conversation
        self.active_conversations[customer_id] = conv_id
        self._save_conversations()
        
        print(f"✅ Started conversation {conv_id}")
        return conversation
    
    def get_active_conversation(self, customer_id: str) -> Optional[Conversation]:
        """Get active conversation for customer"""
        conv_id = self.active_conversations.get(customer_id)
        if conv_id:
            return self.conversations.get(conv_id)
        return None
    
    def get_or_start_conversation(self, customer_id: str, deal_id: str) -> Conversation:
        """Get active conversation or start new one"""
        conv = self.get_active_conversation(customer_id)
        if conv:
            return conv
        return self.start_conversation(customer_id, deal_id)
    
    def add_message(self, customer_id: str, deal_id: str, role: str, content: str) -> Message:
        """Add a message to active conversation"""
        conv = self.get_or_start_conversation(customer_id, deal_id)
        message = conv.add_message(role, content)
        self._save_conversations()
        return message
    
    def end_conversation(self, conversation_id: str, summary: str = ""):
        """End a conversation"""
        conv = self.conversations.get(conversation_id)
        if conv:
            conv.end_conversation(summary)
            if conv.customer_id in self.active_conversations:
                del self.active_conversations[conv.customer_id]
            self._save_conversations()
            print(f"✅ Ended conversation {conversation_id}")
    
    def get_conversation_history(self, customer_id: str) -> List[Conversation]:
        """Get all conversations for a customer"""
        return [
            c for c in self.conversations.values()
            if c.customer_id == customer_id
        ]
    
    def get_recent_context(self, customer_id: str, num_messages: int = 10) -> List[Message]:
        """Get recent messages for context"""
        conv = self.get_active_conversation(customer_id)
        if conv:
            return conv.messages[-num_messages:]
        
        # Get from last conversation if no active one
        history = self.get_conversation_history(customer_id)
        if history:
            last_conv = max(history, key=lambda c: c.started_at)
            return last_conv.messages[-num_messages:]
        
        return []
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """Get formatted conversation summary"""
        conv = self.conversations.get(conversation_id)
        if not conv:
            return f"❌ Conversation {conversation_id} not found"
        
        started = datetime.fromisoformat(conv.started_at).strftime('%Y-%m-%d %H:%M')
        status = "🟢 Active" if conv.active else "⚪ Ended"
        
        summary = f"""
💬 CONVERSATION: {conv.conversation_id}
{'='*60}
Customer: {conv.customer_id}
Deal: {conv.deal_id}
Status: {status}
Started: {started}
Messages: {len(conv.messages)}

"""
        
        if conv.key_points:
            summary += "KEY POINTS:\n"
            for point in conv.key_points:
                summary += f"  • {point}\n"
            summary += "\n"
        
        if conv.action_items:
            summary += "ACTION ITEMS:\n"
            for item in conv.action_items:
                summary += f"  ☐ {item}\n"
            summary += "\n"
        
        if conv.summary:
            summary += f"SUMMARY:\n{conv.summary}\n\n"
        
        summary += f"{'='*60}\n"
        
        return summary
    
    def export_conversation(self, conversation_id: str, format: str = "text") -> str:
        """Export conversation transcript"""
        conv = self.conversations.get(conversation_id)
        if not conv:
            return ""
        
        if format == "text":
            transcript = f"Conversation {conv.conversation_id}\n"
            transcript += f"Started: {conv.started_at}\n"
            transcript += "="*60 + "\n\n"
            
            for msg in conv.messages:
                timestamp = datetime.fromisoformat(msg.timestamp).strftime('%H:%M:%S')
                role_label = "👤 User" if msg.role == "user" else "🤖 Agent"
                transcript += f"[{timestamp}] {role_label}:\n{msg.content}\n\n"
            
            return transcript
        
        elif format == "json":
            return json.dumps(conv.to_dict(), indent=2)
        
        return ""


if __name__ == "__main__":
    # Test conversation store
    print("="*60)
    print("TESTING CONVERSATION STORE")
    print("="*60 + "\n")
    
    store = ConversationStore()
    
    customer_id = "CUST-001"
    deal_id = "DEAL-001"
    
    # Start conversation
    conv = store.start_conversation(customer_id, deal_id)
    
    # Add messages
    store.add_message(customer_id, deal_id, "user", "Hi, I'm interested in your product")
    store.add_message(customer_id, deal_id, "agent", "Great! Tell me about your needs")
    store.add_message(customer_id, deal_id, "user", "We need better automation tools")
    store.add_message(customer_id, deal_id, "agent", "Perfect! Let me ask a few questions...")
    
    # Add key points
    conv.key_points.append("Customer needs automation")
    conv.key_points.append("Budget range: $50K-$100K")
    conv.key_points.append("Decision timeline: Q1 2025")
    
    # Add action items
    conv.action_items.append("Schedule demo for next week")
    conv.action_items.append("Send product brochure")
    
    store._save_conversations()
    
    # Display summary
    print(store.get_conversation_summary(conv.conversation_id))
    
    # Export transcript
    print("\n" + "="*60)
    print("CONVERSATION TRANSCRIPT")
    print("="*60 + "\n")
    print(store.export_conversation(conv.conversation_id))