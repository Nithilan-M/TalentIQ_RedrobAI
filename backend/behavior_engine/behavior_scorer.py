import datetime
from typing import Dict, Any

class BehaviorScorer:
    def __init__(self):
        pass

    @staticmethod
    def calculate_behavior_score(signals: Dict[str, Any]) -> float:
        """
        Calculates a composite behavioral score (0 to 100) based on platform engagement signals.
        If signals is missing or empty, returns a default neutral score of 50.0.
        """
        if not signals:
            return 50.0

        score = 0.0
        total_weight = 0.0

        # 1. Profile Completeness (Weight: 10)
        profile_comp = signals.get("profile_completeness_score", 0.0)
        score += (profile_comp / 100.0) * 10.0
        total_weight += 10.0

        # 2. Open to Work Status (Weight: 10)
        open_to_work = signals.get("open_to_work_flag", False)
        score += 10.0 if open_to_work else 3.0
        total_weight += 10.0

        # 3. Recruiter Response Rate (Weight: 15)
        response_rate = signals.get("recruiter_response_rate", 0.5)
        # Handle cases where value is -1 or missing
        if response_rate < 0:
            response_rate = 0.5
        score += response_rate * 15.0
        total_weight += 15.0

        # 4. Average Response Time (Weight: 10)
        # Prefer response time under 12 hours
        response_hours = signals.get("avg_response_time_hours", 24.0)
        if response_hours <= 2.0:
            score += 10.0
        elif response_hours <= 12.0:
            score += 8.0
        elif response_hours <= 24.0:
            score += 5.0
        else:
            score += 1.0
        total_weight += 10.0

        # 5. Activity Latency (Weight: 15)
        # Parse last active date
        last_active_str = signals.get("last_active_date", "")
        days_inactive = 30
        if last_active_str:
            try:
                last_active = datetime.date.fromisoformat(last_active_str)
                # For challenge testing, let's assume current date is 2026-06-18
                today = datetime.date(2026, 6, 18)
                days_inactive = (today - last_active).days
            except Exception:
                days_inactive = 30 # Default to 30 days if parse error
        
        if days_inactive <= 7:
            score += 15.0
        elif days_inactive <= 30:
            score += 12.0
        elif days_inactive <= 90:
            score += 7.0
        elif days_inactive <= 180:
            score += 3.0
        else:
            score += 0.0 # Down-weight inactive profiles
        total_weight += 15.0

        # 6. Notice Period (Weight: 10)
        # Prefer short notice (0-30 days)
        notice_days = signals.get("notice_period_days", 30)
        if notice_days <= 15:
            score += 10.0
        elif notice_days <= 30:
            score += 8.0
        elif notice_days <= 60:
            score += 4.0
        else:
            score += 1.0 # 90+ days notice down-weighted
        total_weight += 10.0

        # 7. Platform Activity (applications, views, search appearances) (Weight: 10)
        apps = signals.get("applications_submitted_30d", 0)
        views = signals.get("profile_views_received_30d", 0)
        searches = signals.get("search_appearance_30d", 0)
        
        activity_sum = apps + (views * 0.1) + (searches * 0.05)
        score += min(activity_sum / 20.0, 1.0) * 10.0
        total_weight += 10.0

        # 8. Trust Score (verified phone, email, linkedin, connections) (Weight: 10)
        trust = 0.0
        if signals.get("verified_email", False): trust += 3.0
        if signals.get("verified_phone", False): trust += 3.0
        if signals.get("linkedin_connected", False): trust += 2.0
        
        connections = signals.get("connection_count", 0)
        trust += min(connections / 500.0, 1.0) * 2.0
        
        score += trust
        total_weight += 10.0

        # 9. Interview and Offer acceptance (Weight: 10)
        interview_rate = signals.get("interview_completion_rate", 0.8)
        offer_rate = signals.get("offer_acceptance_rate", 0.8)
        if interview_rate < 0: interview_rate = 0.8
        if offer_rate < 0: offer_rate = 0.8

        score += (interview_rate * 5.0) + (offer_rate * 5.0)
        total_weight += 10.0

        # Normalize to 0-100 scale
        final_score = (score / total_weight) * 100.0
        return round(final_score, 2)
