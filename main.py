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

from utilities import FormatFireBaseDoc, FormatUserObject, GenerateId
from models import Location, UserObject, UserPrefsObject

LOGGING_CONFIG_FILE = path.join(path.dirname(
    path.abspath(__file__)), 'logging.conf')
logging.config.fileConfig(LOGGING_CONFIG_FILE)
logger = logging.getLogger('SwapIt')

cred = credentials.Certificate('swapit-5eb81_service_account_keys.json')
firebase = firebase_admin.initialize_app(cred)
db = firestore.client()
pb = pyrebase.initialize_app(json.load(open('firebase_config.json')))
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
async def log_stuff(request: Request, call_next):
    logger.debug(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.debug(response)
    logger.debug(response.status_code)
    print(f"INCOMING REQUEST - {request.url} {response.status_code}")
    return response

# ping endpoint


@app.post("/ping", include_in_schema=False)
async def validate(request: Request):
    headers = request.headers
    jwt = headers.get('authorization')
    print(f"jwt:{jwt}")
    user = auth.verify_id_token(jwt)
    return user["uid"]


@app.get("/checkUserExists")
async def checkUserExists(uid: str = Depends(verify_auth)):
    try:
        user_ref = db.collection(u'users').document(uid)
        user = user_ref.get()
        if user.exists:
            return JSONResponse(content="User exists", status_code=200)
        else:
            raise HTTPException(
                status_code=404, detail="User does not exist: " + str(e))
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
async def swipeRight(userSwiped: UserObject, uid: str = Depends(verify_auth)):
    try:
        logged_in_user_dict = None
        loggedInUser_ref = db.collection(u'users').document(uid)
        doc = loggedInUser_ref.get()
        if doc.exists:
            logged_in_user_dict = FormatFireBaseDoc(doc.to_dict())
        else:
            raise HTTPException(
                status_code=400, detail="User does not exist: " + str(e))

        # Check if user swiped on 'you' (TODO: Migrate to cloud function)
        swipe_ref = db.collection(u'users').document(
            userSwiped.id).collection(u'swipes').document(uid)
        doc = swipe_ref.get()
        user_swiped_dict = FormatUserObject(userSwiped)
        if doc.exists:
            db.collection(u'users').document(uid).collection(
                u'swipes').document(userSwiped.id).set(user_swiped_dict)

            # Create MATCH
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


@app.post("/updateUserPrefs")
async def updateUserDetails(userDetails: UserPrefsObject, uid: str = Depends(verify_auth)):
    try:
        auth.update_user(
            uid,
            display_name=userDetails.displayName,
            photo_url=userDetails.photoURL)
        user_ref = db.collection(u'users').document(uid)
        user = user_ref.get()
        if user.exists:
            prefs_ref = db.collection(u'users').document(uid)
            prefs_ref.update({
                u'displayName': userDetails.displayName,
                u'radius': userDetails.radius,
                u'timestamp': firestore.SERVER_TIMESTAMP
            })
        else:
            db.collection(u'users').document(uid).set({
                u'id': uid,
                u'displayName': userDetails.displayName,
                u'radius': userDetails.radius,
                u'timestamp': firestore.SERVER_TIMESTAMP
            })
        return JSONResponse(content="Successfully updated user preferences", status_code=204)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to update user preferences: " + str(e))


@app.get("/removeProfilePic")
async def removeProfilePic(uid: str = Depends(verify_auth)):
    try:
        auth.update_user(
            uid,
            photo_url="")
        return JSONResponse(content="Successfully removed profile picture", status_code=204)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to remove profile picture: " + str(e))

if __name__ == "__main__":
    uvicorn.run("main:app")


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
