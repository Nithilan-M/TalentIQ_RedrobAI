import re
from typing import Dict, Any, List

class CandidateFeatureCalculator:
    def __init__(self, jd_data: Dict[str, Any]):
        """
        Initializes the feature calculator with the structured Job Description criteria.
        """
        self.jd_title = jd_data.get("title", "").lower()
        self.skills_required = [s.lower().strip() for s in jd_data.get("skills_required", [])]
        self.skills_preferred = [s.lower().strip() for s in jd_data.get("skills_preferred", [])]
        self.technologies = [t.lower().strip() for t in jd_data.get("technologies", [])]
        self.industry = jd_data.get("industry", "").lower()

        # Parse target years of experience
        exp_req = jd_data.get("experience_required", "")
        # Find first digit in string
        digits = re.findall(r"\d+", exp_req)
        self.target_years = int(digits[0]) if digits else 3 # Default to 3 years if not specified

    def calculate_skills_score(self, candidate_skills: List[str]) -> float:
        """Calculates skills overlap score (0 to 100)."""
        if not self.skills_required:
            return 50.0
            
        cand_skills_lower = {s.lower().strip() for s in candidate_skills}
        
        # Calculate required skills match (weighted 75% of skills score)
        req_matches = cand_skills_lower.intersection(self.skills_required)
        req_score = (len(req_matches) / len(self.skills_required)) * 100 if self.skills_required else 100.0
        
        # Calculate preferred skills match (weighted 25% of skills score)
        pref_score = 100.0
        if self.skills_preferred:
            pref_matches = cand_skills_lower.intersection(self.skills_preferred)
            pref_score = (len(pref_matches) / len(self.skills_preferred)) * 100
            
        return round((req_score * 0.75) + (pref_score * 0.25), 2)

    def calculate_experience_score(self, career_history: List[Dict[str, Any]]) -> float:
        """Calculates experience suitability score (0 to 100)."""
        total_months = sum(job.get("duration_months", 0) for job in career_history)
        years = total_months / 12.0
        if years == 0:
            return 0.0
        # Optimal experience is 100% of target; excess experience continues to add slight points, cap at 100
        score = min(years / self.target_years, 1.2) * 100.0
        return round(min(score, 100.0), 2)

    def calculate_career_progression(self, career_history: List[Dict[str, Any]]) -> float:
        """Scores career advancement: promotions and role tenures (0 to 100)."""
        if not career_history:
            return 0.0
        
        score = 50.0 # Start baseline
        
        # 1. Look for promotions (increasing senior titles over time)
        senior_keywords = ["senior", "lead", "staff", "manager", "director", "vp", "chief", "principal", "head"]
        has_senior_roles = False
        
        # Chronological order of jobs (assume last jobs are at the end of the list or start_dates)
        roles_sequence = [job.get("title", job.get("role", "")).lower() for job in career_history]
        
        # If the candidate moved from non-senior to senior titles
        for i in range(len(roles_sequence) - 1):
            prev_role = roles_sequence[i]
            next_role = roles_sequence[i+1]
            
            # Check if promotion indicators appear later in sequence
            prev_senior = any(k in prev_role for k in senior_keywords)
            next_senior = any(k in next_role for k in senior_keywords)
            
            if not prev_senior and next_senior:
                score += 25.0 # Promoted!
                has_senior_roles = True
                
        # 2. Score tenures (job hopping vs stability)
        avg_tenure_months = sum(job.get("duration_months", 0) for job in career_history) / len(career_history)
        if avg_tenure_months >= 24:
            score += 25.0 # Stable tenures
        elif avg_tenure_months <= 12:
            score -= 20.0 # High job hop rate
            
        return round(max(0.0, min(100.0, score)), 2)

    def calculate_industry_match(self, career_history: List[Dict[str, Any]], candidate_skills: List[str]) -> float:
        """Calculates candidate industry alignment (0 to 100)."""
        if not self.industry:
            return 50.0
            
        score = 30.0 # Baseline
        
        # Check if industry keyword is in skills or past experience text
        search_pattern = re.compile(rf"\b{self.industry}\b", re.IGNORECASE)
        for job in career_history:
            desc = job.get("description", "")
            ach = " ".join(job.get("achievements", [])) if isinstance(job.get("achievements"), list) else ""
            role = job.get("title", job.get("role", ""))
            
            if search_pattern.search(desc) or search_pattern.search(ach) or search_pattern.search(role):
                score += 35.0
                break
                
        # Skew industry score based on role title match
        if any(self.industry in job.get("company", "").lower() for job in career_history):
            score += 35.0
            
        return round(min(100.0, score), 2)

    def calculate_education_tier(self, education_list: List[Dict[str, Any]]) -> float:
        """Scores educational accomplishments based on institution tiers (0 to 100)."""
        if not education_list:
            return 0.0
            
        tier_mapping = {
            "tier_1": 1,
            "tier_2": 2,
            "tier_3": 3,
            "tier_4": 4,
            "unknown": 4
        }
        
        best_tier_val = 4
        for edu in education_list:
            tier_str = edu.get("tier", "unknown")
            if not isinstance(tier_str, str):
                if isinstance(tier_str, int) and 1 <= tier_str <= 4:
                    tier_val = tier_str
                else:
                    tier_val = 4
            else:
                tier_val = tier_mapping.get(tier_str.lower(), 4)
                
            if tier_val < best_tier_val:
                best_tier_val = tier_val
                
        tier_scores = {1: 100.0, 2: 75.0, 3: 50.0, 4: 30.0}
        return tier_scores.get(best_tier_val, 30.0)

    def calculate_certification_score(self, certifications: List[str]) -> float:
        """Scores certifications count and match (0 to 100)."""
        if not certifications:
            return 0.0
        # Scale score: 1 cert = 50, 2+ certs = 100
        score = min(len(certifications) * 50.0, 100.0)
        return score

    def calculate_leadership_score(self, career_history: List[Dict[str, Any]]) -> float:
        """Detects leadership keywords in past positions (0 to 100)."""
        if not career_history:
            return 0.0
            
        leadership_terms = ["lead", "manager", "head", "director", "vp", "chief", "founder", "principal", "architect", "president"]
        score = 0.0
        
        for job in career_history:
            role = job.get("title", job.get("role", "")).lower()
            if any(term in role for term in leadership_terms):
                score += 50.0
                # Give extra points if they are currently in a leadership role (last role)
                if job == career_history[-1]:
                    score += 50.0
                break
                
        return round(min(100.0, score), 2)

    def calculate_company_quality(self, career_history: List[Dict[str, Any]]) -> float:
        """Scores past employer quality based on top tech firms list (0 to 100)."""
        top_companies = ["google", "meta", "facebook", "amazon", "microsoft", "netflix", "apple", "uber", "airbnb", "stripe"]
        
        score = 30.0 # Baseline
        for job in career_history:
            company = job.get("company", "").lower()
            if any(tc in company for tc in top_companies):
                score += 35.0
                
        return round(min(100.0, score), 2)

    def calculate_role_similarity(self, career_history: List[Dict[str, Any]]) -> float:
        """Determines similarity between candidate past roles and target role (0 to 100)."""
        if not career_history or not self.jd_title:
            return 50.0
            
        # Check if target title contains backend, frontend, devops, manager, etc.
        target_keywords = set(self.jd_title.split())
        best_overlap = 0.0
        
        for job in career_history:
            past_role_words = set(job.get("title", job.get("role", "")).lower().split())
            overlap = len(target_keywords.intersection(past_role_words)) / len(target_keywords)
            if overlap > best_overlap:
                best_overlap = overlap
                
        return round(best_overlap * 100.0, 2)

    def calculate_technical_depth(self, candidate_skills: List[str]) -> float:
        """Scores candidate depth based on tech skill count (0 to 100)."""
        # A candidate with 15+ tech skills shows high technical depth
        score = min(len(candidate_skills) / 15.0, 1.0) * 100.0
        return round(score, 2)

    def compute_all_features(self, candidate: Dict[str, Any], embedding_similarity: float = 0.5) -> Dict[str, float]:
        """
        Compiles all engineered features for a single candidate profile.
        """
        skills_raw = candidate.get("skills", [])
        skills = [s.get("name", "") if isinstance(s, dict) else str(s) for s in skills_raw]
        career = candidate.get("career_history", [])
        edu = candidate.get("education", [])
        certs_list = candidate.get("certifications", [])
        beh = candidate.get("redrob_signals", candidate.get("behavioral_signals", {}))

        skills_score = self.calculate_skills_score(skills)
        exp_score = self.calculate_experience_score(career)
        prog_score = self.calculate_career_progression(career)
        ind_score = self.calculate_industry_match(career, skills)
        edu_score = self.calculate_education_tier(edu)
        cert_score = self.calculate_certification_score(certs_list)
        lead_score = self.calculate_leadership_score(career)
        comp_quality = self.calculate_company_quality(career)
        role_sim = self.calculate_role_similarity(career)
        tech_depth = self.calculate_technical_depth(skills)

        # Behavioral Score from signals using official BehaviorScorer
        from backend.behavior_engine.behavior_scorer import BehaviorScorer
        beh_score = BehaviorScorer.calculate_behavior_score(beh)

        # Open source activity score from github_activity_score
        github_activity = beh.get("github_activity_score", -1)
        open_source = float(github_activity) if github_activity >= 0 else 0.0

        # Calculate Overall candidate quality score (simple heuristic weight)
        overall_quality = (
            (skills_score * 0.25) +
            (embedding_similarity * 100 * 0.20) +
            (exp_score * 0.15) +
            (prog_score * 0.10) +
            (lead_score * 0.10) +
            (edu_score * 0.05) +
            (comp_quality * 0.05) +
            (role_sim * 0.05) +
            (beh_score * 0.05)
        )

        return {
            "skill_match_score": skills_score,
            "embedding_similarity": embedding_similarity,
            "experience_score": exp_score,
            "career_progression_score": prog_score,
            "industry_match": ind_score,
            "education_tier_score": edu_score,
            "certification_score": cert_score,
            "leadership_score": lead_score,
            "company_quality": comp_quality,
            "role_similarity": role_sim,
            "technical_depth": tech_depth,
            "open_source_score": round(open_source, 2),
            "behavioral_score": round(beh_score, 2),
            "overall_quality_score": round(overall_quality, 2)
        }
