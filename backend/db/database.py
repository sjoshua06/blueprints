from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres.qwzicqpyogewrbjdakin:Virgotesla11&@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DATABASE_URL)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # VERY IMPORTANT
    pool_recycle=300,       # reconnect every 5 minutes
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)