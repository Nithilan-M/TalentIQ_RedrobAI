import re
import datetime
from typing import Dict, Any, List

class TrapDetector:
    def __init__(self):
        pass

    @staticmethod
    def detect_traps(candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scans a candidate profile for keyword stuffing, timeline anomalies,
        unusual career jumps, and inactive honeypots.
        Returns a dict: {"risk_score": float, "risk_level": str, "risk_explanation": str, "is_trap": bool}
        """
        profile = candidate.get("profile", {})
        career = candidate.get("career_history", [])
        skills = candidate.get("skills", [])
        signals = candidate.get("redrob_signals", {})

        risk_score = 0.0
        explanations = []

        # 1. Keyword Stuffing / Skill Inflation Trap
        # Check if skills count is high, but experience is very low
        skills_count = len(skills)
        years_exp = float(profile.get("years_of_experience", 0.0))
        
        if skills_count > 25:
            risk_score += 25.0
            explanations.append(f"Keyword stuffing: extreme number of skills ({skills_count}) listed on profile.")
        
        # Check if they have senior titles with very low years of experience
        current_title = profile.get("current_title", "").lower()
        senior_keywords = ["senior", "lead", "staff", "manager", "director", "vp", "chief", "principal", "head"]
        is_senior_title = any(k in current_title for k in senior_keywords)
        
        if is_senior_title and years_exp < 2.0:
            risk_score += 20.0
            explanations.append(f"Skill inflation: Senior/Lead title '{profile.get('current_title')}' claimed with only {years_exp} years of total experience.")

        # Check if the title is non-technical (e.g. Marketing Manager or Writer) but the profile lists advanced ML skills
        non_tech_titles = ["marketing", "writer", "sales", "hr ", "human resources", "recruiter", "content writer", "designer"]
        is_non_tech = any(nt in current_title for nt in non_tech_titles)
        
        technical_ml_skills = {"pytorch", "tensorflow", "xgboost", "lightgbm", "faiss", "sentence-transformers", "kubernetes", "devops", "docker"}
        cand_skill_names = {s.get("name", "").lower() for s in skills}
        has_advanced_tech = len(cand_skill_names.intersection(technical_ml_skills)) >= 2
        
        if is_non_tech and has_advanced_tech:
            risk_score += 30.0
            explanations.append(f"Keyword stuffing trap: Candidate is in a non-technical role ('{profile.get('current_title')}') but lists advanced ML/Retrieval engineering skills.")

        # 2. Timeline Inconsistencies / Overlapping Jobs
        # Check if jobs overlap in time
        overlapping_count = 0
        for i in range(len(career)):
            for j in range(i + 1, len(career)):
                job1 = career[i]
                job2 = career[j]
                
                s1 = job1.get("start_date", "")
                e1 = job1.get("end_date", "") or datetime.date.today().isoformat()
                s2 = job2.get("start_date", "")
                e2 = job2.get("end_date", "") or datetime.date.today().isoformat()
                
                try:
                    # Convert to datetime dates
                    start1 = datetime.date.fromisoformat(s1)
                    end1 = datetime.date.fromisoformat(e1)
                    start2 = datetime.date.fromisoformat(s2)
                    end2 = datetime.date.fromisoformat(e2)
                    
                    # Check overlap condition
                    if (start1 <= end2) and (start2 <= end1):
                        # Overlap exists, let's see duration of overlap in days
                        overlap_start = max(start1, start2)
                        overlap_end = min(end1, end2)
                        overlap_days = (overlap_end - overlap_start).days
                        if overlap_days > 90: # Overlap of more than 3 months
                            overlapping_count += 1
                except Exception:
                    pass
        
        if overlapping_count > 0:
            risk_score += min(overlapping_count * 15.0, 30.0)
            explanations.append(f"Timeline inconsistency: Detected {overlapping_count} overlapping full-time job tenures.")

        # 3. Impossible Career Progression
        # Junior to Director/VP in under 1.5 years
        if len(career) >= 2:
            try:
                first_job = career[0]
                last_job = career[-1]
                
                # Check if first job was junior-ish and last job was VP/Director
                f_role = first_job.get("title", "").lower()
                l_role = last_job.get("title", "").lower()
                
                is_first_junior = "intern" in f_role or "junior" in f_role or "trainee" in f_role
                is_last_director = "vp" in l_role or "director" in l_role or "chief" in l_role or "head" in l_role
                
                total_duration_months = sum(job.get("duration_months", 0) for job in career)
                
                if is_first_junior and is_last_director and total_duration_months < 18:
                    risk_score += 25.0
                    explanations.append(f"Impossible career progression: Promoted from junior/intern to director/executive in under 18 months.")
            except Exception:
                pass

        # 4. Honeypot Inactive Profiles
        # Response rate 5% and last active was long ago
        response_rate = signals.get("recruiter_response_rate", 1.0)
        last_active_str = signals.get("last_active_date", "")
        
        days_inactive = 0
        if last_active_str:
            try:
                last_active = datetime.date.fromisoformat(last_active_str)
                today = datetime.date(2026, 6, 18)
                days_inactive = (today - last_active).days
            except Exception:
                pass
                
        if response_rate < 0.15 and days_inactive > 120:
            risk_score += 20.0
            explanations.append("Honeypot alert: Profile matches search criteria but shows zero platform engagement (response rate < 15%, inactive > 4 months).")

        # 5. Service Company Trap (Consulting only in career history)
        consulting_firms = ["tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "tata consultancy", "hcl", "tech mahindra", "l&t", "lnt", "mindtree", "deloitte", "pwc", "ey", "kpmg"]
        if len(career) > 0:
            all_consulting = True
            for job in career:
                comp = job.get("company", "").lower()
                is_consulting = any(cf in comp for cf in consulting_firms)
                if not is_consulting:
                    all_consulting = False
                    break
            if all_consulting:
                risk_score += 25.0
                explanations.append("Service company trap: Candidate has only worked at consulting/IT service firms in their entire career.")

        # 6. Title Chaser Trap (Average tenure < 18 months and multiple companies)
        if len(career) >= 2:
            avg_tenure_months = sum(job.get("duration_months", 0) for job in career) / len(career)
            if avg_tenure_months < 18.0:
                companies = {job.get("company", "").lower() for job in career if job.get("company")}
                if len(companies) >= 2:
                    risk_score += 20.0
                    explanations.append(f"Title chaser: Career trajectory shows frequent job hops (average tenure of {avg_tenure_months:.1f} months).")

        # 7. Pure Research / Academic Trap
        research_keywords = ["researcher", "postdoc", "phd scholar", "academic", "professor"]
        title_lower = current_title.lower()
        if any(rk in title_lower for rk in research_keywords) and not any(ek in title_lower for ek in ["engineer", "developer", "architect", "lead"]):
            risk_score += 20.0
            explanations.append("Pure research trap: Candidate is in a pure research/academic role without production deployment experience.")

        # Determine level and boolean flag
        risk_score = round(min(100.0, risk_score), 2)
        is_trap = risk_score >= 40.0
        
        if risk_score >= 60.0:
            risk_level = "High"
        elif risk_score >= 30.0:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        explanation_str = " ; ".join(explanations) if explanations else "Profile verified: No anomalies detected."

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_explanation": explanation_str,
            "is_trap": is_trap
        }
