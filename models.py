from pydantic import BaseModel


class Timestamp(BaseModel):
    nanoseconds: int
    seconds: int


class Coords(dict):
    longitude: float
    latitude: float

    def __init__(self, longitude: float, latitude: float):
        self.longitude = longitude
        self.latitude = latitude


class Location(BaseModel):
    location: str
    coords: Coords


class UserSwiped(BaseModel):
    active: bool
    coords: Coords
    displayName: str
    id: str
    itemName: str
    location: str
    photoUrls: str
    radius: int
    timestamp: Timestamp
