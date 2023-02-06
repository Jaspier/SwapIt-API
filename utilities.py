import re
import json
import datetime
from models import UserSwiped


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


def FormatUserObject(userSwiped: UserSwiped):
    user_swiped_dict = userSwiped.dict()
    user_swiped_dict["coords"] = userSwiped.coords.copy()
    timestamp_dict = user_swiped_dict["timestamp"]
    timestamp = datetime.datetime.fromtimestamp(timestamp_dict["seconds"])
    user_swiped_dict["timestamp"] = timestamp
    return user_swiped_dict
