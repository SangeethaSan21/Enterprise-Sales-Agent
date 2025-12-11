"""
Email Tool - Automated email generation and sending
"""

import os
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict

load_dotenv()


class EmailTool:
    """Generate and send automated follow-up emails"""
    
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.company_name = os.getenv("COMPANY_NAME", "Your Company")
        self.sales_rep_name = os.getenv("SALES_REP_NAME", "Sales Team")
        self.sales_rep_email = os.getenv("SALES_REP_EMAIL", "sales@yourcompany.com")
        print("📧 Email Tool initialized")
    
    def generate_follow_up_email(self, customer_info: Dict, context: str, purpose: str) -> Dict:
        """
        Generate a follow-up email
        
        Args:
            customer_info: Customer details
            context: Conversation context
            purpose: Email purpose (post-demo, proposal-follow-up, etc.)
            
        Returns:
            Dict with subject and body
        """
        
        prompt = f"""You are writing a professional follow-up email.

CUSTOMER:
Company: {customer_info.get('company_name', 'Valued Customer')}
Contact: {customer_info.get('contact_name', 'Customer')}

CONTEXT:
{context}

EMAIL PURPOSE: {purpose}

YOUR TASK:
Write a professional, personalized follow-up email that:
- References specific points from the conversation
- Provides clear value
- Has a clear call-to-action
- Is warm but professional
- Is concise (under 200 words)

RESPOND WITH JSON:
{{
  "subject": "Email subject line",
  "body": "Email body text"
}}
"""
        
        try:
            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7
            )
            
            import json
            result_text = response.choices[0].message.content.strip()
            
            # Clean JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            # Add signature
            result['body'] += f"\n\nBest regards,\n{self.sales_rep_name}\n{self.company_name}\n{self.sales_rep_email}"
            
            print(f"✅ Generated {purpose} email")
            return result
            
        except Exception as e:
            print(f"❌ Email generation error: {str(e)}")
            return self._get_fallback_email(customer_info, purpose)
    
    def generate_proposal_email(self, customer_info: Dict, proposal_path: str) -> Dict:
        """Generate email to send with proposal"""
        
        contact_name = customer_info.get('contact_name', 'there')
        company_name = customer_info.get('company_name', 'your company')
        
        subject = f"Proposal for {company_name}"
        
        body = f"""Hi {contact_name},

Thank you for taking the time to discuss your needs with us. I've prepared a comprehensive proposal that addresses the challenges we discussed.

The proposal includes:
• Detailed solution overview
• Pricing breakdown
• Implementation timeline
• Expected ROI calculations

I believe this solution will help {company_name} achieve your goals. I'm confident you'll find it addresses all your requirements.

Would you be available for a call this week to discuss the proposal? I'm happy to walk you through any section and answer your questions.

Looking forward to hearing from you!"""
        
        body += f"\n\nBest regards,\n{self.sales_rep_name}\n{self.company_name}\n{self.sales_rep_email}"
        
        return {"subject": subject, "body": body}
    
    def _get_fallback_email(self, customer_info: Dict, purpose: str) -> Dict:
        """Fallback email template"""
        
        contact_name = customer_info.get('contact_name', 'there')
        company_name = customer_info.get('company_name', 'your company')
        
        templates = {
            "post-demo": {
                "subject": f"Thanks for the demo, {company_name}!",
                "body": f"Hi {contact_name},\n\nThank you for taking the time to see our demo today. I hope it gave you a good sense of how we can help {company_name}.\n\nWhat are your thoughts? I'd love to discuss next steps.\n\nBest regards,\n{self.sales_rep_name}"
            },
            "proposal-follow-up": {
                "subject": f"Following up on our proposal",
                "body": f"Hi {contact_name},\n\nI wanted to follow up on the proposal I sent over. Have you had a chance to review it?\n\nI'm happy to answer any questions you might have.\n\nBest regards,\n{self.sales_rep_name}"
            },
            "general": {
                "subject": f"Following up",
                "body": f"Hi {contact_name},\n\nI wanted to follow up on our recent conversation. Please let me know if you have any questions.\n\nBest regards,\n{self.sales_rep_name}"
            }
        }
        
        return templates.get(purpose, templates["general"])
    
    def save_email_draft(self, email: Dict, filename: str = None) -> str:
        """Save email draft to file"""
        
        if not filename:
            filename = f"email_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        output_dir = "output/emails"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {email['subject']}\n\n")
            f.write(email['body'])
        
        print(f"💾 Email draft saved: {filepath}")
        return filepath


if __name__ == "__main__":
    # Test email tool
    print("="*60)
    print("TESTING EMAIL TOOL")
    print("="*60 + "\n")
    
    tool = EmailTool()
    
    customer_info = {
        "company_name": "Acme Corp",
        "contact_name": "John Smith"
    }
    
    context = "We discussed their need for better sales automation. They mentioned struggling with lead tracking and follow-ups. Budget is $75K, timeline is Q1 2025."
    
    # Generate follow-up email
    email = tool.generate_follow_up_email(customer_info, context, "post-demo")
    
    print(f"📧 EMAIL PREVIEW:\n")
    print(f"Subject: {email['subject']}\n")
    print(f"{email['body']}\n")
    
    # Save draft
    filepath = tool.save_email_draft(email)
    print(f"\n✅ Email draft saved to: {filepath}")