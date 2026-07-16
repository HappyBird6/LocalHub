from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base
import datetime

############### 모델 정의하는 곳 ###############
# class User(Base):
#     __tablename__ = "users"
    
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, index=True)
#     email = Column(String, unique=True, index=True)

# 챗봇 채팅 테이블
class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    # ip_hash = Column(String, index=True)
    message = Column(String)                   # 사용자 질문
    response = Column(String)                  # 챗봇 응답
    category = Column(String)                  # 카테고리 (쉼표로 구분)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

############### 게시판 관련 TABLE ###############
# 게시글 테이블
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    # ip_hash = Column(String, index=True)
    category = Column(Integer, index=True, nullable=False, default=3)  # 1: 모집, 2: 잡담, 3: 평가
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    locationName = Column(String, nullable=True)
    nickname = Column(String, nullable=True, default="김익명")
    password = Column(String, nullable=False)
    status = Column(Integer, nullable=True, default=1)  # 1: open, 0: closed
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
    
    commentsCount = Column(Integer, default=0)  # 댓글 수를 저장하는 컬럼
    comments = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
    )
# 댓글 테이블
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), index=True)
    nickname = Column(String, nullable=True, default="김익명")
    content = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))
   
    post = relationship("Post", back_populates="comments")

