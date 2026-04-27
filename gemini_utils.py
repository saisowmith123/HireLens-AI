import os
import re
import json
from dotenv import load_dotenv
from google import genai

# -------------------------------
# Setup Gemini
# -------------------------------

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

client = genai.Client(api_key=API_KEY)

# Use latest stable Flash model
MODEL = "models/gemini-2.5-flash"

# -------------------------------
# Utility: Safe JSON Extraction
# -------------------------------

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in model response")
    return json.loads(match.group())

# -------------------------------
# Skill Extraction via Gemini
# -------------------------------

def extract_skills(resume_text, jd_text):
    prompt = f"""
Extract technical skills from the resume and job description.

Return ONLY raw JSON:
{{
  "resume_skills": [],
  "jd_skills": []
}}

Rules:
- Extract tools, frameworks, languages, platforms.
- Include implicit skills (e.g., Flask APIs → Flask, REST API).
- Do NOT include explanation text.

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{jd_text[:3000]}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return extract_json(response.text)
    except Exception:
        return {"resume_skills": [], "jd_skills": []}

# -------------------------------
# Skill Equivalence Mapping
# -------------------------------
SKILL_EQUIVALENCES = {

    # ================= API =================
    "rest api": ["restful api", "rest apis", "api development"],
    "restful api": ["rest api", "api development"],
    "api development": ["rest api", "restful api"],

    # ================= CI/CD =================
    "ci/cd": [
        "continuous integration",
        "continuous deployment",
        "cicd",
        "github workflows",
        "github actions",
        "devops"
    ],
    "continuous integration": ["ci/cd", "cicd"],
    "continuous deployment": ["ci/cd", "cicd"],
    "github workflows": ["ci/cd", "github actions"],
    "github actions": ["ci/cd", "github workflows"],

    # ================= CLOUD =================
    "aws": ["cloud infrastructure", "cloud platforms", "amazon web services"],
    "gcp": ["cloud infrastructure", "cloud platforms", "google cloud"],
    "azure": ["cloud infrastructure", "cloud platforms", "microsoft azure"],
    "cloud infrastructure": ["aws", "gcp", "azure", "cloud platforms"],
    "cloud platforms": ["aws", "gcp", "azure", "cloud infrastructure"],
    "cloud computing": ["aws", "gcp", "azure", "cloud platforms"],

    # ================= BACKEND =================
    "backend development": [
        "flask",
        "django",
        "node.js",
        "express",
        "spring"
    ],
    "flask": ["backend development", "rest api"],
    "django": ["backend development", "rest api"],
    "node.js": ["backend development", "express"],
    "express": ["backend development", "node.js"],
    "spring": ["backend development"],

    # ================= FRONTEND =================
    "frontend development": ["react", "angular", "vue", "frontend frameworks"],
    "frontend frameworks": ["react", "angular", "vue", "frontend development"],
    "react": ["frontend development"],
    "angular": ["frontend development"],
    "vue": ["frontend development"],

    # ================= DATABASE =================
    "databases": ["sql", "mysql", "postgresql", "mongodb", "nosql"],
    "database": ["sql", "mysql", "postgresql", "mongodb", "nosql"],
    "sql": ["mysql", "postgresql", "databases"],
    "mysql": ["sql", "databases"],
    "postgresql": ["sql", "databases"],
    "mongodb": ["nosql", "databases"],
    "nosql": ["mongodb", "databases"],

    # ================= DEVOPS & MICROSERVICES =================
    "docker": ["containerization", "microservices"],
    "kubernetes": ["containerization", "microservices"],
    "containerization": ["docker", "kubernetes"],
    "microservices": ["docker", "kubernetes", "microservices architecture"],
    "microservices architecture": ["microservices", "docker", "kubernetes"],

    # ================= VERSION CONTROL =================
    "git": ["github", "version control"],
    "github": ["git", "version control"],
    "version control": ["git", "github"],

    # ================= METHODOLOGY =================
    "agile": ["scrum", "kanban"],
    "scrum": ["agile"],
    "kanban": ["agile"]
}


# -------------------------------
# Normalization
# -------------------------------

def normalize(skill: str) -> str:
    return skill.lower().strip().replace("-", "").replace("_", "")

# -------------------------------
# Matching Logic
# -------------------------------

def is_full_match(resume_skill, jd_skill):
    r = normalize(resume_skill)
    j = normalize(jd_skill)

    if r == j:
        return True

    if r in SKILL_EQUIVALENCES and j in [normalize(x) for x in SKILL_EQUIVALENCES[r]]:
        return True

    if j in SKILL_EQUIVALENCES and r in [normalize(x) for x in SKILL_EQUIVALENCES[j]]:
        return True

    return False


def is_partial_match(resume_skill, jd_skill):
    r = normalize(resume_skill)
    j = normalize(jd_skill)

    if is_full_match(resume_skill, jd_skill):
        return False

    if r in j or j in r:
        return True

    return False

# -------------------------------
# Semantic Skill Matching
# -------------------------------

def semantic_skill_matching(resume_skills, jd_skills):

    analysis = []
    matched = []
    partial = []
    missing = []

    for jd in jd_skills:
        found = False

        for rs in resume_skills:
            if is_full_match(rs, jd):
                analysis.append({
                    "jd_skill": jd,
                    "status": "Full Match",
                    "resume_evidence": rs,
                    "confidence": "High"
                })
                matched.append(jd)
                found = True
                break

        if not found:
            for rs in resume_skills:
                if is_partial_match(rs, jd):
                    analysis.append({
                        "jd_skill": jd,
                        "status": "Partial Match",
                        "resume_evidence": rs,
                        "confidence": "Medium"
                    })
                    partial.append(jd)
                    found = True
                    break

        if not found:
            analysis.append({
                "jd_skill": jd,
                "status": "Missing",
                "resume_evidence": "",
                "confidence": "Low"
            })
            missing.append(jd)

    total = len(jd_skills)
    full_score = len(matched)
    partial_score = len(partial) * 0.5

    similarity_score = int(((full_score + partial_score) / total) * 100) if total else 0

    return {
        "analysis": analysis,
        "matched_skills": matched,
        "partial_matches": partial,
        "missing_skills": missing,
        "similarity_score": similarity_score
    }

# -------------------------------
# Experience + Project Evaluation
# -------------------------------

def evaluate_experience_and_projects(resume_text, jd_text):

    prompt = f"""
Evaluate the resume against the job description.

Return ONLY JSON:
{{
  "experience_score": number,
  "project_score": number,
  "improvements": [],
  "summary": ""
}}

Score from 0–100.

RESUME:
{resume_text[:2000]}

JOB DESCRIPTION:
{jd_text[:2000]}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return extract_json(response.text)
    except Exception:
        return {
            "experience_score": 0,
            "project_score": 0,
            "improvements": [],
            "summary": "Evaluation failed"
        }

# -------------------------------
# Final ATS Analysis
# -------------------------------

def analyze_resume_jobdesc(resume_text, jd_text):

    skills = extract_skills(resume_text, jd_text)
    resume_skills = skills.get("resume_skills", [])
    jd_skills = skills.get("jd_skills", [])

    skill_result = semantic_skill_matching(resume_skills, jd_skills)
    exp_result = evaluate_experience_and_projects(resume_text, jd_text)

    skill_score = skill_result["similarity_score"]
    exp_score = int(exp_result.get("experience_score", 0))
    proj_score = int(exp_result.get("project_score", 0))

    final_ats = round(
        skill_score * 0.70 +
        exp_score * 0.20 +
        proj_score * 0.10
    )

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "analysis": skill_result["analysis"],
        "matched_skills": skill_result["matched_skills"],
        "partial_matches": skill_result["partial_matches"],
        "missing_skills": skill_result["missing_skills"],
        "improvements": exp_result.get("improvements", []),
        "summary": exp_result.get("summary", ""),
        "score_breakdown": {
            "skill_match": skill_score,
            "experience_match": exp_score,
            "project_match": proj_score
        },
        "final_ats_score": final_ats
    }

# -------------------------------
# Chat Feature
# -------------------------------

def gemini_chat(resume_text, jd_text, user_msg):

    prompt = f"""
Answer the user's question about resume-job match.
Be specific and actionable.

RESUME:
{resume_text[:1500]}

JOB DESCRIPTION:
{jd_text[:1500]}

QUESTION:
{user_msg[:400]}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text
    except Exception:
        return "Chat failed."
