import json
import random
import datetime
import os

def generate_mock_candidates(filename: str, num_candidates: int = 1000):
    """
    Generates a mock candidates.jsonl dataset conforming to the Redrob schemas.
    """
    # Sample lists for generating realistic profiles
    names = ["Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince", "Evan Wright", 
             "Fiona Gallagher", "George Costanza", "Hannah Abbott", "Ian Malcolm", "Julia Roberts",
             "Kevin Bacon", "Laura Croft", "Michael Scott", "Nina Simone", "Oscar Wilde", 
             "Peter Parker", "Quentin Tarantino", "Rachel Green", "Steve Rogers", "Tony Stark",
             "Bruce Wayne", "Clark Kent", "Barry Allen", "Hal Jordan", "Arthur Curry", "Oliver Queen"]
    
    locations = ["Seoul", "San Francisco", "London", "Berlin", "Singapore", "Tokyo", "New York", 
                 "Bangalore", "Toronto", "Sydney", "Paris", "Austin", "Seattle", "Amsterdam"]
    
    companies = ["Google", "Meta", "Amazon", "Microsoft", "Netflix", "Apple", "Uber", 
                 "Airbnb", "Stripe", "Samsung", "Tencent", "Naver", "Kakao", "Coupang"]
    
    roles = [
        "Software Engineer", "Senior Software Engineer", "Backend Developer", 
        "Frontend Developer", "Fullstack Developer", "DevOps Engineer", 
        "Data Scientist", "ML Engineer", "Product Manager", "Engineering Manager"
    ]
    
    skill_pool = [
        "Python", "Flask", "FastAPI", "REST APIs", "Microservices", "Docker", "Kubernetes",
        "React", "TypeScript", "JavaScript", "HTML/CSS", "Next.js", "Tailwind CSS",
        "PostgreSQL", "MongoDB", "Redis", "SQL", "SQLAlchemy", "Alembic", "AWS", "GCP",
        "Git", "CI/CD", "Node.js", "Java", "Spring Boot", "C++", "Go", "Rust", "TensorFlow",
        "PyTorch", "Scikit-Learn", "Pandas", "NumPy", "XGBoost", "LightGBM"
    ]
    
    degrees = ["B.S.", "M.S.", "Ph.D.", "B.Tech", "M.Tech", "B.A."]
    fields = ["Computer Science", "Information Technology", "Software Engineering", 
              "Data Science", "Electrical Engineering", "Mathematics"]
    
    institutions = [
        ("MIT", 1), ("Stanford University", 1), ("IIT Bombay", 1), ("Seoul National University", 1),
        ("UC Berkeley", 1), ("KAIST", 1), ("University of Washington", 2), ("Boston University", 2),
        ("State University of NY", 3), ("Local Tech College", 3)
    ]
    
    certs = ["AWS Certified Solutions Architect", "Google Cloud Professional Engineer", 
             "Certified Kubernetes Administrator (CKA)", "Scrum Master (PSM I)", 
             "TensorFlow Developer Certificate"]
    
    languages = ["English", "Korean", "Spanish", "German", "Japanese", "Mandarin", "French"]

    with open(filename, "w", encoding="utf-8") as f:
        for idx in range(1, num_candidates + 1):
            cand_id = 100000 + idx
            name = random.choice(names) + f" {idx}"
            email = f"candidate_{cand_id}@example.com"
            phone = f"+82-10-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
            location = random.choice(locations)
            open_work = random.choice([True, True, False]) # skewed towards active candidates
            completeness = round(random.uniform(0.6, 1.0), 2)
            
            signup_date = (datetime.date.today() - datetime.timedelta(days=random.randint(30, 365))).isoformat()
            last_active = (datetime.date.today() - datetime.timedelta(days=random.randint(0, 15))).isoformat()
            salary = random.choice([50000, 60000, 75000, 90000, 110000, 130000, 150000])
            notice = random.choice([0, 15, 30, 60, 90])
            work_mode = random.choice(["Remote", "Hybrid", "On-site"])
            relocate = random.choice([True, False])
            linkedin = random.choice([True, False])
            github = f"git_user_{cand_id}"

            # Skills selection
            cand_skills = random.sample(skill_pool, random.randint(4, 12))
            
            # Sub-components: Career history
            num_jobs = random.randint(1, 4)
            career = []
            current_months = 0
            for j_idx in range(num_jobs):
                comp = random.choice(companies)
                role = random.choice(roles)
                duration = random.randint(6, 48)
                current_months += duration
                
                # Make sure senior roles are later in career
                if j_idx == 0 and "Senior" in role:
                    role = role.replace("Senior ", "")
                elif j_idx == num_jobs - 1 and num_jobs > 2:
                    role = "Senior " + role if "Senior" not in role else role

                start = (datetime.date.today() - datetime.timedelta(days=current_months * 30)).isoformat()
                end = (datetime.date.today() - datetime.timedelta(days=(current_months - duration) * 30)).isoformat() if j_idx < num_jobs - 1 else None
                
                career.append({
                    "company": comp,
                    "role": role,
                    "duration_months": duration,
                    "start_date": start,
                    "end_date": end,
                    "description": f"Developed backend services and microservices using {', '.join(random.sample(cand_skills, min(3, len(cand_skills))))}.",
                    "achievements": [f"Improved service performance by {random.randint(10, 45)}% using optimized queries."]
                })
            
            # Education
            num_edu = random.randint(1, 2)
            edu_list = []
            for _ in range(num_edu):
                inst, tier = random.choice(institutions)
                edu_list.append({
                    "degree": random.choice(degrees),
                    "field_of_study": random.choice(fields),
                    "institution": inst,
                    "year": str(random.randint(2012, 2024)),
                    "tier": tier
                })

            # Certifications
            cand_certs = random.sample(certs, random.randint(0, 2))
            
            # Languages
            cand_langs = random.sample(languages, random.randint(1, 3))
            if "English" not in cand_langs:
                cand_langs.append("English")

            # Behavioral signals
            assessments = {}
            for s in random.sample(cand_skills, min(3, len(cand_skills))):
                assessments[s] = round(random.uniform(50.0, 100.0), 1)

            behavioral = {
                "connection_count": random.randint(50, 1500),
                "endorsements_count": random.randint(2, 50),
                "applications_submitted": random.randint(1, 40),
                "skill_assessment_scores": assessments,
                "recruiter_response_rate": round(random.uniform(0.4, 1.0), 2),
                "average_response_time_seconds": random.randint(60, 86400),
                "saved_by_recruiters_count": random.randint(0, 15),
                "interview_completion_rate": round(random.uniform(0.5, 1.0), 2),
                "offer_acceptance_rate": round(random.uniform(0.6, 1.0), 2),
                "verified_email": random.choice([True, True, False]),
                "verified_phone": random.choice([True, True, False]),
                "github_commits_last_year": random.randint(0, 400),
                "search_appearances_last_month": random.randint(5, 200)
            }

            candidate_row = {
                "candidate_id": cand_id,
                "profile": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "open_to_work": open_work,
                    "profile_completeness": completeness,
                    "signup_date": signup_date,
                    "last_active_date": last_active,
                    "salary_expectation": salary,
                    "notice_period_days": notice,
                    "work_mode_preference": work_mode,
                    "relocation_ready": relocate,
                    "linkedin_connected": linkedin,
                    "github_username": github
                },
                "career_history": career,
                "education": edu_list,
                "skills": cand_skills,
                "certifications": cand_certs,
                "languages": cand_langs,
                "behavioral_signals": behavioral
            }
            
            f.write(json.dumps(candidate_row) + "\n")
            
    print(f"Generated {num_candidates} mock candidates in '{filename}' successfully.")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    generate_mock_candidates("candidates.jsonl", 1000)
