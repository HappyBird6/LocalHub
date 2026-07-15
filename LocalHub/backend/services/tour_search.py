# services/tour_search.py

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from services.distance import calculate_distance_km


# 현재 파일 위치에 따라 조정하세요.
# 예: services/tour_search.py에서 ../data가 프로젝트의 data인 경우
DATA_ROOT = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
)

print(DATA_ROOT)
ALLOWED_CATEGORIES = {
    "관광지",
    "레포츠",
    "문화시설",
    "음식점",
    "쇼핑",
    "축제공연행사"
}


def normalize_text(value: str) -> str:
    return re.sub(
        r"[^0-9a-z가-힣]",
        "",
        value.lower().strip(),
    )


# def extract_items(
#     json_data: Any,
# ) -> list[dict[str, Any]]:
#     """
#     JSON이 단순 배열인 경우와
#     TourAPI 전체 응답 구조인 경우를 모두 처리합니다.
#     """

#     if isinstance(json_data, list):
#         return [
#             item
#             for item in json_data
#             if isinstance(item, dict)
#         ]

#     if not isinstance(json_data, dict):
#         return []

#     # TourAPI 전체 응답 구조
#     try:
#         items = (
#             json_data["response"]
#             ["body"]
#             ["items"]
#             ["item"]
#         )
#     except (KeyError, TypeError):
#         # 이미 items 또는 item만 저장한 구조 대응
#         items = (
#             json_data.get("items")
#             or json_data.get("item")
#             or []
#         )

#     if isinstance(items, dict):
#         return [items]

#     if isinstance(items, list):
#         return [
#             item
#             for item in items
#             if isinstance(item, dict)
#         ]

#     return []


# def get_category_from_filename(
#     file_path: Path,
# ) -> str | None:
#     """
#     파일명에서 카테고리를 확인합니다.

#     예:
#     서울_관광지.json → 관광지
#     부산_레포츠.json → 레포츠
#     """

#     stem = file_path.stem

#     for category in CATEGORY_NAMES:
#         if category in stem:
#             return category

#     return None


@lru_cache(maxsize=1)
def load_all_tour_data() -> list[dict[str, Any]]:
    """
    data 하위의 모든 TourAPI JSON을 한 번만 불러옵니다.

    JSON 구조:
    {
        "region": "부산",
        "contentType": "관광지",
        "contentTypeId": 12,
        "total": 351,
        "items": [...]
    }
    """

    all_places: list[dict[str, Any]] = []

    for file_path in DATA_ROOT.rglob("*.json"):
        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                json_data = json.load(file)

        except (OSError, json.JSONDecodeError) as error:
            print(
                f"TourAPI JSON 읽기 실패: "
                f"{file_path} / {error}"
            )
            continue

        if not isinstance(json_data, dict):
            print(
                f"지원하지 않는 JSON 구조: {file_path}"
            )
            continue

        region = json_data.get("region")
        category = json_data.get("contentType")
        content_type_id = json_data.get("contentTypeId")
        items = json_data.get("items", [])

        if category not in ALLOWED_CATEGORIES:
            continue

        if not isinstance(items, list):
            print(
                f"items가 배열이 아닙니다: {file_path}"
            )
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            try:
                longitude = float(item["mapx"])
                latitude = float(item["mapy"])
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            title = str(
                item.get("title", "")
            ).strip()

            if not title:
                continue

            all_places.append(
                {
                    **item,
                    "_region": region,
                    "_category": category,
                    "_content_type_id": content_type_id,
                    "_latitude": latitude,
                    "_longitude": longitude,
                }
            )

    print(
        f"TourAPI 장소 데이터 "
        f"{len(all_places)}개 로드 완료"
    )

    return all_places

def search_nearby_tour_places(
    latitude: float,
    longitude: float,
    categories: list[str] | None = None,
    radius_km: float = 1.0,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """
    마커 좌표 기준 반경 내 TourAPI 장소를 검색합니다.
    """

    category_set = set(categories or [])
    results: list[dict[str, Any]] = []

    for place in load_all_tour_data():
        category = place.get("_category")

        if (
            category_set
            and category not in category_set
        ):
            continue

        try:
            # TourAPI 기준
            # mapx = 경도
            # mapy = 위도
            place_longitude = float(
                place["mapx"]
            )
            place_latitude = float(
                place["mapy"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            place_latitude,
            place_longitude,
        )

        if distance_km > radius_km:
            continue

        results.append(
            {
                "contentid": place.get(
                    "contentid"
                ),
                "title": place.get(
                    "title",
                    "이름 없음",
                ),
                "category": category,
                "region": place.get("_region"),
                "address": place.get("addr1"),
                "latitude": place_latitude,
                "longitude": place_longitude,
                "distance_km": round(
                    distance_km,
                    2,
                ),
                "image": (
                    place.get("firstimage")
                    or place.get("firstimage2")
                ),
            }
        )

    results.sort(
        key=lambda item: item["distance_km"]
    )

    return results[:limit]


def search_nearby_tour_places(
    latitude: float,
    longitude: float,
    categories: list[str] | None = None,
    radius_km: float = 1.0,
    limit: int = 30,
) -> list[dict[str, Any]]:
    category_set = set(categories or [])
    results: list[dict[str, Any]] = []

    for place in load_all_tour_data():
        category = place["_category"]

        if (
            category_set
            and category not in category_set
        ):
            continue

        distance_km = calculate_distance_km(
            latitude,
            longitude,
            place["_latitude"],
            place["_longitude"],
        )

        if distance_km > radius_km:
            continue

        results.append(
            {
                "contentid": place.get("contentid"),
                "title": place["title"],
                "category": category,
                "region": place["_region"],
                "address": place.get("addr1"),
                "addressDetail": place.get("addr2"),
                "lat": place["_latitude"],
                "lng": place["_longitude"],
                "distanceKm": round(
                    distance_km,
                    2,
                ),
                "firstImage": (
                    place.get("firstimage")
                    or place.get("firstimage2")
                    or None
                ),
                "tel": place.get("tel") or None,
            }
        )

    results.sort(
        key=lambda item: item["distanceKm"]
    )

    return results[:limit]

# services/tour_search.py

def search_tour_places_by_title(
    keyword: str,
    categories: list[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    normalized_keyword = normalize_text(keyword)

    if not normalized_keyword:
        return []

    category_set = set(categories or [])

    exact_matches = []
    prefix_matches = []
    partial_matches = []

    for place in load_all_tour_data():
        if (
            category_set
            and place["_category"]
            not in category_set
        ):
            continue

        title = place["title"]
        normalized_title = normalize_text(title)

        if normalized_title == normalized_keyword:
            target = exact_matches

        elif normalized_title.startswith(
            normalized_keyword
        ):
            target = prefix_matches

        elif normalized_keyword in normalized_title:
            target = partial_matches

        else:
            continue

        target.append(
            {
                "contentid": place.get("contentid"),
                "title": title,
                "category": place["_category"],
                "region": place["_region"],
                "address": place.get("addr1"),
                "addressDetail": place.get("addr2"),
                "lat": place["_latitude"],
                "lng": place["_longitude"],
                "firstImage": (
                    place.get("firstimage")
                    or place.get("firstimage2")
                    or None
                ),
            }
        )

    return (
        exact_matches
        + prefix_matches
        + partial_matches
    )[:limit]