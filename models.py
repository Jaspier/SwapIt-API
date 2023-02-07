import typing
from pydantic import BaseModel


class Coords(dict):
    longitude: float
    latitude: float

    def __init__(self, longitude: float, latitude: float):
        self.longitude = longitude
        self.latitude = latitude


class Location(BaseModel):
    location: str
    coords: Coords


class UserObject(BaseModel):
    active: bool
    coords: Coords
    displayName: str
    id: str
    itemName: str
    location: str
    photoUrls: str
    radius: int
    timestamp: typing.Any
