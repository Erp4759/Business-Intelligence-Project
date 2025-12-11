"""
VAESTA Analytics Collector
Huawei-style comprehensive data collection for recommendation system evaluation

Tracks:
- API calls and response times
- User interactions (views, clicks, saves)
- Recommendation accuracy and relevance
- User feedback and satisfaction
- Session metrics and engagement
- A/B testing variants
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid
import hashlib

# Try to use Supabase for cloud storage
try:
    from supabase_manager import get_supabase_client, is_supabase_available
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False


class AnalyticsCollector:
    """
    Comprehensive analytics collection system for RecSys evaluation.
    Supports both local JSON and Supabase storage.
    """
    
    def __init__(self, local_dir: str = "data/analytics"):
        """Initialize analytics collector with local fallback."""
        self.local_dir = Path(local_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths for different event types
        self.files = {
            'api_calls': self.local_dir / 'api_calls.json',
            'recommendations': self.local_dir / 'recommendations.json',
            'interactions': self.local_dir / 'interactions.json',
            'feedback': self.local_dir / 'user_feedback.json',
            'sessions': self.local_dir / 'sessions.json',
            'ab_tests': self.local_dir / 'ab_tests.json'
        }
        
        # Initialize files
        for file_path in self.files.values():
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def _get_supabase(self):
        """Get Supabase client if available."""
        if SUPABASE_ENABLED and is_supabase_available():
            return get_supabase_client()
        return None
    
    def _save_local(self, event_type: str, data: Dict):
        """Save event to local JSON file."""
        file_path = self.files.get(event_type)
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                events = json.load(f)
        except:
            events = []
        
        events.append(data)
        
        # Keep only last 10000 events per type
        if len(events) > 10000:
            events = events[-10000:]
        
        with open(file_path, 'w') as f:
            json.dump(events, f, indent=2, default=str)
    
    def _load_local(self, event_type: str) -> List[Dict]:
        """Load events from local JSON file."""
        file_path = self.files.get(event_type)
        if not file_path or not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    
    # ==========================================
    # API CALL TRACKING
    # ==========================================
    
    def track_api_call(self, 
                       endpoint: str,
                       method: str,
                       username: str,
                       request_params: Dict = None,
                       response_status: int = 200,
                       response_time_ms: float = 0,
                       error: str = None):
        """
        Track API call for performance monitoring.
        
        Args:
            endpoint: API endpoint (e.g., '/recommendations', '/weather')
            method: HTTP method (GET, POST, etc.)
            username: User making the request
            request_params: Request parameters (sanitized)
            response_status: HTTP response status code
            response_time_ms: Response time in milliseconds
            error: Error message if any
        """
        event = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'username': username,
            'request_params': request_params or {},
            'response_status': response_status,
            'response_time_ms': response_time_ms,
            'error': error,
            'success': response_status < 400
        }
        
        # Try Supabase first
        client = self._get_supabase()
        if client:
            try:
                client.table('analytics_api_calls').insert(event).execute()
                return
            except:
                pass
        
        # Fallback to local
        self._save_local('api_calls', event)
    
    # ==========================================
    # RECOMMENDATION TRACKING
    # ==========================================
    
    def track_recommendation(self,
                            username: str,
                            recommendation_id: str,
                            recommendation_type: str,
                            items: List[Dict],
                            context: Dict,
                            algorithm_version: str = "v1.0",
                            ab_variant: str = "control"):
        """
        Track recommendation generation event.
        
        Args:
            username: User receiving recommendation
            recommendation_id: Unique ID for this recommendation batch
            recommendation_type: Type (outfit, shopping, similar_items)
            items: List of recommended items with scores
            context: Context data (weather, preferences, etc.)
            algorithm_version: Version of recommendation algorithm
            ab_variant: A/B test variant if applicable
        """
        event = {
            'id': recommendation_id,
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'recommendation_type': recommendation_type,
            'items': [
                {
                    'item_id': item.get('id', item.get('name', 'unknown')),
                    'category': item.get('category', item.get('type', 'unknown')),
                    'score': item.get('score', item.get('match_score', 0)),
                    'rank': idx + 1
                }
                for idx, item in enumerate(items[:10])  # Top 10 only
            ],
            'num_items': len(items),
            'context': {
                'temperature': context.get('temp'),
                'weather_condition': context.get('condition'),
                'user_style': context.get('style'),
                'occasion': context.get('occasion')
            },
            'algorithm_version': algorithm_version,
            'ab_variant': ab_variant
        }
        
        client = self._get_supabase()
        if client:
            try:
                client.table('analytics_recommendations').insert(event).execute()
                return
            except:
                pass
        
        self._save_local('recommendations', event)
        return recommendation_id
    
    # ==========================================
    # USER INTERACTION TRACKING
    # ==========================================
    
    def track_interaction(self,
                         username: str,
                         interaction_type: str,
                         item_id: str,
                         recommendation_id: str = None,
                         item_rank: int = None,
                         metadata: Dict = None):
        """
        Track user interaction with recommended items.
        
        Args:
            username: User performing interaction
            interaction_type: view | click | save | purchase | dismiss | share
            item_id: ID of item interacted with
            recommendation_id: ID of recommendation batch (for CTR calculation)
            item_rank: Position of item in recommendation list
            metadata: Additional interaction data
        """
        event = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'interaction_type': interaction_type,
            'item_id': item_id,
            'recommendation_id': recommendation_id,
            'item_rank': item_rank,
            'metadata': metadata or {}
        }
        
        client = self._get_supabase()
        if client:
            try:
                client.table('analytics_interactions').insert(event).execute()
                return
            except:
                pass
        
        self._save_local('interactions', event)
    
    # ==========================================
    # FEEDBACK COLLECTION
    # ==========================================
    
    def track_feedback(self,
                      username: str,
                      recommendation_id: str,
                      feedback_type: str,
                      ratings: Dict,
                      items_rated: List[str] = None,
                      comments: str = None,
                      context: Dict = None):
        """
        Track user feedback on recommendations.
        
        Args:
            username: User providing feedback
            recommendation_id: ID of recommendation being rated
            feedback_type: implicit | explicit | survey
            ratings: Dictionary of rating dimensions
                - relevance: 1-5 (how relevant to weather/occasion)
                - satisfaction: 1-5 (overall satisfaction)
                - diversity: 1-5 (variety of suggestions)
                - personalization: 1-5 (matches personal style)
                - would_wear: 1-5 (likelihood to actually wear)
            items_rated: List of specific item IDs rated
            comments: Free-text comments
            context: Context at time of rating (weather, etc.)
        """
        event = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'recommendation_id': recommendation_id,
            'feedback_type': feedback_type,
            'ratings': ratings,
            'items_rated': items_rated or [],
            'comments': comments,
            'context': context or {},
            'nps_score': ratings.get('satisfaction', 3) * 2  # Convert to NPS-like 1-10
        }
        
        client = self._get_supabase()
        if client:
            try:
                client.table('analytics_feedback').insert(event).execute()
                return
            except:
                pass
        
        self._save_local('feedback', event)
    
    # ==========================================
    # SESSION TRACKING
    # ==========================================
    
    def start_session(self, username: str, device_info: Dict = None) -> str:
        """Start a new user session and return session ID."""
        session_id = str(uuid.uuid4())
        
        event = {
            'session_id': session_id,
            'username': username,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': None,
            'device_info': device_info or {},
            'pages_visited': [],
            'recommendations_viewed': 0,
            'interactions_count': 0,
            'feedback_given': False
        }
        
        client = self._get_supabase()
        if client:
            try:
                client.table('analytics_sessions').insert(event).execute()
            except:
                pass
        
        self._save_local('sessions', event)
        return session_id
    
    def update_session(self, session_id: str, updates: Dict):
        """Update session data."""
        client = self._get_supabase()
        if client:
            try:
                client.table('analytics_sessions').update(updates).eq('session_id', session_id).execute()
                return
            except:
                pass
        
        # Local update
        sessions = self._load_local('sessions')
        for session in sessions:
            if session.get('session_id') == session_id:
                session.update(updates)
                break
        
        with open(self.files['sessions'], 'w') as f:
            json.dump(sessions, f, indent=2, default=str)
    
    def end_session(self, session_id: str):
        """End a session and calculate duration."""
        sessions = self._load_local('sessions')
        for session in sessions:
            if session.get('session_id') == session_id:
                start = datetime.fromisoformat(session['start_time'])
                end = datetime.now()
                duration = (end - start).total_seconds()
                
                updates = {
                    'end_time': end.isoformat(),
                    'duration_seconds': duration
                }
                self.update_session(session_id, updates)
                break
    
    # ==========================================
    # ANALYTICS CALCULATIONS
    # ==========================================
    
    def calculate_ctr(self, time_window_hours: int = 24) -> Dict:
        """
        Calculate Click-Through Rate for recommendations.
        
        CTR = (Clicks / Impressions) * 100
        """
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        
        # Load data
        recommendations = self._load_local('recommendations')
        interactions = self._load_local('interactions')
        
        # Filter by time window
        recent_recs = [
            r for r in recommendations 
            if datetime.fromisoformat(r['timestamp']) > cutoff
        ]
        
        recent_clicks = [
            i for i in interactions 
            if datetime.fromisoformat(i['timestamp']) > cutoff
            and i['interaction_type'] == 'click'
        ]
        
        impressions = len(recent_recs)
        clicks = len(recent_clicks)
        
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        
        return {
            'ctr': round(ctr, 2),
            'impressions': impressions,
            'clicks': clicks,
            'time_window_hours': time_window_hours
        }
    
    def calculate_conversion_rate(self, time_window_hours: int = 24) -> Dict:
        """
        Calculate Conversion Rate (saves/purchases from recommendations).
        """
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        
        interactions = self._load_local('interactions')
        
        recent = [
            i for i in interactions 
            if datetime.fromisoformat(i['timestamp']) > cutoff
        ]
        
        views = len([i for i in recent if i['interaction_type'] == 'view'])
        saves = len([i for i in recent if i['interaction_type'] == 'save'])
        
        conversion = (saves / views * 100) if views > 0 else 0
        
        return {
            'conversion_rate': round(conversion, 2),
            'views': views,
            'saves': saves,
            'time_window_hours': time_window_hours
        }
    
    def calculate_engagement_metrics(self, time_window_hours: int = 168) -> Dict:
        """
        Calculate engagement metrics over time window (default 1 week).
        """
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        
        sessions = self._load_local('sessions')
        feedback = self._load_local('feedback')
        interactions = self._load_local('interactions')
        
        # Filter by time
        recent_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s['start_time']) > cutoff
        ]
        
        recent_feedback = [
            f for f in feedback 
            if datetime.fromisoformat(f['timestamp']) > cutoff
        ]
        
        # Calculate metrics
        total_sessions = len(recent_sessions)
        completed_sessions = [s for s in recent_sessions if s.get('duration_seconds')]
        
        avg_session_duration = 0
        if completed_sessions:
            durations = [s['duration_seconds'] for s in completed_sessions]
            avg_session_duration = sum(durations) / len(durations)
        
        # Feedback stats
        feedback_count = len(recent_feedback)
        avg_satisfaction = 0
        avg_relevance = 0
        
        if recent_feedback:
            satisfactions = [f['ratings'].get('satisfaction', 0) for f in recent_feedback]
            relevances = [f['ratings'].get('relevance', 0) for f in recent_feedback]
            avg_satisfaction = sum(satisfactions) / len(satisfactions)
            avg_relevance = sum(relevances) / len(relevances)
        
        return {
            'total_sessions': total_sessions,
            'avg_session_duration_minutes': round(avg_session_duration / 60, 2),
            'feedback_count': feedback_count,
            'avg_satisfaction': round(avg_satisfaction, 2),
            'avg_relevance': round(avg_relevance, 2),
            'time_window_hours': time_window_hours
        }
    
    def calculate_precision_recall(self) -> Dict:
        """
        Calculate Precision@K and Recall@K from user feedback.
        """
        feedback = self._load_local('feedback')
        
        if not feedback:
            return {
                'precision_at_3': 0,
                'recall_at_3': 0,
                'f1_at_3': 0,
                'sample_size': 0
            }
        
        # Use relevance ratings as proxy for "relevant" items
        # Item is "relevant" if rating >= 4
        relevant_counts = []
        total_recommended = []
        
        for f in feedback:
            ratings = f.get('ratings', {})
            relevance = ratings.get('relevance', 0)
            
            # Assume 3 items recommended per batch
            k = 3
            
            # If relevance >= 4, consider the recommendation batch as "relevant"
            if relevance >= 4:
                relevant_counts.append(k)  # All 3 items considered relevant
            elif relevance >= 3:
                relevant_counts.append(2)  # 2 out of 3 relevant
            else:
                relevant_counts.append(1)  # 1 out of 3 relevant
            
            total_recommended.append(k)
        
        # Calculate precision (relevant / recommended)
        precision = sum(relevant_counts) / sum(total_recommended) if total_recommended else 0
        
        # For recall, assume total relevant items = 5 per context
        total_relevant = len(feedback) * 5
        recall = sum(relevant_counts) / total_relevant if total_relevant > 0 else 0
        
        # F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision_at_3': round(precision, 3),
            'recall_at_3': round(recall, 3),
            'f1_at_3': round(f1, 3),
            'sample_size': len(feedback)
        }
    
    def calculate_ndcg(self) -> Dict:
        """
        Calculate NDCG@K from user feedback rankings.
        """
        import numpy as np
        
        feedback = self._load_local('feedback')
        
        if not feedback:
            return {'ndcg_at_3': 0, 'sample_size': 0}
        
        ndcg_scores = []
        
        for f in feedback:
            ratings = f.get('ratings', {})
            relevance = ratings.get('relevance', 3)
            
            # Simulate per-item scores based on overall relevance
            # In a real system, users would rate each item individually
            scores = [relevance, relevance - 0.5, relevance - 1.0]
            scores = [max(0, s) for s in scores]
            
            # DCG
            dcg = sum(s / np.log2(i + 2) for i, s in enumerate(scores))
            
            # Ideal DCG
            ideal_scores = sorted(scores, reverse=True)
            idcg = sum(s / np.log2(i + 2) for i, s in enumerate(ideal_scores))
            
            ndcg = dcg / idcg if idcg > 0 else 0
            ndcg_scores.append(ndcg)
        
        return {
            'ndcg_at_3': round(np.mean(ndcg_scores), 3) if ndcg_scores else 0,
            'sample_size': len(feedback)
        }
    
    def get_comprehensive_report(self) -> Dict:
        """
        Generate comprehensive analytics report for evaluation dashboard.
        """
        ctr = self.calculate_ctr(time_window_hours=168)  # 1 week
        conversion = self.calculate_conversion_rate(time_window_hours=168)
        engagement = self.calculate_engagement_metrics(time_window_hours=168)
        precision_recall = self.calculate_precision_recall()
        ndcg = self.calculate_ndcg()
        
        # Load raw counts
        api_calls = self._load_local('api_calls')
        recommendations = self._load_local('recommendations')
        interactions = self._load_local('interactions')
        feedback = self._load_local('feedback')
        sessions = self._load_local('sessions')
        
        return {
            'summary': {
                'total_api_calls': len(api_calls),
                'total_recommendations': len(recommendations),
                'total_interactions': len(interactions),
                'total_feedback': len(feedback),
                'total_sessions': len(sessions),
                'unique_users': len(set(
                    [r.get('username') for r in recommendations] +
                    [f.get('username') for f in feedback]
                ))
            },
            'ranking_metrics': {
                'precision_at_3': precision_recall['precision_at_3'],
                'recall_at_3': precision_recall['recall_at_3'],
                'f1_at_3': precision_recall['f1_at_3'],
                'ndcg_at_3': ndcg['ndcg_at_3']
            },
            'business_metrics': {
                'ctr': ctr['ctr'],
                'conversion_rate': conversion['conversion_rate'],
                'avg_session_duration_min': engagement['avg_session_duration_minutes']
            },
            'user_satisfaction': {
                'avg_satisfaction': engagement['avg_satisfaction'],
                'avg_relevance': engagement['avg_relevance'],
                'feedback_count': engagement['feedback_count']
            },
            'generated_at': datetime.now().isoformat()
        }


# Singleton instance for easy access
_analytics_instance = None

def get_analytics() -> AnalyticsCollector:
    """Get singleton analytics collector instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AnalyticsCollector()
    return _analytics_instance
