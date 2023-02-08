import re
import json
import datetime
from models import UserObject


def FormatFireBaseError(res: str):
    stri = str(res).split("\n", 1)[1]
    formatted = re.sub(r'^.*?"error"', '{\n"error"', stri)
    res = json.loads(formatted)
    return res["error"]


def FormatFireBaseDoc(doc: object):
    for key, value in doc.items():
        if key == "timestamp":
            doc[key] = value.isoformat()
    return doc


def FormatUserObject(userSwiped: UserObject):
    user_swiped_dict = userSwiped.dict()
    user_swiped_dict["coords"] = userSwiped.coords.copy()
    if (user_swiped_dict["timestamp"] != None):
        timestamp_dict = user_swiped_dict["timestamp"]
        timestamp = datetime.datetime.fromtimestamp(timestamp_dict["seconds"])
        user_swiped_dict["timestamp"] = timestamp
    return user_swiped_dict


def GenerateId(id1: str, id2: str):
    if id1 > id2:
        return id1 + id2
    else:
        return id2 + id1
