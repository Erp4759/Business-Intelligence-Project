"""
VAESTA Evaluation Dashboard
Comprehensive RecSys evaluation with Huawei-style analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import numpy as np
sys.path.append('..')

from ui import inject_css
from evaluation import RecommendationEvaluator
from analytics_collector import get_analytics, AnalyticsCollector

inject_css()

# Guard: require login
if not st.session_state.get("logged_in"):
    st.info("Please log in from the main page to continue.")
    st.stop()

st.markdown("<h1>📊 RecSys Evaluation Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Comprehensive Performance Analytics & Metrics</p>", unsafe_allow_html=True)

# Initialize evaluator and analytics
evaluator = RecommendationEvaluator()
analytics = get_analytics()

# Get comprehensive report (REAL DATA ONLY)
report = analytics.get_comprehensive_report()

# Check if we have real data
has_real_data = (
    report['summary']['total_recommendations'] > 0 or 
    report['summary']['total_interactions'] > 0 or 
    report['summary']['total_feedback'] > 0
)

# ===== TAB NAVIGATION =====
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Overview", 
    "🎯 Ranking Metrics", 
    "💼 Business Metrics",
    "👥 User Study",
    "🌍 Demographics & Location",
    "🔬 Methodology"
])

# ===== TAB 1: OVERVIEW =====
with tab1:
    st.markdown("### 📊 System Performance Overview")
    
    # Show warning if no real data
    if not has_real_data:
        st.warning("""
        ⚠️ **No real data collected yet!**
        
        To collect real data:
        1. Go to **Home** page and generate recommendations
        2. Click on outfits (tracked as interactions)
        3. Submit feedback on the **User Study** tab below
        
        Once you start using the system, real metrics will appear here.
        """)
    
    # Summary Stats
    summary = report['summary']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Total Recommendations",
            summary['total_recommendations'],
            help="Total recommendation batches generated"
        )
    
    with col2:
        st.metric(
            "👆 Total Interactions",
            summary['total_interactions'],
            help="User clicks, views, saves on recommendations"
        )
    
    with col3:
        st.metric(
            "📝 Feedback Collected",
            summary['total_feedback'],
            help="User ratings and reviews collected"
        )
    
    with col4:
        st.metric(
            "👥 Unique Users",
            summary['unique_users'],
            help="Number of unique users tracked"
        )
    
    st.markdown("---")
    
    # Key Performance Indicators
    st.markdown("### 🎯 Key Performance Indicators")
    
    ranking = report['ranking_metrics']
    business = report['business_metrics']
    satisfaction = report['user_satisfaction']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        precision = ranking['precision_at_3']
        if precision > 0:
            st.metric(
                "Precision@3",
                f"{precision:.1%}",
                help="Fraction of recommended items that are relevant"
            )
        else:
            st.metric(
                "Precision@3",
                "No data",
                help="Need feedback data to calculate"
            )
    
    with col2:
        recall = ranking['recall_at_3']
        if recall > 0:
            st.metric(
                "Recall@3",
                f"{recall:.1%}",
                help="Fraction of relevant items that were recommended"
            )
        else:
            st.metric(
                "Recall@3",
                "No data",
                help="Need feedback data to calculate"
            )
    
    with col3:
        ctr = business['ctr']
        if ctr > 0:
            st.metric(
                "CTR",
                f"{ctr:.1f}%",
                help="Click-Through Rate on recommendations"
            )
        else:
            st.metric(
                "CTR",
                "No data",
                help="Need interaction data to calculate"
            )
    
    with col4:
        avg_sat = satisfaction['avg_satisfaction']
        if avg_sat > 0:
            st.metric(
                "Satisfaction",
                f"{avg_sat:.1f}/5",
                help="Average user satisfaction score"
            )
        else:
            st.metric(
                "Satisfaction",
                "No data",
                help="Need user feedback to calculate"
            )
    
    if has_real_data:
        st.markdown("---")
        st.markdown("### 📈 Recent Activity")
        
        # Show time-based stats if we have data
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **Last 24 Hours:**
            - {report['summary']['total_recommendations']} recommendations generated
            - {report['summary']['total_interactions']} user interactions
            """)
        
        with col2:
            st.info(f"""
            **Data Collection:**
            - {report['summary']['total_feedback']} feedback submissions
            - {report['summary']['unique_users']} unique users tracked
            """)

# ===== TAB 2: RANKING METRICS =====
with tab2:
    st.markdown("### 🎯 Ranking Quality Metrics")
    
    if not has_real_data:
        st.warning("""
        ⚠️ **No ranking data available yet.**
        
        Ranking metrics are calculated from user feedback. 
        Please submit feedback on recommendations to see these metrics.
        """)
    
    st.info("""
    **Ranking metrics** measure how well our system orders recommendations. 
    Higher scores indicate better relevance ranking.
    """)
    
    ranking = report['ranking_metrics']
    has_ranking_data = ranking['precision_at_3'] > 0
    
    if has_ranking_data:
        col1, col2 = st.columns(2)
        
        with col1:
            # Precision/Recall/F1 Chart
            metrics_df = pd.DataFrame({
                'Metric': ['Precision@3', 'Recall@3', 'F1@3'],
                'Score': [
                    ranking['precision_at_3'],
                    ranking['recall_at_3'],
                    ranking['f1_at_3']
                ]
            })
            
            fig = go.Figure(data=[
                go.Bar(
                    x=metrics_df['Metric'],
                    y=metrics_df['Score'],
                    marker_color=['#667eea', '#764ba2', '#f093fb'],
                    text=[f"{val:.1%}" for val in metrics_df['Score']],
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title='Ranking Metrics Performance (Real Data)',
                yaxis_title='Score',
                yaxis_range=[0, 1],
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Show detailed breakdown
            st.markdown("### 📋 Metric Details")
            sample_size = ranking.get('sample_size', 0)
            st.metric("Sample Size", f"{sample_size} feedbacks")
            
            # Show calculation explanation
            with st.expander("📊 How these metrics are calculated", expanded=True):
                st.markdown("""
                **Precision@3 Calculation:**
                - Uses **item-specific feedback** when available (outer, top, bottom ratings)
                - Falls back to overall relevance rating if item-specific data unavailable
                - Counts items with **rating ≥ 4** as "relevant"
                - Formula: `(Relevant items) / (Total recommended items)`
                
                **Example:** If you rated 3 items (outer=5, top=2, bottom=4):
                - Relevant items: 2 (outer=5, bottom=4)
                - Total items: 3
                - Precision@3 = 2/3 = 66.7%
                
                **Recall@3 Calculation:**
                - Estimates total relevant items as **5 per feedback context**
                - Formula: `(Relevant items found) / (Total relevant items estimated)`
                
                **F1@3 Calculation:**
                - Harmonic mean of Precision and Recall
                - Formula: `2 × (Precision × Recall) / (Precision + Recall)`
                - Balances both precision and recall metrics
                
                **Note:** The system now uses individual item ratings (outer, top, bottom, dress) 
                for more accurate metrics than overall ratings.
                """)
            
            st.metric("Precision@3", f"{ranking['precision_at_3']:.1%}")
            st.metric("Recall@3", f"{ranking['recall_at_3']:.1%}")
            st.metric("F1@3", f"{ranking['f1_at_3']:.1%}")
    else:
        st.info("💡 Charts will appear here once we have feedback data.")
    
    st.markdown("---")
    
    # Metric Explanations
    st.markdown("### 📖 Metric Definitions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Precision@K**
        - Fraction of top-K recommendations that are relevant
        - Formula: `(Relevant items in top K) / K`
        - Higher = fewer irrelevant recommendations
        
        **Recall@K**
        - Fraction of all relevant items that appear in top-K
        - Formula: `(Relevant in top K) / (Total relevant)`
        - Higher = fewer missed relevant items
        """)
    
    with col2:
        st.markdown("""
        **F1@K**
        - Harmonic mean of Precision and Recall
        - Formula: `2 × (P × R) / (P + R)`
        - Balances both metrics
        
        **NDCG@K**
        - Normalized Discounted Cumulative Gain
        - Accounts for position in ranking
        - Higher = better items ranked first
        """)

# ===== TAB 3: BUSINESS METRICS =====
with tab3:
    st.markdown("### 💼 Business Impact Metrics")
    
    if not has_real_data:
        st.warning("""
        ⚠️ **No business metrics available yet.**
        
        Business metrics track clicks, conversions, and engagement.
        Start using the system to collect these metrics.
        """)
    
    st.info("""
    **Business metrics** measure real-world impact of the recommendation system.
    These metrics directly translate to user engagement and potential revenue.
    """)
    
    business = report['business_metrics']
    has_business_data = business['ctr'] > 0 or report['summary']['total_interactions'] > 0
    
    col1, col2, col3 = st.columns(3)
    
    ctr_value = f"{business['ctr']:.1f}%" if business['ctr'] > 0 else "No data"
    conv_value = f"{business['conversion_rate']:.1f}%" if business['conversion_rate'] > 0 else "No data"
    session_value = f"{business['avg_session_duration_min']:.1f}" if business['avg_session_duration_min'] > 0 else "No data"
    
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 2rem; border-radius: 12px; text-align: center;'>
            <h3 style='margin: 0; font-size: 2.5rem;'>{ctr_value}</h3>
            <p style='margin: 0.5rem 0 0 0;'>Click-Through Rate</p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("% of recommendations clicked by users")
    
    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white; padding: 2rem; border-radius: 12px; text-align: center;'>
            <h3 style='margin: 0; font-size: 2.5rem;'>{conv_value}</h3>
            <p style='margin: 0.5rem 0 0 0;'>Conversion Rate</p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("% of views that lead to saves/actions")
    
    with col3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white; padding: 2rem; border-radius: 12px; text-align: center;'>
            <h3 style='margin: 0; font-size: 2.5rem;'>{session_value}</h3>
            <p style='margin: 0.5rem 0 0 0;'>Avg Session (min)</p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Average time users spend per session")
    
    if has_business_data:
        st.markdown("---")
        st.markdown("### 📊 Engagement Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Recommendations", report['summary']['total_recommendations'])
            st.metric("Total Interactions", report['summary']['total_interactions'])
        
        with col2:
            if business['ctr'] > 0:
                st.metric("Click-Through Rate", f"{business['ctr']:.1f}%")
            if business['conversion_rate'] > 0:
                st.metric("Conversion Rate", f"{business['conversion_rate']:.1f}%")
    else:
        st.info("💡 Business metrics will appear here once users start interacting with recommendations.")

# ===== TAB 4: USER STUDY =====
with tab4:
    st.markdown("### 👥 User Study Results")
    
    user_study = report['user_satisfaction']
    n_responses = user_study['feedback_count']
    
    if n_responses > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "👥 Participants",
                n_responses,
                help="Number of users who provided feedback"
            )
        
        with col2:
            if user_study['avg_satisfaction'] > 0:
                st.metric(
                    "😊 Satisfaction",
                    f"{user_study['avg_satisfaction']:.2f}/5",
                    help="Average user satisfaction rating"
                )
            else:
                st.metric("😊 Satisfaction", "N/A")
        
        with col3:
            if user_study['avg_relevance'] > 0:
                st.metric(
                    "🎯 Relevance",
                    f"{user_study['avg_relevance']:.2f}/5",
                    help="Average relevance rating"
                )
            else:
                st.metric("🎯 Relevance", "N/A")
        
        st.markdown("---")
        
        # Detailed Ratings (REAL DATA ONLY)
        st.markdown("### 📊 Real User Ratings")
        
        # Only show dimensions that have data
        ratings_data = []
        if user_study['avg_relevance'] > 0:
            ratings_data.append(('Relevance', user_study['avg_relevance']))
        if user_study['avg_satisfaction'] > 0:
            ratings_data.append(('Satisfaction', user_study['avg_satisfaction']))
        
        if ratings_data:
            ratings_df = pd.DataFrame(ratings_data, columns=['Dimension', 'Score'])
            
            fig = go.Figure(data=[
                go.Bar(
                    x=ratings_df['Dimension'],
                    y=ratings_df['Score'],
                    marker_color=['#667eea', '#764ba2'],
                    text=[f"{val:.2f}" for val in ratings_df['Score']],
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title=f'User Ratings (n={n_responses})',
                yaxis_title='Rating',
                yaxis_range=[0, 5],
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Collecting detailed ratings...")
    
    else:
        st.warning("""
        ⚠️ **No user feedback collected yet!**
        
        Be the first to contribute feedback using the form below.
        """)
    
    st.markdown("---")
    
    # ===== FEEDBACK COLLECTION FORM =====
    st.markdown("### 📝 Contribute Your Feedback")
    
    st.info("Help us improve by rating your experience with the recommendation system!")
    
    with st.form("comprehensive_feedback"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Recommendation Quality**")
            relevance = st.slider(
                "Relevance to Weather",
                1, 5, 4,
                help="How appropriate were outfits for the weather?"
            )
            satisfaction = st.slider(
                "Overall Satisfaction",
                1, 5, 4,
                help="How satisfied are you overall?"
            )
            diversity = st.slider(
                "Variety of Suggestions",
                1, 5, 4,
                help="Did you see diverse options?"
            )
        
        with col2:
            st.markdown("**Personalization**")
            personalization = st.slider(
                "Matches Your Style",
                1, 5, 4,
                help="Do recommendations match your style?"
            )
            would_wear = st.slider(
                "Would Actually Wear",
                1, 5, 4,
                help="Would you wear these outfits?"
            )
            ease_of_use = st.slider(
                "Ease of Use",
                1, 5, 4,
                help="How easy was the system to use?"
            )
        
        st.markdown("**Additional Feedback**")
        
        col1, col2 = st.columns(2)
        with col1:
            recommend_to_friend = st.radio(
                "Would you recommend to a friend?",
                ["Yes, definitely!", "Maybe", "Probably not"],
                horizontal=True
            )
        with col2:
            use_frequency = st.radio(
                "How often would you use this?",
                ["Daily", "Weekly", "Occasionally", "Rarely"],
                horizontal=True
            )
        
        comments = st.text_area(
            "Any additional comments?",
            placeholder="Tell us what you liked or what could be improved..."
        )
        
        submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")
        
        if submitted:
            # Save to analytics
            feedback_data = {
                'relevance': relevance,
                'satisfaction': satisfaction,
                'diversity': diversity,
                'personalization': personalization,
                'would_wear': would_wear,
                'ease_of_use': ease_of_use
            }
            
            analytics.track_feedback(
                username=st.session_state.username,
                recommendation_id=f"eval_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                feedback_type='survey',
                ratings=feedback_data,
                comments=comments,
                context={
                    'recommend_to_friend': recommend_to_friend,
                    'use_frequency': use_frequency
                }
            )
            
            # Also save to legacy evaluator
            evaluator.save_user_feedback({
                'username': st.session_state.username,
                **feedback_data,
                'comments': comments,
                'recommend_to_friend': recommend_to_friend,
                'use_frequency': use_frequency
            })
            
            st.success("✅ Thank you for your feedback! It helps us improve the system.")
            st.balloons()

# ===== TAB 5: DEMOGRAPHICS & LOCATION =====
with tab5:
    st.markdown("### 🌍 User Demographics & Location Analytics")
    
    # Get data from analytics
    recommendations = analytics._load_events('recommendations')
    sessions = analytics._load_events('sessions')
    feedback = analytics._load_events('feedback')
    
    # Import get_all_users
    from data_manager import get_all_users
    
    # Get all users for gender distribution
    all_users = get_all_users()
    
    # Extract cities from recommendations context
    cities = []
    for rec in recommendations:
        context = rec.get('context', {})
        city = context.get('city')
        if city:
            cities.append(city)
    
    # Extract cities from feedback context
    for fb in feedback:
        context = fb.get('context', {})
        city = context.get('city')
        if city:
            cities.append(city)
    
    # Calculate gender distribution
    gender_counts = {'Male': 0, 'Female': 0, 'Other': 0, 'Unknown': 0}
    for user in all_users:
        gender = str(user.get('gender', 'Unknown')).strip()
        if gender == 'Male':
            gender_counts['Male'] += 1
        elif gender == 'Female':
            gender_counts['Female'] += 1
        elif gender:
            gender_counts['Other'] += 1
        else:
            gender_counts['Unknown'] += 1
    
    # Extract IP addresses from sessions
    ip_addresses = []
    for session in sessions:
        ip = session.get('ip_address')
        if ip and ip != 'unknown':
            ip_addresses.append(ip)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        unique_cities = len(set(cities)) if cities else 0
        st.metric("📍 Cities Used", unique_cities, help="Number of unique cities for recommendations")
    
    with col2:
        total_recommendations_by_city = len(cities)
        st.metric("🌆 Total City Queries", total_recommendations_by_city, help="Total recommendations requested by city")
    
    with col3:
        unique_ips = len(set(ip_addresses)) if ip_addresses else 0
        st.metric("🌐 Unique IP Addresses", unique_ips, help="Number of unique IP addresses tracked")
    
    with col4:
        total_users = len(all_users)
        st.metric("👥 Total Users", total_users, help="Total registered users in system")
    
    st.markdown("---")
    
    # City distribution
    if cities:
        st.markdown("### 📍 City Distribution")
        city_counts = pd.Series(cities).value_counts()
        city_df = pd.DataFrame({
            'City': city_counts.index,
            'Count': city_counts.values,
            'Percentage': (city_counts.values / len(cities) * 100).round(1)
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart
            fig = px.bar(
                city_df.head(10),  # Top 10 cities
                x='City',
                y='Count',
                title='Top 10 Cities by Recommendation Requests',
                labels={'Count': 'Number of Requests', 'City': 'City Name'},
                color='Count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Table
            st.markdown("#### City Statistics")
            st.dataframe(
                city_df.head(15),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("📍 No city data available yet. Cities will appear here once users request recommendations.")
    
    st.markdown("---")
    
    # Gender distribution
    st.markdown("### 👥 Gender Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        gender_data = {k: v for k, v in gender_counts.items() if v > 0}
        if gender_data:
            fig = px.pie(
                values=list(gender_data.values()),
                names=list(gender_data.keys()),
                title='User Gender Distribution',
                color_discrete_map={
                    'Male': '#3498db',
                    'Female': '#e91e63',
                    'Other': '#9b59b6',
                    'Unknown': '#95a5a6'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gender data available")
    
    with col2:
        # Statistics
        st.markdown("#### Gender Statistics")
        total_with_gender = sum(v for k, v in gender_counts.items() if k != 'Unknown')
        
        for gender, count in gender_counts.items():
            if count > 0:
                percentage = (count / total_users * 100) if total_users > 0 else 0
                st.metric(
                    gender,
                    f"{count} users",
                    f"{percentage:.1f}%"
                )
        
        if total_users > 0:
            st.markdown(f"**Total Users:** {total_users}")
            st.markdown(f"**Users with Gender Info:** {total_with_gender}")
    
    st.markdown("---")
    
    # IP Address information
    st.markdown("### 🌐 IP Address & Location Information")
    
    if ip_addresses:
        unique_ips_list = list(set(ip_addresses))
        st.info(f"**Note:** IP addresses are tracked for analytics purposes. Privacy is maintained - only IP addresses are stored, not full location data.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### IP Address Statistics")
            st.metric("Total IP Addresses Tracked", len(ip_addresses))
            st.metric("Unique IP Addresses", len(unique_ips_list))
            
            # Show sample IPs (first 10, masked for privacy)
            if unique_ips_list:
                st.markdown("#### Sample IP Addresses (First 10)")
                sample_ips = unique_ips_list[:10]
                for ip in sample_ips:
                    # Mask last octet for privacy
                    ip_parts = ip.split('.')
                    if len(ip_parts) == 4:
                        masked_ip = '.'.join(ip_parts[:3]) + '.xxx'
                    else:
                        masked_ip = ip
                    st.text(masked_ip)
        
        with col2:
            st.markdown("#### IP Address Distribution")
            ip_counts = pd.Series(ip_addresses).value_counts()
            ip_df = pd.DataFrame({
                'IP Address (Masked)': ['.'.join(ip.split('.')[:3]) + '.xxx' if len(ip.split('.')) == 4 else ip for ip in ip_counts.index[:10]],
                'Sessions': ip_counts.values[:10]
            })
            st.dataframe(ip_df, use_container_width=True, hide_index=True)
    else:
        st.info("🌐 No IP address data available. IP addresses are tracked when sessions are created (may not be available in all deployment environments).")
    
    st.markdown("---")
    
    # Data source information
    with st.expander("ℹ️ About This Data", expanded=False):
        st.markdown("""
        **Data Sources:**
        - **Cities:** Extracted from recommendation context and feedback context
        - **Gender:** From user profile data in database
        - **IP Addresses:** Tracked in session data (may not be available in all Streamlit deployment environments)
        
        **Privacy:**
        - IP addresses are masked in display (last octet hidden)
        - Only aggregated statistics are shown
        - No personally identifiable information beyond username is displayed
        
        **Data Collection:**
        - Cities are tracked when users request recommendations
        - Gender is collected during user registration
        - IP addresses are captured during session creation (when available)
        """)

# ===== TAB 6: METHODOLOGY =====
with tab6:
    st.markdown("### 🔬 Evaluation Methodology")
    
    st.markdown("""
    This dashboard presents a **real-time evaluation** of the VAESTA recommendation system
    using comprehensive analytics tracking and user feedback.
    
    **Data Source:** All metrics shown are based on **real user interactions and feedback**.
    No simulated or synthetic data is displayed.
    """)
    
    with st.expander("📊 Real-Time Metrics", expanded=True):
        st.markdown("""
        **What We Track:**
        
        **Ranking Metrics:**
        - **Precision@K**: Fraction of recommended items that are relevant (based on user ratings ≥4)
        - **Recall@K**: Fraction of all relevant items that were recommended
        - **F1@K**: Harmonic mean of Precision and Recall
        - **NDCG@K**: Normalized Discounted Cumulative Gain (position-aware ranking quality)
        
        **Business Metrics:**
        - **CTR (Click-Through Rate)**: % of recommendations that users clicked
        - **Conversion Rate**: % of views that led to saves/actions
        - **Session Duration**: Average time users spend per session
        
        **User Satisfaction:**
        - **Relevance**: How appropriate recommendations are for weather/context
        - **Satisfaction**: Overall happiness with recommendations
        - **Diversity**: Variety in suggestions
        - **Personalization**: How well recommendations match user style
        """)
    
    with st.expander("🎯 VAESTA Recommendation Algorithm"):
        st.markdown("""
        **Content-Based Filtering with Multi-Attribute Scoring:**
        
        1. **Weather Integration**
           - Real-time weather data from OpenWeatherMap
           - Temperature, humidity, precipitation matching
           - Wind speed for windproof clothing selection
        
        2. **Style Preference Matching**
           - User profile preferences (casual, formal, sport, etc.)
           - Gender-specific recommendations
           - Budget constraints
        
        3. **Color Coordination**
           - Color harmony algorithms
           - Complementary and analogous color schemes
           - Season-appropriate palettes
        
        4. **Layering Optimization**
           - Temperature-based layering decisions
           - Warmth score calculations
           - Impermeability for rain conditions
        """)
    
    with st.expander("👥 User Feedback Collection"):
        st.markdown("""
        **Feedback Protocol:**
        
        1. **Implicit Feedback:**
           - View events (when recommendations are shown)
           - Click events (when users click on items)
           - Save events (adding items to wardrobe)
           - Dismiss events (rejecting recommendations)
        
        2. **Explicit Feedback:**
           - 5-point Likert scale ratings
           - Multiple dimensions measured:
             - Relevance (weather appropriateness)
             - Satisfaction (overall experience)
             - Diversity (variety of options)
             - Personalization (style matching)
             - Would Wear (practical wearability)
             - Ease of Use (system usability)
        
        3. **Qualitative Feedback:**
           - Open-ended comments
           - Feature requests
           - Bug reports
        
        **Data Storage:**
        - All feedback stored in Supabase database
        - Privacy-preserving (no PII beyond username)
        - Used to calculate real-time metrics
        """)
    
    with st.expander("📊 Metrics Calculation"):
        st.markdown(f"""
        **Current Data Status:**
        - Total Recommendations: **{report['summary']['total_recommendations']}**
        - Total Interactions: **{report['summary']['total_interactions']}**
        - Total Feedback: **{report['summary']['total_feedback']}**
        - Unique Users: **{report['summary']['unique_users']}**
        
        **Click-Through Rate (CTR):**
        ```
        CTR = (Number of Clicks / Number of Impressions) × 100
        ```
        Current CTR: **{report['business_metrics']['ctr']}%**
        
        **Conversion Rate:**
        ```
        Conversion = (Actions Taken / Total Views) × 100
        ```
        Current rate: **{report['business_metrics']['conversion_rate']}%**
        
        **Precision@K:**
        ```
        Precision = (Relevant items in top K) / K
        ```
        Based on user ratings ≥4 as "relevant"
        
        Current Precision@3: **{report['ranking_metrics']['precision_at_3']:.1%}**
        """)
    
    with st.expander("🔄 Data Collection System"):
        st.markdown("""
        **Huawei-Style Analytics Pipeline:**
        
        ```
        ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
        │  User Actions   │ ──▶ │  Event Tracking  │ ──▶ │  Analytics DB   │
        │  (clicks, etc)  │     │  (collector.py)  │     │  (Supabase)     │
        └─────────────────┘     └──────────────────┘     └─────────────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │  Real-time       │
                               │  Dashboard       │
                               │  (this page)     │
                               └──────────────────┘
        ```
        
        **Events Tracked:**
        - API calls and response times
        - Recommendation generation
        - User interactions (view, click, save, dismiss)
        - Explicit feedback and ratings
        - Session data (duration, pages visited)
        - A/B test variant assignments
        """)

# ===== FOOTER =====
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("VAESTA RecSys Evaluation Dashboard v2.0")

with col2:
    if st.button("🔄 Refresh Data"):
        st.rerun()
