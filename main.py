import uvicorn
import firebase_admin
import pyrebase
import json
from os import path
import logging

from firebase_admin import credentials, auth
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

# signup endpoint


@app.post("/signup", include_in_schema=False)
async def signup(request: Request):
    req = await request.json()
    email = req['email']
    password = req['password']
    if email is None or password is None:
        logger.warning("Request is missing email or password")
        return HTTPException(detail={'message': 'Error! Missing Email or Password'}, status_code=400)
    try:
        auth.create_user(
            email=email,
            password=password
        )
        return JSONResponse(content={'message': f'User successfully created.'}, status_code=200)
    except Exception as err:
        logger.error(str(err))
        return HTTPException(detail={'message': str(err)}, status_code=400)


# login endpoint
@app.post("/login", include_in_schema=False)
async def login(request: Request):
    req_json = await request.json()
    email = req_json['email']
    password = req_json['password']
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        return JSONResponse(content={'token': jwt}, status_code=200)
    except Exception as err:
        res = FormatFireBaseError(err)
        logger.error(res["message"])
        return HTTPException(detail={'message': res["message"]}, status_code=res["code"])


# ping endpoint
@app.post("/ping", include_in_schema=False)
async def validate(request: Request):
    headers = request.headers
    jwt = headers.get('authorization')
    print(f"jwt:{jwt}")
    user = auth.verify_id_token(jwt)
    return user["uid"]


if __name__ == "__main__":
    uvicorn.run("main:app")
