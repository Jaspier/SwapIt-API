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

from utilities import FormatFireBaseError, FormatFireBaseDoc
from models import Location

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


@app.get("/getSearchPref")
async def getSearchPref(uid: str = Depends(verify_auth)):
    try:
        doc_ref = db.collection(u'users').document(uid)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            prefs = {
                "coords": data['coords'],
                "radius": data['radius']
            }
            return JSONResponse(content=prefs, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to fetch search preferences: " + str(e))


@app.post("/updateLocation")
async def updateLocation(location: Location, uid: str = Depends(verify_auth)):
    try:
        city_ref = db.collection(u'users').document(uid)
        updated_data = {
            **location.dict(),
            u'timestamp': firestore.SERVER_TIMESTAMP
        }
        city_ref.update(updated_data)
        return JSONResponse(content="Successfully updated location", status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Failed to update location: " + str(e))

if __name__ == "__main__":
    uvicorn.run("main:app")
