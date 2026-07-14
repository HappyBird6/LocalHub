import os
from fastapi import APIRouter, Depends  # ✅ FastAPI → APIRouter
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 데이터베이스 및 모델
from database import get_db
from models import User, Chat
from schemas import ChatRequest, ChatResponse
from chatbot import classify_query, get_chatbot_response

# ✅ APIRouter 사용 (FastAPI 아님)
router = APIRouter()

# 라우팅
@router.get("/")
def read_root():
    file_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    return FileResponse(file_path)

# 유저 생성 엔드포인트
@router.post("/users/")
def create_user(name: str, email: str, db: Session = Depends(get_db)):
    db_user = User(name=name, email=email)
    db.add(db_user)
    db.commit()
    return db_user

# user_id를 받아서 해당 유저 정보를 반환하는 엔드포인트
@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()

# 챗봇 엔드포인트
@router.post("/api/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # [Step 1] 질의 유형 분류
    # 질문을 분석해서 어떤 종류의 질문인지 판단
    categories = classify_query(request.message)
    
    # [Step 2] OpenAI API로 응답 생성
    # 분류된 카테고리와 질문을 OpenAI에 전송해서 답변 받음
    response = get_chatbot_response(request.message, categories)
    
    # [Step 3] 데이터베이스에 저장
    # 카테고리를 문자열로 변환해서 저장
    category_str = ", ".join(categories)

    chat_record = Chat(
        user_id=request.user_id,           # 누가 물었는가
        message=request.message,           # 무엇을 물었는가
        response=response,                 # 챗봇이 뭐라고 답했는가
        category=category_str                  # 질문의 종류가 뭔가
    )
    db.add(chat_record)
    db.commit()
    
    # [Step 4] 프론트엔드에 JSON 응답 반환
    # 프론트엔드가 이 데이터를 받아서 화면에 표시
    # [Step 4] 프론트엔드에 응답 반환
    return {
        "response": response,           # 챗봇의 답변
        "categories": categories,       # 분류된 카테고리들
        "user_message": request.message # 사용자 질문 (히스토리용)
    }
