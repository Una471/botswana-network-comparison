"""
AIRTABLE INTEGRATION FOR BOTSWANA NETWORK COMPARISON TOOL
Automates lead capture, affiliate tracking, and email generation
"""

import requests
import json
from datetime import datetime

class AirtableAutomation:
    """
    Handles all Airtable operations for the network comparison tool
    This replaces traditional SQL databases with Basha's preferred Airtable approach
    """
    
    def __init__(self, api_key, base_id):
        """
        Initialize Airtable connection
        
        Args:
            api_key: Your Airtable API key (get from airtable.com/account)
            base_id: Your base ID (from Airtable URL)
        """
        self.api_key = api_key
        self.base_id = base_id
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.base_url = f'https://api.airtable.com/v0/{base_id}'
    
    def create_base_tables(self):
        """
        AIRTABLE TABLE STRUCTURE
        Create these tables manually in Airtable:
        
        1. LEADS TABLE
        Fields:
        - ID (Auto number)
        - Email (Email)
        - Name (Single line text)
        - Recommended_Network (Single select: Orange, Mascom, BTC)
        - Priority (Single line text)
        - Usage_Type (Single line text)
        - Location (Single line text)
        - Created_Time (Created time)
        - Status (Single select: New, Contacted, Converted)
        - AI_Email_Draft (Long text)
        
        2. CLICKS TABLE
        Fields:
        - ID (Auto number)
        - Network (Single select: Orange, Mascom, BTC)
        - Action (Single line text)
        - Session_ID (Single line text)
        - Timestamp (Created time)
        - Converted (Checkbox)
        
        3. REVIEWS TABLE
        Fields:
        - ID (Auto number)
        - Network (Single select: Orange, Mascom, BTC)
        - Rating (Number, 0-10)
        - Comment (Long text)
        - User_Email (Email)
        - Verified (Checkbox)
        - Created_Time (Created time)
        
        4. AFFILIATE_EARNINGS TABLE
        Fields:
        - ID (Auto number)
        - Network (Single select: Orange, Mascom, BTC)
        - Commission_Date (Date)
        - Amount (Currency)
        - Lead_ID (Link to LEADS)
        - Status (Single select: Pending, Paid)
        """
        pass
    
    def add_lead(self, lead_data):
        """
        Capture a new lead and auto-generate follow-up email
        
        Args:
            lead_data: dict with email, name, network, priority, usage, location
        """
        # Generate AI email based on lead data
        ai_email = self.generate_email(lead_data)
        
        # Prepare Airtable record
        record = {
            "fields": {
                "Email": lead_data.get('email'),
                "Name": lead_data.get('name', ''),
                "Recommended_Network": lead_data.get('network'),
                "Priority": lead_data.get('priority'),
                "Usage_Type": lead_data.get('usage'),
                "Location": lead_data.get('location'),
                "Status": "New",
                "AI_Email_Draft": ai_email
            }
        }
        
        # POST to Airtable
        response = requests.post(
            f"{self.base_url}/LEADS",
            headers=self.headers,
            json={"records": [record]}
        )
        
        return response.json()
    
    def generate_email(self, lead_data):
        """
        AUTO-GENERATE PERSONALIZED EMAIL
        This is Basha's magic - AI writes the email, you just copy & send
        """
        network = lead_data.get('network')
        name = lead_data.get('name', 'there')
        priority = lead_data.get('priority')
        
        email_template = f"""
Subject: Your Perfect Network Match: {network} 🎯

Hi {name}!

Thanks for using our Network Comparison Tool! Based on your answers, we found that **{network}** is your best match.

Here's why {network} is perfect for you:

{"✅ **Best Pricing**: Mascom offers the most affordable data packages, perfect for budget-conscious users." if network == "Mascom" else ""}
{"✅ **Fastest Speed**: Orange has the fastest 4G/5G network in Botswana, ideal for streaming and downloads." if network == "Orange" else ""}
{"✅ **Best Service**: BTC has the highest customer satisfaction ratings (8.07/10)." if network == "BTC" else ""}

**Your Next Steps:**

1. **Visit {network}**: [INSERT AFFILIATE LINK]
2. **Ask for**: Student/Corporate discount if applicable
3. **Mention**: Network comparison tool (they may have special offers!)

**Quick Comparison:**
- Overall Rating: [INSERT SCORE]/10
- Customer Service: [INSERT SCORE]/10
- Pricing: [INSERT SCORE]/10

Have questions? Just reply to this email - we're here to help!

Cheers,
Botswana Network Comparison Team

P.S. Save P50-P200/month by switching to the right network! 💰

---
[Unsubscribe] | [Update Preferences]
        """
        
        return email_template.strip()
    
    def track_click(self, click_data):
        """
        Track affiliate clicks for commission attribution
        
        Args:
            click_data: dict with network, action, session_id
        """
        record = {
            "fields": {
                "Network": click_data.get('network'),
                "Action": click_data.get('action'),
                "Session_ID": click_data.get('session_id'),
                "Converted": False
            }
        }
        
        response = requests.post(
            f"{self.base_url}/CLICKS",
            headers=self.headers,
            json={"records": [record]}
        )
        
        return response.json()
    
    def add_review(self, review_data):
        """
        Add user-submitted review (grows your database!)
        
        Args:
            review_data: dict with network, rating, comment, email
        """
        record = {
            "fields": {
                "Network": review_data.get('network'),
                "Rating": review_data.get('rating'),
                "Comment": review_data.get('comment'),
                "User_Email": review_data.get('email'),
                "Verified": False  # Verify later
            }
        }
        
        response = requests.post(
            f"{self.base_url}/REVIEWS",
            headers=self.headers,
            json={"records": [record]}
        )
        
        return response.json()
    
    def get_pending_emails(self):
        """
        Get all new leads that need follow-up emails
        Returns leads with Status = "New" and pre-generated AI emails
        """
        formula = "AND({Status}='New', {Email}!=BLANK())"
        
        response = requests.get(
            f"{self.base_url}/LEADS",
            headers=self.headers,
            params={'filterByFormula': formula}
        )
        
        return response.json()
    
    def update_lead_status(self, record_id, new_status):
        """
        Update lead status after sending email
        
        Args:
            record_id: Airtable record ID
            new_status: 'New', 'Contacted', or 'Converted'
        """
        record = {
            "fields": {
                "Status": new_status
            }
        }
        
        response = requests.patch(
            f"{self.base_url}/LEADS/{record_id}",
            headers=self.headers,
            json=record
        )
        
        return response.json()
    
    def get_dashboard_stats(self):
        """
        Get stats for business dashboard
        Returns total leads, clicks, conversion rate, etc.
        """
        # Get all leads
        leads_response = requests.get(f"{self.base_url}/LEADS", headers=self.headers)
        leads = leads_response.json().get('records', [])
        
        # Get all clicks
        clicks_response = requests.get(f"{self.base_url}/CLICKS", headers=self.headers)
        clicks = clicks_response.json().get('records', [])
        
        stats = {
            'total_leads': len(leads),
            'total_clicks': len(clicks),
            'conversion_rate': len([l for l in leads if l['fields'].get('Status') == 'Converted']) / max(len(leads), 1) * 100,
            'popular_network': self._most_common([l['fields'].get('Recommended_Network') for l in leads])
        }
        
        return stats
    
    def _most_common(self, lst):
        """Helper to find most common item in list"""
        return max(set(lst), key=lst.count) if lst else 'N/A'


# ⚠️ EXAMPLE USAGE - FOR TESTING ONLY
# DO NOT USE IN PRODUCTION!
if __name__ == "__main__":
    """
    HOW TO USE THIS IN YOUR STREAMLIT APP
    
    IMPORTANT: Never hard-code API keys in production!
    Use Streamlit Secrets instead.
    """
    
    print("=" * 60)
    print("AIRTABLE INTEGRATION TEST")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This is for testing only!")
    print("⚠️  Do NOT hard-code your API keys in production!")
    print()
    print("How to use in Streamlit:")
    print()
    print("1. Add your keys to Streamlit Secrets:")
    print("   Go to: https://share.streamlit.io/")
    print("   Click your app → Settings → Secrets")
    print("   Add:")
    print("""
    [airtable]
    api_key = "YOUR_AIRTABLE_API_KEY"
    base_id = "YOUR_BASE_ID"
    """)
    print()
    print("2. In your code, use:")
    print("""
    import streamlit as st
    from airtable_integration import AirtableAutomation
    
    airtable = AirtableAutomation(
        api_key=st.secrets["airtable"]["api_key"],
        base_id=st.secrets["airtable"]["base_id"]
    )
    """)
    print()
    print("=" * 60)
    print()
    
    # Example of how it would work (don't actually run without keys)
    print("Example usage:")
    print()
    print("# When user completes quiz:")
    print("lead_data = {")
    print("    'email': 'user@example.com',")
    print("    'name': 'John Doe',")
    print("    'network': 'Mascom',")
    print("    'priority': 'Best Price',")
    print("    'usage': 'Medium',")
    print("    'location': 'Gaborone'")
    print("}")
    print()
    print("result = airtable.add_lead(lead_data)")
    print("# → Saves to Airtable + generates email automatically!")
    print()
    print("# When user clicks affiliate link:")
    print("click_data = {")
    print("    'network': 'Mascom',")
    print("    'action': 'cta_click',")
    print("    'session_id': 'session_12345'")
    print("}")
    print()
    print("airtable.track_click(click_data)")
    print("# → Tracks the click for commission attribution")
    print()
    print("=" * 60)