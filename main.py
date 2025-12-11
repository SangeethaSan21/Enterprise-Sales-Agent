"""
Enterprise Sales Agent - Complete System

Features:
- ICP Builder (define ideal customers)
- Lead Discovery (find matching companies)
- Voice Agent (AI phone calls)
- Full Sales Pipeline (Lead → Close)
- CRM Integration
"""

from agent.sales_agent import SalesAgent
from agent.icp_builder import ICPBuilder
from tools.lead_discovery import LeadDiscoveryEngine
from tools.voice_agent import VoiceAgent
import sys
import json


def main_menu():
    """Display main menu"""
    print("\n" + "🎯"*30)
    print("ENTERPRISE SALES AGENT - COMPLETE SYSTEM")
    print("AI-Powered Sales from Lead Discovery to Close")
    print("🎯"*30)
    print("\n📋 MAIN MENU")
    print("="*60)
    print("1. 📊 Build ICP (Ideal Customer Profile)")
    print("2. 🔍 Discover Leads (find matching companies)")
    print("3. 📞 Voice Agent Demo (AI sales call)")
    print("4. 💬 Sales Conversation (text-based)")
    print("5. 📈 View Pipeline Report")
    print("6. 🎬 Full Demo (complete workflow)")
    print("7. ❌ Exit")
    print("="*60)


def icp_builder_flow():
    """ICP Building flow"""
    print("\n" + "🎯"*30)
    print("ICP BUILDER - Define Your Ideal Customer")
    print("🎯"*30 + "\n")
    
    builder = ICPBuilder()
    response = builder.start_conversation()
    print(f"🤖 Agent: {response}\n")
    
    context = ""
    while not builder.icp["completed"]:
        user_input = input("👤 You: ").strip()
        if not user_input:
            continue
        
        context += f"User: {user_input}\n"
        response = builder.process_message(user_input, context)
        print(f"\n🤖 Agent: {response}\n")
        context += f"Agent: {response}\n"
        
        if builder.icp["completed"]:
            # Save ICP
            filepath = builder.save_icp()
            print(f"\n✅ ICP saved to: {filepath}")
            return builder.get_icp()
    
    return None


def lead_discovery_flow(icp=None):
    """Lead Discovery flow"""
    print("\n" + "🔍"*30)
    print("LEAD DISCOVERY - Find Perfect-Fit Companies")
    print("🔍"*30 + "\n")
    
    # Load ICP if not provided
    if not icp:
        print("No ICP provided. Using sample ICP...")
        icp = {
            "company_characteristics": {
                "industry": "B2B SaaS",
                "company_size": "50-200",
                "revenue_range": "$5M-$20M",
                "geography": "United States",
                "tech_stack": ["Salesforce", "HubSpot"]
            },
            "buyer_persona": {
                "job_titles": ["VP Sales", "CRO"],
                "pain_points": ["Manual lead tracking"]
            },
            "engagement_signals": {
                "intent_signals": ["Recent funding", "Hiring sales team"]
            }
        }
    
    engine = LeadDiscoveryEngine()
    
    # Discover leads
    max_leads = int(input("How many leads to discover? (5-20): ") or "10")
    leads = engine.discover_leads(icp, max_leads=max_leads)
    
    # Display results
    print(engine.format_lead_list(leads))
    
    return leads


def voice_agent_demo():
    """Voice Agent demonstration"""
    print("\n" + "📞"*30)
    print("VOICE AGENT DEMO - AI Sales Call Simulation")
    print("📞"*30 + "\n")
    
    agent = VoiceAgent()
    
    # Get lead info
    print("Enter lead information:")
    company = input("Company name: ") or "TechCorp Inc"
    contact = input("Contact name: ") or "Sarah Johnson"
    
    lead_info = {
        "company_name": company,
        "contact_name": contact,
        "industry": "B2B SaaS",
        "personalization": "recently raised Series A funding",
        "value_prop": "automate lead qualification and save 10 hours per week"
    }
    
    # Start call
    print("\n📞 Starting AI sales call...\n")
    print("="*60)
    opening = agent.start_call(lead_info)
    print(f"🤖 Agent: {opening}\n")
    print("="*60)
    
    # Conversation loop
    while True:
        user_input = input("\n👤 Prospect: ").strip()
        
        if not user_input or user_input.lower() == 'end call':
            break
        
        response = agent.process_response(user_input, lead_info)
        print(f"\n🤖 Agent: {response}")
        print("="*60)
    
    # Analyze call
    print("\n📊 Call Analysis:")
    print("="*60)
    analysis = agent.analyze_call_quality()
    print(json.dumps(analysis, indent=2))
    
    # Save
    filepath = agent.save_call_recording()
    print(f"\n💾 Call recording saved to: {filepath}")
    
    # Show transcript
    show_transcript = input("\nView full transcript? (y/n): ").strip().lower()
    if show_transcript == 'y':
        print(agent.get_call_transcript())


def sales_conversation_flow():
    """Standard sales conversation flow"""
    print("\n" + "💬"*30)
    print("SALES CONVERSATION - Text-Based Sales Agent")
    print("💬"*30 + "\n")
    
    agent = SalesAgent()
    
    # Get customer info
    company_name = input("👤 Company Name: ").strip()
    if not company_name:
        print("❌ Company name required")
        return
    
    contact_name = input("👤 Contact Name (optional): ").strip()
    contact_email = input("📧 Contact Email (optional): ").strip()
    
    # Start conversation
    welcome = agent.start_conversation(company_name, contact_name, contact_email)
    print(f"\n🤖 Agent:\n{welcome}\n")
    
    # Conversation loop
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'end']:
                print("\n👋 Ending conversation...")
                break
            
            if user_input.lower() == 'status':
                print(f"\n{agent.get_deal_status()}\n")
                continue
            
            if user_input.lower() == 'report':
                if agent.current_customer_id:
                    report = agent.crm.get_customer_report(agent.current_customer_id)
                    print(f"\n{report}\n")
                continue
            
            # Get agent response
            response = agent.chat(user_input)
            print(f"\n🤖 Agent:\n{response}\n")
            
        except KeyboardInterrupt:
            print("\n\n⏸️  Interrupted")
            break


def full_demo():
    """Complete workflow demonstration"""
    print("\n" + "🎬"*30)
    print("FULL DEMO - Complete Sales Workflow")
    print("🎬"*30 + "\n")
    
    print("This demo shows the complete workflow:")
    print("1. Build ICP")
    print("2. Discover leads")
    print("3. Voice agent call")
    print("4. Sales conversation")
    print("5. Pipeline report\n")
    
    input("Press Enter to start demo...")
    
    # Step 1: ICP Builder (quick version)
    print("\n📊 Step 1: ICP Builder")
    print("="*60)
    print("Defining ideal customer profile...")
    
    sample_icp = {
        "company_characteristics": {
            "industry": "B2B SaaS",
            "company_size": "50-200",
            "revenue_range": "$5M-$20M",
            "geography": "United States",
            "tech_stack": ["Salesforce"]
        },
        "buyer_persona": {
            "job_titles": ["VP Sales"],
            "pain_points": ["Manual lead tracking"]
        },
        "engagement_signals": {
            "intent_signals": ["Recent funding"]
        }
    }
    
    print("✅ ICP Created: B2B SaaS, 50-200 employees, $5M-$20M")
    input("\nPress Enter to continue...")
    
    # Step 2: Lead Discovery
    print("\n🔍 Step 2: Lead Discovery")
    print("="*60)
    engine = LeadDiscoveryEngine()
    leads = engine.discover_leads(sample_icp, max_leads=3)
    print(f"✅ Discovered {len(leads)} qualified leads")
    
    for i, lead in enumerate(leads, 1):
        print(f"  {i}. {lead['company_name']} - Score: {lead['icp_score']}/100")
    
    input("\nPress Enter to continue...")
    
    # Step 3: Voice Agent (simulated)
    print("\n📞 Step 3: Voice Agent Call")
    print("="*60)
    print("Simulating AI sales call with top lead...")
    agent = VoiceAgent()
    lead_info = {
        "company_name": leads[0]['company_name'],
        "contact_name": leads[0]['decision_makers'][0]['name'],
        "industry": "B2B SaaS"
    }
    opening = agent.start_call(lead_info)
    print(f"🤖 Agent: {opening}")
    print("✅ Call completed - Lead qualified")
    
    input("\nPress Enter to continue...")
    
    # Step 4: Sales Conversation
    print("\n💬 Step 4: Sales Agent")
    print("="*60)
    sales_agent = SalesAgent()
    welcome = sales_agent.start_conversation(leads[0]['company_name'])
    print(f"🤖 Agent: {welcome[:200]}...")
    print("✅ Deal created in pipeline")
    
    input("\nPress Enter to see final report...")
    
    # Step 5: Pipeline Report
    print("\n📈 Step 5: Pipeline Report")
    print("="*60)
    report = sales_agent.crm.get_pipeline_report()
    print(report)
    
    print("\n🎉 Demo Complete!")
    print("="*60)


def main():
    """Main application loop"""
    
    while True:
        main_menu()
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            icp_builder_flow()
        elif choice == '2':
            lead_discovery_flow()
        elif choice == '3':
            voice_agent_demo()
        elif choice == '4':
            sales_conversation_flow()
        elif choice == '5':
            agent = SalesAgent()
            print(agent.crm.get_pipeline_report())
        elif choice == '6':
            full_demo()
        elif choice == '7':
            print("\n👋 Thanks for using Enterprise Sales Agent! Goodbye!\n")
            break
        else:
            print("❌ Invalid choice. Please select 1-7.")
        
        input("\nPress Enter to return to main menu...")


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--icp":
            icp_builder_flow()
        elif sys.argv[1] == "--discover":
            lead_discovery_flow()
        elif sys.argv[1] == "--voice":
            voice_agent_demo()
        elif sys.argv[1] == "--demo":
            full_demo()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Available: --icp, --discover, --voice, --demo")
    else:
        main()