import typing
from pydantic import BaseModel
from typing import Union


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


class MessageObject(BaseModel):
    matchId: str
    message: str


class MatchNotificationObject(BaseModel):
    loggedInProfile: UserObject
    userSwiped: UserObject


class MessageNotificationObject(BaseModel):
    message: str
    sender: SwipedUserObject
    receiverId: str


class NotificationObject(BaseModel):
    type: str
    matchObj: typing.Optional[MatchNotificationObject] = None
    messageObj: typing.Optional[MessageNotificationObject] = None
