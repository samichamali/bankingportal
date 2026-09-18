from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# This is where the database is initiated. quite normal stuff

SQLALCHEMY_DATABASE_URL = "sqlite:///./banking_portal.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()