from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ERROR = "ERROR"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    repositories = relationship("Repository", back_populates="owner")

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    full_name = Column(String)  # e.g., owner/repo
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="repositories")
    jobs = relationship("AnalysisJob", back_populates="repository")

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    status = Column(SqlEnum(JobStatus), default=JobStatus.PENDING)
    evidence_json = Column(Text, nullable=True) # Storing JSON as text for SQLite simplicity
    steps_json = Column(Text, nullable=True)    # JSON array of {timestamp, message} step entries
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    repository = relationship("Repository", back_populates="jobs")
    documents = relationship("Document", back_populates="job")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"))
    content_md = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("AnalysisJob", back_populates="documents")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    repo_name = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="chat_sessions")
    repository = relationship("Repository", backref="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
