"""Creates all tables for a fresh database. Idempotent —
`Base.metadata.create_all` only creates tables that don't already exist.

Usage: python -m scripts.init_db
"""

from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.memory.database import create_db_engine, init_db

logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_db_engine(settings)
    init_db(engine)
    logger.info("Database initialized at %s", settings.database_url)


if __name__ == "__main__":
    main()
