# ResumeAI

ResumeAI is a dependency-free web application for placement cells. Students paste resume content, select a target role, and receive a resume summary, skill analysis, job recommendations, missing skills, learning suggestions, and improvement guidance.

## Run locally

```powershell
python app.py
```

Open the local URL printed in the terminal. To request a specific port, set `RESUME_PORT`, for example `$env:RESUME_PORT=8080; python app.py`.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Architecture

- Standard-library Python HTTP server
- REST endpoint: `POST /api/analyze`
- Static HTML, CSS, and JavaScript client
- Local resume analysis using a validated skill taxonomy and role profile scoring
- No API key, external service, student-account storage, or resume persistence required

Resume text is processed in memory and is not written to disk.

## Production notes

The current analyzer is a transparent, deterministic AI-style assistant intended for a demo and placement environment. Before public deployment, add authentication, HTTPS, rate limiting, privacy controls, durable logging, dependency scanning, and an LLM provider with prompt-injection controls if generative analysis is required.
