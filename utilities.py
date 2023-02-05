import re
import json


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
