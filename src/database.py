import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

# --- CONNECTION SETUP ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file")

# Ensure we use the async driver for PostgreSQL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# TABLE 1: RAW SUB-INPUTS
# This table strictly stores "What the user entered"
class AssessmentInput(Base):
    __tablename__ = "assessment_inputs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Stores the full nested dictionary of checkboxes (e.g., {"overhead_squat": {"heels_lift": true...}})
    raw_json_data = Column(JSON) 

    # Relationship to link to the scores
    scores = relationship("AssessmentScore", back_populates="input_data", uselist=False)


# TABLE 2: MAIN FMS SCORES
# This table strictly stores "What the system calculated"
class AssessmentScore(Base):
    __tablename__ = "assessment_scores"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key: This links the score back to the specific raw inputs in Table 1
    input_id = Column(Integer, ForeignKey("assessment_inputs.id"))
    
    # The 7 Calculated Scores (0-3)
    overhead_squat = Column(Integer)
    hurdle_step = Column(Integer)
    inline_lunge = Column(Integer)
    shoulder_mobility = Column(Integer)
    active_straight_leg_raise = Column(Integer)
    trunk_stability_pushup = Column(Integer)
    rotary_stability = Column(Integer)
    
    total_score = Column(Integer)
    generated_workout = Column(JSON, nullable=True)

    # Relationship
    input_data = relationship("AssessmentInput", back_populates="scores")

