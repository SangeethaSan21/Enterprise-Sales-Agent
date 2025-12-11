

import os
import json
from datetime import datetime, timedelta
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()


class ProposalGenerator:
    """Generate customized sales proposals"""
    
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.company_name = os.getenv("COMPANY_NAME", "Your Company")
        self.company_website = os.getenv("COMPANY_WEBSITE", "https://yourcompany.com")
        self.sales_rep_name = os.getenv("SALES_REP_NAME", "Sales Team")
        print("📄 Proposal Generator initialized")
    
    def generate_proposal(
        self,
        customer_info: Dict,
        deal_info: Dict,
        requirements: List[str],
        pain_points: List[str]
    ) -> str:
        """
        Generate a comprehensive sales proposal
        
        Args:
            customer_info: Customer profile data
            deal_info: Deal details (value, timeline, etc.)
            requirements: List of customer requirements
            pain_points: List of identified pain points
            
        Returns:
            Formatted proposal document
        """
        
        prompt = f"""You are a professional proposal writer creating a compelling sales proposal.

CUSTOMER INFORMATION:
Company: {customer_info.get('company_name', 'Customer')}
Industry: {customer_info.get('industry', 'Not specified')}
Size: {customer_info.get('company_size', 'Not specified')}
Contact: {customer_info.get('primary_contact', {}).get('name', 'Valued Customer')}

DEAL DETAILS:
Value: ${deal_info.get('value', 0):,.2f}
Timeline: {deal_info.get('timeline', 'To be determined')}

IDENTIFIED PAIN POINTS:
{self._format_list(pain_points)}

CUSTOMER REQUIREMENTS:
{self._format_list(requirements)}

YOUR TASK:
Create a professional, compelling sales proposal that:
1. Addresses each pain point directly
2. Maps solutions to requirements
3. Demonstrates clear ROI and value
4. Includes pricing breakdown
5. Provides implementation timeline
6. Establishes next steps

RESPOND WITH A COMPLETE PROPOSAL IN MARKDOWN FORMAT:

# Sales Proposal for [Company Name]

## Executive Summary
[2-3 paragraphs summarizing the opportunity, solution, and value]

## Current Challenges
[Address each pain point]

## Proposed Solution
[Detailed solution description]

### Key Features & Benefits
[Features mapped to requirements]

## Implementation Plan
### Timeline
[Phases and milestones]

### Support & Training
[What's included]

## Investment
### Pricing Breakdown
[Itemized pricing]

### Return on Investment
[Expected ROI with calculations]

## Why Choose {self.company_name}
[Competitive advantages]

## Next Steps
[Clear path forward]

## Terms & Conditions
[Standard terms]

---
Prepared by: {self.sales_rep_name}
Date: {datetime.now().strftime('%B %d, %Y')}
Valid Until: {(datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')}

Generate the complete proposal now:
"""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=3000
            )
            
            proposal = response.choices[0].message.content.strip()
            
            print(f"✅ Generated proposal ({len(proposal)} characters)")
            return proposal
            
        except Exception as e:
            print(f"❌ Proposal generation error: {str(e)}")
            return self._get_fallback_proposal(customer_info, deal_info)
    
    def generate_executive_summary(self, customer_info: Dict, solution_summary: str) -> str:
        """Generate a brief executive summary"""
        
        prompt = f"""Create a compelling 2-3 paragraph executive summary for a sales proposal.

Customer: {customer_info.get('company_name')}
Industry: {customer_info.get('industry')}
Solution Summary: {solution_summary}

Make it executive-level: focus on business impact, ROI, and strategic value.
Keep it concise and compelling.

RESPOND WITH ONLY THE EXECUTIVE SUMMARY (no headings):
"""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ Error generating executive summary: {str(e)}")
            return f"This proposal outlines a comprehensive solution for {customer_info.get('company_name')} that addresses your key business challenges and delivers measurable value."
    
    def calculate_roi(self, investment: float, time_savings_hours: float, hourly_rate: float = 50) -> Dict:
        """Calculate ROI metrics"""
        
        monthly_savings = time_savings_hours * hourly_rate * 20  # 20 working days
        yearly_savings = monthly_savings * 12
        payback_months = investment / monthly_savings if monthly_savings > 0 else 0
        roi_percentage = ((yearly_savings - investment) / investment * 100) if investment > 0 else 0
        
        return {
            "investment": investment,
            "monthly_savings": monthly_savings,
            "yearly_savings": yearly_savings,
            "payback_months": payback_months,
            "roi_percentage": roi_percentage,
            "three_year_value": (yearly_savings * 3) - investment
        }
    
    def format_roi_section(self, roi: Dict) -> str:
        """Format ROI calculations as markdown"""
        
        section = f"""
## Return on Investment

### Investment Summary
- **Initial Investment**: ${roi['investment']:,.2f}
- **Monthly Savings**: ${roi['monthly_savings']:,.2f}
- **Annual Savings**: ${roi['yearly_savings']:,.2f}

### Financial Impact
- **Payback Period**: {roi['payback_months']:.1f} months
- **First Year ROI**: {roi['roi_percentage']:.1f}%
- **3-Year Total Value**: ${roi['three_year_value']:,.2f}

### Break-Even Analysis
Your investment will pay for itself in just {roi['payback_months']:.1f} months. After that, you'll realize ${roi['monthly_savings']:,.2f} in monthly savings, providing ongoing value to your organization.
"""
        return section
    
    def save_proposal(self, proposal: str, customer_name: str, deal_id: str) -> str:
        """Save proposal to file"""
        
        # Create output directory
        output_dir = "output/proposals"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{customer_name.replace(' ', '_')}_{deal_id}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Save proposal
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(proposal)
        
        print(f"💾 Proposal saved: {filepath}")
        return filepath
    
    def _format_list(self, items: List) -> str:
        """Format list as bullet points"""
        if not items:
            return "- Not specified"
        return "\n".join(f"- {item}" for item in items)
    
    def _get_fallback_proposal(self, customer_info: Dict, deal_info: Dict) -> str:
        """Fallback proposal template"""
        
        company_name = customer_info.get('company_name', 'Valued Customer')
        contact_name = customer_info.get('primary_contact', {}).get('name', 'Customer')
        
        return f"""
# Sales Proposal for {company_name}

## Executive Summary

Dear {contact_name},

Thank you for considering {self.company_name} as your solution provider. This proposal outlines how we can help {company_name} achieve its business objectives.

## Proposed Solution

Our comprehensive solution is designed to address your specific needs and deliver measurable results.

### Key Benefits
- Improved operational efficiency
- Reduced manual workload
- Enhanced data visibility
- Scalable platform for growth

## Investment

**Total Investment**: ${deal_info.get('value', 0):,.2f}

This includes:
- Platform access and licenses
- Implementation and training
- Ongoing support
- Regular updates and enhancements

## Timeline

We propose a phased implementation approach:
- **Phase 1** (Weeks 1-2): Discovery and setup
- **Phase 2** (Weeks 3-4): Implementation
- **Phase 3** (Weeks 5-6): Training and go-live
- **Ongoing**: Support and optimization

## Next Steps

1. Review this proposal
2. Schedule a follow-up call to address questions
3. Finalize agreement
4. Begin implementation

We look forward to partnering with {company_name}.

---
**Prepared by**: {self.sales_rep_name}  
**Date**: {datetime.now().strftime('%B %d, %Y')}  
**Valid Until**: {(datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')}
"""


if __name__ == "__main__":
    # Test proposal generator
    print("="*60)
    print("TESTING PROPOSAL GENERATOR")
    print("="*60 + "\n")
    
    generator = ProposalGenerator()
    
    # Sample data
    customer_info = {
        "company_name": "Acme Corporation",
        "industry": "Technology",
        "company_size": "500-1000 employees",
        "primary_contact": {
            "name": "John Smith",
            "title": "VP of Engineering"
        }
    }
    
    deal_info = {
        "value": 75000,
        "timeline": "Q1 2025"
    }
    
    requirements = [
        "Automated CI/CD pipeline",
        "Real-time monitoring and alerts",
        "Integration with existing tools",
        "Team collaboration features"
    ]
    
    pain_points = [
        "Manual deployment process causing delays",
        "Lack of visibility into system performance",
        "Difficulty coordinating between teams"
    ]
    
    # Generate proposal
    print("📝 Generating proposal...\n")
    proposal = generator.generate_proposal(customer_info, deal_info, requirements, pain_points)
    
    # Display preview
    print("="*60)
    print("PROPOSAL PREVIEW (first 1000 characters)")
    print("="*60)
    print(proposal[:1000] + "...\n")
    
    # Calculate ROI
    print("="*60)
    print("ROI CALCULATION")
    print("="*60)
    roi = generator.calculate_roi(
        investment=75000,
        time_savings_hours=10,  # 10 hours saved per day
        hourly_rate=75
    )
    
    print(f"Investment: ${roi['investment']:,.2f}")
    print(f"Monthly Savings: ${roi['monthly_savings']:,.2f}")
    print(f"Payback Period: {roi['payback_months']:.1f} months")
    print(f"First Year ROI: {roi['roi_percentage']:.1f}%")
    
    # Save proposal
    filepath = generator.save_proposal(proposal, "Acme_Corporation", "DEAL-001")
    print(f"\n✅ Complete proposal saved to: {filepath}")