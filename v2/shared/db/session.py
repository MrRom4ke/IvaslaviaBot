import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_db_url() -> str:
    user = os.getenv("POSTGRES_USER", "ivaslavia")
    password = os.getenv("POSTGRES_PASSWORD", "ivaslavia")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ivaslavia_v2")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(build_db_url(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
