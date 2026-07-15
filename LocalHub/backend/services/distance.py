# services/distance.py

from math import atan2, cos, radians, sin, sqrt


def calculate_distance_km(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """
    위도·경도 두 지점의 직선거리를 km 단위로 계산합니다.
    """

    earth_radius_km = 6371.0

    lat1 = radians(latitude1)
    lng1 = radians(longitude1)
    lat2 = radians(latitude2)
    lng2 = radians(longitude2)

    delta_latitude = lat2 - lat1
    delta_longitude = lng2 - lng1

    value = (
        sin(delta_latitude / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_longitude / 2) ** 2
    )

    central_angle = 2 * atan2(
        sqrt(value),
        sqrt(1 - value),
    )

    return earth_radius_km * central_angle