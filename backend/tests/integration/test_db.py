import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def postgres_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()


def test_db_connection(postgres_url):
    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_db_ping(postgres_url):
    engine = create_engine(postgres_url, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        assert "PostgreSQL" in version
