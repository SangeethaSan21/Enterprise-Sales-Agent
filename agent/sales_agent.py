"""
Enterprise Sales Agent - Main Orchestrator

Manages the entire sales process from lead to close
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from dotenv import load_dotenv
from typing import Dict, Optional

from pipeline.stages import PipelineStage, StageMetadata
from tools.crm_tool import CRMTool
from tools.lead_qualification import LeadQualificationTool
from tools.proposal_generator import ProposalGenerator

load_dotenv()


class SalesAgent:
    """Enterprise Sales Agent - Manages full sales cycle"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("🤖 INITIALIZING ENTERPRISE SALES AGENT")
        print("="*60 + "\n")
        
        # Initialize LLM
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        
        # Initialize tools
        self.crm = CRMTool()
        self.qualifier = LeadQualificationTool()
        self.proposal_gen = ProposalGenerator()
        
        # Current session state
        self.current_customer_id: Optional[str] = None
        self.current_deal_id: Optional[str] = None
        self.current_stage: PipelineStage = PipelineStage.LEAD
        
        print("✅ Sales Agent ready!\n")
    
    def start_conversation(self, company_name: str, contact_name: str = "", 
                          contact_email: str = "") -> str:
        """Start a new sales conversation"""
        
        # Check if customer exists
        existing = self.crm.customers.find_customer_by_company(company_name)
        
        if existing:
            print(f"👋 Welcome back, {company_name}!")
            self.current_customer_id = existing.customer_id
            
            # Get active deals
            deals = self.crm.pipeline.get_deals_by_customer(existing.customer_id)
            active_deals = [d for d in deals if d.stage not in [PipelineStage.CLOSED_WON, PipelineStage.CLOSED_LOST]]
            
            if active_deals:
                self.current_deal_id = active_deals[0].deal_id
                self.current_stage = active_deals[0].stage
                return self._generate_returning_customer_greeting(existing, active_deals[0])
            else:
                # Create new deal for existing customer
                deal = self.crm.pipeline.create_deal(existing.customer_id, company_name)
                self.current_deal_id = deal.deal_id
                self.current_stage = PipelineStage.LEAD
        else:
            # New customer
            result = self.crm.create_customer_with_deal(company_name, contact_name, contact_email)
            self.current_customer_id = result['customer_id']
            self.current_deal_id = result['deal_id']
            self.current_stage = PipelineStage.LEAD
        
        # Start conversation in CRM
        self.crm.conversations.start_conversation(self.current_customer_id, self.current_deal_id)
        
        return self._generate_welcome_message(company_name, contact_name)
    
    def chat(self, user_message: str) -> str:
        """
        Main conversation handler
        
        Args:
            user_message: User's message
            
        Returns:
            Agent's response
        """
        if not self.current_customer_id or not self.current_deal_id:
            return "❌ No active conversation. Please start with a company name."
        
        # Log message
        self.crm.conversations.add_message(
            self.current_customer_id,
            self.current_deal_id,
            "user",
            user_message
        )
        
        # Get conversation context
        context = self._get_conversation_context()
        
        # Route based on current stage
        if self.current_stage == PipelineStage.LEAD:
            response = self._handle_lead_stage(user_message, context)
        elif self.current_stage == PipelineStage.QUALIFICATION:
            response = self._handle_qualification_stage(user_message, context)
        elif self.current_stage == PipelineStage.DISCOVERY:
            response = self._handle_discovery_stage(user_message, context)
        elif self.current_stage == PipelineStage.PROPOSAL:
            response = self._handle_proposal_stage(user_message, context)
        elif self.current_stage == PipelineStage.NEGOTIATION:
            response = self._handle_negotiation_stage(user_message, context)
        else:
            response = self._generate_general_response(user_message, context)
        
        # Log agent message
        self.crm.conversations.add_message(
            self.current_customer_id,
            self.current_deal_id,
            "agent",
            response
        )
        
        return response
    
    # ============================================================================
    # STAGE HANDLERS
    # ============================================================================
    
    def _handle_lead_stage(self, user_message: str, context: str) -> str:
        """Handle conversations in Lead stage"""
        
        # Check if we have enough info to qualify
        customer = self.crm.customers.get_customer(self.current_customer_id)
        
        if len(context) > 200:  # Enough conversation happened
            # Move to qualification
            self.crm.advance_deal(self.current_deal_id, "Moving to qualification")
            self.current_stage = PipelineStage.QUALIFICATION
            return "Thanks for sharing that! Let me ask you a few qualifying questions to see how we can best help you.\n\n" + self._handle_qualification_stage(user_message, context)
        
        # Continue discovery
        prompt = f"""You are a friendly enterprise sales representative having an initial conversation.

CONTEXT:
- Stage: Lead (initial contact)
- Goal: Build rapport, understand basic needs, prepare for qualification

CUSTOMER INFO:
{self._format_customer_info(customer)}

CONVERSATION SO FAR:
{context}

USER'S MESSAGE:
{user_message}

YOUR TASK:
Respond naturally and professionally. Ask open-ended questions to understand:
- Their business challenges
- What they're looking for
- Why they reached out

Keep it conversational, not salesy. 2-3 sentences max.

RESPOND WITH ONLY YOUR MESSAGE:
"""
        
        return self._get_llm_response(prompt)
    
    def _handle_qualification_stage(self, user_message: str, context: str) -> str:
        """Handle BANT qualification"""
        
        customer = self.crm.customers.get_customer(self.current_customer_id)
        customer_info = {
            "company_name": customer.company_name,
            "industry": customer.industry,
            "company_size": customer.company_size
        }
        
        # Analyze BANT status
        bant_status = self.qualifier.analyze_qualification(context, customer_info)
        
        # Update pipeline with BANT scores
        deal = self.crm.pipeline.get_deal(self.current_deal_id)
        for criterion, data in bant_status.items():
            if criterion in ['budget', 'authority', 'need', 'timeline']:
                self.crm.pipeline.update_bant_score(
                    self.current_deal_id,
                    criterion,
                    data.get('qualified', False)
                )
        
        # Check if fully qualified
        if bant_status['overall_score'] >= 4:
            self.crm.advance_deal(self.current_deal_id, "Fully qualified - all BANT criteria met")
            self.current_stage = PipelineStage.DISCOVERY
            return "Excellent! You're a great fit for our solution. Let's dive deeper into your specific requirements.\n\nWhat are the top 3 challenges you're facing right now?"
        
        # Ask next qualifying question
        next_question = self.qualifier.get_next_question(bant_status, context)
        return next_question
    
    def _handle_discovery_stage(self, user_message: str, context: str) -> str:
        """Handle deep discovery"""
        
        customer = self.crm.customers.get_customer(self.current_customer_id)
        
        # Extract pain points and requirements from conversation
        self._extract_and_save_insights(user_message)
        
        # Check if ready for proposal
        if len(customer.pain_points) >= 2 and len(customer.requirements) >= 2:
            return f"""Thank you for sharing all of that valuable information!

Based on our conversation, I have a clear understanding of:
• {len(customer.pain_points)} key pain points
• {len(customer.requirements)} specific requirements

I'd like to prepare a customized proposal that addresses these needs. 

Would you like me to:
1. Generate a detailed proposal now
2. Schedule a demo first
3. Continue our discovery conversation

What works best for you?"""
        
        # Continue discovery
        prompt = f"""You are conducting a discovery call with a qualified prospect.

CUSTOMER:
{self._format_customer_info(customer)}

CONVERSATION:
{context[-1000:]}

DISCOVERED SO FAR:
- Pain Points: {len(customer.pain_points)}
- Requirements: {len(customer.requirements)}

USER'S MESSAGE:
{user_message}

YOUR TASK:
Continue the discovery. Ask probing questions about:
- Specific pain points and their impact
- Current solutions they're using
- What an ideal solution would look like
- Technical requirements

Be consultative, not salesy. 2-3 sentences.

RESPOND WITH ONLY YOUR MESSAGE:
"""
        
        return self._get_llm_response(prompt)
    
    def _handle_proposal_stage(self, user_message: str, context: str) -> str:
        """Handle proposal stage"""
        
        user_lower = user_message.lower()
        
        # Check for proposal generation request
        if any(word in user_lower for word in ['proposal', 'generate', 'yes', 'create', '1']):
            return self._generate_proposal()
        
        # Handle questions about proposal
        prompt = f"""You are discussing a sales proposal with a prospect.

CONTEXT:
{context[-500:]}

USER'S MESSAGE:
{user_message}

YOUR TASK:
Respond to their question or concern about the proposal.
Be helpful and address any objections.
Keep it concise and professional.

RESPOND WITH ONLY YOUR MESSAGE:
"""
        
        response = self._get_llm_response(prompt)
        return response
    
    def _handle_negotiation_stage(self, user_message: str, context: str) -> str:
        """Handle negotiation and objections"""
        
        user_lower = user_message.lower()
        
        # Check for close signals
        if any(word in user_lower for word in ['agree', 'accept', 'deal', 'proceed', 'yes']):
            self.crm.close_deal(self.current_deal_id, won=True, reason="Customer accepted proposal")
            self.current_stage = PipelineStage.CLOSED_WON
            return """🎉 Fantastic! Welcome aboard!

I'm excited to get started. Here's what happens next:

1. I'll send you the contract for signature
2. Our implementation team will reach out within 24 hours
3. We'll schedule a kickoff call for next week

Thank you for choosing us! You've made a great decision.

Is there anything else you need from me right now?"""
        
        # Handle objections
        prompt = f"""You are a skilled sales negotiator handling objections.

CONTEXT:
{context[-500:]}

USER'S OBJECTION/CONCERN:
{user_message}

YOUR TASK:
Address the concern professionally using techniques like:
- Feel, Felt, Found
- Reframing
- Providing social proof
- Offering alternatives

Be empathetic but confident. Don't be pushy.

RESPOND WITH ONLY YOUR MESSAGE:
"""
        
        return self._get_llm_response(prompt)
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _generate_proposal(self) -> str:
        """Generate and save proposal"""
        
        customer = self.crm.customers.get_customer(self.current_customer_id)
        deal = self.crm.pipeline.get_deal(self.current_deal_id)
        
        # Prepare data
        customer_info = {
            "company_name": customer.company_name,
            "industry": customer.industry,
            "company_size": customer.company_size,
            "primary_contact": customer.primary_contact
        }
        
        deal_info = {
            "value": deal.value if deal.value > 0 else 50000,  # Default if not set
            "timeline": customer.decision_timeline or "Q1 2025"
        }
        
        requirements = [r.get('description', str(r)) for r in customer.requirements]
        pain_points = [p.get('description', str(p)) for p in customer.pain_points]
        
        # Generate proposal
        print("\n📄 Generating customized proposal...\n")
        proposal = self.proposal_gen.generate_proposal(
            customer_info,
            deal_info,
            requirements,
            pain_points
        )
        
        # Save proposal
        filepath = self.proposal_gen.save_proposal(
            proposal,
            customer.company_name,
            deal.deal_id
        )
        
        # Move to proposal stage
        self.crm.advance_deal(self.current_deal_id, "Proposal generated and sent")
        self.current_stage = PipelineStage.PROPOSAL
        
        # Log interaction
        self.crm.log_email_sent(
            self.current_customer_id,
            self.current_deal_id,
            f"Proposal for {customer.company_name}"
        )
        
        return f"""✅ I've created a comprehensive proposal tailored to your needs!

The proposal includes:
• Executive summary addressing your key challenges
• Detailed solution overview
• Pricing breakdown (${deal_info['value']:,.2f})
• Implementation timeline
• Expected ROI calculations

📁 Proposal saved to: {filepath}

I've addressed all {len(pain_points)} pain points you mentioned and mapped our solution to your {len(requirements)} requirements.

Would you like me to walk you through any section of the proposal?"""
    
    def _extract_and_save_insights(self, message: str):
        """Extract pain points and requirements from message"""
        
        customer = self.crm.customers.get_customer(self.current_customer_id)
        message_lower = message.lower()
        
        # Simple keyword-based extraction (could be enhanced with LLM)
        pain_keywords = ['problem', 'challenge', 'issue', 'difficult', 'struggling', 'pain']
        requirement_keywords = ['need', 'require', 'must have', 'looking for', 'want']
        
        if any(word in message_lower for word in pain_keywords):
            if message not in [p.get('description', '') for p in customer.pain_points]:
                self.crm.customers.add_pain_point(self.current_customer_id, message)
        
        if any(word in message_lower for word in requirement_keywords):
            if message not in [r.get('description', '') for r in customer.requirements]:
                self.crm.customers.add_requirement(self.current_customer_id, message)
    
    def _get_conversation_context(self) -> str:
        """Get recent conversation context"""
        messages = self.crm.conversations.get_recent_context(self.current_customer_id, 10)
        context = "\n".join([f"{m.role}: {m.content}" for m in messages])
        return context
    
    def _format_customer_info(self, customer) -> str:
        """Format customer info for prompts"""
        return f"""
Company: {customer.company_name}
Industry: {customer.industry or 'Not specified'}
Size: {customer.company_size or 'Not specified'}
Contact: {customer.primary_contact.get('name', 'Not specified')}
Pain Points: {len(customer.pain_points)}
Requirements: {len(customer.requirements)}
"""
    
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM"""
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ LLM error: {str(e)}")
            return "I apologize, I'm having trouble processing that. Could you rephrase?"
    
    def _generate_welcome_message(self, company_name: str, contact_name: str = "") -> str:
        """Generate welcome message for new customer"""
        greeting = f"Hi {contact_name}! " if contact_name else "Hello! "
        
        return f"""{greeting}Thanks for your interest in our solutions!

I'm your AI sales assistant, and I'm here to help {company_name} find the right solution for your needs.

To get started, could you tell me a bit about:
• What challenges you're currently facing
• What brought you to us today

This will help me understand how we can best help you."""
    
    def _generate_returning_customer_greeting(self, customer, deal) -> str:
        """Generate greeting for returning customer"""
        stage_info = StageMetadata.get_info(deal.stage)
        
        return f"""Welcome back, {customer.company_name}! 👋

I see we're currently at the {stage_info['emoji']} {stage_info['name']} stage for your deal.

Current status:
• Deal Value: ${deal.value:,.2f}
• Probability: {deal.probability}%
• Stage: {stage_info['name']}

How can I help you today?"""
    
    def _generate_general_response(self, user_message: str, context: str) -> str:
        """Generate general response"""
        prompt = f"""You are a helpful enterprise sales assistant.

CONTEXT:
{context[-500:]}

USER'S MESSAGE:
{user_message}

YOUR TASK:
Respond helpfully and professionally.

RESPOND WITH ONLY YOUR MESSAGE:
"""
        return self._get_llm_response(prompt)
    
    def get_deal_status(self) -> str:
        """Get current deal status"""
        if not self.current_deal_id:
            return "No active deal"
        
        deal = self.crm.pipeline.get_deal(self.current_deal_id)
        return self.crm.pipeline.get_deal_summary(deal.deal_id)


if __name__ == "__main__":
    # Test the sales agent
    print("="*60)
    print("TESTING ENTERPRISE SALES AGENT")
    print("="*60 + "\n")
    
    agent = SalesAgent()
    
    # Start conversation
    response = agent.start_conversation("TechCorp Inc", "Sarah Johnson", "sarah@techcorp.com")
    print(f"🤖 Agent: {response}\n")
    
    # Simulate conversation
    test_messages = [
        "We're looking for a better CRM solution",
        "Our sales team of 50 people is struggling with lead tracking",
        "We have a budget of around $75,000 and need something by Q1",
        "Yes, I'm the VP of Sales and have approval authority"
    ]
    
    for msg in test_messages:
        print(f"👤 User: {msg}")
        response = agent.chat(msg)
        print(f"🤖 Agent: {response}\n")
    
    # Get deal status
    print("\n" + agent.get_deal_status())