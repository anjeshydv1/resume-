import html
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent

SKILLS = {
    "python": ["python", "django", "flask", "fastapi"],
    "javascript": ["javascript", "typescript", "node.js", "nodejs", "react", "angular", "vue"],
    "java": ["java", "spring", "spring boot", "hibernate"],
    "sql": ["sql", "mysql", "postgresql", "sqlite", "mongodb"],
    "cloud": ["aws", "azure", "gcp", "google cloud", "docker", "kubernetes"],
    "data": ["machine learning", "data analysis", "pandas", "numpy", "tensorflow", "pytorch"],
    "web": ["html", "css", "rest api", "graphql", "bootstrap"],
    "tools": ["git", "github", "linux", "jira", "agile", "scrum"],
    "communication": ["communication", "presentation", "leadership", "teamwork"],
}

ROLE_CATALOG = {
    "Software Engineer": {"python", "javascript", "java", "sql", "web", "tools"},
    "Data Analyst": {"python", "sql", "data", "tools"},
    "Web Developer": {"javascript", "web", "sql", "tools"},
    "Cloud/DevOps Engineer": {"cloud", "tools", "python", "sql"},
    "Full Stack Developer": {"javascript", "python", "java", "sql", "web", "cloud"},
}


def normalize(text):
    return " ".join(text.lower().replace("/", " ").replace("-", " ").split())


def detect_skills(text):
    normalized = normalize(text)
    found = {}
    for category, aliases in SKILLS.items():
        matches = sorted({alias for alias in aliases if alias in normalized})
        if matches:
            found[category] = matches
    return found


def analyze_resume(resume_text, target_role="Software Engineer"):
    text = (resume_text or "").strip()
    if len(text) < 40:
        raise ValueError("Resume content must contain at least 40 characters.")

    found = detect_skills(text)
    found_names = set(found)
    expected = ROLE_CATALOG.get(target_role, ROLE_CATALOG["Software Engineer"])
    missing = sorted(expected - found_names)

    words = text.split()
    has_metrics = any(char.isdigit() for char in text)
    has_experience = any(word in normalize(text) for word in ("experience", "intern", "project", "developed", "implemented", "built"))
    score = 20
    score += min(len(found_names) * 7, 35)
    score += 20 if len(words) >= 80 else min(len(words) // 4, 20)
    score += 15 if has_metrics else 0
    score += 10 if has_experience else 0
    score = min(score, 100)

    flat_skills = sorted({skill.title() for values in found.values() for skill in values})
    role_scores = {}
    for role, requirements in ROLE_CATALOG.items():
        match = len(found_names & requirements)
        role_scores[role] = round(match / len(requirements) * 100)

    recommendations = sorted(role_scores.items(), key=lambda item: item[1], reverse=True)[:3]
    learning = []
    for category in missing[:4]:
        learning.append({
            "skill": category.title(),
            "reason": f"Frequently expected for {target_role} roles.",
            "resource": f"Complete an introductory {category.title()} course and one hands-on project.",
        })

    suggestions = [
        "Start each bullet with a strong action verb and describe the outcome." ,
        "Add measurable impact, such as percentages, time saved, users served, or revenue influenced.",
        "Place the strongest, role-relevant skills near the top of the resume.",
        "Tailor the summary to the target role and keep it concise (2-3 lines).",
    ]
    if not has_metrics:
        suggestions.insert(0, "Quantify achievements with numbers to make experience more credible.")
    if len(words) < 80:
        suggestions.append("Expand project and experience details so the resume does not appear incomplete.")

    summary_parts = []
    if flat_skills:
        summary_parts.append(f"The resume highlights {', '.join(flat_skills[:6])}.")
    summary_parts.append("It includes evidence of practical experience, technical capability, and role alignment." if has_experience else "It would benefit from clearer project or work experience details.")
    summary_parts.append(f"The estimated resume-readiness score is {score}/100.")

    return {
        "score": score,
        "summary": " ".join(summary_parts),
        "skills": found,
        "skillsList": flat_skills,
        "missingSkills": missing,
        "jobRecommendations": [
            {"role": role, "match": match, "reason": f"{match}% of key skill areas are represented in the resume."}
            for role, match in recommendations
        ],
        "learningSuggestions": learning,
        "improvementSuggestions": suggestions,
        "targetRole": target_role,
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            path = "/index.html"
        file_path = (ROOT / "static" / path.lstrip("/")).resolve()
        if ROOT.joinpath("static").resolve() not in file_path.parents and file_path != ROOT.joinpath("static", "index.html").resolve():
            self.send_error(403)
            return
        if not file_path.is_file():
            self.send_error(404)
            return
        content_type = "text/html" if file_path.suffix == ".html" else "text/css" if file_path.suffix == ".css" else "application/javascript"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self):
        path = urlparse(self.path).path
        if path == "/":
            path = "/index.html"
        file_path = (ROOT / "static" / path.lstrip("/")).resolve()
        if ROOT.joinpath("static").resolve() not in file_path.parents and file_path != ROOT.joinpath("static", "index.html").resolve():
            self.send_error(403)
            return
        if not file_path.is_file():
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path != "/api/analyze":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = analyze_resume(payload.get("resume", ""), payload.get("targetRole", "Software Engineer"))
            self.send_json(200, result)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})
        except Exception:
            self.send_json(500, {"error": "Unable to analyze the resume."})

    def log_message(self, format, *args):
        print(f"[resume-analyzer] {format % args}")


if __name__ == "__main__":
    requested_port = int(os.environ.get("RESUME_PORT", "0"))
    server = ThreadingHTTPServer(("127.0.0.1", requested_port), Handler)
    port = server.server_address[1]
    print(f"Resume Analyzer running at http://127.0.0.1:{port}")
    server.serve_forever()
