"""
ICP Builder - Conversational Ideal Customer Profile Creator

Guides users through defining their perfect customer with precision
"""

import json
import os
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()


class ICPBuilder:
    """Build Ideal Customer Profile through conversation"""
    
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        
        # ICP structure
        self.icp = {
            "company_characteristics": {
                "industry": None,
                "sub_vertical": None,
                "company_size": None,
                "revenue_range": None,
                "growth_stage": None,
                "geography": None,
                "tech_stack": [],
                "business_model": None
            },
            "buyer_persona": {
                "job_titles": [],
                "seniority_level": None,
                "department": None,
                "pain_points": [],
                "buying_behavior": {}
            },
            "engagement_signals": {
                "intent_signals": [],
                "timing_indicators": []
            },
            "completed": False
        }
        
        # Track what we've collected
        self.collection_progress = {
            "company_characteristics": False,
            "buyer_persona": False,
            "engagement_signals": False
        }
        
        print("🎯 ICP Builder initialized")
    
    def start_conversation(self) -> str:
        """Start ICP building conversation"""
        return """👋 Welcome to ICP Builder!

I'll help you define your Ideal Customer Profile (ICP) - the perfect companies 
and decision-makers you want to target.

This takes about 5-7 minutes. I'll ask about:
1. Company characteristics (industry, size, etc.)
2. Buyer persona (who makes decisions)
3. Engagement signals (when to reach out)

Let's start simple: What industry are you targeting?

Examples: B2B SaaS, E-commerce, Manufacturing, Healthcare, Financial Services"""
    
    def process_message(self, user_message: str, conversation_history: str) -> str:
        """
        Process user message and guide ICP building
        
        Args:
            user_message: User's response
            conversation_history: Recent conversation
            
        Returns:
            Next question or summary
        """
        
        # Extract information and update ICP
        self._extract_icp_data(user_message, conversation_history)
        
        # Check if complete
        if self._is_complete():
            self.icp["completed"] = True
            return self._generate_icp_summary()
        
        # Ask next question
        return self._get_next_question(conversation_history)
    
    def _extract_icp_data(self, user_message: str, context: str):
        """Extract ICP information from conversation"""
        
        prompt = f"""You are analyzing a conversation to extract Ideal Customer Profile data.

CONVERSATION CONTEXT:
{context}

USER'S LATEST MESSAGE:
{user_message}

YOUR TASK:
Extract any ICP-related information and respond with JSON.

RESPOND WITH ONLY VALID JSON:
{{
  "company_characteristics": {{
    "industry": "B2B SaaS" or null,
    "sub_vertical": "Marketing automation" or null,
    "company_size": "50-200 employees" or null,
    "revenue_range": "$5M-$20M" or null,
    "growth_stage": "Series A" or null,
    "geography": "United States" or null,
    "tech_stack": ["Salesforce", "HubSpot"] or [],
    "business_model": "Subscription" or null
  }},
  "buyer_persona": {{
    "job_titles": ["VP Sales", "CRO"] or [],
    "seniority_level": "Director+" or null,
    "department": "Sales" or null,
    "pain_points": ["Manual lead tracking"] or [],
    "buying_behavior": {{"decision_maker": true}}
  }},
  "engagement_signals": {{
    "intent_signals": ["Hiring sales team"] or [],
    "timing_indicators": ["Recent funding"] or []
  }}
}}

Only fill in fields that were mentioned. Use null for unmentioned fields.
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
            
            extracted = json.loads(result_text.strip())
            
            # Update ICP with extracted data
            for category, data in extracted.items():
                if category in self.icp:
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if value is not None:
                                if isinstance(self.icp[category].get(key), list):
                                    # Append to lists
                                    if isinstance(value, list):
                                        self.icp[category][key].extend(value)
                                    else:
                                        self.icp[category][key].append(value)
                                else:
                                    self.icp[category][key] = value
            
        except Exception as e:
            print(f"⚠️ Extraction error: {str(e)}")
    
    def _get_next_question(self, context: str) -> str:
        """Generate next question based on what's missing"""
        
        # Check what's missing
        missing = []
        
        cc = self.icp["company_characteristics"]
        if not cc["industry"]:
            missing.append("industry")
        elif not cc["company_size"]:
            missing.append("company_size")
        elif not cc["revenue_range"]:
            missing.append("revenue_range")
        elif not cc["geography"]:
            missing.append("geography")
        elif not self.collection_progress["company_characteristics"]:
            self.collection_progress["company_characteristics"] = True
            missing.append("buyer_persona_start")
        
        bp = self.icp["buyer_persona"]
        if self.collection_progress["company_characteristics"] and not bp["job_titles"]:
            missing.append("job_titles")
        elif bp["job_titles"] and not bp["pain_points"]:
            missing.append("pain_points")
        elif bp["pain_points"] and not self.collection_progress["buyer_persona"]:
            self.collection_progress["buyer_persona"] = True
            missing.append("engagement_signals_start")
        
        es = self.icp["engagement_signals"]
        if self.collection_progress["buyer_persona"] and not es["intent_signals"]:
            missing.append("intent_signals")
        
        if not missing:
            return self._generate_icp_summary()
        
        # Generate question for first missing item
        focus = missing[0]
        
        questions = {
            "industry": "Great! Now, what **company size** are you targeting?\n\nExamples: 10-50 employees, 50-200, 200-1000, 1000+",
            "company_size": "Perfect! What's the typical **revenue range** of your target companies?\n\nExamples: $1M-$5M, $5M-$20M, $20M-$100M",
            "revenue_range": "Excellent! Which **geographic regions** do you want to focus on?\n\nExamples: United States, North America, Europe, Global",
            "geography": "Got it! Any specific **technology stack** or tools they should be using?\n\nExamples: Salesforce, HubSpot, Shopify, AWS",
            "buyer_persona_start": "Perfect! Now let's define your **buyer persona**.\n\nWhat **job titles** typically make buying decisions for your product?\n\nExamples: VP Sales, CRO, CEO, Head of Marketing",
            "job_titles": "Great! What are the **top 2-3 pain points** these decision-makers face?\n\nBe specific about the problems your product solves.",
            "pain_points": "Excellent! Almost done.\n\nWhat **signals** tell you a company is ready to buy?\n\nExamples: Recent funding, hiring for specific roles, using competitor products",
            "engagement_signals_start": "What **signals** indicate a company is ready to buy?\n\nExamples: Recent funding, hiring sales team, tech stack changes",
            "intent_signals": "Perfect! Any specific **timing indicators**?\n\nExamples: Fiscal year alignment, seasonal trends, industry events"
        }
        
        return questions.get(focus, "Tell me more about your ideal customer.")
    
    def _is_complete(self) -> bool:
        """Check if ICP building is complete"""
        cc = self.icp["company_characteristics"]
        bp = self.icp["buyer_persona"]
        
        return (
            cc["industry"] is not None and
            cc["company_size"] is not None and
            cc["geography"] is not None and
            len(bp["job_titles"]) > 0 and
            len(bp["pain_points"]) > 0
        )
    
    def _generate_icp_summary(self) -> str:
        """Generate ICP summary"""
        
        cc = self.icp["company_characteristics"]
        bp = self.icp["buyer_persona"]
        es = self.icp["engagement_signals"]
        
        # Calculate estimated market size
        market_size = self._estimate_market_size()
        
        summary = f"""
✅ Your Ideal Customer Profile is Complete!

{'='*60}
🏢 COMPANY PROFILE
{'='*60}
Industry: {cc['industry'] or 'Not specified'}
Sub-vertical: {cc['sub_vertical'] or 'Not specified'}
Company Size: {cc['company_size'] or 'Not specified'}
Revenue Range: {cc['revenue_range'] or 'Not specified'}
Growth Stage: {cc['growth_stage'] or 'Not specified'}
Geography: {cc['geography'] or 'Not specified'}
Tech Stack: {', '.join(cc['tech_stack']) if cc['tech_stack'] else 'Not specified'}
Business Model: {cc['business_model'] or 'Not specified'}

{'='*60}
👤 BUYER PERSONA
{'='*60}
Job Titles: {', '.join(bp['job_titles']) if bp['job_titles'] else 'Not specified'}
Seniority: {bp['seniority_level'] or 'Not specified'}
Department: {bp['department'] or 'Not specified'}

Pain Points:
"""
        
        for i, pain in enumerate(bp['pain_points'], 1):
            summary += f"  {i}. {pain}\n"
        
        summary += f"""
{'='*60}
🎯 ENGAGEMENT SIGNALS
{'='*60}
"""
        
        if es['intent_signals']:
            summary += "Intent Signals:\n"
            for signal in es['intent_signals']:
                summary += f"  • {signal}\n"
        
        if es['timing_indicators']:
            summary += "\nTiming Indicators:\n"
            for indicator in es['timing_indicators']:
                summary += f"  • {indicator}\n"
        
        summary += f"""
{'='*60}
📊 MARKET INSIGHTS
{'='*60}
Estimated Market Size: {market_size['estimate']}
Quality Assessment: {market_size['quality']}
Recommendation: {market_size['recommendation']}

{'='*60}

🎉 Your ICP is ready! I can now:
1. Discover leads matching this profile
2. Generate personalized outreach
3. Qualify prospects automatically

Ready to start discovering leads?
"""
        
        return summary
    
    def _estimate_market_size(self) -> Dict:
        """Estimate market size based on ICP"""
        
        # Simple estimation logic
        cc = self.icp["company_characteristics"]
        
        # Estimate based on specificity
        specificity_score = 0
        if cc["industry"]: specificity_score += 1
        if cc["company_size"]: specificity_score += 1
        if cc["revenue_range"]: specificity_score += 1
        if cc["geography"]: specificity_score += 1
        if cc["tech_stack"]: specificity_score += len(cc["tech_stack"])
        
        if specificity_score <= 3:
            return {
                "estimate": "10M+ companies (Very Broad)",
                "quality": "⚠️ May be too broad",
                "recommendation": "Consider adding more specific criteria"
            }
        elif specificity_score <= 6:
            return {
                "estimate": "100K-1M companies (Broad)",
                "quality": "✅ Good starting point",
                "recommendation": "Well-defined ICP with good market size"
            }
        else:
            return {
                "estimate": "10K-100K companies (Focused)",
                "quality": "✅ Highly targeted",
                "recommendation": "Excellent focus - easier to personalize outreach"
            }
    
    def get_icp(self) -> Dict:
        """Get current ICP"""
        return self.icp
    
    def save_icp(self, filename: str = None) -> str:
        """Save ICP to file"""
        if not filename:
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"icp_{timestamp}.json"
        
        output_dir = "output/icps"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.icp, f, indent=2)
        
        print(f"💾 ICP saved to: {filepath}")
        return filepath


if __name__ == "__main__":
    # Test ICP Builder
    print("="*60)
    print("TESTING ICP BUILDER")
    print("="*60 + "\n")
    
    builder = ICPBuilder()
    
    # Simulate conversation
    print("🤖 Agent:", builder.start_conversation())
    print()
    
    test_messages = [
        ("B2B SaaS companies", "Industry"),
        ("50-200 employees", "Size"),
        ("$5M to $20M annual revenue", "Revenue"),
        ("United States and Canada", "Geography"),
        ("VP of Sales, CRO, Head of Sales", "Titles"),
        ("Manual lead tracking and low pipeline visibility", "Pain points"),
        ("Companies recently funded or hiring sales teams", "Signals")
    ]
    
    context = ""
    for msg, stage in test_messages:
        print(f"[{stage}]")
        print(f"👤 User: {msg}")
        context += f"User: {msg}\n"
        
        response = builder.process_message(msg, context)
        print(f"🤖 Agent: {response}\n")
        print("-"*60 + "\n")
        
        context += f"Agent: {response}\n"
        
        if builder.icp["completed"]:
            break
    
    # Save ICP
    filepath = builder.save_icp()
    print(f"\n✅ ICP saved to: {filepath}")