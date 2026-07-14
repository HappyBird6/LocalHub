from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
import datetime

# 모델 정의하는 곳
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

class Chat(Base):
    """
    채팅 기록 저장 테이블
    
    구조:
    - id: 채팅 ID (자동 증가)
    - user_id: 사용자 ID
    - message: 사용자 메시지
    - response: 챗봇 응답
    - category: 질문 카테고리
    - created_at: 생성 시간
    """
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)                   # 사용자 질문
    response = Column(String)                  # 챗봇 응답
    category = Column(String)                  # 카테고리 (쉼표로 구분)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)