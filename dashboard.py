"""
BOTSWANA TELECOM NETWORK COMPARISON DASHBOARD
Interactive Streamlit App
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page config
st.set_page_config(
    page_title="Botswana Network Comparison",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-box {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and process survey data"""
    # Try multiple possible locations
    possible_paths = [
        'Survey_Responses-Grid_view.csv',  # Same folder
        '../Survey_Responses-Grid_view.csv',  # Parent folder
        '/mnt/user-data/uploads/Survey_Responses-Grid_view.csv',  # Cloud/Linux
    ]
    
    for path in possible_paths:
        try:
            df = pd.read_csv(path)
            print(f"✓ Data loaded from: {path}")
            break
        except FileNotFoundError:
            continue
    else:
        st.error("❌ Could not find Survey_Responses-Grid_view.csv. Please ensure it's in the same folder as dashboard.py")
        st.stop()
    
    # Convert numeric columns
    numeric_cols = ['A36A_Experience_overall_experience', 'A36B_Experience_Customer_Service',
                   'A36C_Experience_communication_channels', 'A36D_Experience_pricing']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def calculate_network_scores(df, network):
    """Calculate comprehensive scores for a network"""
    network_data = df[df['A5_Primary_Mobile_Network'] == network]
    
    scores = {
        'Overall Experience': network_data['A36A_Experience_overall_experience'].mean(),
        'Customer Service': network_data['A36B_Experience_Customer_Service'].mean(),
        'Communication': network_data['A36C_Experience_communication_channels'].mean(),
        'Pricing': network_data['A36D_Experience_pricing'].mean(),
        'Users': len(network_data)
    }
    
    return scores

def main():
    # Header
    st.markdown('<p class="main-header">📱 Botswana Network Comparison</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Real customer insights • 788 verified reviews • Updated 2025</p>', unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filter Options")
    
    # Age filter
    age_groups = df['D1_Age'].dropna().unique().tolist()
    selected_age = st.sidebar.multiselect("Age Group", age_groups, default=age_groups)
    
    # Income filter
    income_levels = df['D7_Monthly_Income_Allowance'].dropna().unique().tolist()
    selected_income = st.sidebar.multiselect("Income Level", income_levels, default=income_levels)
    
    # Location filter
    locations = df['D3_Location_Botswana'].dropna().unique().tolist()
    if len(locations) > 0:
        default_locations = sorted(locations)[:min(3, len(locations))]
        selected_location = st.sidebar.multiselect("Location", sorted(locations)[:20], default=default_locations)
    else:
        selected_location = []
    
    # Apply filters
    filtered_df = df.copy()
    if selected_age:
        filtered_df = filtered_df[filtered_df['D1_Age'].isin(selected_age)]
    if selected_income:
        filtered_df = filtered_df[filtered_df['D7_Monthly_Income_Allowance'].isin(selected_income)]
    if selected_location:
        filtered_df = filtered_df[filtered_df['D3_Location_Botswana'].isin(selected_location)]
    
    st.sidebar.info(f"Showing {len(filtered_df)} responses")
    
    # Check if filtered data is empty
    if len(filtered_df) == 0:
        st.error("⚠️ No data matches your filters. Please adjust your selections.")
        st.stop()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🏆 Network Comparison", "💭 Customer Insights", "📈 Market Analysis", "🎯 Recommendations"])
    
    with tab1:
        st.header("Market Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Responses", f"{len(filtered_df):,}")
        with col2:
            avg_satisfaction = filtered_df['A36A_Experience_overall_experience'].mean()
            if pd.isna(avg_satisfaction):
                st.metric("Avg. Satisfaction", "N/A")
            else:
                st.metric("Avg. Satisfaction", f"{avg_satisfaction:.1f}/10")
        with col3:
            if len(filtered_df) > 0 and not filtered_df['A5_Primary_Mobile_Network'].mode().empty:
                dominant_network = filtered_df['A5_Primary_Mobile_Network'].mode()[0]
                st.metric("Market Leader", dominant_network)
            else:
                st.metric("Market Leader", "N/A")
        with col4:
            btc_churn = len(filtered_df[filtered_df['A3_Networks_Stopped_Using'].str.contains('BTC', na=False)])
            st.metric("BTC Churn Rate", f"{btc_churn} users")
        
        st.markdown("---")
        
        # Market share visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Primary Network Market Share")
            market_share = filtered_df['A5_Primary_Mobile_Network'].value_counts()
            fig = px.pie(
                values=market_share.values,
                names=market_share.index,
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1'],
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top of Mind Brand Awareness")
            brand_awareness = filtered_df['A1_Top_of_Mind_Brand'].value_counts()
            
            # Create a proper DataFrame for the bar chart
            bar_data = pd.DataFrame({
                'Brand': brand_awareness.index.tolist(),
                'Mentions': brand_awareness.values.tolist()
            })
            
            fig = px.bar(
                bar_data,
                x='Mentions',
                y='Brand',
                orientation='h',
                color='Brand',
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
            )
            fig.update_layout(showlegend=False, xaxis_title="Mentions", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Network Head-to-Head Comparison")
        
        # Calculate scores for each network
        networks = ['Orange', 'Mascom', 'BTC']
        all_scores = {}
        
        for network in networks:
            all_scores[network] = calculate_network_scores(filtered_df, network)
        
        # Display comparison cards
        cols = st.columns(3)
        
        for idx, network in enumerate(networks):
            with cols[idx]:
                scores = all_scores[network]
                
                # Color coding based on performance
                if network == 'BTC':
                    color = "#45B7D1"
                elif network == 'Orange':
                    color = "#FF6B6B"
                else:
                    color = "#4ECDC4"
                
                st.markdown(f"""
                <div style="background: {color}; padding: 20px; border-radius: 10px; color: white;">
                    <h2 style="margin: 0; text-align: center;">{network}</h2>
                    <h3 style="margin: 10px 0; text-align: center;">{scores['Overall Experience']:.2f}/10</h3>
                    <p style="margin: 0; text-align: center; font-size: 0.9em;">{scores['Users']} users</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                st.metric("Customer Service", f"{scores['Customer Service']:.2f}/10")
                st.metric("Pricing", f"{scores['Pricing']:.2f}/10")
                st.metric("Communication", f"{scores['Communication']:.2f}/10")
        
        st.markdown("---")
        
        # Radar chart comparison
        st.subheader("Performance Radar")
        
        categories = ['Overall<br>Experience', 'Customer<br>Service', 'Communication', 'Pricing']
        
        fig = go.Figure()
        
        for network in networks:
            scores = all_scores[network]
            values = [
                scores['Overall Experience'],
                scores['Customer Service'],
                scores['Communication'],
                scores['Pricing']
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=network
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Customer Voice: What They Really Think")
        
        # Add network selector
        st.markdown("### 🔍 Select Network to Analyze")
        selected_network = st.radio(
            "Choose a network:",
            ['All Networks', 'Orange', 'Mascom', 'BTC'],
            horizontal=True
        )
        
        st.markdown("---")
        
        if selected_network == 'All Networks':
            # Overall view
            st.subheader("📊 Overall Market Insights (All Networks)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 😤 Top Complaints Across All Networks")
                complaints = filtered_df['A12_Most_Disliked_Feature'].value_counts().head(8)
                
                if len(complaints) > 0:
                    complaints_data = pd.DataFrame({
                        'Complaint': complaints.index.tolist(),
                        'Mentions': complaints.values.tolist()
                    })
                    
                    fig = px.bar(
                        complaints_data,
                        x='Mentions',
                        y='Complaint',
                        orientation='h',
                        color='Mentions',
                        color_continuous_scale='Reds',
                        text='Mentions'
                    )
                    fig.update_traces(textposition='outside')
                    fig.update_layout(showlegend=False, xaxis_title="Mentions", yaxis_title="", height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No complaint data available")
            
            with col2:
                st.markdown("#### 💡 Most Wanted Features Across All Networks")
                desires = filtered_df['A22_Desired_Value_Added_Services'].str.split(',').explode().str.strip().value_counts().head(8)
                
                if len(desires) > 0:
                    desires_data = pd.DataFrame({
                        'Feature': desires.index.tolist(),
                        'Requests': desires.values.tolist()
                    })
                    
                    fig = px.bar(
                        desires_data,
                        x='Requests',
                        y='Feature',
                        orientation='h',
                        color='Requests',
                        color_continuous_scale='Greens',
                        text='Requests'
                    )
                    fig.update_traces(textposition='outside')
                    fig.update_layout(showlegend=False, xaxis_title="Requests", yaxis_title="", height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No feature request data available")
            
            st.markdown("---")
            st.markdown("#### 📋 Quick Summary by Network")
            
            # Summary cards for each network
            cols = st.columns(3)
            for idx, network in enumerate(['Orange', 'Mascom', 'BTC']):
                with cols[idx]:
                    network_df = filtered_df[filtered_df['A5_Primary_Mobile_Network'] == network]
                    
                    if len(network_df) > 0:
                        top_complaint = network_df['A12_Most_Disliked_Feature'].value_counts().head(1)
                        top_desire = network_df['A22_Desired_Value_Added_Services'].str.split(',').explode().str.strip().value_counts().head(1)
                        
                        st.markdown(f"**{network}** ({len(network_df)} users)")
                        
                        if len(top_complaint) > 0:
                            st.markdown(f"😤 **Top Complaint:**")
                            st.caption(f"{top_complaint.index[0]} ({top_complaint.values[0]})")
                        
                        if len(top_desire) > 0:
                            st.markdown(f"💡 **Top Want:**")
                            st.caption(f"{top_desire.index[0]} ({top_desire.values[0]})")
                    else:
                        st.info(f"No data for {network}")
        
        else:
            # Network-specific view
            network_df = filtered_df[filtered_df['A5_Primary_Mobile_Network'] == selected_network]
            
            if len(network_df) == 0:
                st.warning(f"No data available for {selected_network} with current filters.")
            else:
                # Network header with stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Users", f"{len(network_df)}")
                with col2:
                    avg_satisfaction = network_df['A36A_Experience_overall_experience'].mean()
                    st.metric("Avg. Satisfaction", f"{avg_satisfaction:.1f}/10" if not pd.isna(avg_satisfaction) else "N/A")
                with col3:
                    market_share = (len(network_df) / len(filtered_df)) * 100
                    st.metric("Market Share", f"{market_share:.1f}%")
                with col4:
                    avg_service = network_df['A36B_Experience_Customer_Service'].mean()
                    st.metric("Customer Service", f"{avg_service:.1f}/10" if not pd.isna(avg_service) else "N/A")
                
                st.markdown("---")
                
                # Complaints and Desires side by side
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"#### 😤 What {selected_network} Customers Complain About")
                    complaints = network_df['A12_Most_Disliked_Feature'].value_counts().head(8)
                    
                    if len(complaints) > 0:
                        complaints_data = pd.DataFrame({
                            'Complaint': complaints.index.tolist(),
                            'Mentions': complaints.values.tolist()
                        })
                        
                        fig = px.bar(
                            complaints_data,
                            x='Mentions',
                            y='Complaint',
                            orientation='h',
                            color='Mentions',
                            color_continuous_scale='Reds',
                            text='Mentions'
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(showlegend=False, xaxis_title="Mentions", yaxis_title="", height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show percentage
                        st.caption(f"Based on {len(network_df)} {selected_network} users")
                    else:
                        st.info("No complaint data available")
                
                with col2:
                    st.markdown(f"#### 💡 What {selected_network} Customers Want")
                    desires = network_df['A22_Desired_Value_Added_Services'].str.split(',').explode().str.strip().value_counts().head(8)
                    
                    if len(desires) > 0:
                        desires_data = pd.DataFrame({
                            'Feature': desires.index.tolist(),
                            'Requests': desires.values.tolist()
                        })
                        
                        fig = px.bar(
                            desires_data,
                            x='Requests',
                            y='Feature',
                            orientation='h',
                            color='Requests',
                            color_continuous_scale='Greens',
                            text='Requests'
                        )
                        fig.update_traces(textposition='outside')
                        fig.update_layout(showlegend=False, xaxis_title="Requests", yaxis_title="", height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.caption(f"Based on {len(network_df)} {selected_network} users")
                    else:
                        st.info("No feature request data available")
                
                st.markdown("---")
                
                # What they like vs dislike
                st.markdown(f"#### ✅ What {selected_network} Users LOVE vs ❌ What They HATE")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Most Liked Features:**")
                    liked = network_df['A11_Most_Liked_Feature'].value_counts().head(5)
                    if len(liked) > 0:
                        for feature, count in liked.items():
                            st.write(f"✅ **{feature}**: {count} mentions")
                    else:
                        st.info("No data")
                
                with col2:
                    st.markdown("**Priority Improvements Needed:**")
                    improvements = network_df['A24_Improvement_Areas_Primary_Network'].str.split(',').explode().str.strip().value_counts().head(5)
                    if len(improvements) > 0:
                        for improvement, count in improvements.items():
                            st.write(f"🔧 **{improvement}**: {count} mentions")
                    else:
                        st.info("No data")
                
                st.markdown("---")
                
                # Competitive insights
                st.markdown(f"#### 🎯 Why Users Chose {selected_network}")
                choice_factors = network_df['A6_Factors_Influencing_Choice'].str.split(',').explode().str.strip().value_counts().head(5)
                
                if len(choice_factors) > 0:
                    for factor, count in choice_factors.items():
                        percentage = (count / len(network_df)) * 100
                        st.progress(percentage / 100)
                        st.caption(f"{factor}: {count} users ({percentage:.1f}%)")
                else:
                    st.info("No data on choice factors")
        
        st.markdown("---")
        
        # Comparison view - always show
        st.subheader("📊 Network-by-Network Comparison")
        
        comparison_metrics = {}
        for network in ['Orange', 'Mascom', 'BTC']:
            network_df = filtered_df[filtered_df['A5_Primary_Mobile_Network'] == network]
            
            if len(network_df) > 0:
                top_complaint = network_df['A12_Most_Disliked_Feature'].value_counts().head(1)
                top_desire = network_df['A22_Desired_Value_Added_Services'].str.split(',').explode().str.strip().value_counts().head(1)
                top_strength = network_df['A11_Most_Liked_Feature'].value_counts().head(1)
                
                comparison_metrics[network] = {
                    'Users': len(network_df),
                    'Top Complaint': top_complaint.index[0] if len(top_complaint) > 0 else 'N/A',
                    'Complaint Count': top_complaint.values[0] if len(top_complaint) > 0 else 0,
                    'Top Want': top_desire.index[0] if len(top_desire) > 0 else 'N/A',
                    'Want Count': top_desire.values[0] if len(top_desire) > 0 else 0,
                    'Top Strength': top_strength.index[0] if len(top_strength) > 0 else 'N/A'
                }
        
        if comparison_metrics:
            comparison_df = pd.DataFrame(comparison_metrics).T
            st.dataframe(comparison_df, use_container_width=True)
        else:
            st.info("No comparison data available with current filters")
    
    with tab4:
        st.header("Market Trends & Churn Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Network Abandonment")
            churned = filtered_df['A3_Networks_Stopped_Using'].value_counts().head(5)
            
            # Create DataFrame for churned networks
            churned_data = pd.DataFrame({
                'Network': churned.index.tolist(),
                'Users': churned.values.tolist()
            })
            
            fig = px.bar(
                churned_data,
                x='Network',
                y='Users',
                color='Users',
                color_continuous_scale='Blues'
            )
            fig.update_layout(xaxis_title="Network", yaxis_title="Users Who Left", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            if len(churned) > 0:
                st.info(f"💡 **Key Insight**: {churned.index[0]} has the highest churn rate with {churned.iloc[0]} users abandoning the network")
            else:
                st.info("💡 **Key Insight**: No churn data available with current filters")
        
        with col2:
            st.subheader("Customer Loyalty (Length of Use)")
            loyalty = filtered_df['A9_How_Long_Primary_Network'].value_counts()
            fig = px.pie(
                values=loyalty.values,
                names=loyalty.index,
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Demographics
        st.markdown("---")
        st.subheader("User Demographics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            age_dist = filtered_df['D1_Age'].value_counts()
            age_data = pd.DataFrame({
                'Age Group': age_dist.index.tolist(),
                'Users': age_dist.values.tolist()
            })
            fig = px.bar(age_data, x='Age Group', y='Users', title="Age Distribution")
            fig.update_layout(xaxis_title="Age Group", yaxis_title="Users", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            employment = filtered_df['D5_Employment_Status'].value_counts()
            fig = px.pie(values=employment.values, names=employment.index, title="Employment Status")
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            income = filtered_df['D7_Monthly_Income_Allowance'].value_counts()
            income_data = pd.DataFrame({
                'Income Level': income.index.tolist(),
                'Users': income.values.tolist()
            })
            fig = px.bar(income_data, x='Users', y='Income Level', orientation='h', title="Income Levels")
            fig.update_layout(xaxis_title="Users", yaxis_title="", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        st.header("🎯 Data-Driven Recommendations")
        
        st.subheader("For Consumers: Which Network Should You Choose?")
        
        # Recommendation engine
        col1, col2 = st.columns(2)
        
        with col1:
            priority = st.selectbox(
                "What matters most to you?",
                ["Overall Satisfaction", "Best Customer Service", "Best Value for Money", "Fastest Internet", "Most Reliable"]
            )
        
        with col2:
            budget = st.selectbox(
                "Your budget?",
                ["Budget-conscious", "Mid-range", "Premium"]
            )
        
        if st.button("Get Recommendation", type="primary"):
            st.markdown("---")
            
            if priority == "Overall Satisfaction":
                st.success("### Recommended: BTC")
                st.write("- Highest overall satisfaction: 8.07/10")
                st.write("- Best customer service: 8.02/10")
                st.write("- Best pricing satisfaction: 7.88/10")
            elif priority == "Best Value for Money":
                st.success("### Recommended: Mascom")
                st.write("- Strong balance of price and quality")
                st.write("- Wide network coverage")
                st.write("- Popular choice among students")
            else:
                st.success("### Recommended: Orange")
                st.write("- Fastest internet speeds")
                st.write("- Modern infrastructure")
                st.write("- Good for data-heavy users")
        
        st.markdown("---")
        
        st.subheader("For Network Providers: Strategic Improvements")
        
        with st.expander("🟠 Orange Botswana"):
            st.markdown("""
            **Priority Actions:**
            1. **Reduce data prices** - #1 complaint (160 mentions)
            2. **Improve customer service** - Currently 6.97/10 (lowest)
            3. **Introduce loyalty programs** - 126 customers want this
            4. **Offer unlimited data plans** - 182 requests
            
            **Opportunity:** You have the fastest network, but pricing is holding you back
            """)
        
        with st.expander("🔵 Mascom"):
            st.markdown("""
            **Priority Actions:**
            1. **Improve internet speed** - 233 complaints
            2. **More flexible data packages** - 155 requests
            3. **Better app experience** - High app usage but frequent issues
            4. **Transparency in billing** - Hidden charges complaint
            
            **Opportunity:** You're the market leader, focus on maintaining quality
            """)
        
        with st.expander("🟢 BTC"):
            st.markdown("""
            **Priority Actions:**
            1. **Reduce churn** - 134 users left (highest churn)
            2. **Expand market share** - Only 5.6% market share
            3. **Maintain high satisfaction** - You score highest (8.07/10)
            4. **Improve network coverage** - Main complaint
            
            **Opportunity:** High satisfaction but low awareness - invest in marketing
            """)

if __name__ == "__main__":
    main()