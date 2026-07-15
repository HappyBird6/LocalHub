from datetime import datetime
from typing import Any
from openai import BaseModel
from pydantic import BaseModel,Field
from typing import Optional
############### 챗봇 관련 스키마 ###############
class MapMarker(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
class ChatRequest(BaseModel):
    # user_id: int      # 어느 사용자의 채팅인지
    message: str = Field(min_length=1, max_length=1000)      # 사용자가 입력한 질문
    marker: Optional[MapMarker] = None  # 사용자의 위치 정보 (선택적)
class ChatResponse(BaseModel):
    response: str     # OpenAI가 생성한 답변
    categories: list[str] = Field(default_factory=list)     # 질의 유형 (관광지, 축제, 음식점 등)

    intent: Optional[str] = None  # 사용자의 의도 (선택적)
    item: list[dict[str, Any]] = Field(default_factory=list)  # 관련 항목 (선택적)

    requires_marker: Optional[bool] = False  # 마커 표시 여부 (선택적)
## 프론트엔트 요청 JSON 예시
# {
#    "message": "근처 맛집 추천해줘",
#    "marker": {
#        "latitude": 37.5665,
#        "longitude": 126.9780
#    }
# }
# {
#   "message": "경복궁 찾아줘",
#   "marker": null
# }
################ 게시판 관련 스키마 ###############
class PostCreate(BaseModel):
    category: int
    title: str
    content: str
    lat : Optional[float] = None
    lng : Optional[float] = None
    locationName: Optional[str] = None
    nickname: Optional[str] = "김익명"
    password: str
    status: Optional[int] = 1  # 1: open, 0: closed

class PostUpdate(BaseModel):
    category: int
    title: Optional[str] = None
    content: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    locationName: Optional[str] = None
    nickname: Optional[str] = None
    password: str
    status: Optional[int] = None

class PostStatusUpdate(BaseModel):
    password: str

class PostDelete(BaseModel):
    password: str

class PostResponse(BaseModel):
    id: int
    category: int
    title: str
    content: str
    nickname: Optional[str] = "김익명"
    lat: Optional[float] = None
    lng: Optional[float] = None
    locationName: Optional[str]
    created_at: datetime
    comments: list["CommentResponse"] = Field(
        default_factory=list
    )
    commentsCount: int
    status: int = 1  # 1: open, 0: closed

class NearbyPostResponse(BaseModel):
    id: int
    category: int
    title: str
    content: str
    nickname: Optional[str] = "김익명"

    lat: float
    lng: float

    locationName: Optional[str] = None
    created_at: datetime
    commentsCount: int
    status: int

    distanceKm: float

class PostPassword(BaseModel):
    password: str

################# 댓글 관련 스키마 ###############
class CommentCreate(BaseModel):
    nickname: Optional[str] = "김익명"
    content: str
    password: str

class CommentUpdate(BaseModel):
    nickname: Optional[str] = "김익명"
    content: str
    password: str

class CommentDelete(BaseModel):
    password: str

class CommentResponse(BaseModel):
    id: int
    post_id: int
    nickname: Optional[str] = "김익명"
    content: str
    created_at: datetime

class CommentPassword(BaseModel):
    password: str