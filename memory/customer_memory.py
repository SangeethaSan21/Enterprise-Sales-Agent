"""
Customer Memory - Long-term storage of customer data and interactions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class Customer:
    """Represents a customer/prospect"""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.company_name = ""
        self.industry = ""
        self.company_size = ""
        self.website = ""
        
        # Contact information
        self.primary_contact = {
            "name": "",
            "title": "",
            "email": "",
            "phone": ""
        }
        
        # Additional contacts
        self.contacts = []
        
        # Business context
        self.pain_points = []
        self.requirements = []
        self.budget_range = ""
        self.decision_timeline = ""
        self.competitors = []
        
        # Relationship
        self.relationship_strength = "new"  # new, warm, hot, champion
        self.engagement_level = 0  # 0-10
        
        # Metadata
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.tags = []
        self.custom_fields = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "customer_id": self.customer_id,
            "company_name": self.company_name,
            "industry": self.industry,
            "company_size": self.company_size,
            "website": self.website,
            "primary_contact": self.primary_contact,
            "contacts": self.contacts,
            "pain_points": self.pain_points,
            "requirements": self.requirements,
            "budget_range": self.budget_range,
            "decision_timeline": self.decision_timeline,
            "competitors": self.competitors,
            "relationship_strength": self.relationship_strength,
            "engagement_level": self.engagement_level,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
            "custom_fields": self.custom_fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Customer':
        """Create from dictionary"""
        customer = cls(data['customer_id'])
        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        return customer


class CustomerMemory:
    """Manages customer data and history"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.customers_file = os.path.join(data_dir, "customers.json")
        self.customers: Dict[str, Customer] = {}
        self._load_customers()
    
    def _load_customers(self):
        """Load customers from disk"""
        if os.path.exists(self.customers_file):
            try:
                with open(self.customers_file, 'r') as f:
                    data = json.load(f)
                    for customer_data in data.get('customers', []):
                        customer = Customer.from_dict(customer_data)
                        self.customers[customer.customer_id] = customer
                print(f"✅ Loaded {len(self.customers)} customers")
            except Exception as e:
                print(f"⚠️ Error loading customers: {str(e)}")
        else:
            print("📝 Creating new customer database")
            self._save_customers()
    
    def _save_customers(self):
        """Save customers to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        data = {
            "customers": [c.to_dict() for c in self.customers.values()],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.customers_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_customer(self, company_name: str) -> Customer:
        """Create a new customer"""
        customer_id = f"CUST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        customer = Customer(customer_id)
        customer.company_name = company_name
        self.customers[customer_id] = customer
        self._save_customers()
        print(f"✅ Created customer {customer_id}: {company_name}")
        return customer
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        return self.customers.get(customer_id)
    
    def find_customer_by_company(self, company_name: str) -> Optional[Customer]:
        """Find customer by company name"""
        for customer in self.customers.values():
            if customer.company_name.lower() == company_name.lower():
                return customer
        return None
    
    def update_customer(self, customer_id: str, **kwargs):
        """Update customer fields"""
        customer = self.get_customer(customer_id)
        if customer:
            for key, value in kwargs.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            customer.updated_at = datetime.now().isoformat()
            self._save_customers()
            print(f"✅ Updated customer {customer_id}")
    
    def add_contact(self, customer_id: str, name: str, title: str, email: str, phone: str = ""):
        """Add a contact to customer"""
        customer = self.get_customer(customer_id)
        if customer:
            contact = {
                "name": name,
                "title": title,
                "email": email,
                "phone": phone,
                "added_at": datetime.now().isoformat()
            }
            customer.contacts.append(contact)
            customer.updated_at = datetime.now().isoformat()
            self._save_customers()
            print(f"✅ Added contact {name} to {customer.company_name}")
    
    def add_pain_point(self, customer_id: str, pain_point: str):
        """Add a pain point"""
        customer = self.get_customer(customer_id)
        if customer:
            customer.pain_points.append({
                "description": pain_point,
                "added_at": datetime.now().isoformat()
            })
            customer.updated_at = datetime.now().isoformat()
            self._save_customers()
    
    def add_requirement(self, customer_id: str, requirement: str):
        """Add a requirement"""
        customer = self.get_customer(customer_id)
        if customer:
            customer.requirements.append({
                "description": requirement,
                "priority": "medium",
                "added_at": datetime.now().isoformat()
            })
            customer.updated_at = datetime.now().isoformat()
            self._save_customers()
    
    def update_relationship_strength(self, customer_id: str, strength: str):
        """Update relationship strength (new, warm, hot, champion)"""
        customer = self.get_customer(customer_id)
        if customer and strength in ["new", "warm", "hot", "champion"]:
            customer.relationship_strength = strength
            customer.updated_at = datetime.now().isoformat()
            self._save_customers()
            print(f"✅ Relationship with {customer.company_name}: {strength}")
    
    def update_engagement_level(self, customer_id: str, level: int):
        """Update engagement level (0-10)"""
        customer = self.get_customer(customer_id)
        if customer:
            customer.engagement_level = max(0, min(10, level))
            customer.updated_at = datetime.now().isoformat()
            self._save_customers()
    
    def add_tag(self, customer_id: str, tag: str):
        """Add a tag to customer"""
        customer = self.get_customer(customer_id)
        if customer and tag not in customer.tags:
            customer.tags.append(tag)
            customer.updated_at = datetime.now().isoformat()
            self._save_customers()
    
    def get_customer_summary(self, customer_id: str) -> str:
        """Get formatted customer summary"""
        customer = self.get_customer(customer_id)
        if not customer:
            return f"❌ Customer {customer_id} not found"
        
        summary = f"""
👤 CUSTOMER PROFILE: {customer.customer_id}
{'='*60}
🏢 Company: {customer.company_name}
🏭 Industry: {customer.industry or 'Not specified'}
👥 Size: {customer.company_size or 'Not specified'}
🌐 Website: {customer.website or 'Not specified'}

PRIMARY CONTACT:
  Name: {customer.primary_contact['name'] or 'Not specified'}
  Title: {customer.primary_contact['title'] or 'Not specified'}
  Email: {customer.primary_contact['email'] or 'Not specified'}
  Phone: {customer.primary_contact['phone'] or 'Not specified'}

Additional Contacts: {len(customer.contacts)}
Pain Points: {len(customer.pain_points)}
Requirements: {len(customer.requirements)}

RELATIONSHIP:
  Strength: {customer.relationship_strength.upper()}
  Engagement: {customer.engagement_level}/10
  Tags: {', '.join(customer.tags) if customer.tags else 'None'}

Budget Range: {customer.budget_range or 'Not specified'}
Timeline: {customer.decision_timeline or 'Not specified'}
{'='*60}
"""
        return summary
    
    def search_customers(self, query: str = "", tag: str = None, industry: str = None) -> List[Customer]:
        """Search customers by various criteria"""
        results = []
        query_lower = query.lower()
        
        for customer in self.customers.values():
            # Text search
            if query and query_lower not in customer.company_name.lower():
                continue
            
            # Tag filter
            if tag and tag not in customer.tags:
                continue
            
            # Industry filter
            if industry and customer.industry.lower() != industry.lower():
                continue
            
            results.append(customer)
        
        return results


if __name__ == "__main__":
    # Test customer memory
    print("="*60)
    print("TESTING CUSTOMER MEMORY")
    print("="*60 + "\n")
    
    # Create memory
    cm = CustomerMemory()
    
    # Create customer
    customer = cm.create_customer("Acme Corporation")
    
    # Update details
    cm.update_customer(
        customer.customer_id,
        industry="Technology",
        company_size="500-1000 employees",
        website="https://acme.com",
        budget_range="$50K-$100K",
        decision_timeline="Q1 2025"
    )
    
    # Update primary contact
    customer.primary_contact = {
        "name": "John Smith",
        "title": "VP of Engineering",
        "email": "john.smith@acme.com",
        "phone": "+1-555-0123"
    }
    cm._save_customers()
    
    # Add additional contact
    cm.add_contact(
        customer.customer_id,
        "Sarah Johnson",
        "CTO",
        "sarah.johnson@acme.com"
    )
    
    # Add pain points
    cm.add_pain_point(customer.customer_id, "Manual deployment process causing delays")
    cm.add_pain_point(customer.customer_id, "Lack of visibility into system performance")
    
    # Add requirements
    cm.add_requirement(customer.customer_id, "Automated CI/CD pipeline")
    cm.add_requirement(customer.customer_id, "Real-time monitoring dashboard")
    
    # Update relationship
    cm.update_relationship_strength(customer.customer_id, "warm")
    cm.update_engagement_level(customer.customer_id, 7)
    
    # Add tags
    cm.add_tag(customer.customer_id, "enterprise")
    cm.add_tag(customer.customer_id, "tech-stack-python")
    
    # Display summary
    print(cm.get_customer_summary(customer.customer_id))