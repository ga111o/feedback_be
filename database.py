from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
app = FastAPI()

# MongoDB 연결
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.survey_db

# Pydantic 모델 정의
class Survey(BaseModel):
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
class Question(BaseModel):
    survey_id: str  # Survey의 ObjectId
    question_text: str
    question_type: str  # 'multiple_choice', 'text', 'rating', 'checkboxes', 'paragraph', 'short_answer'
    options: Optional[List[Dict[str, str]]] = None  # For multiple_choice and checkboxes: [{"value": "option1", "label": "Option 1"}]
    order: int  # 질문 순서
    is_required: bool = True
    section_id: Optional[Dict[int, str]] = None  # 문항이 속한 섹션 ID와 섹션 이름
    rating_min: Optional[int] = None  # rating 타입인 경우 최소값
    rating_max: Optional[int] = None  # rating 타입인 경우 최대값
    rating_labels: Optional[Dict[int, str]] = None  # rating 값에 대한 라벨 (예: {1: "매우 불만족", 5: "매우 만족"})
    bun_gi: Optional[List[int]] = None  # 분기문.
    
class Response(BaseModel):
    survey_id: str  # Survey의 ObjectId
    respondent_id: str  # 응답자 식별자
    answers: Dict[str, Any]  # {question_id: answer}
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

# 컬렉션 생성
surveys = db.surveys
questions = db.questions
responses = db.responses 