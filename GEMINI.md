# GEMINI.md

This file contains foundational mandates for Gemini CLI when working in this repository. These instructions take absolute precedence over general workflows.

## Foundational Mandates

### 1. Development Integrity
- **Surgical Updates:** Apply precise changes strictly related to the task. Avoid unrelated refactoring.
- **Idiomatic Quality:** Adhere to existing patterns: Layered architecture (API → Service → Repository), `success_response()`/`error_response()` in API, and parameterized SQL only.
- **Migrations:** NEVER edit existing migration files in `migrations/`. New schema changes MUST be in a new sequentially numbered file (e.g., `007_...`).
- **Security:** Never log, print, or commit secrets from `.env`. Protect DB credentials and JWT secrets.

### 2. Validation & Testing
- **Unit Tests:** ALWAYS run `pytest tests/unit/ -q` before proposing or committing changes, especially for pricing logic or validators.
- **Linting:** Use `ruff check src/` to ensure code quality.
- **Manual Verification:** For UI changes, verify using existing templates and JS modules.

---

## Project Context

### Tech Stack
- **Backend:** Python 3.13, Flask 3.0.2, PostgreSQL
- **Frontend:** Tailwind CSS (CDN), Vanilla JS
- **Tools:** Pytest, Ruff, PyJWT, bcrypt

### Core Commands
```bash
source .venv/bin/activate
pip install -r requirements.txt
python run.py                       # Server at 0.0.0.0:5000
python -m src.database.migrate      # Run migrations
python -m src.database.seed         # Load demo data
pytest tests/                       # Run all tests
```

### Business Logic Highlights
- **Pricing:** Catering sizes (Small/Medium/Large) apply a 10% discount on the per-plate price.
- **Discounts:** Staff-only. Types: `percent` (0-100) or `fixed`.
- **Validation:** Phone numbers must be exactly 10 digits.

### Architecture
- `src/api/`: Blueprints & web routes.
- `src/services/`: Business logic (primary entry point for API).
- `src/repositories/`: SQL queries using `BaseRepository` helpers.
- `src/utils/`: Common responses, validators, and security helpers.
- `src/database/`: Connection pooling and migration runner.
