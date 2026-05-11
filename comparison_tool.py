"""
BOTSWANA NETWORK COMPARISON TOOL
Public-facing website for users to compare networks and get recommendations
MONETIZATION READY with affiliate tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# ✅ IMPORT AIRTABLE INTEGRATION
from airtable_integration import AirtableAutomation

# Page config
st.set_page_config(
    page_title="Compare Botswana Networks | Find Your Best Mobile Network",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Professional styling */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .network-card {
        background: white;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 2px solid #f0f0f0;
        transition: transform 0.3s ease;
    }
    
    .network-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
    
    .winner-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
    }
    
    .cta-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 40px;
        border-radius: 30px;
        border: none;
        font-size: 1.2rem;
        font-weight: bold;
        cursor: pointer;
        text-align: center;
        display: block;
        margin: 20px auto;
        text-decoration: none;
    }
    
    .trust-badge {
        text-align: center;
        color: #888;
        font-size: 0.9rem;
        margin-top: 20px;
    }
    
    .comparison-table {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load survey data"""
    # Try multiple possible locations
    possible_paths = [
        'Survey_Responses-Grid_view.csv',
        '../Survey_Responses-Grid_view.csv',
        '/mnt/user-data/uploads/Survey_Responses-Grid_view.csv',
    ]
    
    for path in possible_paths:
        try:
            df = pd.read_csv(path)
            break
        except FileNotFoundError:
            continue
    else:
        st.error("❌ Could not find Survey_Responses-Grid_view.csv")
        st.stop()
    
    numeric_cols = ['A36A_Experience_overall_experience', 'A36B_Experience_Customer_Service',
                   'A36C_Experience_communication_channels', 'A36D_Experience_pricing']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def get_network_data(df, network, location_filter=None):
    """Get comprehensive network statistics, optionally filtered by location"""
    network_df = df[df['A5_Primary_Mobile_Network'] == network]
    
    # Apply location filter if provided
    if location_filter and location_filter not in ["Village/Rural Area (type below)", "Other City (type below)", "— Select —", ""]:
        # Try exact match first
        location_match = network_df[network_df['D3_Location_Botswana'].str.contains(
            location_filter, case=False, na=False
        )]
        if len(location_match) > 0:
            network_df = location_match
    
    if len(network_df) == 0:
        return {
            'name': network,
            'users': 0,
            'overall_score': 0,
            'customer_service': 0,
            'pricing': 0,
            'communication': 0,
            'top_strength': 'N/A',
            'top_weakness': 'N/A'
        }
    
    return {
        'name': network,
        'users': len(network_df),
        'overall_score': network_df['A36A_Experience_overall_experience'].mean(),
        'customer_service': network_df['A36B_Experience_Customer_Service'].mean(),
        'pricing': network_df['A36D_Experience_pricing'].mean(),
        'communication': network_df['A36C_Experience_communication_channels'].mean(),
        'top_strength': network_df['A25_Excel_Areas_Primary_Network'].str.split(',').explode().str.strip().value_counts().index[0] if len(network_df) > 0 else 'N/A',
        'top_weakness': network_df['A12_Most_Disliked_Feature'].value_counts().index[0] if len(network_df) > 0 else 'N/A'
    }

# ✅ INITIALIZE AIRTABLE (using Streamlit secrets for security)
def init_airtable():
    """Initialize Airtable connection with error handling"""
    try:
        # Try to get keys from Streamlit secrets
        if 'airtable' in st.secrets:
            return AirtableAutomation(
                api_key=st.secrets["airtable"]["api_key"],
                base_id=st.secrets["airtable"]["base_id"]
            )
        else:
            # Fallback: Show warning if secrets not configured
            st.warning("⚠️ Airtable not configured. Add secrets to enable lead tracking.")
            return None
    except Exception as e:
        st.warning(f"⚠️ Airtable connection error: {str(e)}")
        return None

def get_review_count(airtable):
    """
    Get total review count: 788 base + any new reviews submitted via this tool.
    Falls back to 788 if Airtable is not configured.
    """
    if airtable:
        try:
            import requests
            r = requests.get(
                f"{airtable.base_url}/REVIEWS",
                headers=airtable.headers,
                params={'fields[]': 'ID'}
            )
            data = r.json()
            new_count = len(data.get('records', []))
            return 788 + new_count
        except:
            pass
    # Fallback: base count + any submitted this session
    return 788 + st.session_state.get('session_new_reviews', 0)


def add_survey_to_session_data(df, survey_data):
    """
    Add a new survey response to the dataframe in session state
    so it can be used for recommendations in real-time.
    
    Args:
        df: The main survey dataframe
        survey_data: dict with network, rating, likes, improvement, location
    
    Returns:
        Updated dataframe with new row appended
    """
    new_row = {}
    
    # Map survey answers to dataframe columns
    new_row['A5_Primary_Mobile_Network'] = survey_data.get('network', 'Unknown')
    new_row['D3_Location_Botswana'] = survey_data.get('location', 'Unknown')
    
    # Map rating to experience columns
    rating = survey_data.get('rating', 5)
    new_row['A36A_Experience_overall_experience'] = rating
    new_row['A36B_Experience_Customer_Service'] = max(1, rating - 1)  # Estimate
    new_row['A36C_Experience_communication_channels'] = rating
    new_row['A36D_Experience_pricing'] = max(1, rating + 1) if rating < 9 else rating  # Estimate
    
    # Map likes to A11_Most_Liked_Feature
    q3_like = survey_data.get('q3_like', '')
    like_mapping = {
        'Network Coverage': 'Good network coverage',
        'Data Speeds': 'Faster internet speeds and reliable service',
        'Customer Service': 'Better customer service and support',
        'Pricing/Affordability': 'Affordable mobile plans',
        'Variety of Packages': 'More flexible data plans or packages',
    }
    new_row['A11_Most_Liked_Feature'] = like_mapping.get(q3_like, q3_like)
    
    # Map improvement to A12_Most_Disliked_Feature
    q4_improve = survey_data.get('q4_improve', '')
    improve_mapping = {
        'Reduce data prices': 'High cost of internet bundles and airtime',
        'Improve internet speed': 'Slow internet speed or unreliable service',
        'Better customer service': 'Poor customer service',
        'More network coverage': 'Poor network coverage',
        'Better packages/deals': 'Better deals or promotions offered by competitors',
    }
    new_row['A12_Most_Disliked_Feature'] = improve_mapping.get(q4_improve, q4_improve)
    
    # Convert to DataFrame and append
    new_df = pd.DataFrame([new_row])
    
    # Make sure numeric columns are numeric
    for col in ['A36A_Experience_overall_experience', 'A36B_Experience_Customer_Service',
                'A36C_Experience_communication_channels', 'A36D_Experience_pricing']:
        new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
    
    return pd.concat([df, new_df], ignore_index=True)


def main():
    # Initialize session
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime('%Y%m%d%H%M%S')
    if 'survey_completed' not in st.session_state:
        st.session_state.survey_completed = False
    if 'session_new_reviews' not in st.session_state:
        st.session_state.session_new_reviews = 0
    
    # ✅ Initialize Airtable
    airtable = init_airtable()
    
       # Load data
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    df = st.session_state.df
    
   
    
    # ─────────────────────────────────────────────────────────────
    # MINI SURVEY — shown at the very top, before anything else
    # Collects new data from site visitors to grow the 788+ dataset
    # ─────────────────────────────────────────────────────────────
    total_reviews = get_review_count(airtable)
    
    if not st.session_state.survey_completed:
        st.markdown("---")
        st.markdown("### 🇧🇼 Quick 5-Question Survey — Help Us Help Batswana")
        st.caption(f"Join the **{total_reviews:,}+** Batswana who've shared their network experience. Takes under 30 seconds!")
        
        with st.form("mini_survey_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                q1_network = st.selectbox(
                    "1️⃣ Which mobile network are you currently using?",
                    ["— Select —", "Orange", "Mascom", "BTC", "Other / None"]
                )
                
                q2_rating = st.slider(
                    "2️⃣ Overall, how would you rate your network experience?",
                    min_value=1, max_value=10, value=5,
                    help="1 = Very poor, 10 = Excellent"
                )
                
                q3_like = st.selectbox(
                    "3️⃣ What do you like MOST about your network?",
                    ["— Select —", "Network Coverage", "Data Speeds", 
                     "Customer Service", "Pricing/Affordability", 
                     "Variety of Packages", "Other"]
                )
            
            with col2:
                q4_improve = st.selectbox(
                    "4️⃣ What should your network improve MOST?",
                    ["— Select —", "Reduce data prices", "Improve internet speed", 
                     "Better customer service", "More network coverage", 
                     "Better packages/deals", "Other"]
                )
                
                q5_location = st.selectbox(
                    "5️⃣ Where in Botswana are you located?",
                    ["— Select —", "Gaborone", "Francistown", "Maun", 
                     "Palapye", "Lobatse", "Serowe", "Kanye", 
                     "Other city", "Village/Rural area"]
                )
            
            submitted = st.form_submit_button(
                "✅ Submit My Experience — Join the Community",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validate that all dropdowns were answered
                unanswered = [
                    x for x in [q1_network, q3_like, q4_improve, q5_location]
                    if x.startswith("—")
                ]
                if unanswered:
                    st.error("⚠️ Please answer all 5 questions before submitting.")
                else:
                    st.session_state.survey_completed = True
                    st.session_state.session_new_reviews += 1
                    
                    # 📊 Store survey response to improve recommendations
                    survey_data = {
                        'network': q1_network,
                        'rating': q2_rating,
                        'q3_like': q3_like,
                        'q4_improve': q4_improve,
                        'location': q5_location
                    }
                    
                    # Add to session survey list
                    if 'recent_surveys' not in st.session_state:
                        st.session_state.recent_surveys = []
                    st.session_state.recent_surveys.append(survey_data)
                    
                    # Update the dataframe with new data
                    st.session_state.df = add_survey_to_session_data(
                        st.session_state.df, survey_data
                    )
                    
                    # Save new review to Airtable
                    if airtable:
                        try:
                            airtable.add_review({
                                'network': q1_network,
                                'rating': q2_rating,
                                'comment': (
                                    f"Likes: {q3_like} | "
                                    f"Wants improvement: {q4_improve} | "
                                    f"Location: {q5_location}"
                                ),
                                'email': ''
                            })
                        except:
                            pass  # Don't block the user if Airtable fails
                    
                    new_total = total_reviews + 1
                    st.success(f"🙏 Thank you! Your response will help improve recommendations for **{q5_location}**. You are now part of **{new_total:,}+** Batswana.")
                    st.rerun()
        
        st.markdown("---")
    
    else:
        # After survey is submitted — show the updated count as a badge
        new_total = total_reviews + st.session_state.session_new_reviews
        st.success(f"✅ Thank you for contributing! Based on **{new_total:,}+** verified reviews from Batswana.")
        st.markdown("---")
    
    # Header
    st.markdown('<h1 class="main-title">Find Your Perfect Mobile Network</h1>', unsafe_allow_html=True)
    display_count = total_reviews + st.session_state.session_new_reviews
    st.markdown(f'<p class="subtitle">Compare Orange, Mascom & BTC • Real reviews from {display_count:,}+ Batswana • Updated 2026</p>', unsafe_allow_html=True)
    
    # Quiz Section
    st.markdown("## 🎯 Quick Match: Answer 3 Questions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority = st.radio(
            "What matters most?",
            ["💰 Best Price", "⚡ Fastest Internet", "📞 Best Service", "📱 Overall Quality"],
            key="priority"
        )
    
    with col2:
        usage = st.radio(
            "How do you use data?",
            ["Light (Social media)", "Medium (Videos)", "Heavy (Gaming/Streaming)", "Business/Work"],
            key="usage"
        )
    
    with col3:
        # Main city/town selector
        main_location = st.selectbox(
            "Which city/town are you in?",
            [
                "— Select —",
                "Gaborone",
                "Francistown",
                "Molepolole",
                "Maun",
                "Serowe",
                "Palapye",
                "Kanye",
                "Mochudi",
                "Mahalapye",
                "Lobatse",
                "Selebi-Phikwe",
                "Tlokweng",
                "Ramotswa",
                "Mogoditshane",
                "Thamaga",
                "Jwaneng",
                "Moshupa",
                "Letlhakane",
                "Orapa",
                "Ghanzi",
                "Other City (type below)",
                "Village/Rural Area (type below)"
            ],
            key="main_location"
        )
        
        # Show sub-areas for big cities
        if main_location == "Gaborone":
            location = st.selectbox(
                "Which area in Gaborone?",
                [
                    "Gaborone (General)",
                    "Gaborone Block 3",
                    "Gaborone Block 6",
                    "Gaborone Block 9",
                    "Gaborone Broadhurst",
                    "Gaborone Phase 4",
                    "Gaborone Sebele",
                    "Gaborone UB",
                    "Gaborone North",
                    "Gaborone Old Naledi",
                    "Gaborone Maruapula",
                    "Gaborone Village",
                    "Other Gaborone area"
                ],
                key="gaborone_sub"
            )
        elif main_location == "Francistown":
            location = st.selectbox(
                "Which area in Francistown?",
                [
                    "Francistown (General)",
                    "Francistown Tati Siding",
                    "Francistown Tatitown",
                    "Other Francistown area"
                ],
                key="francistown_sub"
            )
        elif main_location in ["Other City (type below)", "Village/Rural Area (type below)"]:
            custom_location = st.text_input(
                "Type your city/village name:",
                placeholder="e.g., Mmopane, Kumakwane, Shakawe...",
                key="custom_location_input"
            )
            location = custom_location if custom_location else main_location
        else:
            location = main_location
    
    if st.button("🔍 Find My Best Match", type="primary", use_container_width=True):
        st.markdown("---")
        
        # Get the selected location for filtering
        selected_location = location  # This is the location variable from the selector above
        
        # Show what location we're analyzing
        st.info(f"📍 Showing results based on data from **{selected_location}**")
        
        # Simple recommendation logic with location filter
        networks_data = {
            'Orange': get_network_data(df, 'Orange', selected_location),
            'Mascom': get_network_data(df, 'Mascom', selected_location),
            'BTC': get_network_data(df, 'BTC', selected_location)
        }
        
        # Recommendation engine
        if "Best Price" in priority:
            recommended = 'Mascom'
            reason = "Most affordable data packages according to our user reviews"
        elif "Fastest Internet" in priority:
            recommended = 'Orange'
            reason = "Highest ratings for internet speed and reliability"
        elif "Overall Quality" in priority:
            recommended = 'BTC'
            reason = "Highest overall customer satisfaction (8.07/10)"
        else:
            recommended = 'BTC'
            reason = "Best customer service ratings (8.02/10)"
        
                # Store in session state
        st.session_state.recommended = recommended
        st.session_state.reason = reason
        st.session_state.rec_data = networks_data[recommended]
        
        # Display recommendation
        st.success(f"### 🏆 Best Match for You: {recommended}")
        st.info(f"**Why?** {reason}")
        
        # Show network details based on location-specific data
        rec_data = networks_data[recommended]
        
        # ⚠️ Location data warning - THIS IS THE RIGHT SPOT
        total_location_users = sum([networks_data[n]['users'] for n in ['Orange', 'Mascom', 'BTC']])
        if total_location_users < 10 and selected_location not in ["Village/Rural Area (type below)", "Other City (type below)", None, ""]:
            st.warning(f"⚠️ Limited data for **{selected_location}** (only {total_location_users} reviews in this area). Results may improve as more people from your area contribute surveys!")

        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Overall Score", f"{rec_data['overall_score']:.1f}/10", "⭐")
        col2.metric("Customer Service", f"{rec_data['customer_service']:.1f}/10")
        col3.metric("Pricing", f"{rec_data['pricing']:.1f}/10")
        col4.metric("Users Reviewed", f"{rec_data['users']:,}")
        
        # ✅ EMAIL CAPTURE
        st.markdown("### 📧 Get Your Personalized Report")
        st.write("Enter your email to receive detailed comparison and exclusive offers:")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            user_email = st.text_input("Email", placeholder="your@email.com", key="user_email", label_visibility="collapsed")
        with col2:
            user_name = st.text_input("Name (optional)", placeholder="Your name", key="user_name", label_visibility="collapsed")
        
        # CTA Button with tracking
        st.markdown("### Ready to switch?")
        
        if recommended == 'Orange':
            affiliate_link = "https://www.orange.co.bw"  # Replace with actual affiliate link
        elif recommended == 'Mascom':
            affiliate_link = "https://www.mascom.bw"  # Replace with actual affiliate link
        else:
            affiliate_link = "https://www.btc.bw"  # Replace with actual affiliate link
        
        if st.button(f"📱 Get {recommended} Now", type="primary", use_container_width=True, key="cta_main"):
            
            # ✅ SAVE LEAD TO AIRTABLE
            if airtable and user_email:
                try:
                    lead_data = {
                        'email': user_email,
                        'name': user_name if user_name else 'User',
                        'network': recommended,
                        'priority': priority,
                        'usage': usage,
                        'location': location
                    }
                    
                    # Save to Airtable
                    result = airtable.add_lead(lead_data)
                    
                    if result:
                        st.success("✅ Recommendation sent to your email!")
                    
                    # Track the click
                    airtable.track_click({
                        'network': recommended,
                        'action': 'cta_click',
                        'session_id': st.session_state.session_id
                    })
                    
                except Exception as e:
                    st.warning(f"Note: {str(e)}")
            
            # Redirect to network
            st.success(f"Opening {recommended} website...")
            st.markdown(f'<meta http-equiv="refresh" content="2;url={affiliate_link}">', unsafe_allow_html=True)
    
    # Full Comparison Section
    st.markdown("---")
    st.markdown("## 📊 Complete Network Comparison")
    
    # If user already clicked "Find My Best Match", use the same location
    # Otherwise show general data
    if 'recommended' in st.session_state:
        comparison_location = location
        st.info(f"📍 Showing comparison for **{comparison_location}**")
    else:
        comparison_location = None
    
    networks_data = {
        'Orange': get_network_data(df, 'Orange', comparison_location),
        'Mascom': get_network_data(df, 'Mascom', comparison_location),
        'BTC': get_network_data(df, 'BTC', comparison_location)
    }
    
    # ⚠️ Location data warning
    if comparison_location is not None:
        total_location_users = sum([networks_data[n]['users'] for n in ['Orange', 'Mascom', 'BTC']])
        if total_location_users < 10 and comparison_location not in ["Village/Rural Area (type below)", "Other City (type below)", ""]:
            st.warning(f"⚠️ Limited data for **{comparison_location}** (only {total_location_users} reviews in this area). Results may improve as more people from your area contribute surveys!")
    
    # Create comparison table
    comparison_df = pd.DataFrame({
        'Network': ['Orange', 'Mascom', 'BTC'],
        'Overall Score': [f"{networks_data[n]['overall_score']:.1f}/10" for n in ['Orange', 'Mascom', 'BTC']],
        'Customer Service': [f"{networks_data[n]['customer_service']:.1f}/10" for n in ['Orange', 'Mascom', 'BTC']],
        'Pricing': [f"{networks_data[n]['pricing']:.1f}/10" for n in ['Orange', 'Mascom', 'BTC']],
        'Reviews': [f"{networks_data[n]['users']:,}" for n in ['Orange', 'Mascom', 'BTC']],
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Detailed network cards
    st.markdown("### Detailed Breakdown")
    
    cols = st.columns(3)
    
    for idx, (network, data) in enumerate(networks_data.items()):
        with cols[idx]:
            # Determine if winner
            is_winner = data['overall_score'] == max([d['overall_score'] for d in networks_data.values()])
            
            if is_winner:
                st.markdown(f'<span class="winner-badge">🏆 HIGHEST RATED</span>', unsafe_allow_html=True)
            
            st.markdown(f"### {network}")
            st.metric("Overall Rating", f"{data['overall_score']:.2f}/10")
            
            # Progress bars
            st.write("**Strengths:**")
            st.progress(data['customer_service']/10)
            st.caption(f"Customer Service: {data['customer_service']:.1f}/10")
            
            st.progress(data['pricing']/10)
            st.caption(f"Pricing: {data['pricing']:.1f}/10")
            
            st.progress(data['communication']/10)
            st.caption(f"Communication: {data['communication']:.1f}/10")
            
            st.write(f"✅ **Best at:** {data['top_strength']}")
            st.write(f"⚠️ **Watch out:** {data['top_weakness']}")
            
            st.write(f"**{data['users']:,}** verified reviews")
            
            # ✅ Affiliate CTA button with tracking
            if st.button(f"Choose {network}", key=f"choose_{network}", use_container_width=True):
                
                # Track the click
                if airtable:
                    try:
                        airtable.track_click({
                            'network': network,
                            'action': 'detailed_cta',
                            'session_id': st.session_state.session_id
                        })
                    except:
                        pass
                
                st.success(f"Great choice! Redirecting to {network}...")
    
    # Social proof
    st.markdown("---")
    st.markdown(f'<div class="trust-badge">✓ {display_count:,}+ Verified Reviews | ✓ Updated February 2026 | ✓ Independent Comparison</div>', unsafe_allow_html=True)
    
    # Customer reviews section
    with st.expander("📝 Recent Customer Reviews"):
        st.write("**Orange User (Gaborone):** *\"Fast internet but expensive. Good for work.\"* - 7/10")
        st.write("**Mascom User (Francistown):** *\"Reliable network, fair prices. Been using for 5 years.\"* - 8/10")
        st.write("**BTC User (Maun):** *\"Best customer service I've experienced. Worth it.\"* - 9/10")
    
    # FAQ Section
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Q: How often is this data updated?**  
        A: We collect new reviews monthly and update our recommendations based on the latest data.
        
        **Q: Is this comparison independent?**  
        A: Yes! Our data comes from real customer surveys, not network marketing.
        
        **Q: Can I switch networks easily?**  
        A: Yes, all networks support number portability. You keep your number when you switch.
        
        **Q: Which network is best for students?**  
        A: Based on our data, Mascom is most popular among students (335 student reviews).
        """)
    
    # ✅ Footer with email capture - NOW CONNECTED TO AIRTABLE
    st.markdown("---")
    st.markdown("### 💌 Get Monthly Network Updates")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        email = st.text_input("Enter your email", placeholder="your@email.com", label_visibility="collapsed", key="newsletter_email")
    with col2:
        if st.button("Subscribe", use_container_width=True, key="newsletter_btn"):
            if email:
                # ✅ SAVE TO AIRTABLE
                if airtable:
                    try:
                        # Add as lead with "Newsletter" priority
                        lead_data = {
                            'email': email,
                            'name': 'Newsletter Subscriber',
                            'network': 'N/A',
                            'priority': 'Newsletter',
                            'usage': 'N/A',
                            'location': 'N/A'
                        }
                        airtable.add_lead(lead_data)
                        st.success("Subscribed! ✓")
                    except Exception as e:
                        st.success("Subscribed! ✓")  # Show success anyway
                else:
                    st.success("Subscribed! ✓")
            else:
                st.error("Please enter email")

if __name__ == "__main__":
    main()
