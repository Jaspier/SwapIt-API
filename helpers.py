from typing import List
from firebase_admin import auth, firestore
from models import DeleteMatchesObject, NotificationObject, UserObject, UserPrefsObject
from utilities import DeleteS3Folder, FormatFireBaseDoc, FormatUserObject, GenerateId, GetMatchedUserInfo


def get_user_preferences(db, uid: str):
    preferences = {}

    # Retrieve user's coordinates and search radius
    data = db.collection(u'users').document(uid).get().to_dict()
    preferences["coords"] = data['coords']
    preferences["radius"] = data['radius']

    # Retrieve user's passes and swipes
    passes = [doc.id for doc in db.collection(
        u'users').document(uid).collection(u'passes').stream()]
    swipes = [doc.id for doc in db.collection(
        u'users').document(uid).collection(u'swipes').stream()]
    preferences["passes"] = passes
    preferences["swipes"] = swipes

    return preferences


def get_logged_in_user(db, uid: str):
    logged_in_user_dict = None
    user_ref = db.collection(u'users').document(uid)
    user = user_ref.get()
    logged_in_user_dict = FormatFireBaseDoc(user.to_dict())

    return logged_in_user_dict


def create_match(db, uid: str, user_swiped, logged_in_user):
    # Add swipe
    db.collection(u'users').document(uid).collection(
        u'swipes').document(user_swiped["id"]).set(user_swiped)

    # Create MATCH
    db.collection(u'matches').document(GenerateId(uid, user_swiped["id"])).set(
        {
            u'users': {
                uid: logged_in_user,
                user_swiped["id"]: user_swiped
            },
            u'usersMatched': [uid, user_swiped["id"]],
            u'timestamp': firestore.SERVER_TIMESTAMP
        }
    )


def update_or_set_user_prefs(db, uid: str, prefs: UserPrefsObject):
    user_ref = db.collection(u'users').document(uid)
    user = user_ref.get()
    if user.exists:
        prefs_ref = db.collection(u'users').document(uid)
        prefs_ref.update({
            u'displayName': prefs.displayName,
            u'radius': prefs.radius,
            u'timestamp': firestore.SERVER_TIMESTAMP
        })
    else:
        db.collection(u'users').document(uid).set({
            u'id': uid,
            u'displayName': prefs.displayName,
            u'radius': prefs.radius,
            u'timestamp': firestore.SERVER_TIMESTAMP
        })


def UpdateProfilePicInChatMessages(db, uid: str, key: str):
    # Update profile pic key in messages
    query = db.collection("matches").where(
        "usersMatched", "array_contains", uid)
    docs = query.stream()

    matches = []
    for doc in docs:
        matches.append(doc.id)

    # Iterate through the matches and get the relevant messages
    for match_id in matches:
        # Query the messages subcollection for messages with the provided userId
        query = db.collection("matches").document(
            match_id).collection("messages").where("userId", "==", uid)
        docs = query.stream()

        # Update the photoUrl field for each relevant message
        for doc in docs:
            message_ref = db.collection("matches").document(
                match_id).collection("messages").document(doc.id)
            message_ref.update({"photoUrl": key})


def create_or_update_profile(db, profile: UserObject, uid: str):
    res = {
        u'message': "Successfully updated profile",
        u'isNewUser': False,
    }
    profile_dict = FormatUserObject(profile)
    isNewUser = profile_dict['isNewUser']
    profile_dict["timestamp"] = firestore.SERVER_TIMESTAMP
    del profile_dict["isNewUser"]

    if isNewUser:
        db.collection(u'users').document(uid).set(profile_dict)
        res['message'] = "Successfully created profile"
        res['isNewUser'] = True
    else:
        doc_ref = db.collection(u'users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            data = FormatFireBaseDoc(doc.to_dict())
            radius = data["radius"]
            profile_dict["radius"] = radius
            coords = data["coords"]
            profile_dict["coords"] = coords
            db.collection(u'users').document(uid).update(profile_dict)

    return res


def delete_match(db, s3_bucket, usersMatched: List[str]):
    # Delete Swipe for user 1
    db.collection(u'users').document(usersMatched[0]).collection(
        "swipes").document(usersMatched[1]).delete()
    # Delete Swipe for user 2
    db.collection(u'users').document(usersMatched[1]).collection(
        "swipes").document(usersMatched[0]).delete()

    match_id = GenerateId(usersMatched[0], usersMatched[1])

    # Delete Chat Messages
    subcollection_ref = db.collection("matches").document(
        match_id).collection("messages")
    docs = subcollection_ref.get()
    for doc in docs:
        doc.reference.delete()

    # Delete Match Document
    db.collection(u'matches').document(match_id).delete()

    # Delete photos sent in chat messages if any
    folder_path = f'public/chats/{match_id}'
    DeleteS3Folder(s3_bucket, folder_path)


def get_all_users_to_notify(uid: str, all_users_matched: List[str], payload: DeleteMatchesObject):
    users_to_notify = []
    user = auth.get_user(uid)
    for userId in all_users_matched:
        if userId != uid and userId != payload.matchedUserId:
            notification_object = {
                "sender": user.display_name,
                "receiverId": userId
            }
            users_to_notify.append(notification_object)

    notifications_object = {
        "type": "delete",
        "notifications": users_to_notify
    }

    return notifications_object


def check_match_exists(db, uid: str, usersMatched: List[str]):
    matchedUser = None
    match_dict = None

    match_ref = db.collection(u'matches').document(
        GenerateId(usersMatched[0], usersMatched[1]))
    match = match_ref.get()
    if match.exists:
        match_dict = match.to_dict()
        matchedUser = GetMatchedUserInfo(match_dict["users"], uid)

    return matchedUser, match_dict, match_ref


def toggle_swap_confirmation(match_ref, matched_user, match_dict, confirm: bool, uid: str):
    currentUser = match_dict["users"][uid]
    updatedCurrentUser = {
        **currentUser,
        u'isConfirmed': True if confirm is True else False,
        u'timestamp': firestore.SERVER_TIMESTAMP
    }
    updatedMatchedUsers = {
        uid: updatedCurrentUser,
        matched_user["id"]: matched_user
    }

    match_ref.update({
        u'users': updatedMatchedUsers,
        u'timestamp': firestore.SERVER_TIMESTAMP
    })


def get_notification_type(notification: NotificationObject, uid: str):
    receiver_id = GetMatchedUserInfo(
        notification.matchDetails.users, uid)["id"]
    sender_name = notification.matchDetails.users[uid].displayName
    item_name = notification.matchDetails.users[uid].itemName
    if notification.type == "match":
        title = "New Swap Partner!"
        body = f"{sender_name} wants to swap with you!"
        data = {
            "type": notification.type,
            "match": {
                "loggedInProfile": notification.matchDetails.users[uid].dict(),
                "userSwiped": notification.matchDetails.users[receiver_id].dict()
            },
            "matchDetails": notification.matchDetails.dict()
        }
    elif notification.type == "message":
        title = f"{sender_name} ({item_name})"
        body = notification.message
        data = {
            "type": notification.type,
            "message": {
                "message": notification.message,
                "sender": notification.matchDetails.users[uid].dict()
            },
            "matchDetails": notification.matchDetails.dict()
        }

    return title, body, data
