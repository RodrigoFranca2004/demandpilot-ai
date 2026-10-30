import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core import database
from app.core.config import Settings


def test_settings_loads_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = "sqlite+pysqlite:///:memory:"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings(_env_file=None)

    assert settings.database_url == database_url


def test_get_db_provides_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(database, "get_engine", lambda: test_engine)

    session_generator = database.get_db()

    try:
        session = next(session_generator)

        assert isinstance(session, Session)
        assert session.scalar(text("SELECT 1")) == 1
    finally:
        session_generator.close()
        test_engine.dispose()
