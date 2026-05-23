from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import JobStatus

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class JobResponse(BaseModel):
    id: int
    repository_id: int
    status: JobStatus
    created_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    steps_json: Optional[str] = None
    class Config:
        from_attributes = True

class RepositoryCreate(BaseModel):
    url: str

class RepositoryResponse(BaseModel):
    id: int
    full_name: str
    url: str
    created_at: datetime
    jobs: List[JobResponse] = []
    class Config:
        from_attributes = True
