# Backend — US Insurance Claim Processing Agent

FastAPI + LangGraph backend implementing the 9-agent claim processing pipeline. See
[../docs](../docs) for full architecture documentation and [../README.md](../README.md) for
top-level setup instructions.

## Local development

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env   # fill in OPENAI_API_KEY or ANTHROPIC_API_KEY
python -m scripts.init_db
python -m scripts.build_policy_index
python -m scripts.generate_synthetic_claims
uvicorn app.main:app --reload
```

## Tests

```bash
pytest
```

## Layout

See [../docs/architecture.md](../docs/architecture.md) section 2 for the full annotated folder
structure and the reasoning behind it.
