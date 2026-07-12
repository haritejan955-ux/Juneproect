"""Test-wide fixtures.

Sets a dummy OpenAI key and redirects all storage paths into a temp
directory before any test imports `app.config.settings` — constructing
`ChatOpenAI`/`OpenAIEmbeddings` with a dummy key succeeds without a network
call (the key is only used when a request is actually made), so this lets
the full app (including its lifespan) start up in CI with no real
credentials and no external calls.
"""

import os

import pytest

TEST_API_KEY = "test-api-key-do-not-use-in-production"
"""Fixed, obviously-fake key for tests that exercise the authenticated HTTP surface —
see `tests/integration/test_auth.py`. Never used as a default anywhere in application
code (see the fail-closed design note on `Settings.api_keys`); it only exists here."""


@pytest.fixture(scope="session", autouse=True)
def _test_environment(tmp_path_factory: pytest.TempPathFactory) -> None:
    data_dir = tmp_path_factory.mktemp("claim_agent_test_data")
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key-for-tests"
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["DATABASE_URL"] = f"sqlite:///{data_dir / 'test.db'}"
    os.environ["VECTOR_INDEX_DIR"] = str(data_dir / "indices")
    os.environ["POLICY_CORPUS_DIR"] = str(data_dir / "policy_corpus")
    os.environ["SYNTHETIC_CLAIMS_DIR"] = str(data_dir / "synthetic_claims")
    os.environ["UPLOAD_STORAGE_DIR"] = str(data_dir / "uploads")
    os.environ["API_KEYS"] = f'["{TEST_API_KEY}"]'
    (data_dir / "policy_corpus").mkdir(parents=True, exist_ok=True)

    from app.config.settings import get_settings

    get_settings.cache_clear()
