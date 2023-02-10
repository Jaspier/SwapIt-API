import re
import json
import datetime
from models import UserObject


def FormatFireBaseDoc(doc: object):
    for key, value in doc.items():
        if key == "timestamp":
            doc[key] = value.isoformat()
    return doc


def FormatUserObject(userSwiped: UserObject):
    user_swiped_dict = userSwiped.dict()
    # user_swiped_dict["coords"] = userSwiped.coords.copy()
    if (user_swiped_dict["timestamp"] != None):
        timestamp_dict = user_swiped_dict["timestamp"]
        try:
            timestamp = datetime.datetime.fromtimestamp(
                timestamp_dict["seconds"])
            user_swiped_dict["timestamp"] = timestamp
        except Exception:
            return user_swiped_dict
    return user_swiped_dict


def GenerateId(id1: str, id2: str):
    if id1 > id2:
        return id1 + id2
    else:
        return id2 + id1


def GetMatchedUserInfo(users, user_logged_in):
    new_users = {**users}
    del new_users[user_logged_in]

    (id, user) = list(new_users.items())[0]

    return {'id': id, **user}
