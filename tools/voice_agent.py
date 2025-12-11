"""
Voice Agent - AI-powered voice sales calls using ElevenLabs

Simulates natural sales conversations for lead qualification
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List
from datetime import datetime

load_dotenv()


class VoiceAgent:
    """AI Voice Agent for sales calls"""
    
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        # Conversation state
        self.conversation_history = []
        self.qualification_data = {
            "budget": None,
            "authority": None,
            "need": None,
            "timeline": None
        }
        self.objections_encountered = []
        self.call_duration = 0
        
        print("📞 Voice Agent initialized")
        
        if not self.elevenlabs_api_key:
            print("⚠️  ElevenLabs API key not found - text simulation mode only")
            print("   Get your key at: https://elevenlabs.io")
    
    def start_call(self, lead_info: Dict) -> str:
        """
        Start a sales call
        
        Args:
            lead_info: Information about the lead
            
        Returns:
            Opening message
        """
        
        company_name = lead_info.get("company_name", "your company")
        contact_name = lead_info.get("contact_name", "there")
        
        opening = f"""Hi {contact_name}, this is Alex calling from SalesAI.

I'm reaching out because I noticed {company_name} {lead_info.get('personalization', 'is growing rapidly')}.

We help companies like yours {lead_info.get('value_prop', 'automate their sales process')}.

Do you have a quick minute to chat?"""
        
        self.conversation_history.append({
            "role": "agent",
            "message": opening,
            "timestamp": datetime.now().isoformat()
        })
        
        return opening
    
    def process_response(self, user_message: str, lead_info: Dict) -> str:
        """
        Process prospect's response and generate appropriate reply
        
        Args:
            user_message: What the prospect said
            lead_info: Lead information
            
        Returns:
            Agent's response
        """
        
        # Log user message
        self.conversation_history.append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Analyze response
        user_lower = user_message.lower()
        
        # Handle common objections
        if any(word in user_lower for word in ["busy", "not interested", "no time"]):
            response = self._handle_objection(user_message, "busy")
        
        elif any(word in user_lower for word in ["email", "send", "information"]):
            response = self._handle_objection(user_message, "send_email")
        
        elif any(word in user_lower for word in ["already have", "current solution", "using"]):
            response = self._handle_objection(user_message, "current_solution")
        
        elif any(word in user_lower for word in ["yes", "sure", "okay", "go ahead"]):
            # Positive response - start qualification
            response = self._ask_qualification_question()
        
        else:
            # Generate contextual response
            response = self._generate_response(user_message, lead_info)
        
        # Log agent response
        self.conversation_history.append({
            "role": "agent",
            "message": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _handle_objection(self, objection: str, objection_type: str) -> str:
        """Handle common sales objections"""
        
        self.objections_encountered.append({
            "objection": objection,
            "type": objection_type,
            "timestamp": datetime.now().isoformat()
        })
        
        responses = {
            "busy": """I completely understand. That's actually why I'm calling - 
we help companies save about 10 hours per week on their sales process.

Would a quick 5-minute call on Thursday at 2 PM work better?""",
            
            "send_email": """Happy to send you information. To make sure I send exactly what's relevant, 
quick question: what's your biggest challenge with your current sales process?

Based on that, I'll send over the specific resources that will help.""",
            
            "current_solution": """That's great that you have something in place. 
Most companies we work with started with similar tools.

Are you seeing any challenges with follow-up automation or lead scoring?

We've helped companies increase their close rate by 30% even with existing systems.""",
            
            "not_interested": """No worries at all. Just curious - is it timing, budget, 
or you're just not seeing this as a priority right now?

Understanding that helps me know if it makes sense to follow up later."""
        }
        
        return responses.get(objection_type, "I understand. What would be helpful for you?")
    
    def _ask_qualification_question(self) -> str:
        """Ask next BANT qualification question"""
        
        # Determine what to ask based on what's missing
        if self.qualification_data["need"] is None:
            return """Great! So tell me, what's your biggest challenge with your current sales process?

Is it lead management, follow-ups, or something else?"""
        
        elif self.qualification_data["timeline"] is None:
            return """That makes sense. When are you looking to have a solution in place?

Are you evaluating options now, or is this more exploratory?"""
        
        elif self.qualification_data["budget"] is None:
            return """Perfect. To make sure we're aligned, what budget range have you allocated for improving your sales process?

Most of our clients invest between $5K-$20K annually."""
        
        elif self.qualification_data["authority"] is None:
            return """Understood. Who else besides yourself would be involved in evaluating this type of solution?

I want to make sure we get everyone's input from the start."""
        
        else:
            # All qualified - book meeting
            return self._generate_meeting_request()
    
    def _generate_meeting_request(self) -> str:
        """Generate meeting booking request"""
        
        return """Based on what you've shared, I think it makes sense for you to speak with our sales specialist who can show you exactly how we'd solve your challenges.

I have Thursday at 2 PM or Friday at 10 AM available. Which works better for you?"""
    
    def _generate_response(self, user_message: str, lead_info: Dict) -> str:
        """Generate contextual response using LLM"""
        
        context = self._format_conversation_context()
        
        prompt = f"""You are an expert sales development representative (SDR) on a phone call.

LEAD INFORMATION:
Company: {lead_info.get('company_name', 'Company')}
Contact: {lead_info.get('contact_name', 'Contact')}
Industry: {lead_info.get('industry', 'Technology')}

CONVERSATION SO FAR:
{context}

PROSPECT'S LATEST MESSAGE:
{user_message}

YOUR TASK:
Respond naturally and professionally. You're trying to:
1. Build rapport
2. Understand their challenges
3. Qualify them (BANT: Budget, Authority, Need, Timeline)
4. Book a meeting if qualified

GUIDELINES:
- Keep it conversational (2-3 sentences)
- Ask one question at a time
- Be consultative, not pushy
- Show empathy and understanding
- Reference their specific situation

RESPOND WITH ONLY YOUR MESSAGE (no labels):
"""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ Error generating response: {str(e)}")
            return "Could you tell me more about that?"
    
    def _format_conversation_context(self) -> str:
        """Format conversation history for context"""
        context = ""
        for msg in self.conversation_history[-6:]:  # Last 6 messages
            role_label = "Agent" if msg["role"] == "agent" else "Prospect"
            context += f"{role_label}: {msg['message']}\n"
        return context
    
    def analyze_call_quality(self) -> Dict:
        """Analyze call quality and extract insights"""
        
        context = self._format_conversation_context()
        
        prompt = f"""Analyze this sales call and extract key information.

CONVERSATION:
{context}

YOUR TASK:
Analyze and respond with JSON:

{{
  "qualification_status": {{
    "budget": "qualified/not_qualified/unclear",
    "authority": "qualified/not_qualified/unclear",
    "need": "qualified/not_qualified/unclear",
    "timeline": "qualified/not_qualified/unclear"
  }},
  "call_quality": {{
    "rapport_building": "excellent/good/fair/poor",
    "question_quality": "excellent/good/fair/poor",
    "objection_handling": "excellent/good/fair/poor",
    "overall_score": "1-10"
  }},
  "next_steps": ["action 1", "action 2"],
  "key_insights": ["insight 1", "insight 2"],
  "recommendation": "book_meeting/nurture/disqualify"
}}
"""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(result_text.strip())
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Analysis error: {str(e)}")
            return {
                "qualification_status": self.qualification_data,
                "call_quality": {"overall_score": "5"},
                "next_steps": ["Follow up via email"],
                "recommendation": "nurture"
            }
    
    def get_call_transcript(self) -> str:
        """Get formatted call transcript"""
        
        transcript = f"""
📞 CALL TRANSCRIPT
{'='*60}
Duration: {len(self.conversation_history)} exchanges
Objections: {len(self.objections_encountered)}

"""
        
        for msg in self.conversation_history:
            role_emoji = "🤖" if msg["role"] == "agent" else "👤"
            role_label = "Agent" if msg["role"] == "agent" else "Prospect"
            
            transcript += f"\n{role_emoji} {role_label}:\n{msg['message']}\n"
        
        transcript += f"\n{'='*60}\n"
        
        return transcript
    
    def save_call_recording(self, filename: str = None) -> str:
        """Save call transcript and analysis"""
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"call_{timestamp}.json"
        
        output_dir = "output/calls"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        call_data = {
            "conversation": self.conversation_history,
            "qualification": self.qualification_data,
            "objections": self.objections_encountered,
            "analysis": self.analyze_call_quality(),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(call_data, f, indent=2)
        
        print(f"💾 Call recording saved: {filepath}")
        return filepath


if __name__ == "__main__":
    # Test voice agent
    print("="*60)
    print("TESTING VOICE AGENT")
    print("="*60 + "\n")
    
    agent = VoiceAgent()
    
    # Lead info
    lead_info = {
        "company_name": "TechCorp Inc",
        "contact_name": "Sarah Johnson",
        "industry": "B2B SaaS",
        "personalization": "recently raised Series A funding",
        "value_prop": "automate lead qualification and save 10 hours per week"
    }
    
    # Start call
    print("📞 Starting call...\n")
    opening = agent.start_call(lead_info)
    print(f"🤖 Agent: {opening}\n")
    
    # Simulate conversation
    test_responses = [
        "Yes, I have a few minutes",
        "Our biggest challenge is manual lead tracking and follow-ups",
        "We're looking to implement something within the next quarter",
        "We have a budget of around $15K for sales tools this year",
        "It would be me and our VP of Sales making the decision"
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"[Exchange {i}]")
        print(f"👤 Prospect: {response}")
        
        agent_response = agent.process_response(response, lead_info)
        print(f"🤖 Agent: {agent_response}\n")
        print("-"*60 + "\n")
    
    # Analyze call
    print("\n📊 CALL ANALYSIS")
    print("="*60)
    analysis = agent.analyze_call_quality()
    print(json.dumps(analysis, indent=2))
    
    # Save recording
    filepath = agent.save_call_recording()
    print(f"\n✅ Call saved to: {filepath}")