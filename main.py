import uvicorn
import pyrebase
from fastapi import FastAPI
from models import *
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
import firebase_admin
from firebase_admin import credentials,auth


app = FastAPI(
    description="Test app",
    title="EarthLinksSB",
    docs_url="/"
)


if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

firebaseConfig = {
  "apiKey": "AIzaSyBFV0RkPrt5jJmIhvVdRl_oCdVWXLtlGsg",
  "authDomain": "earthlinks-7c491.firebaseapp.com",
  "projectId": "earthlinks-7c491",
  "storageBucket": "earthlinks-7c491.appspot.com",
  "messagingSenderId": "699164993677",
  "appId": "1:699164993677:web:2b01a53426ec0386c09ac4",
  "measurementId": "G-V17GM0DBC0",
  "databaseURL": "https://earthlinks-7c491-default-rtdb.firebaseio.com/"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()


# post method for creating new account
@app.post('/signup')
async def create_account(user_data:SignUpSchema):
    email = user_data.email
    password = user_data.password

    try:
        user = auth.create_user(
            email = email,
            password = password
        )


        data = {"UID" : user.uid, "username": user.uid, "bio": "", "profile_picture": "gs://earthlinks-7c491.appspot.com/person-24px.xml"}
        db_result = db.child("users").push(data)


        return JSONResponse(content={"message": f"User account created succesfully for user {user.uid}"},
                            status_code= 201)

    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=400,
            detail=f"Account already created for the email {email}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


#post for creating access token for user login
@app.post('/login')
async def create_access_token(user_data:LoginSchema):
    email = user_data.email
    password = user_data.password

    try:
        user = firebase.auth().sign_in_with_email_and_password(
            email=email,
            password = password
        )

        token = user['idToken']

        return JSONResponse(
            content={
                "token":token
            }, status_code=200
        )
    except:
        raise HTTPException(
            status_code=400,
            detail="Invalid email/password"
        )

#post for validdting the token before logging in
#request: the 
@app.post('/ping')
async def validate_token(request:Request):
    headers = request.headers
    jwt = headers.get('authorization')

    user = auth.verify_id_token(jwt)

    return user["user_id"]



@app.post('/message')
async def post_message(message_data:MessageSchema):

    data = message_data.dict()
    data['timestamp'] = data['timestamp'].isoformat()  # Convert datetime to string for Firebase

    try:
        result = db.child("messages").push(data)


        return JSONResponse(content ={"message": "Message posted successfully", 
                                      "message_id": result["name"]},
                            status_code = 200)
    
    except db.TransactionAbortedError:
        raise HTTPException(
            status_code = 400,
            detail="Failed to store message"
        )
    

#request to get all users
@app.get("/getUsers")
async def get_users():
    data = db.child("users").get()
    return JSONResponse(content = {data},
                        status_code = 200)



#retrieve user information by their UID
@app.get("/getUser/{user_uid}")
async def get_user_by_uid(user_uid: str):
    user = db.child("users").order_by_child("UID").equal_to(user_uid).get()
    return JSONResponse(user.pyres[0].item[1], status_code = 200)



#testing getting data from database
@app.get("/getAllMessages")
async def get__all_messages():
    data = db.child("messages").get().val()
    return JSONResponse(content=data, status_code = 200)

@app.get("/getMessagesByRadius")
async def get_messages_by_radius():
    return

if __name__ == "__main__":
    uvicorn.run("main:app",reload=True)


