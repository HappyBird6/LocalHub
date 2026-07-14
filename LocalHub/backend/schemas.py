from openai import BaseModel

class ChatRequest(BaseModel):
    user_id: int
    message: str

# ✅ 프론트엔드에서 보낼 JSON 데이터 형식
class ChatRequest(BaseModel):
    """
    프론트엔드가 이 형식으로 데이터를 전송해야 함
    
    예시:
    {
        "user_id": 1,
        "message": "서울에서 추천하는 관광지는?"
    }
    """
    user_id: int      # 어느 사용자의 채팅인지
    message: str      # 사용자가 입력한 질문

# ✅ 백엔드가 프론트엔드에게 반환할 JSON 형식
class ChatResponse(BaseModel):
    """
    백엔드가 프론트엔드에게 이 형식으로 응답함
    
    예시:
    {
        "response": "서울 최고의 관광지는...",
        "category": "관광지"
    }
    """
    response: str     # OpenAI가 생성한 답변
    category: str     # 질의 유형 (관광지, 축제, 음식점 등)