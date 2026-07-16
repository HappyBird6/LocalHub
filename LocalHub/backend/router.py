from email.mime import message
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
# 데이터베이스 및 모델
from .database import get_db
from .models import *
from .schemas import *
from .chatbot import *
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from .chatbot import (
    analyze_query,
    get_general_chat_response,
)
from .database import get_db
from .models import Chat
from .schemas import (
    ChatRequest,
    ChatResponse,
)
from .services.post_search import (
    search_nearby_posts,
)
from .services.tour_search import (
    search_nearby_tour_places,
    search_tour_places_by_title,
)

# ✅ APIRouter 사용 (FastAPI 아님)
router = APIRouter()

# 라우팅
@router.get("/")
def read_root():
    file_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    return FileResponse(file_path)

############### 챗봇 ###############
# 챗봇 엔드포인트
# @router.post("/api/chat")
# def chat_endpoint(req: Request, request: ChatRequest, db: Session = Depends(get_db)):
#     # [Step 1] 질의 유형 분류
#     # 질문을 분석해서 어떤 종류의 질문인지 판단
#     categories = classify_query(request.message)
    
#     # [Step 2] OpenAI API로 응답 생성
#     # 분류된 카테고리와 질문을 OpenAI에 전송해서 답변 받음
#     response = get_chatbot_response(request.message, categories)
    
#     # [Step 3] 데이터베이스에 저장
#     # 카테고리를 문자열로 변환해서 저장
#     category_str = ", ".join(categories)

#     db.add(
#         Chat(
#             message=request.message,
#             response=response,
#             category=category_str
#         )
#     )
#     db.commit()
    
#     return ChatResponse(
#         response=response,
#         categories=categories
#     )
"""
{
  "message": "주변 관광지를 알려줘",
  "marker": {
    "latitude": 37.5665,
    "longitude": 126.978
  }
}
"""
@router.post("/api/chat",response_model=ChatResponse,)
def chat_endpoint(req: Request,request: ChatRequest,db: Session = Depends(get_db),):
    # Step 1: AI가 intent와 검색 조건 분석
    analysis = analyze_query(
        request.message
    )

    intent = analysis["intent"]
    categories = analysis["categories"]
    keyword = analysis["keyword"]
    radius_km = analysis["radius_km"]

    response_message = ""
    items = []
    requires_marker = False

    # Step 2-1: 마커 주변 모집글 검색
    if intent == "search_nearby_posts":
        if request.marker is None:
            response_message = (
                "주변 모집글을 검색하려면 "
                "카카오맵에서 기준 위치를 선택해 주세요."
            )
            requires_marker = True

        else:
            items = search_nearby_posts(
                db=db,
                latitude=(
                    request.marker.latitude
                ),
                longitude=(
                    request.marker.longitude
                ),
                radius_km=radius_km,
            )

            if items:
                response_message = (
                    f"선택한 위치에서 "
                    f"{radius_km:g}km 이내의 "
                    f"모집글 {len(items)}개를 "
                    f"찾았어요."
                )
            else:
                response_message = (
                    f"선택한 위치에서 "
                    f"{radius_km:g}km 이내의 "
                    "모집글을 찾지 못했어요."
                )

    # Step 2-2: 마커 주변 TourAPI 장소 검색
    elif intent == "search_nearby_places":
        if request.marker is None:
            response_message = (
                "주변 장소를 검색하려면 "
                "카카오맵에서 기준 위치를 선택해 주세요."
            )
            requires_marker = True

        else:
            items = search_nearby_tour_places(
                latitude=(
                    request.marker.latitude
                ),
                longitude=(
                    request.marker.longitude
                ),
                categories=categories,
                radius_km=radius_km,
            )

            category_text = (
                ", ".join(categories)
                if categories
                else "장소"
            )

            if items:
                response_message = (
                    f"선택한 위치에서 "
                    f"{radius_km:g}km 이내의 "
                    f"{category_text} "
                    f"{len(items)}곳을 찾았어요."
                )
                
                print("검색 결과 items:", items)
            else:
                response_message = (
                    f"선택한 위치에서 "
                    f"{radius_km:g}km 이내의 "
                    f"{category_text}을 "
                    "찾지 못했어요."
                )


    # Step 2-3: TourAPI title 검색
    elif intent == "search_place_by_title":
        if not keyword:
            response_message = (
                "검색할 장소 이름을 입력해 주세요."
            )

        else:
            items = search_tour_places_by_title(
                keyword=keyword
            )

            if items:
                response_message = (
                    f"'{keyword}' 검색 결과 "
                    f"{len(items)}곳을 찾았어요."
                )
            else:   
                response_message = (
                    f"'{keyword}'에 해당하는 "
                    "장소를 찾지 못했어요."
                )

    # Step 2-4: 일반 대화
    else:
        response_message = (
            get_general_chat_response(
                request.message
            )
        )

    # Step 3: 대화 기록 저장
    category_str = (
        ", ".join(categories)
        if categories
        else intent
    )

    chat_log = Chat(
        message=request.message,
        response=response_message,
        category=category_str,
    )

    db.add(chat_log)
    db.commit()

    # Step 4: 최종 응답
    return ChatResponse(
        response=response_message,
        categories=categories,
        intent=intent,
        items=items,
        requires_marker=requires_marker,
    )
############### 게시판 ###############
# 게시글 목록 조회  
@router.get("/api/posts")
def get_posts(req: Request, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회
    posts = db.query(Post).order_by(Post.created_at.desc(),Post.id.desc()).all()
    # [Step 2] 프론트엔드에 JSON 응답 반환
    return [PostResponse(
        id=post.id,
        category=post.category,
        title=post.title,
        content=post.content,
        lat=post.lat,
        lng=post.lng,
        locationName=post.locationName,
        status=post.status,
        created_at=post.created_at,
        commentsCount=post.commentsCount
    ) for post in posts]

# 게시글 목록 조회 (카테고리별)
@router.get("/api/posts/category/{category}")
def get_posts_by_category(req: Request, category: int, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회 (카테고리별)
    posts = db.query(Post).filter(Post.category == category).order_by(Post.created_at.desc(), Post.id.desc()).all()
    
    # [Step 2] 프론트엔드에 JSON 응답 반환
    return [PostResponse(
        id=post.id,
        category=post.category,
        title=post.title,
        content=post.content,
        locationName=post.locationName,
        status=post.status,
        created_at=post.created_at,
        commentsCount=post.commentsCount
    ) for post in posts]

# 게시글 생성
@router.post("/api/posts")
def create_post(req: Request, request: PostCreate, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에 게시글 생성
    new_post = Post(
        category=request.category,
        title=request.title,
        content=request.content,
        lat=request.lat,
        lng=request.lng,
        locationName=request.locationName,
        nickname=request.nickname,
        password=request.password,
        status=request.status
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # [Step 2] 프론트엔드에 JSON 응답 반환
    return {"message": "Post created successfully"}

# 게시글 조회
@router.get("/api/posts/{post_id}")
def get_posts(req: Request, post_id: int, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회
    post = db.query(Post).filter(Post.id == post_id).first()
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()

    if not post:
        return {"error": "Post not found"}
    
    # [Step 2] 프론트엔드에 JSON 응답 반환
    return [PostResponse(
        id=post.id,
        category=post.category,
        title=post.title,
        content=post.content,
        lat=post.lat,
        lng=post.lng,
        locationName=post.locationName,
        nickname=post.nickname,
        status=post.status,
        created_at=post.created_at,
        commentsCount = post.commentsCount,
        comments=[CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            nickname=comment.nickname,
            content=comment.content,
            created_at=comment.created_at
        ) for comment in comments])]

# 게시글 수정
@router.put("/api/posts/{post_id}")
def update_post(req: Request, post_id: int, request: PostUpdate, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        return {"error": "Post not found"}
    
    # # [Step 2] 비밀번호 확인
    # if post.password != request.password:
    #     return {"error": "Incorrect password"}
    
    # [Step 3] 게시글 수정
    
    if request.category is not None:
        post.category = request.category
    if request.title is not None:
        post.title = request.title
    if request.content is not None:
        post.content = request.content
    if request.locationName is not None:
        post.locationName = request.locationName
    if request.lat is not None:
        post.lat = request.lat
    if request.lng is not None:
        post.lng = request.lng
    if request.status is not None:
        post.status = request.status
    
    db.commit()
    
    # [Step 4] 프론트엔드에 JSON 응답 반환
    return {"message": "Post modified successfully"}

# 게시글 삭제
@router.delete("/api/posts/{post_id}")
def delete_post(req: Request, post_id: int, request: PostDelete, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return {"error": "Post not found"}
    
    # # [Step 2] 비밀번호 확인
    # if post.password != request.password:
    #     return {"error": "Incorrect password"}
    
    # [Step 3] 게시글 삭제
    db.delete(post)
    db.commit()
    
    # [Step 4] 프론트엔드에 JSON 응답 반환
    return {"message": "Post deleted successfully"}

# 게시글 모집 완료 변경
@router.put("/api/posts/{post_id}/status")
def update_post_status(req: Request, post_id: int, request: PostStatusUpdate, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        return {"error": "Post not found"}
    
    if post.password != request.password:
        return {"error": "Incorrect password"}
    
    # [Step 2] 모집 상태 변경 (1: open, 0: closed)
    post.status = 0 if post.status == 1 else 1
    db.commit()
    
    # [Step 3] 프론트엔드에 JSON 응답 반환
    return {"message": f"Post status updated to {'closed' if post.status == 0 else 'open'}"}

############### 댓글 관련 엔드포인트 ###############
# 댓글 생성
@router.post("/api/posts/{post_id}/comments")
def create_comment(req: Request, post_id: int, request: CommentCreate, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return {"error": "Post not found"}
    
    # [Step 2] 댓글 생성
    new_comment = Comment(
        post_id=post_id,
        nickname=request.nickname,
        content=request.content,
        password=request.password
    )
    db.add(new_comment)
    post.commentsCount += 1
    db.commit()
    db.refresh(new_comment)
    
    # [Step 3] 프론트엔드에 JSON 응답 반환
    return CommentResponse(
        id=new_comment.id,
        post_id=new_comment.post_id,
        nickname=new_comment.nickname,
        content=new_comment.content,
        created_at=new_comment.created_at
    )

# 댓글 수정
@router.put("/api/posts/{post_id}/comments/{comment_id}")
def update_comment(req: Request, post_id: int, comment_id: int, request: CommentUpdate, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 댓글 조회
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        return {"error": "Comment not found"}
    
    # [Step 2] 비밀번호 확인
    # if comment.password != request.password:
    #     return {"error": "Incorrect password"}
    
    # [Step 3] 댓글 수정
    comment.content = request.content
    comment.nickname = request.nickname
    comment.password = request.password
    db.commit()
    
    # [Step 4] 프론트엔드에 JSON 응답 반환
    return {"message": "Comment updated successfully"}

# 댓글 삭제
@router.delete("/api/posts/{post_id}/comments/{comment_id}")
def delete_comment(req: Request, post_id: int, comment_id: int, request: CommentDelete, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 댓글 조회
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        return {"error": "Comment not found"}

    # # [Step 2] 비밀번호 확인
    # if comment.password != request.password:
    #     return {"error": "Incorrect password"}
    
    # [Step 3] 게시글의 댓글 수 감소 
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        post.commentsCount = max(post.commentsCount - 1, 0)
        
    # [Step 4] 댓글 삭제
    db.delete(comment)
    db.commit()

    # [Step 4] 프론트엔드에 JSON 응답 반환
    return {"message": "Comment deleted successfully"}

# 게시글 비밀번호 체크
@router.post("/api/posts/{post_id}/check_password")
def check_password(req: Request, post_id: int, request: PostPassword, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 게시글 조회
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        return {"error": "Post not found"}
    print("포스트의 비번 : " + post.password + " password : " + request.password)
    # [Step 2] 비밀번호 확인
    if post.password != request.password:
        return {"error": "Incorrect password"}
    
    # [Step 3] 프론트엔드에 JSON 응답 반환
    return {"message": "Password is correct"}

# 댓글 비밀번호 체크
@router.post("/api/posts/{comment_id}/check_password/2")
def check_password(req: Request, comment_id: int, request: CommentPassword, db: Session = Depends(get_db)):
    # [Step 1] 데이터베이스에서 댓글 조회
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        return {"error": "Comment not found"}
    print("댓글의 비번 : " + comment.password + " password : " + request.password)
    # [Step 2] 비밀번호 확인
    if comment.password != request.password:
        return {"error": "Incorrect password"}
    
    # [Step 3] 프론트엔드에 JSON 응답 반환
    return {"message": "Password is correct"}

# @router.put("/api/posts/{post_id}/status")
# async def create_post(req: Request, db: Session = Depends(get_db)):
#     body = await req.json()
#     print("raw body:", body)
#     return {"received": body}