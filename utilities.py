import datetime
from models import UserObject, SwipedUserObject


def format_firebase_doc(doc: object):
    for key, value in doc.items():
        if key == "timestamp" or key == "lastOnline":
            doc[key] = value.isoformat()
    return doc


def format_user_object(userSwiped: UserObject):
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


def generate_id(id1: str, id2: str):
    if id1 > id2:
        return id1 + id2
    else:
        return id2 + id1


def get_matched_user_info(users, user_logged_in):
    new_users = {}
    for key, value in users.items():
        if isinstance(value, SwipedUserObject):
            value = value.__dict__
        new_users[key] = value

    del new_users[user_logged_in]

    (id, user) = list(new_users.items())[0]

    return {'id': id, **user}


def delete_s3_folder(bucket, folder_path):
    try:
        objects = bucket.objects.filter(Prefix=folder_path)
        for obj in objects:
            obj.delete()
    except Exception as e:
        raise e
