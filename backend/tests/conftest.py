import os
import tempfile
from pathlib import Path

_TEST_DB_DIR = Path(tempfile.mkdtemp())
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB_DIR / 'test.db'}")
os.environ.setdefault("API_KEYS", '["test-key"]')
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-real")

import pytest  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.rag.store import InteractionRetriever  # noqa: E402
from tests.fakes import FakeChatModel, FakeEmbeddings  # noqa: E402

TEST_API_KEY = "test-key"


@pytest.fixture(autouse=True)
async def _ensure_tables_exist() -> None:
    """httpx's ASGITransport doesn't fire FastAPI's lifespan startup, so tables
    wouldn't otherwise get created before an integration test hits the DB."""
    from app.db.session import init_db

    await init_db()


@pytest.fixture
def fake_llm() -> FakeChatModel:
    return FakeChatModel()


@pytest.fixture
def interaction_retriever(tmp_path: Path) -> InteractionRetriever:
    settings = get_settings()
    return InteractionRetriever.build(settings.interaction_corpus_dir, tmp_path / "index", FakeEmbeddings())


@pytest.fixture
def graph_fakes(monkeypatch: pytest.MonkeyPatch, fake_llm: FakeChatModel, interaction_retriever: InteractionRetriever):
    """Patches every LLM/RAG call site the graph's nodes use so a full pipeline run
    hits zero network calls. Returns the fake chat model so tests can `.queue(...)`
    the structured responses they need, in call order."""
    import app.agents.nodes.prescription_parser as parser_node
    import app.agents.nodes.risk_synthesizer as synthesizer_node
    import app.agents.nodes.self_critic as critic_node
    import app.agents.nodes.interaction_retriever as retriever_node
    import app.api.routes.health as health_route

    monkeypatch.setattr(parser_node, "get_chat_model", lambda: fake_llm)
    monkeypatch.setattr(synthesizer_node, "get_chat_model", lambda: fake_llm)
    monkeypatch.setattr(critic_node, "get_chat_model", lambda: fake_llm)
    monkeypatch.setattr(retriever_node, "get_interaction_retriever", lambda: interaction_retriever)
    monkeypatch.setattr(health_route, "get_interaction_retriever", lambda: interaction_retriever)

    return fake_llm
