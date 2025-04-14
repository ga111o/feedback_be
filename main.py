import os
import fastapi
import uvicorn
from datetime import datetime
import json

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId

from database import app, Survey, Question, Response, surveys, questions, responses
import json
import dotenv
dotenv.load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/")
def read_root():
    return {"goood": "ga111o"}

class QuestionCreate(BaseModel):
    question_text: str
    question_type: str
    options: Optional[List[Dict[str, str]]] = None
    order: int
    is_required: bool = True
    rating_min: Optional[int] = None
    rating_max: Optional[int] = None
    rating_labels: Optional[Dict[int, str]] = None

class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True
    questions: List[QuestionCreate]

class SurveyResponse(BaseModel):
    survey_id: Optional[str] = None
    respondent_id: str
    answers: Dict[str, Any]

class SurveyDelete(BaseModel):
    survey_id: str
    password: str

class SurveyList(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    is_active: bool

class QuestionResponse(BaseModel):
    id: str
    survey_id: str
    question_text: str
    question_type: str
    options: Optional[List[Dict[str, str]]] = None
    order: int
    is_required: bool = True
    rating_min: Optional[int] = None
    rating_max: Optional[int] = None
    rating_labels: Optional[Dict[int, str]] = None

"""
POST /api/surveys/
{
    "title": "고객 만족도 조사",
    "description": "서비스 품질 개선을 위한 설문조사입니다.",
    "is_active": true,
    "questions": [
        {
          "question_text": "사용해본 기술은?",
          "question_type": "checkboxes",
          "options": [
            {"value": "react", "label": "React.js"},
            {"value": "vue", "label": "Vue.js"},
            {"value": "angular", "label": "Angular"}
          ],
          "order": 2,
          "is_required": true
        }
    ]
}
"""
@app.post("/api/surveys/", response_model=Survey)
async def create_survey(survey_create: SurveyCreate):
    # MongoDB에 저장할 설문 데이터 준비
    survey_data = Survey(
        title=survey_create.title,
        description=survey_create.description,
        is_active=survey_create.is_active
    ).dict()
    
    # MongoDB에 설문 저장
    result = await surveys.insert_one(survey_data)
    survey_id = str(result.inserted_id)
    
    # 질문 데이터 준비 및 저장
    for question in survey_create.questions:
        # Convert QuestionCreate to Question with survey_id
        question_dict = question.dict()
        question_dict["survey_id"] = survey_id
        question_data = Question(**question_dict)
        await questions.insert_one(question_data.dict())
    
    # 저장된 설문의 ID를 포함하여 반환
    survey_data["id"] = survey_id
    return survey_data

"""
POST /api/surveys/{survey_id}/responses
{
    "respondent_id": "user123",
    "answers": {
        "question_id_1": "선택된 답변",
        "question_id_2": ["checkbox1", "checkbox2"],  # 체크박스의 경우 복수 선택 가능
        "question_id_3": "주관식 답변"
    }
}
"""
@app.post("/api/surveys/{survey_id}/responses", response_model=Response)
async def submit_survey_response(survey_id: str, response: SurveyResponse):
    # JSON string으로 전달된 respondent_id 처리
    try:
        # 이미 객체인 경우 처리
        if isinstance(response.respondent_id, dict):
            respondent_id = json.dumps(response.respondent_id)
        else:
            # JSON 문자열인지 확인
            json.loads(response.respondent_id)
            respondent_id = response.respondent_id
    except json.JSONDecodeError:
        # 일반 문자열인 경우
        respondent_id = response.respondent_id
    
    # 설문이 존재하는지 확인
    survey = await surveys.find_one({"_id": ObjectId(survey_id)})
    if not survey:
        raise fastapi.HTTPException(status_code=404, detail="Survey not found")
    
    # 설문이 활성화되어 있는지 확인
    if not survey.get("is_active", False):
        raise fastapi.HTTPException(status_code=400, detail="Survey is not active")
    
    # 모든 필수 질문이 답변되었는지 확인
    required_questions = await questions.find(
        {"survey_id": survey_id, "is_required": True}
    ).to_list(length=None)
    
    required_question_ids = [str(q["_id"]) for q in required_questions]
    answered_questions = set(response.answers.keys())
    missing_questions = set(required_question_ids) - answered_questions
    
    if missing_questions:
        raise fastapi.HTTPException(
            status_code=400,
            detail=f"Missing answers for required questions: {missing_questions}"
        )
    
    # 응답 데이터 생성 및 저장
    response_data = Response(
        survey_id=survey_id,
        respondent_id=respondent_id,
        answers=response.answers
    ).dict()
    
    result = await responses.insert_one(response_data)
    response_data["id"] = str(result.inserted_id)
    
    return response_data

@app.delete("/api/surveys/")
async def delete_survey(survey_delete: SurveyDelete):
    if survey_delete.password != os.getenv("PASSWORD"):
        raise fastapi.HTTPException(status_code=401, detail="Invalid password")
    result = await surveys.delete_one({"_id": ObjectId(survey_delete.survey_id)})
    if result.deleted_count == 0:
        raise fastapi.HTTPException(status_code=404, detail="Survey not found")
    return {"success": True, "message": "Survey deleted successfully"}

@app.get("/api/surveys/", response_model=List[SurveyList])
async def get_surveys():
    survey_list = await surveys.find().to_list(length=None)
    
    # MongoDB ObjectId를 문자열로 변환
    for survey in survey_list:
        survey["id"] = str(survey["_id"])
        del survey["_id"]
    
    return survey_list

@app.get("/api/surveys/{survey_id}/questions", response_model=List[QuestionResponse])
async def get_survey_questions(survey_id: str):
    # 설문이 존재하는지 확인
    survey = await surveys.find_one({"_id": ObjectId(survey_id)})
    if not survey:
        raise fastapi.HTTPException(status_code=404, detail="Survey not found")
    
    # 설문에 해당하는 질문들 조회
    survey_questions = await questions.find({"survey_id": survey_id}).sort("order").to_list(length=None)
    
    # MongoDB ObjectId를 문자열로 변환
    for question in survey_questions:
        question["id"] = str(question["_id"])
        del question["_id"]
    
    return survey_questions


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=61310)

