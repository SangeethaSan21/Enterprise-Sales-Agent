"""
Lead Discovery Engine - Find companies matching ICP

Uses web search to discover and score potential leads
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List
import re

load_dotenv()


class LeadDiscoveryEngine:
    """Discover leads matching Ideal Customer Profile"""
    
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        print("🔍 Lead Discovery Engine initialized")
    
    def generate_search_queries(self, icp: Dict) -> List[str]:
        """
        Generate search queries based on ICP
        
        Args:
            icp: Ideal Customer Profile
            
        Returns:
            List of search queries
        """
        cc = icp.get("company_characteristics", {})
        bp = icp.get("buyer_persona", {})
        es = icp.get("engagement_signals", {})
        
        queries = []
        
        # Basic company queries
        industry = cc.get("industry", "")
        size = cc.get("company_size", "")
        geo = cc.get("geography", "")
        
        if industry and size:
            queries.append(f"{industry} companies {size} {geo}")
        
        # Tech stack queries
        tech_stack = cc.get("tech_stack", [])
        if tech_stack and industry:
            for tech in tech_stack[:2]:  # Top 2 technologies
                queries.append(f"{industry} companies using {tech} {geo}")
        
        # Job posting queries (intent signal)
        job_titles = bp.get("job_titles", [])
        if job_titles and industry:
            queries.append(f"{industry} companies hiring {job_titles[0]} {geo}")
        
        # Funding queries (intent signal)
        if "funding" in str(es.get("intent_signals", [])).lower():
            queries.append(f"{industry} companies recent funding {geo}")
        
        # Growth stage queries
        growth_stage = cc.get("growth_stage", "")
        if growth_stage and industry:
            queries.append(f"{growth_stage} {industry} companies {geo}")
        
        return queries[:5]  # Return top 5 queries
    
    def discover_leads(self, icp: Dict, max_leads: int = 20) -> List[Dict]:
        """
        Discover leads matching ICP
        
        Args:
            icp: Ideal Customer Profile
            max_leads: Maximum number of leads to return
            
        Returns:
            List of discovered leads
        """
        
        print(f"🔍 Discovering leads matching ICP...")
        
        # Generate search queries
        queries = self.generate_search_queries(icp)
        print(f"📝 Generated {len(queries)} search queries")
        
        # Discover leads
        all_leads = []
        
        for query in queries:
            leads = self._search_for_leads(query, icp)
            all_leads.extend(leads)
        
        # Remove duplicates
        unique_leads = self._deduplicate_leads(all_leads)
        
        # Score and rank leads
        scored_leads = self._score_leads(unique_leads, icp)
        
        # Return top leads
        top_leads = sorted(scored_leads, key=lambda x: x['icp_score'], reverse=True)[:max_leads]
        
        print(f"✅ Discovered {len(top_leads)} qualified leads")
        
        return top_leads
    
    def _search_for_leads(self, query: str, icp: Dict) -> List[Dict]:
        """
        Search for leads using web search
        
        This is a simplified version - in production, you'd integrate with:
        - Apollo.io API
        - Clearbit API
        - LinkedIn Sales Navigator
        - Company databases
        """
        
        print(f"  🔎 Searching: {query}")
        
        # Generate synthetic leads for demo
        # In production, replace with actual web search/API calls
        leads = self._generate_sample_leads(query, icp)
        
        return leads
    
    def _generate_sample_leads(self, query: str, icp: Dict) -> List[Dict]:
        """Generate sample leads for demo purposes"""
        
        cc = icp.get("company_characteristics", {})
        industry = cc.get("industry", "Technology")
        
        # Sample company names by industry
        company_templates = {
            "B2B SaaS": ["DataFlow", "SalesHub", "CloudSync", "MarketPro", "TeamConnect"],
            "E-commerce": ["ShopFast", "CartMaster", "OnlineGoods", "FastShip", "WebStore"],
            "Healthcare": ["MedTech", "HealthFirst", "CareSync", "WellnessHub", "MediConnect"],
            "Financial Services": ["FinSecure", "BankTech", "PayStream", "WealthHub", "InvestPro"],
            "Manufacturing": ["FactoryTech", "ProduceLine", "ManuSys", "QualityPro", "IndustryHub"]
        }
        
        # Get templates for industry
        templates = company_templates.get(industry, ["TechCorp", "InnovateCo", "DataSystems"])
        
        leads = []
        for i, template in enumerate(templates[:3], 1):
            lead = {
                "company_name": f"{template} Inc.",
                "website": f"https://{template.lower()}.com",
                "industry": industry,
                "employee_count": self._get_random_size(cc.get("company_size")),
                "revenue_estimate": cc.get("revenue_range", "$5M-$20M"),
                "location": cc.get("geography", "United States"),
                "tech_stack": cc.get("tech_stack", [])[:2],
                "recent_activity": ["Hiring for sales team", "Recent product launch"],
                "decision_makers": [
                    {
                        "name": f"Contact {i}",
                        "title": icp.get("buyer_persona", {}).get("job_titles", ["VP Sales"])[0] if icp.get("buyer_persona", {}).get("job_titles") else "VP Sales",
                        "email": f"contact{i}@{template.lower()}.com"
                    }
                ],
                "icp_score": 0  # Will be calculated
            }
            leads.append(lead)
        
        return leads
    
    def _get_random_size(self, size_range: str) -> int:
        """Extract employee count from range"""
        if not size_range:
            return 100
        
        # Extract numbers from range like "50-200"
        numbers = re.findall(r'\d+', size_range)
        if len(numbers) >= 2:
            return (int(numbers[0]) + int(numbers[1])) // 2
        elif numbers:
            return int(numbers[0])
        return 100
    
    def _deduplicate_leads(self, leads: List[Dict]) -> List[Dict]:
        """Remove duplicate leads"""
        seen = set()
        unique = []
        
        for lead in leads:
            company_name = lead.get("company_name", "").lower()
            if company_name not in seen:
                seen.add(company_name)
                unique.append(lead)
        
        return unique
    
    def _score_leads(self, leads: List[Dict], icp: Dict) -> List[Dict]:
        """
        Score leads against ICP
        
        Score = Company Fit (40%) + Persona Fit (30%) + Intent Signals (20%) + Data Quality (10%)
        """
        
        for lead in leads:
            company_fit = self._calculate_company_fit(lead, icp)
            persona_fit = self._calculate_persona_fit(lead, icp)
            intent_signals = self._calculate_intent_score(lead, icp)
            data_quality = self._calculate_data_quality(lead)
            
            total_score = (
                company_fit * 0.4 +
                persona_fit * 0.3 +
                intent_signals * 0.2 +
                data_quality * 0.1
            )
            
            lead['icp_score'] = round(total_score, 1)
            lead['score_breakdown'] = {
                'company_fit': company_fit,
                'persona_fit': persona_fit,
                'intent_signals': intent_signals,
                'data_quality': data_quality
            }
        
        return leads
    
    def _calculate_company_fit(self, lead: Dict, icp: Dict) -> float:
        """Calculate company fit score (0-100)"""
        score = 0
        max_score = 100
        
        cc = icp.get("company_characteristics", {})
        
        # Industry match (25 points)
        if lead.get("industry") == cc.get("industry"):
            score += 25
        
        # Size match (20 points)
        target_size = self._get_random_size(cc.get("company_size", ""))
        lead_size = lead.get("employee_count", 0)
        if target_size * 0.5 <= lead_size <= target_size * 1.5:
            score += 20
        
        # Geography match (15 points)
        if cc.get("geography", "").lower() in lead.get("location", "").lower():
            score += 15
        
        # Tech stack match (20 points)
        target_tech = set(cc.get("tech_stack", []))
        lead_tech = set(lead.get("tech_stack", []))
        if target_tech and lead_tech:
            overlap = len(target_tech & lead_tech) / len(target_tech)
            score += 20 * overlap
        
        # Revenue match (20 points)
        if lead.get("revenue_estimate") == cc.get("revenue_range"):
            score += 20
        
        return min(score, max_score)
    
    def _calculate_persona_fit(self, lead: Dict, icp: Dict) -> float:
        """Calculate buyer persona fit score (0-100)"""
        score = 0
        
        bp = icp.get("buyer_persona", {})
        decision_makers = lead.get("decision_makers", [])
        
        if not decision_makers:
            return 0
        
        # Title match (50 points)
        target_titles = [t.lower() for t in bp.get("job_titles", [])]
        lead_titles = [dm.get("title", "").lower() for dm in decision_makers]
        
        for lead_title in lead_titles:
            for target_title in target_titles:
                if target_title in lead_title or lead_title in target_title:
                    score += 50
                    break
        
        # Has contact info (50 points)
        if any(dm.get("email") for dm in decision_makers):
            score += 50
        
        return min(score, 100)
    
    def _calculate_intent_score(self, lead: Dict, icp: Dict) -> float:
        """Calculate intent signal score (0-100)"""
        score = 0
        
        es = icp.get("engagement_signals", {})
        target_signals = [s.lower() for s in es.get("intent_signals", [])]
        lead_activity = [a.lower() for a in lead.get("recent_activity", [])]
        
        # Match signals
        for signal in target_signals:
            for activity in lead_activity:
                if signal in activity or activity in signal:
                    score += 50
        
        return min(score, 100)
    
    def _calculate_data_quality(self, lead: Dict) -> float:
        """Calculate data quality score (0-100)"""
        score = 0
        
        # Has website (20 points)
        if lead.get("website"):
            score += 20
        
        # Has employee count (20 points)
        if lead.get("employee_count"):
            score += 20
        
        # Has decision maker (30 points)
        if lead.get("decision_makers"):
            score += 30
        
        # Has contact email (30 points)
        if any(dm.get("email") for dm in lead.get("decision_makers", [])):
            score += 30
        
        return min(score, 100)
    
    def format_lead_list(self, leads: List[Dict]) -> str:
        """Format leads for display"""
        
        output = f"""
🎯 DISCOVERED LEADS
{'='*60}
Found {len(leads)} qualified leads

"""
        
        for i, lead in enumerate(leads, 1):
            priority = "🔥 HOT" if lead['icp_score'] >= 75 else "🌡️ WARM" if lead['icp_score'] >= 50 else "❄️ COLD"
            
            output += f"""
{priority} LEAD #{i}: {lead['company_name']}
Score: {lead['icp_score']}/100
──────────────────────────────────────────────────────────
Company: {lead['company_name']}
Industry: {lead['industry']}
Size: {lead['employee_count']} employees
Location: {lead['location']}
Website: {lead['website']}

Decision Maker:
"""
            
            if lead.get('decision_makers'):
                dm = lead['decision_makers'][0]
                output += f"  • {dm.get('name')} - {dm.get('title')}\n"
                if dm.get('email'):
                    output += f"    Email: {dm['email']}\n"
            
            output += f"""
Recent Activity:
"""
            for activity in lead.get('recent_activity', [])[:2]:
                output += f"  • {activity}\n"
            
            output += f"""
Score Breakdown:
  Company Fit: {lead['score_breakdown']['company_fit']:.0f}/100
  Persona Fit: {lead['score_breakdown']['persona_fit']:.0f}/100
  Intent Signals: {lead['score_breakdown']['intent_signals']:.0f}/100
  Data Quality: {lead['score_breakdown']['data_quality']:.0f}/100

"""
        
        output += "="*60 + "\n"
        
        return output


if __name__ == "__main__":
    # Test lead discovery
    print("="*60)
    print("TESTING LEAD DISCOVERY ENGINE")
    print("="*60 + "\n")
    
    # Sample ICP
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
    
    # Generate queries
    queries = engine.generate_search_queries(icp)
    print("Generated Search Queries:")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    print()
    
    # Discover leads
    leads = engine.discover_leads(icp, max_leads=5)
    
    # Display results
    print(engine.format_lead_list(leads))