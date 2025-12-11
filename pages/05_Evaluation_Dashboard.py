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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", 
    "🎯 Ranking Metrics", 
    "💼 Business Metrics",
    "👥 User Study",
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
            st.metric("Sample Size", f"{ranking.get('sample_size', 0)} feedbacks")
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

# ===== TAB 5: METHODOLOGY =====
with tab5:
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
