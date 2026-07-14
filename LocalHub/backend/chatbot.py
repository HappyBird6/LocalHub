from openai import OpenAI
import os
from dotenv import load_dotenv
# 환경변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
models = client.models.list()

for model in models.data:
    print(model.id)
def classify_query(message: str) -> list:
    """모든 매칭 카테고리 반환"""
    keywords = {
        "관광지": ["추천", "어디", "가볼", "명소"],
        "축제": ["축제", "행사", "일정", "언제"],
        "음식점": ["음식", "맛집", "식당", "카페"],
        "커뮤니티": ["게시글", "글", "포스트", "댓글"]
    }
    
    matched_categories = []
    for category, keys in keywords.items():
        if any(key in message for key in keys):
            matched_categories.append(category)
    
    return matched_categories if matched_categories else ["일반"]

# 예시: "축제에서 음식 추천"
# 반환: ["축제", "음식점"]

def get_chatbot_response(message: str, categories: list) -> str:
    # 카테고리를 문자열로 변환
    category_str = ", ".join(categories)

    # 프롬프트 구성
    prompt = f"""
당신은 지역 관광 정보 챗봇입니다.

질문 카테고리: {category_str}
사용자 질문: {message}

유용하고 친절한 정보를 한국어로 제공해주세요.
2-3줄 정도의 간결한 답변으로 부탁합니다.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 지역 관광 정보를 제공하는 친절한 챗봇입니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content

        if not content:
            return "챗봇 응답 내용이 비어 있습니다."

        return content

    except Exception as e:
        print(f"OpenAI API 오류: {e}")
        return "현재 챗봇이 응답할 수 없습니다. 잠시 후 다시 시도해 주세요."