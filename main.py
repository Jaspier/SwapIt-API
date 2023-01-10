import uvicorn
import firebase_admin
import pyrebase
import json
from os import path
import logging

from firebase_admin import credentials, auth, firestore
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from utilities import FormatFireBaseError

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
async def getProfiles(user: str = ""):
    doc_ref = db.collection(u'users').document(user)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return 'No such document!'


if __name__ == "__main__":
    uvicorn.run("main:app")
