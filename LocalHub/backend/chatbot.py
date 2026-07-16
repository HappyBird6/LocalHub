from openai import OpenAI
import os
from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel, Field
import json
from typing import Any

# 환경변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 의도
ALLOWED_INTENTS = {
    "search_nearby_posts",
    "search_nearby_places",
    "search_place_by_title",
    "general_chat",
}

ALLOWED_CATEGORIES = {
    "관광지",
    "레포츠",
    "문화시설",
    "음식점",
    "쇼핑",
}
def analyze_query(message: str) -> dict[str, Any]:
    """
    사용자 문장을 분석하여 intent와 검색 조건을 반환합니다.

    반환 예:
    {
        "intent": "search_nearby_places",
        "keyword": None,
        "categories": ["관광지", "레포츠"],
        "radius_km": 1.0
    }
    """

    system_prompt = """
당신은 지도 기반 익명 동행 커뮤니티 '같이갈사람'의
사용자 요청 분석기입니다.

사용자 요청을 반드시 다음 intent 중 하나로 분류하세요.

1. search_nearby_posts
- 현재 지도 마커 주변의 모집글, 동행글, 게시글을 찾는 요청
- 예: "이 주변 모집글 찾아줘"
- 예: "여기 근처 동행글 있어?"

2. search_nearby_places
- 현재 지도 마커 주변의 관광지, 레포츠, 문화시설,
  음식점, 쇼핑 장소를 찾는 요청
- 예: "이 주변 관광지 보여줘"
- 예: "여기 근처 쇼핑이랑 음식점 찾아줘"

3. search_place_by_title
- 특정 장소 이름을 직접 검색하는 요청
- 예: "경복궁 찾아줘"
- 예: "해운대 해수욕장 위치 보여줘"
- keyword에는 장소 이름만 넣으세요.

4. general_chat
- 위 검색 요청 이외의 질문
- 예: "처음 만나는 동행자와 만날 때 주의할 점 알려줘"

categories에는 다음 값만 넣으세요.
- 관광지
- 레포츠
- 문화시설
- 음식점
- 쇼핑

규칙:
- 사용자가 반경을 말하지 않으면 radius_km는 1.0입니다.
- keyword가 필요하지 않으면 null입니다.
- categories가 필요하지 않으면 빈 배열입니다.
- 반드시 JSON 객체만 반환하세요.
- 설명이나 마크다운은 작성하지 마세요.

반환 형식:
{
  "intent": "search_nearby_posts",
  "keyword": null,
  "categories": [],
  "radius_km": 1.0
}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            response_format={
                "type": "json_object"
            },
        )

        content = response.choices[0].message.content

        if not content:
            return default_analysis()

        analysis = json.loads(content)

        return validate_analysis(analysis)

    except (json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"AI 분석 JSON 오류: {error}")
        return default_analysis()

    except Exception as error:
        print(f"OpenAI API 오류: {error}")
        return default_analysis()


def default_analysis() -> dict[str, Any]:
    """
    AI 분석 실패 시 일반 대화로 처리합니다.
    """

    return {
        "intent": "general_chat",
        "keyword": None,
        "categories": [],
        "radius_km": 1.0,
    }


def validate_analysis(analysis: dict[str, Any],) -> dict[str, Any]:
    """
    AI가 반환한 JSON 값을 서버에서 다시 검증합니다.
    """

    intent = analysis.get("intent", "general_chat")

    if intent not in ALLOWED_INTENTS:
        intent = "general_chat"

    keyword = analysis.get("keyword")

    if keyword is not None:
        keyword = str(keyword).strip() or None

    raw_categories = analysis.get("categories", [])

    if not isinstance(raw_categories, list):
        raw_categories = []

    categories = [
        category
        for category in raw_categories
        if category in ALLOWED_CATEGORIES
    ]

    try:
        radius_km = float(
            analysis.get("radius_km", 1.0)
        )
    except (TypeError, ValueError):
        radius_km = 1.0

    # 임의의 너무 넓은 검색 방지
    radius_km = max(0.1, min(radius_km, 20.0))

    return {
        "intent": intent,
        "keyword": keyword,
        "categories": categories,
        "radius_km": radius_km,
    }


def get_general_chat_response(
    message: str,
) -> str:
    """
    general_chat으로 분류된 질문에만 사용합니다.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 지도 기반 익명 동행 커뮤니티 "
                        "'같이갈사람'의 친절한 챗봇입니다. "
                        "여행, 관광, 동행 및 사이트 이용 질문에 "
                        "간결한 한국어로 답변하세요. "
                        "개인정보 공유를 유도하지 말고, "
                        "처음 만나는 사람과는 공개된 장소에서 "
                        "만나도록 안내하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            return "챗봇 응답 내용이 비어 있습니다."

        return content.strip()

    except Exception as error:
        print(f"OpenAI API 오류: {error}")
        return (
            "현재 챗봇이 응답할 수 없습니다. "
            "잠시 후 다시 시도해 주세요."
        )

    
