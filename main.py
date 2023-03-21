import os
from typing import List
import uvicorn
import firebase_admin
import pyrebase
import json
from os import path
import logging

from firebase_admin import credentials, auth, firestore
from fastapi import FastAPI, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from exponent_server_sdk import PushClient
from exponent_server_sdk import PushMessage

from utilities import FormatFireBaseDoc, FormatUserObject, GenerateId, GetMatchedUserInfo, DeleteS3Folder
from helpers import UpdateProfilePicInChatMessages
from models import Location, UserObject, UserPrefsObject, MessageObject, SwipedUserObject, NotificationObject, ManyNotificationsObject, DeleteMatchesObject
import boto3

s3 = boto3.resource('s3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get(
                        'AWS_SECRET_ACCESS_KEY')
                    )
bucket_name = os.environ.get('AWS_BUCKET_NAME')
s3_bucket = s3.Bucket(bucket_name)

LOGGING_CONFIG_FILE = path.join(path.dirname(
    path.abspath(__file__)), 'logging.conf')
logging.config.fileConfig(LOGGING_CONFIG_FILE)
logger = logging.getLogger('SwapIt')

cred_json = os.environ.get('FIREBASE_ADMIN_SDK_CREDENTIALS')
cred = credentials.Certificate(json.loads(cred_json))
firebase = firebase_admin.initialize_app(cred)
db = firestore.client()
config_json = os.environ.get('FIREBASE_PYREBASE_CONFIG')
pb = pyrebase.initialize_app(json.loads(config_json))
app = FastAPI()
allow_all = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_all,
    allow_credentials=True,
    allow_methods=allow_all,
    allow_headers=allow_all
)


async def verify_auth(authorization: str = Header(None)):
    id_token = authorization.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid']
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unauthorized: " + str(e))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.debug(response)
    logger.debug(response.status_code)
    print(f"INCOMING REQUEST - {request.url} {response.status_code}")
    return response


@app.get("/checkUserExists")
async def checkUserExists(uid: str = Depends(verify_auth)):
    try:
        user_ref = db.collection(u'users').document(uid)
        user = user_ref.get()
        if user.exists:
            return JSONResponse(content="User exists", status_code=200)
        else:
            return JSONResponse(content="User does not exist", status_code=404)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch user: " + str(e))


@app.get("/myprofile")
async def myProfile(uid: str = Depends(verify_auth)):
    try:
        doc_ref = db.collection(u'users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            data = FormatFireBaseDoc(doc.to_dict())
            return JSONResponse(content=data, status_code=200)
        else:
            raise HTTPException(
                status_code=400, detail="Failed to fetch profile: Profile does not exist")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch profile: " + str(e))


@app.get("/getSearchPreferences")
async def getSearchPref(uid: str = Depends(verify_auth)):
    preferences = {}
    try:
        doc_ref = db.collection(u'users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            preferences["coords"] = data['coords']
            preferences["radius"] = data['radius']

        passes = [doc.id for doc in db.collection(
            u'users').document(uid).collection(u'passes').stream()]
        swipes = [doc.id for doc in db.collection(
            u'users').document(uid).collection(u'swipes').stream()]
        preferences["passes"] = passes
        preferences["swipes"] = swipes

        return JSONResponse(content=preferences, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch search preferences: " + str(e))


@app.post("/updateLocation")
async def updateLocation(location: Location, uid: str = Depends(verify_auth)):
    try:
        location_ref = db.collection(u'users').document(uid)
        updated_data = {
            **location.dict(),
            u'timestamp': firestore.SERVER_TIMESTAMP
        }
        location_ref.update(updated_data)
        return JSONResponse(content="Successfully updated location", status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to update location: " + str(e))


@app.post("/swipeLeft")
async def swipeLeft(userSwiped: UserObject, uid: str = Depends(verify_auth)):
    try:
        user_passed_dict = FormatUserObject(userSwiped)
        db.collection(u'users').document(uid).collection(
            u'passes').document(userSwiped.id).set(user_passed_dict)
        return JSONResponse(content="Successfully added Pass", status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Unable to pass user: " + str(e))


@app.post("/swipeRight")
async def swipeRight(userSwiped: SwipedUserObject, uid: str = Depends(verify_auth)):
    try:
        logged_in_user_dict = None
        loggedInUser_ref = db.collection(u'users').document(uid)
        doc = loggedInUser_ref.get()
        if doc.exists:
            logged_in_user_dict = FormatFireBaseDoc(doc.to_dict())
        else:
            return JSONResponse(content="User does not exist", status_code=404)

        # Check if user swiped on 'you' (TODO: Migrate to cloud function)
        swipe_ref = db.collection(u'users').document(
            userSwiped.id).collection(u'swipes').document(uid)
        doc = swipe_ref.get()
        user_swiped_dict = FormatUserObject(userSwiped)
        if doc.exists:
            db.collection(u'users').document(uid).collection(
                u'swipes').document(userSwiped.id).set(user_swiped_dict)

            # Create MATCH
            logged_in_user = auth.get_user(uid)
            user_swiped = auth.get_user(userSwiped.id)
            logged_in_user_dict["profilePic"] = logged_in_user.photo_url
            user_swiped_dict["profilePic"] = user_swiped.photo_url
            db.collection(u'matches').document(GenerateId(uid, userSwiped.id)).set(
                {
                    u'users': {
                        uid: logged_in_user_dict,
                        userSwiped.id: user_swiped_dict
                    },
                    u'usersMatched': [uid, userSwiped.id],
                    u'timestamp': firestore.SERVER_TIMESTAMP
                }
            )
            return JSONResponse(content=logged_in_user_dict, status_code=201)
        else:
            # // User has swiped as first interaction with another user or no match :(
            db.collection(u'users').document(uid).collection(
                u'swipes').document(userSwiped.id).set(user_swiped_dict)
            return JSONResponse(content="Successfully added Swipe", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Unable to swipe user: " + str(e))


@app.get("/getSearchRadius")
async def getSearchRadius(uid: str = Depends(verify_auth)):
    try:
        doc_ref = db.collection(u'users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            data = FormatFireBaseDoc(doc.to_dict())
            radius = data["radius"]
            return JSONResponse(content=radius, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch search radius: " + str(e))


@app.post("/login", include_in_schema=False)
async def login(request: Request):
    req_json = await request.json()
    email = req_json['email']
    password = req_json['password']
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        return JSONResponse(content={'token': jwt}, status_code=200)
    except:
        return HTTPException(detail={'message': 'There was an error logging in'}, status_code=400)


@app.post("/updateUserPreferences")
async def updateUserPreferences(prefs: UserPrefsObject, uid: str = Depends(verify_auth)):
    try:
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

        if (prefs.photoKey != ""):
            UpdateProfilePicInChatMessages(db, uid, prefs.photoKey)

        return JSONResponse(content="Successfully updated user preferences", status_code=204)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to update user preferences: " + str(e))


@app.post("/createProfile")
async def createProfile(profile: UserObject, uid: str = Depends(verify_auth)):
    try:
        res = {
            u'message': "Successfully created/updated profile",
            u'isNewUser': False,
        }
        profile_dict = FormatUserObject(profile)
        profile_dict["timestamp"] = firestore.SERVER_TIMESTAMP
        if (profile_dict["isNewUser"]):
            del profile_dict["isNewUser"]
            db.collection(u'users').document(uid).set(profile_dict)
            res["isNewUser"] = True
            return JSONResponse(content=res, status_code=204)
        else:
            doc_ref = db.collection(u'users').document(uid)
            doc = doc_ref.get()
            if doc.exists:
                data = FormatFireBaseDoc(doc.to_dict())
                radius = data["radius"]
                profile_dict["radius"] = radius
                coords = data["coords"]
                profile_dict["coords"] = coords

            del profile_dict["isNewUser"]
            db.collection(u'users').document(uid).update(profile_dict)
            return JSONResponse(content=res, status_code=204)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to create/update profile: " + str(e))


@app.post("/deleteMatch")
async def deleteMatch(usersMatched: List[str], uid: str = Depends(verify_auth)):
    try:
        # Delete Swipe for user 1
        db.collection(u'users').document(usersMatched[0]).collection(
            "swipes").document(usersMatched[1]).delete()
        # Delete Swipe for user 2
        db.collection(u'users').document(usersMatched[1]).collection(
            "swipes").document(usersMatched[0]).delete()

        match_id = GenerateId(usersMatched[0], usersMatched[1])

        # Delete Messages
        subcollection_ref = db.collection("matches").document(
            match_id).collection("messages")
        docs = subcollection_ref.get()
        for doc in docs:
            doc.reference.delete()

        # Delete Match Document
        db.collection(u'matches').document(match_id).delete()

        # Delete images from s3 if any
        folder_path = f'public/chats/{match_id}'
        DeleteS3Folder(s3_bucket, folder_path)

        return JSONResponse(content="Successfully deleted match", status_code=204)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to delete match: " + str(e))


@app.post("/deleteMatches")
async def deleteMatches(payload: DeleteMatchesObject, uid: str = Depends(verify_auth)):
    try:
        collection_ref = db.collection(u'matches')
        query = collection_ref.where(
            u'users.' + uid + '.itemName', u'==', payload.itemName)
        docs = [doc.to_dict() for doc in query.stream()]

        all_users_matched = []
        for doc in docs:
            users_matched = doc["usersMatched"]
            match_id = GenerateId(users_matched[0], users_matched[1])
            # Delete swipes
            db.collection(u'users').document(users_matched[0]).collection(
                "swipes").document(users_matched[1]).delete()
            db.collection(u'users').document(users_matched[1]).collection(
                "swipes").document(users_matched[0]).delete()

            # Delete messages
            subcollection_ref = db.collection("matches").document(
                match_id).collection("messages")
            docs = subcollection_ref.get()
            for doc in docs:
                doc.reference.delete()

            all_users_matched.extend(users_matched)

            # Delete match
            db.collection(u'matches').document(match_id).delete()

            # Delete images from S3
            DeleteS3Folder(s3_bucket, f'public/chats/{match_id}')
            DeleteS3Folder(s3_bucket, f'public/profiles/{uid}/items')

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

        return JSONResponse(content=notifications_object, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to delete matches: " + str(e)
        )


@app.post("/sendMessage")
async def sendMessage(message: MessageObject, uid: str = Depends(verify_auth)):
    try:
        user = auth.get_user(uid)
        db.collection(u'matches').document(message.matchId).collection(u'messages').add({
            u'userId': uid,
            u'displayName': user.email if user.display_name is None else user.display_name,
            u'photoUrl': user.photo_url,
            u'message': message.message,
            u'type': message.type,
            u'timestamp': firestore.SERVER_TIMESTAMP
        })
        return JSONResponse(content="Successfully sent message", status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to send message: " + str(e))


@app.post("/confirmSwap")
async def confirmSwap(matchedUsers: List[str], uid: str = Depends(verify_auth)):
    try:
        matchedUser = None
        match_ref = db.collection(u'matches').document(
            GenerateId(matchedUsers[0], matchedUsers[1]))
        match = match_ref.get()
        match_dict = match.to_dict()
        if match.exists:
            matchedUser = GetMatchedUserInfo(match_dict["users"], uid)
        else:
            return JSONResponse(content="Match does not exist!", status_code=404)
        currentUser = match_dict["users"][uid]
        updatedCurrentUser = {
            **currentUser,
            u'isConfirmed': True,
            u'timestamp': firestore.SERVER_TIMESTAMP
        }
        updatedMatchedUsers = {
            uid: updatedCurrentUser,
            matchedUser["id"]: matchedUser
        }

        match_ref.update({
            u'users': updatedMatchedUsers,
            u'timestamp': firestore.SERVER_TIMESTAMP
        })
        return JSONResponse(content="Successfully confirmed swap", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to confirm swap: " + str(e))


@app.post("/cancelSwap")
async def confirmSwap(matchedUsers: List[str], uid: str = Depends(verify_auth)):
    try:
        matchedUser = None
        match_ref = db.collection(u'matches').document(
            GenerateId(matchedUsers[0], matchedUsers[1]))
        match = match_ref.get()
        match_dict = match.to_dict()
        if match.exists:
            matchedUser = GetMatchedUserInfo(match_dict["users"], uid)
        else:
            return JSONResponse(content="Match does not exist!", status_code=404)
        currentUser = match_dict["users"][uid]
        updatedCurrentUser = {
            **currentUser,
            u'isConfirmed': False,
            u'timestamp': firestore.SERVER_TIMESTAMP
        }
        updatedMatchedUsers = {
            uid: updatedCurrentUser,
            matchedUser["id"]: matchedUser
        }

        match_ref.update({
            u'users': updatedMatchedUsers,
            u'timestamp': firestore.SERVER_TIMESTAMP
        })
        return JSONResponse(content="Successfully canceled swap", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to cancel swap: " + str(e))


@app.get("/resetProfile")
async def resetProfile(uid: str = Depends(verify_auth)):
    try:
        db.collection("users").document(uid).update({
            "itemName": None,
            "location": None,
            "photoUrls": None,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "active": False
        })
        return JSONResponse(content="Successfully reset profile", status_code=204)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to reset profile: " + str(e))


@app.post("/storeDeviceToken")
async def storeDeviceToken(request: Request, uid: str = Depends(verify_auth)):
    try:
        token = await request.json()
        doc_ref = db.collection('users').document(uid)
        doc_snapshot = doc_ref.get()
        if doc_snapshot.exists and 'deviceToken' in doc_snapshot.to_dict():
            device_token = doc_snapshot.get('deviceToken')
            if device_token == token:
                return JSONResponse(content="Device token already saved.", status_code=200)
            else:
                doc_ref.update({
                    "deviceToken": token
                })
        else:
            doc_ref.set({
                "deviceToken": token
            }, merge=True)
        return JSONResponse(content="Successfully stored device token", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to store push token: " + str(e)
        )


@app.post("/sendPushNotification")
async def sendPushNotification(notification: NotificationObject, uid: str = Depends(verify_auth)):

    receiver_id = GetMatchedUserInfo(
        notification.matchDetails.users, uid)["id"]

    sender_name = notification.matchDetails.users[uid].displayName
    item_name = notification.matchDetails.users[uid].itemName

    doc_ref = db.collection("users").document(receiver_id)
    doc_snapshot = doc_ref.get().to_dict()
    if "deviceToken" in doc_snapshot:
        device_token = doc_snapshot["deviceToken"]
    else:
        return JSONResponse(content=f"Receiver {receiver_id} device token does not exist", status_code=400)
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

    push_client = PushClient()
    try:
        # Send the notification
        response = push_client.publish(
            PushMessage(to=device_token, data=data,
                        title=title, body=body)
        )
        compressed_response = {
            "status": response.status,
            "message": response.message
        }
        return JSONResponse(content=compressed_response, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to send notification: " + str(e)
        )


@app.post("/sendManyPushNotifications")
async def sendPushNotification(notifications: ManyNotificationsObject, uid: str = Depends(verify_auth)):
    push_client = PushClient()
    notified = []
    not_notified = []
    for notification in notifications.notifications:
        device_token = None
        notification_dict = notification.dict()
        receiver_id = notification_dict["receiverId"]
        sender = notification_dict["sender"]

        doc_ref = db.collection("users").document(
            receiver_id)
        doc_snapshot = doc_ref.get().to_dict()
        if "deviceToken" in doc_snapshot:
            device_token = doc_snapshot["deviceToken"]
        else:
            print(f"Receiver {receiver_id} device token does not exist")
            not_notified.append(receiver_id)
        if notifications.type == "delete":
            title = "Match Deleted"
            body = f"{sender} swapped with someone else :("
            data = {
                "type": notifications.type,
                "title": "Match Deleted",
                "text": f"{sender} swapped with someone else :("
            }
        try:
            # Send notifications
            if device_token:
                push_client.publish(
                    PushMessage(to=device_token, data=data,
                                title=title, body=body)
                )
                notified.append(receiver_id)
        except Exception as e:
            print(
                f"Failed to send notification for device token {device_token}: {str(e)}")
            notified.append(receiver_id)

    res = {
        "notified": notified,
        "failedToNotify": not_notified
    }
    return JSONResponse(content=res, status_code=200)


@app.post("/updateUserStatus")
async def updateUserStatus(request: Request, uid: str = Depends(verify_auth)):
    try:
        status = await request.json()
        user_ref = db.collection('users').document(uid)
        user = user_ref.get()
        if user.exists:
            if status == "offline":
                user_ref.set({
                    u"status": status,
                    u"lastOnline": firestore.SERVER_TIMESTAMP
                }, merge=True)
            else:
                user_ref.set({
                    u"status": status,
                }, merge=True)
        else:
            return JSONResponse(content="Failed to update status: user does not exist", status_code=400)
        return JSONResponse(content="Successfully updated status", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to update status: " + str(e)
        )

if __name__ == "__main__":
    uvicorn.run("main:app")
