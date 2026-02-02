import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, JSON, ARRAY, DateTime
from datetime import datetime

load_dotenv()

# 1. Get URL from .env
DATABASE_URL = os.getenv("DATABASE_URL").replace("?sslmode=require", "")

# Fix for NeonDB connection string format
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# 2. Create Database Engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# --- TABLE 1: EXERCISES (Your Knowledge Base) ---
class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    difficulty_level = Column(Integer)
    tags = Column(ARRAY(String)) 
    description = Column(String, nullable=True)
    benefits = Column(String, nullable=True)
    setup = Column(String, nullable=True)
    execution = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)

# --- TABLE 2: RESULTS (History Log) ---
class FMSResult(Base):
    __tablename__ = "fms_results"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    input_profile = Column(JSON)
    effective_scores = Column(JSON)
    analysis_summary = Column(JSON)
    final_plan_output = Column(JSON)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)