

import os
import json
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()


class LeadQualificationTool:
    """Qualify leads using BANT framework (Budget, Authority, Need, Timeline)"""
    
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        print("🎯 Lead Qualification Tool initialized")
    
    def analyze_qualification(self, conversation_context: str, customer_info: Dict) -> Dict:
        """
        Analyze conversation to determine BANT qualification
        
        Args:
            conversation_context: Recent conversation messages
            customer_info: Customer profile data
            
        Returns:
            BANT qualification results
        """
        
        prompt = f"""You are a sales qualification expert analyzing a conversation to determine BANT qualification.

BANT FRAMEWORK:
- Budget: Does the prospect have budget allocated or accessible?
- Authority: Are we speaking with a decision-maker or key influencer?
- Need: Is there a clear, urgent business need?
- Timeline: Is there a defined timeline for making a decision?

CUSTOMER INFORMATION:
{json.dumps(customer_info, indent=2)}

CONVERSATION CONTEXT:
{conversation_context}

YOUR TASK:
Analyze the conversation and determine qualification status for each BANT criteria.

RESPOND WITH ONLY VALID JSON:
{{
  "budget": {{
    "qualified": true/false,
    "evidence": "quote or summary from conversation",
    "notes": "additional context",
    "confidence": "high/medium/low"
  }},
  "authority": {{
    "qualified": true/false,
    "evidence": "quote or summary",
    "notes": "additional context",
    "confidence": "high/medium/low"
  }},
  "need": {{
    "qualified": true/false,
    "evidence": "quote or summary",
    "notes": "additional context",
    "confidence": "high/medium/low"
  }},
  "timeline": {{
    "qualified": true/false,
    "evidence": "quote or summary",
    "notes": "additional context",
    "confidence": "high/medium/low"
  }},
  "overall_score": "number from 0-4",
  "recommendation": "qualify/nurture/disqualify",
  "next_steps": ["suggested action 1", "suggested action 2"],
  "missing_information": ["what still needs to be discovered"]
}}
"""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            result = json.loads(response_text.strip())
            
            print(f"✅ BANT Analysis complete - Score: {result['overall_score']}/4")
            return result
            
        except Exception as e:
            print(f"❌ Qualification analysis error: {str(e)}")
            return self._get_fallback_qualification()
    
    def get_next_question(self, bant_status: Dict, conversation_history: str) -> str:
        """
        Generate next qualifying question based on BANT status
        
        Args:
            bant_status: Current BANT qualification status
            conversation_history: Recent conversation
            
        Returns:
            Next qualifying question to ask
        """
        
        # Determine what's missing
        missing = []
        if not bant_status['budget']['qualified']:
            missing.append('budget')
        if not bant_status['authority']['qualified']:
            missing.append('authority')
        if not bant_status['need']['qualified']:
            missing.append('need')
        if not bant_status['timeline']['qualified']:
            missing.append('timeline')
        
        if not missing:
            return "Great! You're qualified. Let's move forward with a proposal."
        
        # Focus on the first missing criterion
        focus = missing[0]
        
        prompt = f"""You are a skilled sales professional conducting a qualification call.

CURRENT BANT STATUS:
- Budget: {'✅ Qualified' if bant_status['budget']['qualified'] else '❌ Not yet qualified'}
- Authority: {'✅ Qualified' if bant_status['authority']['qualified'] else '❌ Not yet qualified'}
- Need: {'✅ Qualified' if bant_status['need']['qualified'] else '❌ Not yet qualified'}
- Timeline: {'✅ Qualified' if bant_status['timeline']['qualified'] else '❌ Not yet qualified'}

RECENT CONVERSATION:
{conversation_history[-500:]}

FOCUS AREA: {focus.upper()}

YOUR TASK:
Generate the next natural, conversational question to qualify the "{focus}" criterion.

GUIDELINES:
- Be conversational and professional
- Don't be too direct or salesy
- Build on the previous conversation
- One question at a time
- Keep it under 30 words

RESPOND WITH ONLY THE QUESTION (no preamble):
"""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7
            )
            
            question = response.choices[0].message.content.strip()
            return question
            
        except Exception as e:
            print(f"⚠️ Error generating question: {str(e)}")
            return self._get_fallback_question(focus)
    
    def _get_fallback_qualification(self) -> Dict:
        """Fallback qualification result"""
        return {
            "budget": {
                "qualified": False,
                "evidence": "Not enough information",
                "notes": "Need to ask about budget",
                "confidence": "low"
            },
            "authority": {
                "qualified": False,
                "evidence": "Not enough information",
                "notes": "Need to identify decision-maker",
                "confidence": "low"
            },
            "need": {
                "qualified": False,
                "evidence": "Not enough information",
                "notes": "Need to understand pain points",
                "confidence": "low"
            },
            "timeline": {
                "qualified": False,
                "evidence": "Not enough information",
                "notes": "Need to understand timeline",
                "confidence": "low"
            },
            "overall_score": 0,
            "recommendation": "nurture",
            "next_steps": ["Continue discovery", "Ask qualifying questions"],
            "missing_information": ["budget", "authority", "need", "timeline"]
        }
    
    def _get_fallback_question(self, focus: str) -> str:
        """Fallback questions for each BANT criterion"""
        questions = {
            "budget": "To help me provide the right solution, what budget range have you allocated for this initiative?",
            "authority": "Who else besides yourself will be involved in evaluating and approving this decision?",
            "need": "What specific challenges or pain points are you looking to address with this solution?",
            "timeline": "What's driving your timeline for implementing a solution?"
        }
        return questions.get(focus, "Tell me more about your requirements.")
    
    def format_qualification_report(self, bant_status: Dict) -> str:
        """Format BANT qualification results as a report"""
        
        score = bant_status['overall_score']
        recommendation = bant_status['recommendation'].upper()
        
        report = f"""
🎯 LEAD QUALIFICATION REPORT
{'='*60}
Overall BANT Score: {score}/4
Recommendation: {recommendation}

BUDGET {'✅' if bant_status['budget']['qualified'] else '❌'}
  Status: {'Qualified' if bant_status['budget']['qualified'] else 'Not Qualified'}
  Evidence: {bant_status['budget']['evidence']}
  Confidence: {bant_status['budget']['confidence'].upper()}
  Notes: {bant_status['budget']['notes']}

AUTHORITY {'✅' if bant_status['authority']['qualified'] else '❌'}
  Status: {'Qualified' if bant_status['authority']['qualified'] else 'Not Qualified'}
  Evidence: {bant_status['authority']['evidence']}
  Confidence: {bant_status['authority']['confidence'].upper()}
  Notes: {bant_status['authority']['notes']}

NEED {'✅' if bant_status['need']['qualified'] else '❌'}
  Status: {'Qualified' if bant_status['need']['qualified'] else 'Not Qualified'}
  Evidence: {bant_status['need']['evidence']}
  Confidence: {bant_status['need']['confidence'].upper()}
  Notes: {bant_status['need']['notes']}

TIMELINE {'✅' if bant_status['timeline']['qualified'] else '❌'}
  Status: {'Qualified' if bant_status['timeline']['qualified'] else 'Not Qualified'}
  Evidence: {bant_status['timeline']['evidence']}
  Confidence: {bant_status['timeline']['confidence'].upper()}
  Notes: {bant_status['timeline']['notes']}

NEXT STEPS:
"""
        
        for i, step in enumerate(bant_status.get('next_steps', []), 1):
            report += f"  {i}. {step}\n"
        
        if bant_status.get('missing_information'):
            report += "\nSTILL NEED TO QUALIFY:\n"
            for item in bant_status['missing_information']:
                report += f"  • {item.upper()}\n"
        
        report += f"\n{'='*60}\n"
        
        return report


if __name__ == "__main__":
    # Test lead qualification
    print("="*60)
    print("TESTING LEAD QUALIFICATION TOOL")
    print("="*60 + "\n")
    
    tool = LeadQualificationTool()
    
    # Sample conversation
    conversation = """
User: We're looking for a CRM solution for our sales team.
Agent: Great! Tell me about your team size and current challenges.
User: We have 20 sales reps and we're struggling with tracking leads. Our VP of Sales wants to improve our close rate.
Agent: That makes sense. What's your timeline for getting this implemented?
User: We'd like to have something in place by end of Q1. Our annual budget review allocated $50K for this.
"""
    
    customer_info = {
        "company_name": "Acme Corp",
        "industry": "Technology",
        "company_size": "100-500 employees"
    }
    
    # Analyze qualification
    print("📊 Analyzing BANT qualification...\n")
    bant_status = tool.analyze_qualification(conversation, customer_info)
    
    # Display report
    print(tool.format_qualification_report(bant_status))
    
    # Get next question
    print("\n💬 NEXT QUESTION:")
    next_q = tool.get_next_question(bant_status, conversation)
    print(f"  {next_q}")