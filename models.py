from pydantic import BaseModel


class Coords(BaseModel):
    longitude: float
    latitude: float


class Location(BaseModel):
    location: str
    coords: Coords
