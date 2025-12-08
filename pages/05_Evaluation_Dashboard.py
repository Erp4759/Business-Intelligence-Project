import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.append('..')

from ui import inject_css
from evaluation import RecommendationEvaluator

inject_css()

# Guard: require login
if not st.session_state.get("logged_in"):
    st.info("Please log in from the main page to continue.")
    st.stop()

st.markdown("<h1>📊 System Evaluation Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Comprehensive Performance Metrics & Analysis</p>", unsafe_allow_html=True)

# Initialize evaluator
evaluator = RecommendationEvaluator()

# Generate comprehensive report
report = evaluator.generate_evaluation_report()

# ===== SECTION 1: OVERVIEW METRICS =====
st.markdown("### 🎯 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    precision = report['offline_metrics']['precision_at_3']
    st.metric(
        "Precision@3",
        f"{precision:.1%}",
        delta=f"+{(precision - 0.73):.1%}",
        help="Fraction of recommended items that are relevant"
    )

with col2:
    recall = report['offline_metrics']['recall_at_3']
    st.metric(
        "Recall@3",
        f"{recall:.1%}",
        delta=f"+{(recall - 0.70):.1%}",
        help="Fraction of relevant items that were recommended"
    )

with col3:
    f1 = report['offline_metrics']['f1_at_3']
    st.metric(
        "F1@3",
        f"{f1:.1%}",
        delta=f"+{(f1 - 0.715):.1%}",
        help="Harmonic mean of Precision and Recall"
    )

with col4:
    weather_match = report['offline_metrics']['weather_match_accuracy']
    st.metric(
        "Weather Match",
        f"{weather_match:.1%}",
        delta=f"+{(weather_match - 0.80):.1%}",
        help="How well outfits match weather conditions"
    )

st.markdown("---")

# ===== SECTION 2: BASELINE COMPARISON =====
st.markdown("### 📈 Performance vs Baseline")

baseline_data = report['offline_metrics']['baseline_comparison']

col1, col2 = st.columns([2, 1])

with col1:
    # Create comparison chart
    comparison_df = pd.DataFrame({
        'Method': ['Content-Based (Ours)', 'Rule-Based Baseline'],
        'Accuracy': [baseline_data['our_method'], baseline_data['rule_based_baseline']],
        'Color': ['#667eea', '#cccccc']
    })
    
    fig = go.Figure(data=[
        go.Bar(
            x=comparison_df['Method'],
            y=comparison_df['Accuracy'],
            marker_color=comparison_df['Color'],
            text=[f"{val:.1%}" for val in comparison_df['Accuracy']],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Recommendation Accuracy Comparison',
        yaxis_title='Accuracy Score',
        yaxis_range=[0, 1],
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Performance Improvement")
    improvement = baseline_data['improvement']
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 12px; text-align: center;'>
        <h2 style='margin: 0; font-size: 3rem;'>{improvement:.1f}%</h2>
        <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem;'>Better than Baseline</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;'>
        <strong>Key Finding:</strong><br>
        Our content-based weather-aware recommendation system achieves 
        <strong>{improvement:.1f}% higher accuracy</strong> compared to simple 
        temperature-based rules.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ===== SECTION 3: USER STUDY RESULTS =====
st.markdown("### 👥 User Study Results")

user_study = report['user_study']
n_responses = user_study['n_responses']

if n_responses > 0:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "👥 Participants",
            n_responses,
            help="Number of users who provided feedback"
        )
    
    with col2:
        satisfaction = user_study['avg_satisfaction']
        st.metric(
            "😊 Avg Satisfaction",
            f"{satisfaction:.2f}/5",
            help="Average user satisfaction rating"
        )
    
    with col3:
        would_use = user_study.get('would_use_daily_pct', 0)
        st.metric(
            "🔄 Would Use Daily",
            f"{would_use:.0f}%",
            help="Percentage who would use the system daily"
        )
    
    # Detailed ratings breakdown
    st.markdown("#### Detailed User Ratings")
    
    ratings_df = pd.DataFrame({
        'Metric': ['Relevance', 'Satisfaction', 'Diversity'],
        'Score': [
            user_study['avg_relevance'],
            user_study['avg_satisfaction'],
            user_study['avg_diversity']
        ]
    })
    
    fig = go.Figure(data=[
        go.Bar(
            x=ratings_df['Metric'],
            y=ratings_df['Score'],
            marker_color='#667eea',
            text=[f"{val:.2f}" for val in ratings_df['Score']],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Average User Ratings (Scale: 1-5)',
        yaxis_title='Rating',
        yaxis_range=[0, 5],
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("""
    **No user feedback collected yet.**
    
    Start collecting feedback by:
    1. Using the rating system on the Home page after getting recommendations
    2. Inviting friends and family to test the system
    3. Having users rate recommendations on relevance and satisfaction
    
    **Target:** Get feedback from 10+ users for statistical significance.
    """)

st.markdown("---")

# ===== SECTION 4: BUSINESS METRICS =====
st.markdown("### 💼 Business Impact Metrics")

business = report['business_metrics']

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class='content-box' style='text-align: center;'>
        <h3 style='color: #667eea; margin: 0;'>{business['avg_session_time_minutes']:.1f} min</h3>
        <p style='margin: 0.5rem 0 0 0; color: #666;'>Avg Session Time</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    ctr = business['recommendation_ctr']
    st.markdown(f"""
    <div class='content-box' style='text-align: center;'>
        <h3 style='color: #667eea; margin: 0;'>{ctr:.0%}</h3>
        <p style='margin: 0.5rem 0 0 0; color: #666;'>Click-Through Rate</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    addition_rate = business['wardrobe_addition_rate']
    st.markdown(f"""
    <div class='content-box' style='text-align: center;'>
        <h3 style='color: #667eea; margin: 0;'>{addition_rate:.0%}</h3>
        <p style='margin: 0.5rem 0 0 0; color: #666;'>Wardrobe Addition Rate</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ===== SECTION 5: METHODOLOGY =====
with st.expander("📋 Evaluation Methodology", expanded=False):
    st.markdown("""
    ### Offline Evaluation
    
    **Precision@K**: Measures the fraction of recommended items that are relevant/appropriate.
    - Formula: `(# relevant items in top K) / K`
    - Our Precision@3: **{:.1%}**
    
    **Recall@K**: Measures the fraction of all relevant items that were recommended.
    - Formula: `(# relevant items in top K) / (total # relevant items)`
    - Our Recall@3: **{:.1%}**
    
    **F1@K**: Harmonic mean of Precision and Recall, balancing both metrics.
    - Formula: `2 * (Precision * Recall) / (Precision + Recall)`
    - Our F1@3: **{:.1%}**
    
    **Weather Match Score**: Custom metric measuring how well outfit attributes (warmth, impermeability) 
    match weather conditions (temperature, rain).
    - Our Weather Match: **{:.1%}**
    
    ### Baseline Comparison
    
    **Content-Based System (Ours)**: Multi-attribute scoring with warmth, impermeability, and layering scores 
    matched to weather requirements.
    
    **Rule-Based Baseline**: Simple temperature thresholds (< 10°C = warm, 10-20°C = moderate, > 20°C = light).
    
    **Result**: **{:.1f}% improvement** over baseline
    
    ### User Study
    
    Collected feedback from {} participants on:
    - **Relevance** (1-5): Is the outfit appropriate for the weather?
    - **Satisfaction** (1-5): How satisfied with the recommendation?
    - **Diversity** (1-5): Is there good variety in suggestions?
    
    ### Business Metrics
    
    - **Session Time**: Average time users spend interacting with recommendations
    - **CTR**: Percentage of recommendations that users engage with
    - **Addition Rate**: Percentage of recommended items added to wardrobe
    """.format(
        report['offline_metrics']['precision_at_3'],
        report['offline_metrics']['recall_at_3'],
        report['offline_metrics']['f1_at_3'],
        report['offline_metrics']['weather_match_accuracy'],
        report['offline_metrics']['baseline_comparison']['improvement'],
        user_study['n_responses']
    ))

# ===== SECTION 6: COLLECT FEEDBACK =====
st.markdown("---")
st.markdown("### 📝 Contribute to Our Study")

st.info("""
**Help us improve!** After using the recommendation system on the Home page, 
please provide your feedback to contribute to our evaluation metrics.
""")

# Quick feedback form
with st.form("quick_feedback"):
    st.markdown("#### Quick Feedback Form")
    
    col1, col2 = st.columns(2)
    
    with col1:
        relevance = st.slider("Relevance of recommendations", 1, 5, 4,
                            help="How appropriate were the suggested outfits?")
        satisfaction = st.slider("Overall satisfaction", 1, 5, 4,
                               help="How satisfied are you with the system?")
    
    with col2:
        diversity = st.slider("Variety in suggestions", 1, 5, 4,
                            help="Do you see good diversity?")
        personalization = st.slider("Personalization quality", 1, 5, 4,
                                   help="Does it match your style?")
    
    comments = st.text_area("Additional comments (optional)")
    
    submitted = st.form_submit_button("Submit Feedback", use_container_width=True)
    
    if submitted:
        feedback = {
            'username': st.session_state.username,
            'relevance': relevance,
            'satisfaction': satisfaction,
            'diversity': diversity,
            'personalization': personalization,
            'comments': comments,
            'timestamp': datetime.now().isoformat()
        }
        
        evaluator.save_user_feedback(feedback)
        st.success("✅ Thank you for your feedback! Refresh the page to see updated metrics.")
        st.balloons()

# ===== FOOTER =====
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Evaluation Dashboard | VAESTA Recommendation System")
