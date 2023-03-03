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
    isNewUser: typing.Optional[bool] = False


class SwipedUserObject(BaseModel):
    active: bool
    coords: Coords
    displayName: str
    id: str
    itemName: str
    location: str
    photoUrls: str
    radius: int
    timestamp: typing.Any
    isNewUser: typing.Optional[bool] = False
    profilePic: typing.Optional[str] = ""


class UserPrefsObject(BaseModel):
    displayName: str
    radius: int


class MessageObject(BaseModel):
    matchId: str
    message: str


class DeviceTokenObject(BaseModel):
    token: str


class MatchObject(BaseModel):
    id: str
    timestamp: typing.Optional[typing.Any]
    users: typing.Dict[str, SwipedUserObject]
    usersMatched: typing.List[str]
    deactivated: typing.Optional[bool] = False


class NotificationObject(BaseModel):
    type: str
    matchDetails: MatchObject
    message: typing.Optional[str] = ""
