# services/post_search.py

from typing import Any

from sqlalchemy.orm import Session

from models import Post
from services.distance import calculate_distance_km


from typing import Any

from sqlalchemy.orm import Session

from models import Post
from services.distance import calculate_distance_km


def search_nearby_posts(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 1.0,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    선택한 마커 주변의 모집 중인 게시글을 검색합니다.

    category == 1: 모집글
    status == 1: 모집 중
    """

    posts = (
        db.query(Post)
        .filter(
            Post.category == 1,
            Post.status == 1,
            Post.lat.is_not(None),
            Post.lng.is_not(None),
        )
        .all()
    )

    results: list[dict[str, Any]] = []

    for post in posts:
        distance_km = calculate_distance_km(
            latitude,
            longitude,
            float(post.lat),
            float(post.lng),
        )

        if distance_km > radius_km:
            continue

        results.append(
            {
                "id": post.id,
                "category": post.category,
                "title": post.title,
                "content": post.content,
                "nickname": (
                    post.nickname
                    or "김익명"
                ),
                "lat": float(post.lat),
                "lng": float(post.lng),
                "locationName": post.locationName,
                "created_at": post.created_at,
                "commentsCount": (
                    post.commentsCount or 0
                ),
                "status": post.status,
                "distanceKm": round(
                    distance_km,
                    2,
                ),
            }
        )

    results.sort(
        key=lambda item: (
            item["distanceKm"],
            -item["created_at"].timestamp(),
        )
    )

    return results[:limit]