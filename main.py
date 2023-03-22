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

from utilities import format_firebase_doc, format_user_object, get_matched_user_info, delete_s3_folder
from helpers import UpdateProfilePicInChatMessages, get_search_prefs, get_logged_in_user, create_match, update_or_set_user_prefs, create_or_update_profile, delete_single_match, get_all_users_to_notify, check_match_exists, toggle_swap_confirmation, get_notification_type
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
version = "v1"


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


@app.get(f"/{version}/check_user_exists")
async def check_user_exists(uid: str = Depends(verify_auth)):
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


@app.get(f"/{version}/my_profile")
async def my_profile(uid: str = Depends(verify_auth)):
    try:
        doc_ref = db.collection(u'users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            data = format_firebase_doc(doc.to_dict())
            return JSONResponse(content=data, status_code=200)
        else:
            raise HTTPException(
                status_code=400, detail="Failed to fetch profile: Profile does not exist")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch profile: " + str(e))


@app.get(f"/{version}/get_search_preferences")
async def get_search_preferences(uid: str = Depends(verify_auth)):
    try:
        preferences = get_search_prefs(db, uid)
        return JSONResponse(content=preferences, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch search preferences: " + str(e))


@app.post(f"/{version}/update_location")
async def update_location(location: Location, uid: str = Depends(verify_auth)):
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


@app.post(f"/{version}/swipe_left")
async def swipe_left(userSwiped: UserObject, uid: str = Depends(verify_auth)):
    try:
        user_passed_dict = format_user_object(userSwiped)
        db.collection(u'users').document(uid).collection(
            u'passes').document(userSwiped.id).set(user_passed_dict)
        return JSONResponse(content="Successfully added Pass", status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Unable to pass user: " + str(e))


@app.post(f"/{version}/swipe_right")
async def swipe_right(userSwiped: SwipedUserObject, uid: str = Depends(verify_auth)):
    try:
        logged_in_user = get_logged_in_user(db, uid)
        user_swiped = format_user_object(userSwiped)

        # Check if user has already been swiped
        swipe_ref = db.collection(u'users').document(
            userSwiped.id).collection(u'swipes').document(uid)
        doc = swipe_ref.get()
        if doc.exists:
            create_match(db, uid, user_swiped, logged_in_user)
            return JSONResponse(content=logged_in_user, status_code=201)
        else:
            # User has swiped as first interaction with another user or no match :(
            db.collection(u'users').document(uid).collection(
                u'swipes').document(userSwiped.id).set(user_swiped)
            return JSONResponse(content="Successfully added Swipe", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Unable to swipe user: " + str(e))


@app.get(f"/{version}/get_search_radius")
async def get_search_radius(uid: str = Depends(verify_auth)):
    try:
        doc_ref = db.collection(u'users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            data = format_firebase_doc(doc.to_dict())
            radius = data["radius"]
            return JSONResponse(content=radius, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch search radius: " + str(e))


@app.post(f"/{version}/update_user_preferences")
async def update_user_preferences(prefs: UserPrefsObject, uid: str = Depends(verify_auth)):
    try:
        update_or_set_user_prefs(db, uid, prefs)
        if (prefs.photoKey != ""):
            UpdateProfilePicInChatMessages(db, uid, prefs.photoKey)

        return JSONResponse(content="Successfully updated user preferences", status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to update user preferences: " + str(e))


@app.post(f"/{version}/create_profile")
async def create_profile(profile: UserObject, uid: str = Depends(verify_auth)):
    try:
        res = create_or_update_profile(db, profile, uid)
        return JSONResponse(content=res, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to create/update profile: " + str(e))


@app.post(f"/{version}/delete_match")
async def delete_match(usersMatched: List[str], uid: str = Depends(verify_auth)):
    try:
        delete_single_match(db, s3_bucket, usersMatched)
        return JSONResponse(content="Successfully deleted match", status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to delete match: " + str(e))


@app.post(f"/{version}/delete_matches")
async def delete_matches(payload: DeleteMatchesObject, uid: str = Depends(verify_auth)):
    try:
        collection_ref = db.collection(u'matches')
        query = collection_ref.where(
            u'users.' + uid + '.itemName', u'==', payload.itemName)
        matches = [doc.to_dict() for doc in query.stream()]

        all_users_matched = []
        for match in matches:
            users_matched = match["usersMatched"]
            delete_single_match(db, s3_bucket, users_matched)

            all_users_matched.extend(users_matched)

            # Delete item images from S3
            delete_s3_folder(s3_bucket, f'public/profiles/{uid}/items')

        notifications_object = get_all_users_to_notify(
            uid, all_users_matched, payload)

        return JSONResponse(content=notifications_object, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to delete matches: " + str(e)
        )


@app.post(f"/{version}/send_message")
async def send_message(message: MessageObject, uid: str = Depends(verify_auth)):
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


@app.post(f"/{version}/confirm_swap")
async def confirm_swap(usersMatched: List[str], uid: str = Depends(verify_auth)):
    try:
        matched_user, match_dict, match_ref = check_match_exists(
            db, uid, usersMatched)
        if matched_user == None:
            return JSONResponse(content="Match does not exist!", status_code=404)

        toggle_swap_confirmation(
            match_ref, matched_user, match_dict, True, uid)
        return JSONResponse(content="Successfully confirmed swap", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to confirm swap: " + str(e))


@app.post(f"/{version}/cancel_swap")
async def cancel_swap(usersMatched: List[str], uid: str = Depends(verify_auth)):
    try:
        matched_user, match_dict, match_ref = check_match_exists(
            db, uid, usersMatched)
        if matched_user == None:
            return JSONResponse(content="Match does not exist!", status_code=404)

        toggle_swap_confirmation(
            match_ref, matched_user, match_dict, False, uid)
        return JSONResponse(content="Successfully canceled swap", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to cancel swap: " + str(e))


@app.get(f"/{version}/reset_profile")
async def reset_profile(uid: str = Depends(verify_auth)):
    try:
        db.collection("users").document(uid).update({
            "itemName": None,
            "location": None,
            "photoUrls": None,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "active": False
        })
        return JSONResponse(content="Successfully reset profile", status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to reset profile: " + str(e))


@app.post(f"/{version}/store_device_token")
async def store_device_token(request: Request, uid: str = Depends(verify_auth)):
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


@app.post(f"/{version}/send_push_notification")
async def send_push_notification(notification: NotificationObject, uid: str = Depends(verify_auth)):

    receiver_id = get_matched_user_info(
        notification.matchDetails.users, uid)["id"]

    doc_ref = db.collection("users").document(receiver_id)
    doc_snapshot = doc_ref.get().to_dict()
    if "deviceToken" in doc_snapshot:
        device_token = doc_snapshot["deviceToken"]
    else:
        return JSONResponse(content=f"Receiver {receiver_id} device token does not exist", status_code=400)
    title, body, data = get_notification_type(notification, uid)
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


@app.post(f"/{version}/send_many_push_notifications")
async def send_many_push_notifications(notifications: ManyNotificationsObject, uid: str = Depends(verify_auth)):
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


@app.post(f"/{version}/update_user_status")
async def update_user_status(request: Request, uid: str = Depends(verify_auth)):
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
