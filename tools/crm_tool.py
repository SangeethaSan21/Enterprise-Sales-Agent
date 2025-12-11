"""
CRM Tool - Customer Relationship Management Operations

Integrates Pipeline, Customer Memory, and Interaction Log
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.manager import PipelineManager, Deal
from pipeline.stages import PipelineStage
from memory.customer_memory import CustomerMemory, Customer
from memory.interaction_log import InteractionLog, InteractionType
from memory.conversation_store import ConversationStore
from typing import Dict, List, Optional


class CRMTool:
    """Central CRM operations - integrates all customer data systems"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        
        # Initialize all systems
        self.pipeline = PipelineManager(data_dir)
        self.customers = CustomerMemory(data_dir)
        self.interactions = InteractionLog(data_dir)
        self.conversations = ConversationStore(data_dir)
        
        print("🏢 CRM Tool initialized")
    
    # ============================================================================
    # CUSTOMER OPERATIONS
    # ============================================================================
    
    def create_customer_with_deal(self, company_name: str, contact_name: str = "", 
                                   contact_email: str = "", initial_value: float = 0) -> Dict:
        """
        Create a new customer and associated deal
        
        Returns dict with customer_id, deal_id
        """
        # Create customer
        customer = self.customers.create_customer(company_name)
        
        # Update contact info if provided
        if contact_name or contact_email:
            customer.primary_contact['name'] = contact_name
            customer.primary_contact['email'] = contact_email
            self.customers._save_customers()
        
        # Create deal
        deal = self.pipeline.create_deal(customer.customer_id, company_name)
        
        if initial_value > 0:
            self.pipeline.update_deal_value(deal.deal_id, initial_value)
        
        # Log interaction
        self.interactions.log_interaction(
            customer.customer_id,
            deal.deal_id,
            InteractionType.NOTE,
            f"New customer created: {company_name}"
        )
        
        print(f"✅ Created customer and deal for {company_name}")
        
        return {
            "customer_id": customer.customer_id,
            "deal_id": deal.deal_id,
            "customer": customer,
            "deal": deal
        }
    
    def get_customer_360(self, customer_id: str) -> Dict:
        """
        Get complete 360-degree view of customer
        
        Returns all customer data, deals, interactions, conversations
        """
        customer = self.customers.get_customer(customer_id)
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
        
        deals = self.pipeline.get_deals_by_customer(customer_id)
        interactions = self.interactions.get_customer_interactions(customer_id)
        conversations = self.conversations.get_conversation_history(customer_id)
        
        return {
            "customer": customer,
            "deals": deals,
            "interactions": interactions,
            "conversations": conversations,
            "summary": {
                "total_deals": len(deals),
                "total_value": sum(d.value for d in deals),
                "total_interactions": len(interactions),
                "total_conversations": len(conversations),
                "relationship_strength": customer.relationship_strength,
                "engagement_level": customer.engagement_level
            }
        }
    
    # ============================================================================
    # DEAL OPERATIONS
    # ============================================================================
    
    def advance_deal(self, deal_id: str, note: str = "") -> bool:
        """
        Advance deal to next stage in pipeline
        
        Automatically determines next appropriate stage
        """
        deal = self.pipeline.get_deal(deal_id)
        if not deal:
            print(f"❌ Deal {deal_id} not found")
            return False
        
        current_stage = deal.stage
        
        # Determine next stage based on current
        next_stage_map = {
            PipelineStage.LEAD: PipelineStage.QUALIFICATION,
            PipelineStage.QUALIFICATION: PipelineStage.DISCOVERY,
            PipelineStage.DISCOVERY: PipelineStage.PROPOSAL,
            PipelineStage.PROPOSAL: PipelineStage.NEGOTIATION,
            PipelineStage.NEGOTIATION: PipelineStage.CLOSED_WON
        }
        
        next_stage = next_stage_map.get(current_stage)
        if not next_stage:
            print(f"❌ Deal is already in final stage: {current_stage.value}")
            return False
        
        # Move deal
        success = self.pipeline.move_deal(deal_id, next_stage, note)
        
        if success:
            # Log interaction
            self.interactions.log_interaction(
                deal.customer_id,
                deal_id,
                InteractionType.NOTE,
                f"Deal advanced to {next_stage.value}",
                note
            )
        
        return success
    
    def close_deal(self, deal_id: str, won: bool, reason: str = ""):
        """Close deal as won or lost"""
        deal = self.pipeline.get_deal(deal_id)
        if not deal:
            return False
        
        final_stage = PipelineStage.CLOSED_WON if won else PipelineStage.CLOSED_LOST
        note = f"{'Won' if won else 'Lost'}: {reason}" if reason else f"Deal {'won' if won else 'lost'}"
        
        success = self.pipeline.move_deal(deal_id, final_stage, note)
        
        if success:
            self.interactions.log_interaction(
                deal.customer_id,
                deal_id,
                InteractionType.NOTE,
                f"Deal closed {'won' if won else 'lost'}",
                reason,
                sentiment="positive" if won else "negative"
            )
        
        return success
    
    # ============================================================================
    # INTERACTION TRACKING
    # ============================================================================
    
    def log_email_sent(self, customer_id: str, deal_id: str, subject: str, body: str = ""):
        """Log email interaction"""
        return self.interactions.log_email(customer_id, deal_id, subject, body)
    
    def log_call_completed(self, customer_id: str, deal_id: str, summary: str, duration: int = 0):
        """Log call interaction"""
        return self.interactions.log_call(customer_id, deal_id, summary, duration)
    
    def log_meeting(self, customer_id: str, deal_id: str, summary: str, participants: List[str]):
        """Log meeting interaction"""
        return self.interactions.log_meeting(customer_id, deal_id, summary, participants)
    
    # ============================================================================
    # REPORTING & ANALYTICS
    # ============================================================================
    
    def get_pipeline_report(self) -> str:
        """Get formatted pipeline report"""
        summary = self.pipeline.get_pipeline_summary()
        
        report = f"""
📊 SALES PIPELINE REPORT
{'='*60}
Generated: {os.environ.get('TZ', 'UTC')}

OVERVIEW:
  Total Deals: {summary['total_deals']}
  Total Value: ${summary['total_value']:,.2f}
  Weighted Value: ${summary['weighted_value']:,.2f}

DEALS BY STAGE:
"""
        
        for stage, data in summary['by_stage'].items():
            if data['count'] > 0:
                report += f"\n{data['emoji']} {stage.upper()}\n"
                report += f"  Deals: {data['count']}\n"
                report += f"  Value: ${data['value']:,.2f}\n"
        
        report += f"\n{'='*60}\n"
        
        return report
    
    def get_customer_report(self, customer_id: str) -> str:
        """Get comprehensive customer report"""
        data = self.get_customer_360(customer_id)
        
        if "error" in data:
            return data["error"]
        
        customer = data['customer']
        summary = data['summary']
        
        report = f"""
{'='*60}
CUSTOMER REPORT: {customer.company_name}
{'='*60}

COMPANY INFORMATION:
  ID: {customer.customer_id}
  Industry: {customer.industry or 'Not specified'}
  Size: {customer.company_size or 'Not specified'}
  Website: {customer.website or 'Not specified'}

PRIMARY CONTACT:
  Name: {customer.primary_contact['name'] or 'Not specified'}
  Title: {customer.primary_contact['title'] or 'Not specified'}
  Email: {customer.primary_contact['email'] or 'Not specified'}

RELATIONSHIP:
  Strength: {customer.relationship_strength.upper()}
  Engagement: {customer.engagement_level}/10
  Tags: {', '.join(customer.tags) if customer.tags else 'None'}

BUSINESS CONTEXT:
  Pain Points: {len(customer.pain_points)}
  Requirements: {len(customer.requirements)}
  Budget Range: {customer.budget_range or 'Not specified'}
  Timeline: {customer.decision_timeline or 'Not specified'}

ACTIVITY SUMMARY:
  Total Deals: {summary['total_deals']}
  Total Value: ${summary['total_value']:,.2f}
  Interactions: {summary['total_interactions']}
  Conversations: {summary['total_conversations']}

ACTIVE DEALS:
"""
        
        for deal in data['deals']:
            if deal.stage not in [PipelineStage.CLOSED_WON, PipelineStage.CLOSED_LOST]:
                report += f"  • {deal.deal_id}: {deal.stage.value} - ${deal.value:,.2f} ({deal.probability}%)\n"
        
        report += f"\n{'='*60}\n"
        
        return report
    
    def get_activity_feed(self, customer_id: str, limit: int = 10) -> str:
        """Get recent activity feed for customer"""
        interactions = self.interactions.get_recent_interactions(customer_id, limit)
        
        if not interactions:
            return "No recent activity"
        
        feed = f"\n📰 RECENT ACTIVITY FEED\n{'='*60}\n"
        
        for interaction in interactions:
            emoji = self.interactions._get_interaction_emoji(interaction.interaction_type)
            timestamp = interaction.timestamp.split('T')[0]  # Just date
            
            feed += f"\n{emoji} {timestamp}: {interaction.summary}\n"
        
        feed += f"\n{'='*60}\n"
        
        return feed


if __name__ == "__main__":
    # Test CRM tool
    print("="*60)
    print("TESTING CRM TOOL")
    print("="*60 + "\n")
    
    crm = CRMTool()
    
    # Create customer with deal
    result = crm.create_customer_with_deal(
        company_name="Acme Corporation",
        contact_name="John Smith",
        contact_email="john@acme.com",
        initial_value=50000
    )
    
    customer_id = result['customer_id']
    deal_id = result['deal_id']
    
    # Update customer info
    crm.customers.update_customer(
        customer_id,
        industry="Technology",
        company_size="500-1000 employees",
        budget_range="$50K-$100K"
    )
    
    # Add interactions
    crm.log_email_sent(customer_id, deal_id, "Introduction to our solutions")
    crm.log_call_completed(customer_id, deal_id, "Discovery call completed", 45)
    
    # Advance deal
    crm.advance_deal(deal_id, "Completed initial qualification")
    
    # Get reports
    print("\n" + crm.get_pipeline_report())
    print("\n" + crm.get_customer_report(customer_id))
    print("\n" + crm.get_activity_feed(customer_id))
    
    # Get 360 view
    view_360 = crm.get_customer_360(customer_id)
    print(f"\n360 View Summary:")
    print(f"  Total Deals: {view_360['summary']['total_deals']}")
    print(f"  Total Value: ${view_360['summary']['total_value']:,.2f}")
    print(f"  Interactions: {view_360['summary']['total_interactions']}")
    print(f"  Relationship: {view_360['summary']['relationship_strength']}")